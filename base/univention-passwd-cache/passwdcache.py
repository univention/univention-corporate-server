# -*- coding: utf-8 -*-
#
# Univention passwdcache
#  removed deleted user from passwd cache
#
# Copyright 2010-2019 Univention GmbH
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

__package__ = ''  # workaround for PEP 366
import listener
import os
import univention.debug
import grp
import string

name = 'passwdcache'
description = 'Remove deleted user from passwd cache'

filter = '(objectClass=shadowAccount)'
attributes = []


def clean():
	listener.setuid(0)
	try:
		# It might be possible to cleanup the files
		# during an resync but I think the better way
		# is to keep the files.

		#_clean_file('shadow')
		#_clean_file('passwd')
		#_clean_file('group')
		_set_shadow_permissions()
	finally:
		listener.unsetuid()


def _remove_user_from_file(filename, uid):
	filename_orig = '/etc/univention/passwdcache/%s' % filename
	filename_new = '/etc/univention/passwdcache/%s.new' % filename

	if os.path.exists(filename_orig):
		modify = False
		in_lines = open(filename_orig, 'r').readlines()
		out_lines = []
		for in_line in in_lines:
			if in_line.startswith('%s:' % (uid)):
				modify = True
			else:
				out_lines.append(in_line)

		if modify:
			out_file = open(filename_new, 'w')
			out_file.write(string.join(out_lines, ''))
			out_file.close()
			os.rename(filename_new, filename_orig)
			return True
	return False


def _clean_file(filename):
	f = open('/etc/univention/passwdcache/%s' % filename, 'w')
	f.close()
	os.chown('/etc/univention/passwdcache/%s' % filename, 0, 0)


def _set_shadow_permissions():
	filename = '/etc/univention/passwdcache/shadow'
	if os.path.exists(filename):
		os.chmod(filename, 0o640)
		try:
			shadow_gid = grp.getgrnam('shadow')[2]
		except:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'The shadow gidNumber was not found. Check the installation.')
			shadow_gid = 0
		os.chown(filename, 0, shadow_gid)


def _cleanup_groups():
	shadow_file = '/etc/univention/passwdcache/shadow'
	group_file = '/etc/univention/passwdcache/group'

	users = []
	fp = open(shadow_file, 'r')
	shadow_lines = fp.readlines()
	fp.close()

	for shadow_line in shadow_lines:
		users.append(shadow_line.split(':')[0].lower())

	if users:
		fp = open(group_file, 'r')
		groups_new = []
		group_lines = fp.readlines()
		fp.close()
		modified = False
		for group_line_unstrip in group_lines:
			group_line = group_line_unstrip.strip()
			needed = False
			members = group_line.split(':')[-1].split(',')
			for member in members:
				if member.lower() in users:
					needed = True
					break
			if needed:
				groups_new.append(group_line_unstrip)
			else:
				modified = True
		if modified:
			new_fp = '/etc/univention/passwdcache/group.new'
			out_file = open(new_fp, 'w')
			out_file.write(string.join(groups_new, ''))
			out_file.close()
			os.rename(new_fp, group_file)

	else:
		_clean_file('group')


def _remove_user(uid):
	listener.setuid(0)
	try:
		_remove_user_from_file('passwd', uid)
		modified = _remove_user_from_file('shadow', uid)
		if modified:
			_set_shadow_permissions()
			_cleanup_groups()
	finally:
		listener.unsetuid()


def handler(dn, new, old):
	if not new and old:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'User was removed: uid: %s' % old['uid'][0])
		_remove_user(old['uid'][0])

	else:
		# if the user was disabled he should be removed from the cache
		if new and 'sambaAcctFlags' in new:
			if new['sambaAcctFlags'][0].find('D') > 0:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'User was disabled: uid: %s' % new['uid'][0])
				_remove_user(new['uid'][0])


def initialize():
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'init passwdcache')
