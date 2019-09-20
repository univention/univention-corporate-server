#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Univention Directory Listener script for the s4 connector
#
# Copyright 2004-2019 Univention GmbH
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
import cPickle
import listener
import os
import time
import shutil
import univention.debug
import subprocess

name = 's4-connector'
description = 'S4 Connector replication'
filter = '(objectClass=*)'
attributes = []

# use the modrdn listener extension
modrdn = "1"

# While initialize copy all group objects into a list:
# https://forge.univention.org/bugzilla/show_bug.cgi?id=18619#c5
s4_init_mode = False
group_objects = []
connector_needs_restart = False

dirs = [listener.configRegistry.get('connector/s4/listener/dir', '/var/lib/univention-connector/s4')]
if 'connector/listener/additionalbasenames' in listener.configRegistry and listener.configRegistry['connector/listener/additionalbasenames']:
	for configbasename in listener.configRegistry['connector/listener/additionalbasenames'].split(' '):
		if '%s/s4/listener/dir' % configbasename in listener.configRegistry and listener.configRegistry['%s/s4/listener/dir' % configbasename]:
			dirs.append(listener.configRegistry['%s/s4/listener/dir' % configbasename])
		else:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, "s4-connector: additional config basename %s given, but %s/s4/listener/dir not set; ignore basename." % (configbasename, configbasename))


def _save_old_object(directory, dn, old):
	filename = os.path.join(directory, 'tmp', 'old_dn')

	f = open(filename, 'w+')
	os.chmod(filename, 0600)
	p = cPickle.Pickler(f)
	p.dump((dn, old))
	p.clear_memo()
	f.close()


def _load_old_object(directory):
	f = open(os.path.join(directory, 'tmp', 'old_dn'), 'r')
	p = cPickle.Unpickler(f)
	(old_dn, old_object) = p.load()
	f.close()

	return (old_dn, old_object)


def _dump_changes_to_file_and_check_file(directory, dn, new, old, old_dn):
	ob = (dn, new, old, old_dn)

	tmpdir = os.path.join(directory, 'tmp')
	filename = '%f' % (time.time(),)
	filepath = os.path.join(tmpdir, filename)

	with open(filepath, 'w+') as fd:
		os.chmod(filepath, 0600)
		p = cPickle.Pickler(fd)
		p.dump(ob)
		p.clear_memo()

	# prevent a race condition between the pickle file is only partly written to disk and then read
	# by moving it to the final location after it is completely written to disk
	shutil.move(filepath, os.path.join(directory, filename))


def _is_module_disabled():
	return listener.baseConfig.is_true('connector/s4/listener/disabled', False)


def _restart_connector():
	listener.setuid(0)
	try:
		if not subprocess.call(['pgrep', '-f', 'python.*s4connector.s4.main']):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, "s4-connector: restarting connector ...")
			subprocess.call(('service', 'univention-s4-connector', 'restart'))
			univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, "s4-connector: ... done")
	finally:
		listener.unsetuid()


def handler(dn, new, old, command):

	global group_objects
	global s4_init_mode
	global connector_needs_restart

	if _is_module_disabled():
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "s4-connector: UMC module is disabled by UCR variable connector/s4/listener/disabled")
		return

	# restart connector on extended attribute changes
	if 'univentionUDMProperty' in new.get('objectClass', []) or 'univentionUDMProperty' in old.get('objectClass', []):
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
			old_object = {}

			if os.path.exists(os.path.join(directory, 'tmp', 'old_dn')):
				(old_dn, old_object) = _load_old_object(directory)
			if command == 'r':
				_save_old_object(directory, dn, old)
			else:
				# Normally we see two steps for the modrdn operation. But in case of the selective replication we
				# might only see the first step.
				#  https://forge.univention.org/bugzilla/show_bug.cgi?id=32542
				if old_dn and new.get('entryUUID') != old_object.get('entryUUID'):
					univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS, "The entryUUID attribute of the saved object (%s) does not match the entryUUID attribute of the current object (%s). This can be normal in a selective replication scenario." % (old_dn, dn))
					_dump_changes_to_file_and_check_file(directory, old_dn, {}, old_object, None)
					old_dn = None

				if s4_init_mode:
					if new and 'univentionGroup' in new.get('objectClass', []):
						group_objects.append((dn, new, old, old_dn))

				_dump_changes_to_file_and_check_file(directory, dn, new, old, old_dn)

				if os.path.exists(os.path.join(directory, 'tmp', 'old_dn')):
					os.unlink(os.path.join(directory, 'tmp', 'old_dn'))

	finally:
		listener.unsetuid()


def clean():
	listener.setuid(0)
	try:
		for directory in dirs:
			if not os.path.exists(directory):
				continue
			for filename in os.listdir(directory):
				if filename != "tmp":
					os.remove(os.path.join(directory, filename))
			if os.path.exists(os.path.join(directory, 'tmp')):
				for filename in os.listdir(os.path.join(directory, 'tmp')):
					os.remove(os.path.join(directory, filename))
	finally:
		listener.unsetuid()


def postrun():
	global s4_init_mode
	global group_objects
	global connector_needs_restart

	if s4_init_mode:
		listener.setuid(0)
		try:
			s4_init_mode = False
			for ob in group_objects:
				for directory in dirs:
					filename = os.path.join(directory, "%f" % time.time())
					f = open(filename, 'w+')
					os.chmod(filename, 0600)
					p = cPickle.Pickler(f)
					p.dump(ob)
					p.clear_memo()
					f.close()
			del group_objects
			group_objects = []
		finally:
			listener.unsetuid()

	if connector_needs_restart is True:
		_restart_connector()
		connector_needs_restart = False


def initialize():
	global s4_init_mode
	s4_init_mode = True
	clean()
