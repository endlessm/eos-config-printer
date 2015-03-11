#!/usr/bin/python3
#
# pkgvalidator.py
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
import gnupg
import hashlib
import os
import re
import shutil
import utils

from gi.repository import GLib

from debug import *


class PackageValidator:
    """
    Class that allows validating a debian package based on its full URL and the
    fingerprint of the GPG public key used to sign the source APT repository.
    """
    def __init__(self, uri, fingerprint, temporary_dir=config.TEMPORARY_DIR):
        self._uri = uri
        self._fingerprint = fingerprint
        self._temporary_dir = temporary_dir

        # Build needed URIs based on the package's full URI.
        self._release_file_uri = self._getReleaseFileURI()
        self._release_gpg_uri = self._release_file_uri + '.gpg'
        self._packages_file_uri = os.path.join(os.path.dirname(self._uri), 'Packages')

        # We need to make sure the directory for the the trusted.gpg
        # file exists before starting to use GPG.
        keyring_basedir = os.path.dirname(config.TRUSTED_KEYRING_FILE)
        os.makedirs(keyring_basedir, exist_ok=True)
        self._gpg = gnupg.GPG(keyring=config.TRUSTED_KEYRING_FILE)
        self._gpg.encoding = 'utf-8'

    def run(self, localfile=None):
        """
        Run the checks required to validate the debian package, downloading the
        package from the URI specified in the constructor, unless an absolute path
        to an already present local file is provided via the localfile parameter.

        Return True if the debian package could be validated, or False otherwise.
        """
        # If no local file has been specified, we download it from
        # the URI provided and check if it's valid from there.
        with_localfile = localfile is not None
        if not with_localfile:
            localfile = utils.downloadToTemporaryFile(self._uri)

        release_file_path = utils.downloadToTemporaryFile(self._release_file_uri, self._temporary_dir)
        release_gpg_path = utils.downloadToTemporaryFile(self._release_gpg_uri, self._temporary_dir)
        packages_file_path = utils.downloadToTemporaryFile(self._packages_file_uri, self._temporary_dir)

        self._importKeyIfNeeded(self._fingerprint)
        verified = self._verifySignature(release_gpg_path, release_file_path)

        result = verified and \
               self._findHashForFile(release_file_path, packages_file_path, hashlib.sha256) and \
               self._findHashForFile(packages_file_path, localfile, hashlib.sha1)

        os.remove(packages_file_path)
        os.remove(release_gpg_path)
        os.remove(release_file_path)
        if not with_localfile:
            os.remove(localfile)

        return result

    def _getReleaseFileURI(self, suffix=None):
        try:
            archive_root_index = self._uri.index('dists')
        except ValueError:
            debugprint("Could not find repository root for %s" %self._uri)
            return ''

        # URI is something like "$archive_root/dists/$distribution/",
        # so we need to look for the first '/' after (root_index + 6)
        # to be able to find the base URL of the distribution.
        try:
            dist_index = self._uri.find('/', archive_root_index + 6)
        except ValueError:
            debugprint("Could not find distribution base URL for %s" %self._uri)
            return ''

        return os.path.join(self._uri[:dist_index], 'Release')

    def _importKeyIfNeeded(self, key):
        keys = self._gpg.list_keys()
        for fp in keys.fingerprints:
            if fp == key:
                debugprint("Key %s found in local keyring" % fp)
                return
        self._gpg.recv_keys(config.TRUSTED_KEY_SERVER, key)

    def _verifySignature(self, signature_path, signed_path):
        signature_bfile = open(signature_path, 'rb')
        verified = self._gpg.verify_file(signature_bfile, signed_path)
        signature_bfile.close()

        if verified.trust_level is not None:
            debugprint("%s verified with signature %s" %
                       (os.path.basename(signed_path),
                        os.path.basename(signature_path)))
            return True

        debugprint("%s could NOT be verified with signature %s" %
                   (os.path.basename(signed_path),
                    os.path.basename(signature_path)))
        return False

    def _findHashForFile(self, haystack_path, needle_path, hash_func):
        needle_bfile = open(needle_path, 'rb')
        needle_hash = hash_func(needle_bfile.read())
        needle_hash_str = needle_hash.hexdigest()
        needle_bfile.close()

        debugprint("Hash %s for %s: %s" % (needle_hash.name, needle_path, needle_hash_str))

        found = False
        haystack_file = open(haystack_path, 'r')
        for line in haystack_file:
            if re.search(needle_hash_str, line):
                found = True
                break
        haystack_file.close()

        debugprint("%s hash %sfound in %s" % (os.path.basename(needle_path),
                                              ("" if found else "NOT "),
                                              os.path.basename(haystack_path)))
        return found


if __name__== "__main__":
    # Values meant just for debugging purposes.
    TEST_URL='http://www.openprinting.org/download/printdriver/debian/dists/lsb3.2/main/binary-amd64/openprinting-ppds-postscript-brother_20130226-1lsb3.2_all.deb'
    TEST_KEY='F8897B6F00075648E248B7EC24CBF5474CFD1E2F'
    set_debugging(True)

    # By default every temporary file will be downloaded to config.TEMPORARY_DIR.
    shutil.rmtree(config.TEMPORARY_DIR, ignore_errors=True)
    os.makedirs(config.TEMPORARY_DIR, exist_ok=True)

    validator = PackageValidator(TEST_URL, TEST_KEY)

    try:
        debugprint("Validating package without specifying a local file...")
        if validator.run():
            debugprint("OK")
        else:
            debugprint("FAIL")
    except GLib.GError as e:
        debugprint("EXCEPTION: %s)" % repr(e))

    try:
        debpkg_path = utils.downloadToTemporaryFile(TEST_URL)
        debugprint("Validating package specifying a local file in %s..." % debpkg_path)
        if validator.run(localfile=debpkg_path):
            debugprint("OK")
        else:
            debugprint("FAIL")
        os.remove(debpkg_path)
    except GLib.GError as e:
        debugprint("EXCEPTION: %s)" % repr(e))

    shutil.rmtree(config.TEMPORARY_DIR, ignore_errors=True)
