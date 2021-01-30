#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Univention Helper functions for creating or renaming share directories
"""
# Copyright 2011-2021 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

import os
import pipes
import sys
import fnmatch
import shutil
from functools import reduce
from typing import Dict, List, Optional  # noqa F401

if sys.version_info >= (3,):
	from subprocess import getstatusoutput
else:
	from commands import getstatusoutput

from univention.config_registry import ConfigRegistry


DEFAULT_FS = "ext2/ext3:ext2:ext3:ext4:xfs:btrfs"
DIR_BLACKLIST = []
DIR_BLACKLIST.append("/bin")
DIR_BLACKLIST.append("/boot")
DIR_BLACKLIST.append("/dev")
DIR_BLACKLIST.append("/etc")
DIR_BLACKLIST.append("/lib")
DIR_BLACKLIST.append("/lib64")
DIR_BLACKLIST.append("/proc")
DIR_BLACKLIST.append("/root")
DIR_BLACKLIST.append("/sbin")
DIR_BLACKLIST.append("/sys")
DIR_BLACKLIST.append("/tmp")
DIR_BLACKLIST.append("/usr")
DIR_BLACKLIST.append("/var")
# whitelisted via UCR by default
DIR_BLACKLIST.append("/home")
DIR_BLACKLIST.append("/media")
DIR_BLACKLIST.append("/mnt")
DIR_BLACKLIST.append("/opt")
DIR_BLACKLIST.append("/run")
DIR_BLACKLIST.append("/srv")


def dirIsMountPoint(path):
	# type: (str) -> Optional[str]
	"""
	Check if `path` is a mount point.

	:param str path: The path to check.
	:returns: A string if the path is a mount point, `None` otherwise.
	:rtype: str or None
	"""
	if path == "/":
		return "/ is a mount point"

	for tab in ["/etc/fstab", "/etc/mtab"]:
		if os.path.isfile(tab):
			f = open(tab, "r")
			for line in f:
				if line.startswith("#"):
					continue
				if "\t" in line:
					tmp = line.split("\t")
				else:
					tmp = line.split()
				if len(tmp) > 1:
					tmp[1] = tmp[1].rstrip("/")
					if tmp[1] == path:
						return "%s is a mount point" % path
	return None


def checkDirFileSystem(path, cr):
	# type: (str, ConfigRegistry) -> Optional[str]
	"""
	Check if the given path is of a known file system type.

	:param str path: A file system path.
	:param ConfigRegistry cr: A |UCR| instance.
	:returns: A string if the path is a known file system, `None` otherwise.
	:rtype: str or None
	"""
	knownFs = cr.get("listener/shares/rename/fstypes", DEFAULT_FS).split(":")
	ret, out = getstatusoutput("LC_ALL=C stat -f %s" % pipes.quote(path))
	myFs = ""
	for line in out.split("\n"):
		tmp = line.split("Type: ")
		if len(tmp) == 2:
			myFs = tmp[1].strip()
			for fs in knownFs:
				if fs.lower() == myFs.lower():
					# ok, found fs is fs whitelist
					return None
			break
	return "filesystem %s for %s is not on a known filesystem" % (myFs, path)


def createOrRename(old, new, cr):
	# type: (Dict[str, List[str]], Dict[str, List[str]], ConfigRegistry) -> Optional[str]
	"""
	Create or rename a share.

	:param str old: The old path.
	:param str new: The new path.
	:param ConfigRegistry cr: A |UCR| instance.
	:returns: A string if an error occurs, `None` on success.
	:rtype: str or None
	"""
	rename = False
	if cr.is_true("listener/shares/rename", False) and old:
		# rename only if old object exists and
		# share host is unchanged and
		# path was changed
		if old.get("univentionShareHost") and new.get("univentionShareHost"):
			if new["univentionShareHost"][0] == old["univentionShareHost"][0]:
				if old.get("univentionSharePath") and new.get("univentionSharePath"):
					if not new["univentionSharePath"][0] == old["univentionSharePath"][0]:
						rename = True
	# check new path
	if not new.get("univentionSharePath"):
		return "univentionSharePath not set"
	newPath = new['univentionSharePath'][0].decode('UTF-8').rstrip("/")
	if not newPath.startswith("/"):
		newPath = "/" + newPath
	newPath = os.path.realpath(newPath)
	if newPath == "/":
		return "/ as new path is not allowed"
	share_name = new.get('univentionShareSambaName', new.get('cn', [b'']))[0].decode('UTF-8')

	# rename it
	if rename:
		# old path (source)
		if not old.get("univentionSharePath"):
			return "not old univentionSharePath found, renaming not possible"
		oldPath = old["univentionSharePath"][0].decode('UTF-8').rstrip("/")
		if not oldPath.startswith("/"):
			oldPath = "/" + oldPath
		if os.path.islink(oldPath):
			oldPath = os.path.realpath(oldPath)
		if oldPath == "/":
			return "/ as old path is not allowed"

		# return silently if destination exists and source not
		# probably someone else has done the job
		if not os.path.isdir(oldPath) and os.path.exists(newPath):
			return None

		# check source and destination
		if os.path.exists(newPath):
			return "destination %s exists" % newPath
		if not os.path.isdir(oldPath):
			return "source %s is not a directory" % oldPath

		# check blacklist
		if is_blacklisted(newPath, cr):
			return "%r as destination for renaming not allowed! WARNING: the path %r for the share %r matches a blacklisted path. The whitelist can be extended via the UCR variables listener/shares/whitelist/. After changing the variables univention-directory-listener needs to be restartet." % (newPath, newPath, share_name)
		if is_blacklisted(oldPath, cr):
			return "%r as source for renaming not allowed! WARNING: the path %r for the share %r matches a blacklisted path. The whitelist can be extended via the UCR variables listener/shares/whitelist/. After changing the variables univention-directory-listener needs to be restartet." % (oldPath, newPath, share_name)

		# check mount point
		for i in [oldPath, newPath]:
			ret = dirIsMountPoint(i)
			if ret:
				return ret

		# check path to destination
		# get existing part of path
		newPathDir = os.path.dirname(newPath)
		existingNewPathDir = "/"
		for path in newPathDir.split("/"):
			if path and os.access(existingNewPathDir, os.F_OK):
				if os.access(os.path.join(existingNewPathDir, path), os.F_OK):
					existingNewPathDir = os.path.join(existingNewPathDir, path)

		if newPathDir == "/" or existingNewPathDir == "/":
			return "moving to directory level one is not allowed (%s)" % newPath

		# check know fs
		for i in [oldPath, existingNewPathDir]:
			ret = checkDirFileSystem(i, cr)
			if ret:
				return ret

		# check if source and destination are on the same device
		if not os.stat(oldPath).st_dev == os.stat(existingNewPathDir).st_dev:
			return "source %s and destination %s are not on the same device" % (oldPath, newPath)

		# create path to destination
		if not os.access(newPathDir, os.F_OK):
			try:
				os.makedirs(newPathDir, 0o755)
			except Exception as exc:
				return "creation of directory %s failed: %s" % (newPathDir, exc)

		# TODO: check size of source and free space in destination

		# move
		try:
			if oldPath != "/" and newPath != "/":
				shutil.move(oldPath, newPath)
		except Exception as exc:
			return "failed to move directory %s to %s: %s" % (oldPath, newPath, exc)

	# or create directory anyway
	if not os.access(newPath, os.F_OK):
		try:
			os.makedirs(newPath, 0o755)
		except Exception as exc:
			return "creation of directory %s failed: %s" % (newPath, exc)

	# set custom permissions for path in new
	uid = 0
	gid = 0
	mode = new.get("univentionShareDirectoryMode", [b"0755"])[0]

	if new.get("univentionShareUid"):
		try:
			uid = int(new["univentionShareUid"][0])
		except ValueError:
			pass

	if new.get('univentionShareGid'):
		try:
			gid = int(new["univentionShareGid"][0])
		except ValueError:
			pass

	# only dirs
	if not os.path.isdir(newPath):
		return "custom permissions only for directories allowed (%s)" % newPath

	# check blacklist
	if is_blacklisted(newPath, cr):
		return "WARNING: the path %r for the share %r matches a blacklisted path. The whitelist can be extended via the UCR variables listener/shares/whitelist/." % (newPath, share_name)

	# set permissions, only modify them if a change has occurred
	try:
		mode = int(mode, 16 if mode.startswith(b'0x') else (8 if mode.startswith(b'0') else 10))
		if (not old or (new.get("univentionShareDirectoryMode") and old.get("univentionShareDirectoryMode") and new["univentionShareDirectoryMode"][0] != old["univentionShareDirectoryMode"][0])):
			os.chmod(newPath, mode)

		if (not old or (new.get("univentionShareUid") and old.get("univentionShareUid") and new["univentionShareUid"][0] != old["univentionShareUid"][0])):
			os.chown(newPath, uid, -1)

		if (not old or (new.get("univentionShareGid") and old.get("univentionShareGid") and new["univentionShareGid"][0] != old["univentionShareGid"][0])):
			os.chown(newPath, -1, gid)
	except Exception:
		return "setting custom permissions for %s failed" % newPath


def is_blacklisted(path, ucr):
	# type: (str, ConfigRegistry) -> bool
	"""

	>>> is_blacklisted('/home/', {})
	True
	>>> is_blacklisted('/home/', {'listener/shares/whitelist/default': '/home/*:/var/*'})
	False
	>>> is_blacklisted('/home', {})
	True
	>>> is_blacklisted('/home', {'listener/shares/whitelist/default': '/home/*:/var/*'})
	False
	>>> is_blacklisted('/home/Administrator', {})
	True
	>>> is_blacklisted('/home/Administrator', {'listener/shares/whitelist/default': '/home/*:/var/*'})
	False
	>>> is_blacklisted('/home/Administrator/', {'listener/shares/whitelist/admin': '/home/Administrator'})
	False
	"""
	path = '%s/' % (path.rstrip('/'),)
	whitelist = [set(val.split(':')) for key, val in ucr.items() if key.startswith('listener/shares/whitelist/')]
	whitelist = reduce(set.union, whitelist) if whitelist else set()
	for directory in DIR_BLACKLIST:
		if any(path in allowed or path.rstrip('/') in allowed or fnmatch.fnmatch(path, allowed) for allowed in whitelist):
			continue
		if path.startswith(directory):
			return True
	return False


if __name__ == '__main__':
	import doctest
	doctest.testmod()
