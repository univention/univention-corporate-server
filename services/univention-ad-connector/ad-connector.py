#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  Univention LDAP Listener script for the ad connector
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2022 Univention GmbH
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

from __future__ import absolute_import
import listener
from six.moves import cPickle as pickle
import time
import os
import univention.debug as ud
import shutil
import subprocess
try:
	from typing import Dict, List, Optional, Tuple  # noqa: F401
except ImportError:
	pass

name = 'ad-connector'
description = 'AD Connector replication'
filter = '(objectClass=*)'
attributes = []  # type: List[str]


# use the modrdn listener extension
modrdn = "1"

# While initialize copy all group objects into a list:
# https://forge.univention.org/bugzilla/show_bug.cgi?id=18619#c5
init_mode = False
group_objects = []
connector_needs_restart = False

dirs = [listener.configRegistry['connector/ad/listener/dir']]
if 'connector/listener/additionalbasenames' in listener.configRegistry and listener.configRegistry['connector/listener/additionalbasenames']:
	for configbasename in listener.configRegistry['connector/listener/additionalbasenames'].split(' '):
		if '%s/ad/listener/dir' % configbasename in listener.configRegistry and listener.configRegistry['%s/ad/listener/dir' % configbasename]:
			dirs.append(listener.configRegistry['%s/ad/listener/dir' % configbasename])
		else:
			ud.debug(ud.LISTENER, ud.WARN, "ad-connector: additional config basename %s given, but %s/ad/listener/dir not set; ignore basename." % (configbasename, configbasename))
dirs = [dir_ for dir_ in dirs if dir_]
if not dirs:
	raise ImportError('UCR variable connector/ad/listener/dir needs to be set!')


def _save_old_object(directory, dn, old):
	# type: (str, str, Optional[Dict[str, List[bytes]]]) -> None
	filename = os.path.join(directory, 'tmp', 'old_dn')

	with open(filename, 'wb+') as fd:
		os.chmod(filename, 0o600)
		p = pickle.Pickler(fd)
		p.dump((dn, old))
		p.clear_memo()


def _load_old_object(directory):
	# type: (str) -> Tuple[str, Dict[str, List[bytes]]]
	with open(os.path.join(directory, 'tmp', 'old_dn'), 'rb') as fd:
		p = pickle.Unpickler(fd)
		(old_dn, old_object) = p.load()

	return (old_dn, old_object)


def _dump_changes_to_file_and_check_file(directory, dn, new, old, old_dn):
	# type: (str, str, Optional[Dict[str, List[bytes]]], Optional[Dict[str, List[bytes]]], Optional[str]) -> None
	ob = (dn, new, old, old_dn)

	tmpdir = os.path.join(directory, 'tmp')
	filename = '%f' % (time.time(),)
	filepath = os.path.join(tmpdir, filename)

	with open(filepath, 'wb+') as fd:
		os.chmod(filepath, 0o600)
		p = pickle.Pickler(fd)
		p.dump(ob)
		p.clear_memo()

	# prevent a race condition between the pickle file is only partly written to disk and then read
	# by moving it to the final location after it is completely written to disk
	shutil.move(filepath, os.path.join(directory, filename))


def _restart_connector():
	# type: () -> None
	listener.setuid(0)
	try:
		if not subprocess.call(['pgrep', '-f', 'python.*connector.ad.main']):
			ud.debug(ud.LISTENER, ud.PROCESS, "ad-connector: restarting connector ...")
			subprocess.call(('service', 'univention-ad-connector', 'restart'))
			ud.debug(ud.LISTENER, ud.PROCESS, "ad-connector: ... done")
	finally:
		listener.unsetuid()


def handler(dn, new, old, command):
	# type: (str, Optional[Dict[str, List[bytes]]], Optional[Dict[str, List[bytes]]], str) -> None
	global group_objects
	global init_mode
	global connector_needs_restart

	# restart connector on extended attribute changes
	if b'univentionUDMProperty' in new.get('objectClass', []) or b'univentionUDMProperty' in old.get('objectClass', []):
		connector_needs_restart = True
	else:
		if connector_needs_restart is True:
			_restart_connector()
			connector_needs_restart = False

	listener.setuid(0)
	try:
		for directory in dirs:
			if not os.path.exists(os.path.join(directory, 'tmp')):
				os.makedirs(os.path.join(directory, 'tmp'))

			old_dn = None
			old_object = {}  # type: Dict[str, List[bytes]]

			if os.path.exists(os.path.join(directory, 'tmp', 'old_dn')):
				(old_dn, old_object) = _load_old_object(directory)
			if command == 'r':
				_save_old_object(directory, dn, old)
			else:
				# Normally we see two steps for the modrdn operation. But in case of the selective replication we
				# might only see the first step.
				#  https://forge.univention.org/bugzilla/show_bug.cgi?id=32542
				if old_dn and new.get('entryUUID') != old_object.get('entryUUID'):
					ud.debug(ud.LISTENER, ud.PROCESS, "The entryUUID attribute of the saved object (%s) does not match the entryUUID attribute of the current object (%s). This can be normal in a selective replication scenario." % (old_dn, dn))
					_dump_changes_to_file_and_check_file(directory, old_dn, {}, old_object, None)
					old_dn = None

				if init_mode:
					if new and b'univentionGroup' in new.get('objectClass', []):
						group_objects.append((dn, new, old, old_dn))

				_dump_changes_to_file_and_check_file(directory, dn, new, old, old_dn)

				if os.path.exists(os.path.join(directory, 'tmp', 'old_dn')):
					os.unlink(os.path.join(directory, 'tmp', 'old_dn'))

	finally:
		listener.unsetuid()


def clean():
	# type: () -> None
	listener.setuid(0)
	try:
		for directory in dirs:
			for filename in os.listdir(directory):
				if os.path.isfile(filename):
					os.remove(os.path.join(directory, filename))
			if os.path.exists(os.path.join(directory, 'tmp')):
				for filename in os.listdir(os.path.join(directory, 'tmp')):
					os.remove(os.path.join(directory, filename))
	finally:
		listener.unsetuid()


def postrun():
	# type: () -> None
	global init_mode
	global group_objects
	global connector_needs_restart
	if init_mode:
		listener.setuid(0)
		try:
			init_mode = False
			for ob in group_objects:
				for directory in dirs:
					filename = os.path.join(directory, "%f" % time.time())
					with open(filename, 'wb+') as fd:
						os.chmod(filename, 0o600)
						p = pickle.Pickler(fd)
						p.dump(ob)
						p.clear_memo()
			del group_objects
			group_objects = []
		finally:
			listener.unsetuid()
	if connector_needs_restart is True:
		_restart_connector()
		connector_needs_restart = False


def initialize():
	# type: () -> None
	global init_mode
	init_mode = True
	clean()
