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

from univention.lib.i18n import Translation

_ = Translation( 'univention-management-console-module-luga' ).translate




class Groups():
	def groups_parse(self, category='groupname', pattern='*'):
		f = open('/etc/group', 'r')
		result = []
		groups = {}
		for line in f:
			groupSplit = line[:-1].split(':')
			if len(groupSplit) == 4:
				group = {'groupname' : groupSplit[0], 'status' : groupSplit[1], 'gid' : int(groupSplit[2]), 'users' : groupSplit[3]}
				attributes = []
				if category == 'users':
					attributes.extend(group['users'].split(','))
				else:
					attributes.append(group[category])
				for attribute in attributes:
					if fnmatch(str(attribute), str(pattern)):
						groups[group['groupname']] = group
						break
		f.close()
		f = open('/etc/gshadow', 'r')
		for line in f:
			groupSplit = line[:-1].split(':')
			if groupSplit[0] in groups:
				if groupSplit[1] in ('*', '!', '!!'):
					groups[groupSplit[0]]['status'] = groupSplit[1]
				else:
					groups[groupSplit[0]]['status'] = ''
				result.append(groups[groupSplit[0]])
				del groups[groupSplit[0]]
		f.close()
		for group in groups:
			result.append(group)
		return result

	def groups_query(self, request):
		success = True
		message = None
		result = []
		category = request.options.get('category', '')
		if category == '':
			category = 'groupname'
		if not category in ('groupname', 'gid', 'users'):
			success = False
			message = 'Invalid category "%s"' % category
		else:
			result.extend(self.groups_parse(category, request.options.get('pattern', '*')))
			message = 'Success'
		self.finished(request.id, result, message, success)

	def groups_getGroups(self, request):
		result = []
		groups = self.groups_parse()
		for group in groups:
			result.append({'id' : group['groupname'], 'label' : group['groupname']})
		self.finished(request.id, result)

	def groups_getAdditionalGroups(self, username):
		result = []
		groups = self.groups_parse('users', username)
		for group in groups:
			result.append(group['groupname'])
		return result

	def groups_get(self, request):
		result = []
		for group in self.groups_parse():
			if group['groupname'] in request.options:
				result.append(group)
		self.finished(request.id, result)

	def groups_validateGid(gid):
		return gid.isdigit()
	
	def groups_validateGroupname(groupname):
		if not len(groupname) <= 32 and not groupname.startswith('-') and not ':' in groupname and not ' ' in groupname and not '\n' in groupname and not '\t' in groupname:
			return True
		else:
			return False

	def groups_add(self, request):
		message = ''
		success = True
		for id in request:
			args = ''
			groupname = id.options.get('groupname')
			gid = id.options.get('gid')
			password = id.options.get('password')
			try:
				if groupname:
					if not self.groups_validateGroupname(groupname):
						raise ValueError('"%s" is no valid groupname' % groupname)
				else:
					raise ValueError('groupname required')
				if gid:
					if self.groups_validateGid(gid):
						args += ' -g "%s"' % gid
					else:
						raise ValueError('"%s" is no valid GID')
			except ValueError as e:
				message += 'Could not create group "%s" (%s)\n' % (groupname, e.message)
				success = False
			else:
				if not self.process('/usr/sbin/groupadd %s %s' % (args, groupname))['returncode']:
					if password is None or password is not None and not self.process('/usr/bin/gpasswd "%s"' % groupname, '%s\n%s\n' % (password, password)):
						message += 'Successfully created group "%s"' % groupname
					else:
						success = False
						message += 'An error occured during setting password for group "%s"\n' % groupname
						self.process('/usr/sbin/groupdel "%s"' % groupname)
				else:
					success = False
					message += 'An unexpected error occured during creating group "%s"\n' % groupname
		self.finished(request.id, None, message[:-1], success)

	def groups_put(self, request):
		message = ''
		success = True
		for id in request.options:
			args = ''
			newGroupname = id.get('newGroupname')
			newGid = id.get('newGid')
			newPassword = id.get('newPassword')
			try:
				if newGroupname:
						if self.groups_validateeGroupname(newGroupname):
							args += ' -n %s' % newGroupname
						else:
							raise ValueError('"%s" is no valid groupname' % newGroupname)
				if newGid:
						if self.groups_validateGid(newGid):
							args += ' -g %s' % newGid
						else:
							raise ValueError('"%s" is no valid groupname' % newGid)
				if removePassword:
					if self.process('/usr/sbin/gpasswd -r "%s"' % id)['returncode']:
						raise ValueError('could not remove password')
				else:
					if newPassword:
							if self.process('/usr/bin/gpasswd "%s"' % id, '%s\n%s' % (newPassword, newPassword))['returncode']:
								raise ValueError('could not change password')
			except ValueError as e:
				message += 'Could not modify group "%s" (%s\n)' % (id, e.message)
				success = False
			else:
				if not self.process('/usr/sbin/groupmod%s %s' % (args, id))['returncode']:
					message += 'Successfully modified group "%s"\n' % id
				else:
					message += 'An unexpected error occured while modifying group "%s"\n' % id
		self.finished(request.id, None, message[:-1], success)
	
	def groups_remove(self, request):
		success = True
		message = ''
		for id in request.options:
			if self.process('/usr/sbin/groupdel "%s"' % id)['returncode']:
				success = False
				message += 'Could not remove group "%s"\n' % id
		self.finished(request.id, None, message[:-1], success)



