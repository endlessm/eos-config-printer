#!/usr/bin/python3
#
# config.py
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

# Used for validating packages from signed repositories
TRUSTED_KEYRING_FILE='/var/lib/eos-config-printer/trusted.gpg'
TRUSTED_KEY_SERVER='keyserver.ubuntu.com'

# Directory where CUPS will look for PPD files installed through this service
CUPS_VISIBLE_PPD_DIR = '/var/lib/cups/ppd/eos-config-printer'

# Directory used by default for downloading temporary files
TEMPORARY_DIR = '/tmp/eos-config-printer'
