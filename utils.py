#!/usr/bin/python3
#
# utils.py
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
import os
import tempfile
import urllib.request

from gi.repository import GLib
from urllib.error import URLError

from debug import *


def downloadToTemporaryFile(uri, dest_dir=config.TEMPORARY_DIR):
    """
    Download a file from the given URI and stores it in a temporary file under @dest_dir.

    Return the path of the temporary file being stored, or None otherwise.
    """
    debugprint("Downloading file from %s..." % uri)
    try:
        url_obj = urllib.request.urlopen(uri)
        content = url_obj.read()
        url_obj.close()
    except ValueError:
        raise GLib.GError("%s is not a recognized URI" % uri)
    except URLError as e:
        raise GLib.GError("Error downloading file %s: %s" % (uri, repr(e.reason)))

    try:
        (tmpfd, filepath) = tempfile.mkstemp(dir=dest_dir)
    except OSError as e:
        raise GLib.GError("Temporary file could not be created: %s" % repr(e))

    debugprint("Storing file in %s..." % filepath)
    try:
        file_obj = os.fdopen(tmpfd, 'wb')
        file_obj.write(content)
        file_obj.close()
    except OSError as e:
        raise GLib.GError("File could not be opened: %s" % repr(e))

    return filepath

