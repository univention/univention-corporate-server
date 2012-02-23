#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Helper
#  function for creating or rename share directories
#
# Copyright 2011-2012 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import os
import commands
import shutil

DEFAUL_FS = "ext2/ext3:ext2:ext3:ext4:xfs:btrfs"
DIR_BLACKLIST = []
DIR_BLACKLIST.append("/boot")
DIR_BLACKLIST.append("/sys")
DIR_BLACKLIST.append("/proc")
DIR_BLACKLIST.append("/etc")
DIR_BLACKLIST.append("/dev")
DIR_BLACKLIST.append("/tmp")
DIR_BLACKLIST.append("/root")

def dirIsMountPoint(path):

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

	knownFs = cr.get("listener/shares/rename/fstypes", DEFAUL_FS).split(":")
	ret, out = commands.getstatusoutput("LC_ALL=C stat -f '%s'" % path)
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

	# create or rename
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
	newPath = new['univentionSharePath'][0].rstrip("/")
	if not newPath.startswith("/"):
		newPath = "/" + newPath
	if os.path.islink(newPath):
		newPath = os.path.realpath(newPath)
	if newPath == "/":
		return "/ as new path is not allowed" 

	# rename it
	if rename:	

		# old path (source)
		if not old.get("univentionSharePath"):
			return "not old univentionSharePath found, renaming not possible"
		oldPath = old["univentionSharePath"][0].rstrip("/")
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
		for dir in DIR_BLACKLIST:
			if newPath.startswith(dir):
				return "%s as destination for renaming not allowed" % newPath
			if oldPath.startswith(dir):
				return "%s as source for renaming not allowed" % oldPath

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
				os.makedirs(newPathDir, int('0755',0))
			except Exception, e:
				return "creation of directory %s failed: %s" % (newPathDir, str(e))

		# check size of source and free space in destination
		# TODO

		# move
		try:
			if not oldPath == "/" and not newPath == "/":
				shutil.move(oldPath, newPath)
		except Exception, e:
			return "failed to move directory %s to %s: %s" % (oldPath, newPath, str(e))

	# or create directory anyway
	if not os.access(newPath, os.F_OK):
		try:
			os.makedirs(newPath, int('0755',0))
		except Exception, e:
			return "creation of directory %s failed: %s" % (newPath, str(e))

	# set custom permissions for path in new
	uid = 0
	gid = 0
	mode = "0755"

	if new.get("univentionShareUid"):
		try:
			uid = int(new["univentionShareUid"][0])
		except:
			pass

	if new.get('univentionShareGid'):
		try:
			gid = int(new["univentionShareGid"][0])
		except:
			pass

	if new.get("univentionShareDirectoryMode"):
		try:
			mode = new["univentionShareDirectoryMode"][0]
		except:
			pass

	# only dirs
	if not os.path.isdir(newPath):
		return "custom permissions only for directories allowed (%s)" % newPath 

	# check blacklist
	for dir in DIR_BLACKLIST:
		if newPath.startswith(dir):
			return "custom permissions for %s not allowed" % newPath

	# set permissions
	try:
		os.chmod(newPath, int(mode, 0))
		os.chown(newPath, uid, gid)
	except:
		return "setting custom permissions for %s failed" % newPath

	return None
