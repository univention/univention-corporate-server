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
from univention.management.console.modules import UMC_CommandError, UMC_OptionTypeError
from univention.lib.i18n import Translation

_ = Translation( 'univention-management-console-module-luga' ).translate


class Groups():
	def parse_groups(self):
		'''
		Reads every line in /etc/group and /etc/gshadow to collect as many informations
		about every group as possible and stores it in a dictionary (one for each group):
		{ 'groupname' : '', 'gid' : '', 'users' : '', 'administrators' : '' }
		=================================================================================
		returns:
			<list> containing every found <dictionary>group
		'''
		try:
			f = open('/etc/group', 'r')
			result = [] # list wich will be returned (containing the collected group dictionarys)
			shadowGroups = {} # 
			for line in f:
				lineSplit = line[:-1].split(':') # group attributes are devided by ':'
				if len(lineSplit) == 4 and lineSplit[2] and lineSplit[2].isdigit(): # valid line?
					group = {'groupname' : lineSplit[0], 'gid' : int(lineSplit[2]), 'users' : lineSplit[3], 'administrators' : ''}
					if lineSplit[1] == 'x': # additional information about group administrators in in /etc/gshadow?
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
				if len(lineSplit) == 4 and lineSplit[0] in shadowGroups: # valid line wich contains a group wich is also part of shadowGroups?
					shadowGroups[lineSplit[0]]['administrators'] = lineSplit[2]
					result.append(shadowGroups[lineSplit[0]])
					del shadowGroups[lineSplit[0]] # remove group from shadowGroups to possibly accelerate the loop for the next line
			f.close()
		except IOError:
			raise UMC_CommandError(_('Could not read from file /etc/gshadow'))
		return result

	def group_search(self, category, pattern):
		'''
		Uses self.parse_groups() to get a list containing every group as a dictionary
		and extracts certain groups of it.
		=============================================================================
		expects:
			<string>category: attribute of the groups wich will be compared with ...
		... <string>pattern
		=============================================================================
		returns:
			<list> containing every <dictionary>group matching the given parameters
		'''
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
		'''
		Uses self.group_search() to find every group in wich a certain user is member.
		============================================================================
		expects:
			<string>username: name of the user wich should be looked for
		============================================================================
		returns:
			<list> of <string>groupnames in wich the user is member
		'''
		result = []
		groups = self.group_search('users', username)
		for group in groups:
			result.append(group['groupname'])
		return result

	def get_groups(self, request):
		result = []
		groups = self.parse_groups()
		for group in groups:
			result.append({'id' : group['groupname'], 'label' : group['groupname']})
		self.finished(request.id, result)

	def validate_groupname(self, groupname):
		'''
		Validates if a certain groupname complys with debian rules for groupnames.
		============================================================================
		expects:
			<string>groupname: groupname wich should be validated
		============================================================================
		returns:
			<boolean>True if the given groupname fullfils the rules ...
			... or
			<boolean>False if it does not.
		'''
		return len(groupname) <= 32 and not groupname.startswith('-') and not ':' in groupname and not ' ' in groupname and not '\n' in groupname and not '\t' in groupname


	def groups_get(self, request):
		if not type(request.options) == list:
			raise UMC_OptionTypeError(_('Options have to be given as list of strings'))
		result = []
		for group in self.parse_groups():
			if group['groupname'] in request.options:
				result.append(group)
		self.finished(request.id, result)

	def groups_query(self, request):
		if not type(request.options) == dict:
			raise UMC_OptionTypeError(_('Options have to be given as dictionary'))
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
		if not type(request.options) == list:
			raise UMC_OptionTypeError(_('Options have to be given as list of dictionarys'))
		messages = []
		group_cache = self.parse_groups()
		for group in request.options:
			args = ''
			error_code = None
			options = None
			groupname = None
			users = None
			administrators = None
			try:
				if not type(group) == dict:
					raise ValueError(_('Invalid optiontype'))
				options = group.get('object', {})
				if not type(options) == dict:
					raise ValueError(_('Invalid optiontype'))
				groupname = options.get('groupname')
				users = options.get('users')
				administrators = options.get('administrators')
				if not groupname:
					raise ValueError(_('Groupname is required'))
				if not type(groupname) == str:
					raise ValueError(_('Groupname has to be given as string'))
				if not self.validate_groupname(groupname):
					raise ValueError(_('"%s" is no valid groupname.<br/>Groupnames may consist of one to 32 characters, not start with "-" and not contain ":" or whitespaces') % groupname)
				# iterate over every groupname to check if the groupname is already in use
				for cached_group in group_cache:
					if cached_group['groupname'] == groupname:
						raise ValueError(_('Groupname "%s" is already in use') % groupname)
				error_code = self.process('/usr/sbin/groupadd%s "%s"' % (args, groupname))
				if error_code:
					raise CreatingError(_('Groupadd returned %d') % error_code)
				if users is not None:
					if not type(users) == list:
						raise ModifyError(_('Users have to be given as list'))
					error_code = self.process('/usr/bin/gpasswd -M "%s" "%s"' % (','.join(users), groupname))
					if error_code:
						raise ModifyError(_('Could not set list of users, gpasswd returned %d') % error_code)
				if administrators is not None:
					if not type(administrators) == list:
						raise ModifyError(_('Administrators have to be given as list'))
					error_code = self.process('/usr/bin/gpasswd -A "%s" "%s"' % (','.join(administrators), groupname))
					if error_code:
						raise ModifyError(_('Could not set list of administrators, gpasswd returned %d') % error_code)
			except (ValueError, CreatingError, ModifyError) as e:
				messages.append(str(e))
				if type(e) == ModifyError:
					self.process('/usr/sbin/groupdel "%s"' % groupname)
			else:
				messages.append('')
				group_cache.append({'groupname' : groupname})
		self.finished(request.id, messages)

	def groups_put(self, request):
		if not type(request.options) == list:
			raise UMC_OptionTypeError(_('Options have to be given as list of dictionarys'))
		messages = []
		group_cache = self.parse_groups()
		for group in request.options:
			group_index = None
			args = ''
			error_code = None
			options = None
			id = None
			groupname = None
#			password = None
#			remove_password = None
			users = None
			administrators = None
			try:
				if not type(group) == dict:
					raise ValueError(_('Invalid optiontype'))
				options = group.get('object', {})
				if not type(options) == dict:
					raise ValueError(_('Invalid opiontype'))
				id = options.get('id')
				groupname = options.get('groupname')
				gid = options.get('gid')
#				password = options.get('password')
#				remove_password = options.get('remove_password')
				users = options.get('users')
				administrators = options.get('administrators')
				if not id:
					raise ValueError(_('No group has been specified'))
				if not type(id) == str:
					raise ValueError(_('ID has to be given as string'))
				# iterate over all groupnames to check if the group specified by 'id' exists
				for i in range(0, len(group_cache)):
					if group_cache[i]['groupname'] == id:
						group_index = i
						break
				else: # no groups name equals 'id'
					raise ValueError(_('Specified group does not exist'))
				if groupname is None and gid is None and users is None and administrators is None:
					raise ModifyError(_('No changes have been made'))
				if groupname is not None:
					if not self.validate_groupname(groupname):
						raise ValueError(_('"%s" is no valid groupname.<br/>Groupnames may consist of one to 32 characters, not start with "-" and not contain ":" or whitespaces') % groupname)
					args += ' -n "%s"' % groupname
				if gid is not None:
					if not gid.isdigit():
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
				messages.append('')
				if groupname:
						group_cache[group_index]['groupname'] = groupname
		self.finished(request.id, messages)
	
	def groups_remove(self, request):
		if not type(request.options) == list:
			raise UMC_OptionTypeError(_('Options have to be given as list of strings'))
		messages = []
		group_cache = self.parse_groups()
		user_cache = self.parse_users()
		for group in request.options:
			id = group.get('object', '').replace('&lt;', '<') # frontend converts '<' to '&lt' for some reasons (undo that)
			gid = None
			primary_users = []
			try:
				if not type(id) == str:
					raise ValueError(_('ID has to be given as string'))
				# iterate over all groups to check if the group specified by 'id' exists
				for cached_group in group_cache:
					if cached_group['groupname'] == id:
						gid = cached_group['gid']
						break
				else: # no groups name equals 'id'
					raise ModifyError(_('Group "%s" does not exist') % id)
				# iterate over all users to check if one of them has the group as primary group
				for cached_user in user_cache:
					if cached_user['gid'] == gid:
						primary_users.append(cached_user['username'])
				if primary_users: # users found wich have the group as primary group?
					raise ModifyError(_('Can not remove the primary group of user(s): %s') % ', '.join(primary_users))
				error_code = self.process('/usr/sbin/groupdel "%s"' % id)
				if error_code: # no exception occured till here and still groupdel failed?
					raise ModifyError(_('groupdel returned %d') % error_code)
			except (ValueError, ModifyError) as e:
				messages.append('%s: %s' % (id, str(e)))
			else:
				messages.append('')
		self.finished(request.id, messages)



