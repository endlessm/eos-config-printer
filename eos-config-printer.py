#!/usr/bin/python3
#
# eos-config-printer.py
#
# Copyright (C) 2015 Endless Mobile, Inc.
# Authors:
#  Mario Sanchez Prada <mario@endlessm.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import config
import dbus.exceptions
import dbus.service
import killtimer
import os
import pkgvalidator
import shutil
import subprocess
import tempfile
import threading
import time
import utils

from gi.repository import GLib
from gi.repository import Polkit

from debug import *

CONFIG_PRINTING_BUS = 'com.endlessm.Config.Printing'
CONFIG_PRINTING_PATH = '/com/endlessm/Config/Printing'
CONFIG_PRINTING_IFACE = 'com.endlessm.Config.Printing'


class PrinterDriver:
    """
    General class representing a printer driver that can be installed
    and which we can ask for a list of installed PPD files to.
    """
    def __init__(self, name):
        self._name = name

    def install(self):
        debugprint("Installing printer driver '%s'..." % self._name)

    def getInstalledPPDFiles(self):
        return []


class PrinterDriverOpenPrinting(PrinterDriver):
    """
    Subclass of PrinterDriver, represents a type of driver that will be
    retrieved from OpenPrinting.org, and which follows a certain structure.
    """
    def __init__(self, args):
        super().__init__("OpenPrinting")

        if not args or 'uri' not in args:
            raise TypeError("Can't find the URI parameter in %s" % repr(args))
        self._uri = args['uri']

        self._fingerprint = None
        if 'fingerprint' in args:
            self._fingerprint = args['fingerprint']

        self._installedPPDs = []
        self._temporary_dir = None

    def install(self):
        """
        Install a printer driver in the system by downloading it from
        OpenPrinting.org, extracting its contents and making it available
        to CUPS by placing it under a path reachable from /usr/share/ppd.
        """
        super().install()

        try:
            self._ensureTemporaryDir()
            self._doInstall()
        except Exception as e:
            raise e
        finally:
            self._cleanupTemporaryFiles()

    def _doInstall(self):
        # Try to download the file pointed by the URI and validate it.
        # If any of these operations fails an GLib.GError exception
        # will be raised and handled by the run() function.
        filepath = utils.downloadToTemporaryFile(self._uri, self._temporary_dir)

        # If no GPG fingerpring is provided, the package is considered to
        # be 'trusted' (e.g. client checked it does not contain binaries)
        if self._fingerprint is not None:
            validator = pkgvalidator.PackageValidator(self._uri, self._fingerprint,
                                                      temporary_dir=self._temporary_dir)
            if not validator.run(localfile=filepath):
                raise GLib.GError("The package file could not be validated")

        # Now that the package has been downloaded and validated, extract
        # it to a temporary directory and begin its installation.
        extraction_dir = os.path.join(self._temporary_dir, 'extract')
        self._extractDriverPackage(filepath, extraction_dir)
        try:
            os.remove(filepath)
        except OSError as e:
            raise GLib.GError("Error removing file %s" % repr(e))

        # For the purpose of this script, assume drivers from OpenPrinting will
        # always be installed under '/opt' so bail out early if not the case.
        try:
            dircontents = os.listdir(extraction_dir)
        except OSError as e:
            raise GLib.GError("Error listing contents of directory: %s" % repr(e))

        if len(dircontents) != 1 or dircontents[0] != 'opt':
            raise GLib.GError("Driver packages not meant to be installed "
                              "inside the /opt directory are not currently "
                              "supported")

        # Move the driver into the desired location, search for the directory
        # containing the PPD files and create symlinks pointing there from the
        # /var/lib/eos-config-printer/ppd  directory, so that CUPS can find them.
        # Also, fill the self._installedPPDs list to report to the caller.
        moved_dirs = self._deployDriverDirectories(extraction_dir)
        self._installedPPDs = []
        for path in moved_dirs:
            debugprint("Searching for the directory containing PPD files")
            ppd_files = self._searchForPPDFiles(path)
            if ppd_files:
                ppd_dirs = list(set([os.path.dirname(f) for f in ppd_files]))
                debugprint("Found %d PPD directory(s)" % len(ppd_dirs))
                self._createSymlinksForCUPS(ppd_dirs)
            self._installedPPDs.extend(ppd_files)

    def _ensureTemporaryDir(self):
        if os.path.exists(config.TEMPORARY_DIR):
            try:
                # Make sure there are no leftovers from previous installation attempts.
                dircontents = os.listdir(config.TEMPORARY_DIR)
                for path in dircontents:
                    abs_path = os.path.join(config.TEMPORARY_DIR, path)
                    shutil.rmtree(abs_path, ignore_errors=True)
            except OSError as e:
                raise GLib.GError("Error listing contents of directory: %s" % repr(e))
        else:
            os.makedirs(config.TEMPORARY_DIR, exist_ok=True)

        try:
            self._temporary_dir = tempfile.mkdtemp(dir=config.TEMPORARY_DIR)
            debugprint("Created temporary directory in %s" % self._temporary_dir)
        except OSError as e:
            self._temporary_dir = None
            raise GLib.GError("Temporary directory could not be created: %s" % repr(e))

    def _cleanupTemporaryFiles(self):
        if self._temporary_dir:
            shutil.rmtree(self._temporary_dir, ignore_errors=True)
            debugprint("Removed temporary directory from %s" % self._temporary_dir)
        self._temporary_dir = None

    def getInstalledPPDFiles(self):
        """
        Return the list of installed PPD files for this driver, or an
        empty list if no file has been installed.
        """
        return self._installedPPDs

    def _extractDriverPackage(self, driver_path, dest_dir):
        """
        Extracts the content of a driver package (always a debian package for now),
        pointed by driver_path, and places the result under dest_dir.
        """
        # FIXME: We could use the python-debian module, but for now just executing
        # 'dpkg -x' is probably enough, as we are treating .deb files as simple
        # 'tarballs', and we avoid pulling an extra dependency just for this task.
        args = ['dpkg', '-x', driver_path, dest_dir]
        new_environ = os.environ.copy()
        new_environ['LC_ALL'] = 'C'
        debugprint("Extracting contents for file %s into %s..." % (driver_path,
                                                                   dest_dir))
        try:
            process = subprocess.Popen(args, env=new_environ, close_fds=True,
                                       stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            process.wait()

            if process.returncode != 0:
                raise GLib.GError("Error extracting the contents of %s" % driver_path)
        except:
            raise GLib.GError("An error has occurred executing %s" % repr(args))

    def _deployDriverDirectories(self, extraction_dir):
        """
        Move all the directories related to one driver from extraction_dir into
        their definite location, under '/opt'.

        Returns a list with the full path of the directories moved.
        """
        extracted_opt_dir = os.path.join(extraction_dir, 'opt')
        try:
            dircontents = os.listdir(extracted_opt_dir)
        except OSError as e:
            raise GLib.GError("Error listing contents of directory: %s" % repr(e))

        copied_dirs = []
        for path in dircontents:
            debugprint("Driver package found: %s" % path)
            src = os.path.join(extracted_opt_dir, path)
            dest = os.path.join('/opt', path)

            if os.path.exists(dest):
                shutil.rmtree(dest, ignore_errors=True)

            try:
                debugprint("Copying %s into %s..." % (src, dest))
                shutil.copytree(src, dest, symlinks=True)
                copied_dirs.append(dest)

            except shutil.Error as e:
                raise GLib.GError("Error copying the files from %s into %s: %s"
                                                % (src, dest, repr(e)))

        return copied_dirs

    def _searchForPPDFiles(self, base_dir):
        """
        Looks for directories containing PPD files, and the paths to each of
        those files, inside of the path referenced by base_dir.

        Return a list of paths to the installed PPDs, or an empty list otherwise.
        """
        result = []
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                file_l = file.lower()
                if file_l.endswith('.ppd') or file_l.endswith('.ppd.gz'):
                    ppd_file_path = os.path.join(root, file)
                    result.append(ppd_file_path)
                    debugprint("PPD file found!: %s" % ppd_file_path)

        debugprint("Found %d PPD file(s)" % len(result))
        return result

    def _createSymlinksForCUPS(self, ppd_dirs):
        """
        Creates a symlink to every path in ppd_dirs from a CUPS visible directory.
        """
        # First of all, ensure the CUPS visible directory is created.
        os.makedirs(config.CUPS_VISIBLE_PPD_DIR, exist_ok=True)

        for path in ppd_dirs:
            # Sanity check.
            if not path.startswith('/opt'):
                continue

            # First we need to create an unique name for the symlink, and we do
            # that by ignoring the '/opt' preffix and replacing '/' with '_'.
            symlink_name = path[5:].replace('/', '_')

            symlink_path = os.path.join(config.CUPS_VISIBLE_PPD_DIR, symlink_name)
            if os.path.exists(symlink_path):
                os.unlink(symlink_path)

            os.symlink(path, symlink_path)
            debugprint("Symlink created: %s -> %s" % (symlink_path, path))


class ConfigPrintingService(dbus.service.Object):
    """
    Class representing a D-Bus service offering a method to install
    printer drivers in Endless OS.
    """
    # We only support drivers from OpenPrinting.org for now.
    DriverTypeOpenPrinting = 1

    def __init__(self):
        self.bus = dbus.SystemBus()
        bus_name = dbus.service.BusName(CONFIG_PRINTING_BUS, bus=self.bus)
        super().__init__(bus_name, CONFIG_PRINTING_PATH)
        self._polkit_authority = None
        self._killtimer = None
        self._driver = None
        self._loop = None

    def start(self):
        """
        Starts the D-Bus service, which will remain running 30 seconds after
        having finished dispatching the last request.
        """
        if self._loop is None:
            self._loop = GLib.MainLoop()

        if self._loop.is_running():
            debugprint("Service already running. Nothing to do")
            return

        self._killtimer = killtimer.KillTimer(killfunc=self.stop)
        self._loop.run()

    def stop(self):
        """
        Stops the D-Bus service.
        """
        if self._loop is None or not self._loop.is_running():
            debugprint("Service not running. Nothing to do")
            return

        self._loop.quit()

    @dbus.service.method(dbus_interface=CONFIG_PRINTING_IFACE,
                         in_signature='ua{ss}', out_signature='as',
                         sender_keyword='sender',
                         async_callbacks=('reply_cb', 'error_cb'))
    def InstallDriver(self, type_, args, reply_cb, error_cb, sender=None):
        """
        Installs a Printer driver by type_ and uri in a separate thread,
        invoking reply_cb or error_cb when done.

        Note: The only supported type for now is '1' ("OpenPrinting driver").
        """
        thread = threading.Thread(target=self._installDriverThreadFunc,
                                  kwargs={ 'type_': type_,
                                           'args': args,
                                           'reply_cb': reply_cb,
                                           'error_cb': error_cb,
                                           'sender' : sender })
        self._killtimer.add_hold()
        thread.start()

    def _installDriverThreadFunc(self, type_, args, reply_cb, error_cb, sender):
        """
        Worker function to be executed in a separate thread to install the driver.
        """
        # Check Polkit authorization policies.
        try:
            authorized = self._methodIsAuthorized('InstallDriver', sender)
        except GLib.GError as e:
            self._reportError(error_cb, GLib.GError("Error checking authorization: %s" % repr(e)))
            return

        if not authorized:
            self._reportError(error_cb, GLib.GError("Method not authorized"))
            return

        # Check driver type.
        if not self._driversIsSupported(type_):
            self._reportError(error_cb, GLib.GError("Unsupported driver type: %d" % type_))
            return

        try:
            # Only OpenPrinting supported for now.
            self._driver = PrinterDriverOpenPrinting(args)
            self._driver.install()
        except TypeError as e:
            self._reportError(error_cb, GLib.GError("Error initializing driver installer: %s" % repr(e)))
            return
        except GLib.GError as e:
            self._reportError(error_cb, GLib.GError("Error installing printer driver: %s" % repr(e)))
            return

        # All good, let the caller know that.
        self._reportSuccess(reply_cb)

    def _methodIsAuthorized(self, method_name, sender):
        """
        Return True if the method is authorized by PolicyKit, or False otherwise.
        """
        debugprint("Checking authorization for method %s and sender %s" %
                   (method_name, sender))

        # Lazy initialization of the Polkit authority object.
        if self._polkit_authority is None:
            self._polkit_authority = Polkit.Authority.get_sync(None)

        auth_result = None
        subject = Polkit.SystemBusName.new(sender)
        action_id = ".".join([CONFIG_PRINTING_IFACE, method_name])

        auth_result = self._polkit_authority.check_authorization_sync(subject, action_id, None,
                                                                      Polkit.CheckAuthorizationFlags.NONE,
                                                                      None)
        if auth_result is None:
            return False

        retval = auth_result.get_is_authorized()
        debugprint("Method is %sAUTHORIZED" % ("" if retval else "NOT "))
        return retval

    def _driversIsSupported(self, type_):
        """
        Return True if the driver type_ is supported, or False otherwise.
        """
        # Only OpenPrinting drivers supported for now.
        return type_ == self.DriverTypeOpenPrinting

    def _reportError(self, error_cb, error_data):
        """
        Call error_cb passing error_data as parameter, and restores the timer
        that will kill this D-Bus service after 30 seconds if not invoked again.
        """
        debugprint("Reporting error to caller process: %s" % repr(error_data))
        error_cb(error_data)
        self._killtimer.remove_hold()

    def _reportSuccess(self, reply_cb):
        """
        Call reply_cb passing the list of installed PPD files as parameter,
        and restores the timer that will kill this D-Bus service after 30 seconds
        if not invoked again.
        """
        installed_PPDs = self._driver.getInstalledPPDFiles()
        reply_cb(installed_PPDs)
        debugprint("Reporting success to caller process. Installed files: %s"
                   % installed_PPDs)
        self._killtimer.remove_hold()


class ConfigPrintingClient:
    """
    Class representing a D-Bus client meant to be used for testing.

    This class expects a list of arguments in its constructor, with the list of
    parameters needed to determine type and source URI of the printer driver.
    """
    def __init__(self, args):
        self._args = args
        self._loop = None

    def start(self):
        if not self._args or len(self._args) < 2:
            print("Error: Mising printer driver Type, URI and fingerprint (optional)")
            return

        type_ = int(self._args[0])
        args = { 'uri': self._args[1] }
        if len(self._args) > 2:
            args['fingerprint'] = self._args[2]

        debugprint("Running client for type %d and args %s..." % (type_, args))

        bus = dbus.SystemBus()
        obj = bus.get_object(CONFIG_PRINTING_BUS, CONFIG_PRINTING_PATH)

        try:
            debugprint("Executing remote method from client...")
            obj.InstallDriver(type_, args,
                              dbus_interface=CONFIG_PRINTING_IFACE,
                              reply_handler=self._installDriverReplyCb,
                              error_handler=self._installDriverErrorCb,
                              timeout=GLib.MAXINT32/1000)
        except dbus.exceptions.DBusException as e:
            debugprint("Unable to execute remote method: %s" % e.get_dbus_message())

        self._loop = GLib.MainLoop()
        self._loop.run()

    def stop(self):
        self._loop.quit()

    def _installDriverReplyCb(self, reply):
        debugprint("Remote method successfully executed. Installed PPD files: %s"
                   % reply)
        self.stop()

    def _installDriverErrorCb(self, error):
        debugprint("Error executing remote method: %s" % repr(error))
        self.stop()


if __name__ == '__main__':
    import getopt

    from dbus.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)

    run_client = False
    try:
        optlist, args = getopt.getopt(sys.argv[1:], [], ['debug', 'client'])
    except getopt.GetoptError as e:
        print("Error parsing command line: %s" % e)
        sys.exit(2)

    for opt, optval in optlist:
        if opt == '--debug':
            set_debugging(True)
        elif opt == '--client':
            run_client = True

    if run_client:
        client = ConfigPrintingClient(args)
        client.start()
        sys.exit(0)

    debugprint("Service running...")
    service = ConfigPrintingService()
    service.start()
    debugprint("Service stopping...")
