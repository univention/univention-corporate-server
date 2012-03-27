#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console module:
#   manage local users and groups
#
# Copyright 2012 Univention GmbH
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

from fnmatch import fnmatch
from pexpect import spawn
from GroupExceptions import *
from univention.lib.i18n import Translation

_ = Translation( 'univention-management-console-module-luga' ).translate


class Groups():
	def parse_groups(self):
		try:
			f = open('/etc/group', 'r')
			result = []
			shadowGroups = {}
			for line in f:
				lineSplit = line[:-1].split(':')
				if len(lineSplit) == 4:
					group = {'groupname' : lineSplit[0], 'gid' : int(lineSplit[2]), 'users' : lineSplit[3], 'administrators' : ''}
					if lineSplit[1] == 'x':
						shadowGroups[lineSplit[0]] = group
					else:
						result.append(group)
			f.close()
		except IOError:
			raise UMC_CommandError(_('Could not read from file /etc/group'))
		try:
			f = open('/etc/gshadow', 'r')
			for line in f:
				lineSplit = line[:-1].split(':')
				if len(lineSplit) == 4 and lineSplit[0] in shadowGroups:
					shadowGroups[lineSplit[0]]['administrators'] = lineSplit[2]
					result.append(shadowGroups[lineSplit[0]])
					del shadowGroups[lineSplit[0]]
			f.close()
		except IOError:
			raise UMC_CommandError(_('Could not read from file /etc/gshadow'))
		return result

	def group_search(self, category, pattern):
		result = []
		groups = self.parse_groups()
		for group in groups:
			attributes = []
			if category == 'users' or category == 'administrators':
				attributes.extend(group[category].split(','))
			else:
				attributes.append(group[category])
			for attribute in attributes:
				if fnmatch(str(attribute), str(pattern)):
					result.append(group)
					break
		return result

	def get_additional_groups(self, username):
		return self.group_search('users', username)

	def get_groups(self, request):
		result = []
		groups = self.parse_groups()
		for group in groups:
			result.append({'id' : group['groupname'], 'label' : group['groupname']})
		self.finished(request.id, result)

	def validate_groupname(self, groupname):
		if len(groupname) <= 32 and not groupname.startswith('-') and not ':' in groupname and not ' ' in groupname and not '\n' in groupname and not '\t' in groupname:
			return True
		else:
			return False

#	def change_group_password(self, groupname, password):
#		subprocess = None
#		if password:
#			subprocess = spawn('/usr/bin/gpasswd "%s"' % groupname)
#			subprocess.expect(':')
#			subprocess.sendline(password)
#			subprocess.expect(':')
#			subprocess.sendline(password)
#		else:
#			subprocess = spawn('/usr/bin/gpasswd -r "%s"' % groupname)
#		subprocess.close()

	def validate_gid(self, gid):
		return gid.isdigit()

	def groups_get(self, request):
		result = []
		for group in self.parse_groups():
			if group['groupname'] in request.options:
				result.append(group)
		self.finished(request.id, result)

	def groups_query(self, request):
		result = []
		groups = []
		category = request.options.get('category', '')
		if category == '':
			category = 'groupname'
		if category in ('groupname', 'gid', 'users', 'administrators'):
			groups.extend(self.group_search(category, request.options.get('pattern', '*')))
			for group in groups:
				result.append({'groupname' : group['groupname']})
		self.finished(request.id, result)

	def groups_add(self, request):
		messages = []
		group_cache = self.parse_groups()
		for group in request.options:
			args = ''
			error_code = None
			options = group.get('object', {})
			groupname = options.get('groupname')
			gid = group['object'].get('gid')
#			password = options.get('password')
			users = options.get('users')
			administrators = options.get('administrators')
			if groupname:
				try:
					for cached_group in group_cache:
						if cached_group['groupname'] == groupname:
							raise ValueError(_('Groupname "%s" is already in use') % groupname)
					if not self.validate_groupname(groupname):
						raise ValueError(_('"%s" is no valid groupname') % groupname)
					if gid:
						if not self.validate_gid(gid):
							args += ' -g "%s"' % gid
							raise ValueError(_('"%s" is no valid GID') % gid)
						args += ' -g "%s"' % gid
					error_code = self.process('/usr/sbin/groupadd%s "%s"' % (args, groupname))
					if error_code:
						raise CreatingError(_('Groupadd returned %d') % error_code)
#					if password:
#						self.change_group_password(groupname)
					if users:
						error_code = self.process('/usr/bin/gpasswd -M "%s" "%s"' % (','.join(users), groupname))
						if error_code:
							raise ModifyError(_('Could not set list of users, gpasswd returned %d') % error_code)
					if administrators:
						error_code = self.process('/usr/bin/gpasswd -A "%s" "%s"' % (','.join(administrators), groupname))
						if error_code:
							raise ModifyError(_('Could not set list of administrators, gpasswd returned %d') % error_code)
				except (ValueError, CreatingError, ModifyError) as e:
					messages.append(str(e))
					if type(e) == ModifyError:
						self.process('/usr/sbin/groupdel "%s"' % groupname)
				else:
					group_cache.append({'groupname' : groupname})
			else:
				messages.append(_('Groupname required'))
		self.finished(request.id, messages)

	def groups_put(self, request):
		messages = []
		group_cache = self.parse_groups()
		for group in request.options:
			group_index = None
			args = ''
			error_code = None
			options = group.get('object', {})
			id = options.get('id')
			groupname = options.get('groupname')
			gid = options.get('gid')
#			password = options.get('password')
#			remove_password = options.get('remove_password')
			users = options.get('users')
			administrators = options.get('administrators')
			if id:
				try:
					for i in range(0, len(group_cache)):
						if group_cache[i]['groupname'] == id:
							group_index = i
							break
					else:
						raise ValueError(_('Specified group does not exist'))
					if groupname is None and gid is None and users is None and administrators is None:
						raise ModifyError(_('No changes have been made'))
					if groupname is not None:
						if not self.validate_groupname(groupname):
							raise ValueError(_('"%s" is no valid groupname') % groupname)
						args += ' -n "%s"' % groupname
					if gid is not None:
						if not self.validate_gid(gid):
							raise ValueError(_('"%s" is no valid gid') % gid)
						args += ' -g "%s"' % gid
					if users is not None:
						error_code = self.process('/usr/bin/gpasswd -M "%s" "%s"' % (','.join(users), id))
						if error_code:
							raise ModifyError(_('Could not modify list of users, gpasswd returned %d') % error_code)
					if administrators is not None:
						error_code = self.process('/usr/bin/gpasswd -A "%s" "%s"' % (','.join(administrators), id))
						if error_code:
							raise ModifyError(_('Could not modify list of administrators, gpasswd returned %d') % error_code)
					error_code = self.process('/usr/sbin/groupmod%s "%s"' % (args, id))
					if error_code:
						raise ModifyError(_('Groupmod returned %d') % error_code)
				except (ValueError, ModifyError) as e:
					messages.append(str(e))
				else:
					if groupname:
						group_cache[group_index]['groupname'] = groupname
			else:
				messages.append(_('No group has been specified'))
		self.finished(request.id, messages)
	
	def groups_remove(self, request):
		messages = []
		group_cache = self.parse_groups()
		ids = request.options[0].get('object', {})
		for id in ids:
			group_index = None
			try:
				for i in range(0, len(group_cache)):
					if group_cache[i]['groupname'] == id:
						group_index = i
						break
				else:
					raise ModifyError(_('Specified group does not exist'))
				error_code = self.process('/usr/sbin/groupdel "%s"' % id)
				if error_code == 8:
					raise ModifyError(_('Can not remove a users primary group'))
				elif error_code:
					raise ModifyError(_('groupdel returned %d') % error_code)
			except ModifyError as e:
				messages.append(str(e))
			else:
				group_cache.pop(group_index)
		self.finished(request.id, messages)



