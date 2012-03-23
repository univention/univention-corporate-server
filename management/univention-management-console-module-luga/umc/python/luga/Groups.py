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

	def get_administrators(self, group):
		return self.group_search('groupname', group)[0]['administrators'].split(',')

	def validate_groupname(self, groupname):
		if len(groupname) <= 32 and not groupname.startswith('-') and not ':' in groupname and not ' ' in groupname and not '\n' in groupname and not '\t' in groupname:
			return True
		else:
			return False

	def validate_gid(self, gid):
		return gid.isdigit()

	def groups_get(self, request):
		result = []
		for group in self.parse_groups():
			if group['groupname'] in request.options:
				result.append(group)
		self.finished(request.id, result)

	def groups_query(self, request):
		success = True
		message = None
		result = []
		groups = []
		category = request.options.get('category', '')
		if category == '':
			category = 'groupname'
		if category in ('groupname', 'gid', 'users', 'administrators'):
			groups.extend(self.group_search(category, request.options.get('pattern', '*')))
			for group in groups:
				result.append({'groupname' : group['groupname']})
		else:
			success = False
			message = _('Invalid category "%s"') % category
		self.finished(request.id, result, message, success)
	
	def groups_add(self, request):
		message = ''
		success = True
		for group in request.options:
			args = ''
			error_code = None
			groupname = group.get('groupname')
			gid = group.get('gid')
			users = group.get('users')
			administrators = groups.get('administrators')
			if groupname:
				try:
					if not self.validate_groupname(groupname):
						raise ValueError(_('"%s" is no valid groupname') % groupname)
					if gid:
						if not self.validate_gid(gid):
							args += ' -g "%s"' % gid
							raise ValueError(_('"%s" is no valid GID') % gid)
						args += ' -g "%s"' % gid
					error_code = self.process('/usr/sbin/groupadd%s "%s"' % (args, groupname))
					if error_code:
						raise CreatingError(_('groupadd returned %d') % error_code)
					if users:
						error_code = self.process('/usr/bin/gpasswd -M "%s" "%s"' % (users, groupname))
						if error_code:
							raise ModifyError(_('could not set list of users, gpasswd returned %d') % error_code)
					if administrators:
						error_code = self.process('/usr/bin/gpasswd -A "%s" "%s"' % (administrators, groupname))
						if error_code:
							raise ModifyError(_('could not set list of administrators, gpasswd returned %d') % error_code)
				except (ValueError, CreatingError, ModifyError) as e:
					message += _('Did not create group "%s" (%s)\n') % (groupname, e.message)
					success = False
				else:
					message += _('Successfully created group "%s"\n') % groupname
			else:
				message += _('A group was not created because no groupname was given\n')
				success = False
		self.finished(request.id, None, message[:-1], success)

	def groups_put(self, request):
		message = ''
		success = True
		for group in request.options:
			args = ''
			error_code = None
			id = group.get('id')
			groupname = group.get('groupname')
			gid = group.get('gid')
			users = group.get('users')
			administratos = id.get('administrators')
			try:
				if groupname:
					if not self.validate_groupname(groupname):
						args += ' -n %s' % groupname
						raise ValueError(_('"%s" is no valid groupname)\n') % groupname)
					args += ' -n %s' % groupname
				if gid:
					if not self.validate_gid(gid):
						raise ValueError(_('"%s" is no valid gid)\n') % id)
					args += ' -g %s' % gid
				error_code = self.process('/usr/sbin/groupmod%s "%s"' % (args, id))
				if error_code:
					raise ModifyError(_('groumod returned %d)\n') % error_code)
				if users:
					error_code = self.process('/usr/bin/gpasswd -M "%s" "%s"' % (users, groupname))
					if error_code:
						raise ModifyError(_('could not modify list of users, gpasswd returned %d)\n') % error_code)
				if administrators:
					error_code = self.process('/usr/bin/gpasswd -A "%s" "%s"' % (administrators, groupname))
					if error_code:
						raise ModifyError(_('could not modify list of administrators, gpasswd returned %d)\n') % error_code)
			except (ValueError, ModifyError) as e:
				message += _('Did not modify group "%s" (%s)\n' ) % (id, e.message)
				success = False
			else:
				message += _('Successfully modified group "%s"\n') % id
		self.finished(request.id, None, message[:-1], success)
	
	def groups_remove(self, request):
		success = True
		message = ''
		for id in request.options:
			error_code = self.process('/usr/sbin/groupdel "%s"' % id)
			if error_code:	
				success = False
				message += _('Did not remove group "%s" (groupdel returned %d)\n') % (id, error_code)
			else:
				message += _('Successfully removed group "%s"\n') % id
		self.finished(request.id, None, message[:-1], success)



