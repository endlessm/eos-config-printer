# eos-config-printer
D-Bus service for installing printer drivers

## Description

eos-config-service provides a D-Bus activatable service to install
printer drivers in EOS providing the type of driver (an integer)
and a variable list of arguments (depending on the driver type).

At the moment, only drivers coming from OpenPrinting.org and packaged
as debian files are supported, so the required parameters to install
those will be the following ones:

  * Type, always set to 1 for now (meaning 'OpenPrinting drivers')
  * A list of two elements:
    * URI to know where to download the package from (an APT repository)
    * Fingerprint of the GPG public key used to sign the APT repository

The InstallDriver service will receive those parameters and, after
checking that the needed Polkit policies are satisfied for the current
user (should belong to 'lpadmin' group), will proceed with the
installation in N different stages:

  1. Download the .deb package pointed by URI to a temporary location
  2. Validate the package with the GPG-based signature of its repository
  3. Extract the contents of the .deb package to a temporary location
  4. Move the extracted files to their intented location, under '/opt'
  5. Create the symlinks from '/var/lib/cups/ppd/eos-config-printer/',
     pointing to '/opt/<driver-package>/', so that CUPS can find them
  6. On succesful completion, notify the calling process passing a
     list of the absolute paths to the installed PPD files
  7. On error, report the error via a GError with a descriptive message

Last, a symlink pointing from '/usr/share/ppd/eos-config-printer/' to
'/var/lib/cups/ppd/eos-config-printer/' is required for CUPS to be
able to find the installed PPD files without requiring additional
configuration. In EOS, we create this symlink as part of the
installation of the CUPS package, but

## License

eos-config-printer is Copyright (C) 2015 Endless Mobile, Inc. and
is licensed under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of
the License, or (at your option) any later version.

Additionally, the following components from system-config-printer,
licensed under the same license GNU General Public License with
Copyright (C) 2006 - 2015 Red Hat, Inc., were reused:
  * debug.py is Copyright (C) 2008, 2010 Red Hat, Inc.
  * killtimer.py is Copyright (C) 2010, 2011, 2012, 2013, 2014 Red Hat, Inc.

See the COPYING file for the full version of the GNU GPLv2 license
