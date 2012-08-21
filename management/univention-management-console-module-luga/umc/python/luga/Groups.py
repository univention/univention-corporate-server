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




# TODO: implement certain logging through MODULE.error

from fnmatch import fnmatch
from GroupExceptions import *
from univention.management.console.modules import UMC_CommandError, UMC_OptionTypeError
from univention.management.console.log import MODULE
from univention.lib.i18n import Translation

_ = Translation( 'univention-management-console-module-luga' ).translate


class Groups():
	def validate_name(self, name):
		if not name:
			raise ValueError( _('No name given.') )
		if not self.username_pattern.match(str(name)):
			raise ValueError( _('Name may only contain letters, numbers, "-" and "_" and must not start with "-".') )

	def _parse_groups(self):
		'''
		Reads every line in /etc/group and /etc/gshadow to collect as many informations
		about every group as possible and stores it in a dictionary (one for each group):
		{ 'groupname' : '', 'gid' : '', 'users' : '', 'administrators' : '' }
		=================================================================================
		returns:
			<list> containing every found <dictionary>group
		'''

		result = [] # list wich will be returned (containing the collected group dictionarys)
		try:
			f = open('/etc/group', 'r')
			for line in f:
				line_split = line[:-1].split(':') # group attributes are devided by ':'
				if len(line_split) == 4 and line_split[0] and line_split[2] and line_split[2].isdigit(): # valid line?
					result += [{'groupname' : line_split[0], 'gid' : int(line_split[2]), 'users' : line_split[3]}]
			f.close()
		except IOError:
			raise UMC_CommandError(_('Could not read from file /etc/group.'))
		return result

	def _search_groups(self, category, pattern):
		'''
		Uses self._parse_groups() to get a list containing every group as a dictionary
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
		groups = self._parse_groups()

		for group in groups:
			attributes = []
			if category == 'users':
				attributes += group[category].split(',')
			else:
				attributes += [group[category]]
			for attribute in attributes:
				if fnmatch(str(attribute), str(pattern)):
					result += [group]
					break
		return result

	def _get_additional_groups(self, username):
		'''
		Uses self._search_groups() to find every group in wich a certain user is member.
		============================================================================
		expects:
			<string>username: name of the user wich should be looked for
		============================================================================
		returns:
			<list> of <string>groupnames in wich the user is member
		'''

		result = []
		groups = self._search_groups('users', username)
		for group in groups:
			result += [group['groupname']]
		return result

	def get_groups(self, request):
		result = []
		groups = self._parse_groups()
		for group in groups:
			result += [group['groupname']]
		self.finished(request.id, result)

		if not len(groupname) <= 32 and not groupname.startswith('-') and not ':' in groupname and not ' ' in groupname and not '\n' in groupname and not '\t' in groupname:
			raise ValueError(_('"%s" is no valid groupname. Groupnames may consist of one to 32 characters, excluding ":" and whitespaces, and not start with "-".') % groupname)


	def groups_get(self, request):
		if not type(request.options) == list:
			raise UMC_OptionTypeError(_('Options have to be given as list of strings.'))

		result = []
		for group in self._parse_groups():
			if group['groupname'] in request.options:
				result.append(group)
		self.finished(request.id, result)

	def groups_query(self, request):
		if not type(request.options) == dict:
			raise UMC_OptionTypeError(_('Options have to be given as dictionary.'))

		result = []
		groups = []
		category = request.options.get('category', '')

		if category == '':
			category = 'groupname'
		if category in ('groupname', 'gid', 'users', 'administrators'):
			groups += self._search_groups(category, request.options.get('pattern', '*'))
			for group in groups:
				result += [{'groupname' : group['groupname']}]
		self.finished(request.id, result)

	def groups_add(self, request):
		if not type(request.options) == list:
			raise UMC_OptionTypeError(_('Options have to be given as list of dictionarys.'))

		messages = []
		for group in request.options:
			options = None
			groupname = None
			users = None
			command = ['/usr/sbin/groupadd']
			exit_code = None

			try:
				if not type(group) == dict:
					raise ValueError(_('Invalid optiontype.'))
				options = group.get('object', {})
				if not type(options) == dict:
					raise ValueError(_('Invalid optiontype.'))

				groupname = options.get('groupname')
				users = options.get('users')

				if not groupname is not None:
					raise ValueError(_('Groupname is required.'))
				if not type(groupname) == str:
					raise ValueError(_('Groupname has to be given as string.'))
				self.validate_name(groupname)
				command += [groupname]

				# execute "groupadd"
				exit_code = self.process(command)
				if exit_code == 9:
					raise ValueError(_('Groupname "%s" is already in use.') % groupname)
				if exit_code:
					MODULE.error('Processing "%s" failed and returned %s' % (str(command), str(exit_code)))
					raise CreatingError(_('Could not create group. See log for more information.'))
				if users is not None:
					if not type(users) == list:
						raise ModifyError(_('Users have to be given as list.'))
					if self.process(['/usr/bin/gpasswd', '-M', ','.join(users), groupname]):
						raise ModifyError(_('Could not set list of users.'))
			except (ValueError, CreatingError, ModifyError) as e:
				messages += [str(e)]
				if type(e) == ModifyError:
					self.process(['/usr/sbin/groupdel', groupname])
			else:
				messages += ['']
		self.finished(request.id, messages)

	def groups_put(self, request):
		if not type(request.options) == list:
			raise UMC_OptionTypeError(_('Options have to be given as list of dictionarys.'))

		messages = []
		for group in request.options:
			group_index = None
			command = ['/usr/sbin/groupmod']
			options = None
			identifier = None
			groupname = None
			users = None
			exit_code = None

			try:
				if not type(group) == dict:
					raise ValueError(_('Invalid optiontype.'))
				options = group.get('object', {})
				if not type(options) == dict:
					raise ValueError(_('Invalid opiontype.'))

				identifier = options.get('$groupname$')
				groupname = options.get('groupname')
				gid = options.get('gid')
				users = options.get('users')

				if not identifier:
					raise ValueError(_('No group has been specified.'))
				if not type(identifier) == str:
					raise ValueError(_('ID has to be given as string.'))
				command += [identifier]
				if groupname is None and gid is None and users is None and administrators is None:
					raise ModifyError(_('No changes have been made.'))

				# first try to set new list of users, if given, with "gpasswd"
				if users is not None:
					if self.process(['/usr/bin/gpasswd', '-M', ','.join(users), identifier]):
						raise ModifyError(_('Could not modify list of users.'))

				# collect arguements for "groupmod" command
				if groupname is not None:
					self.validate_name(groupname)
					command += ['-n', groupname]
				if gid is not None:
					if not type(gid) == int:
						raise ValueError(_('"Group ID has to be given as string.'))
					command += ['-g', '%s' % gid]

				# exceute "groupmod"
				exit_code = self.process(command)
				if exit_code == 3:
					raise ValueError(_('"%s" is no valid Group ID. Group IDs may only consit of digits.') % gid)
				if exit_code == 4:
					raise ValueError(_('Group ID "%s" is already in use.') % gid)
				if exit_code == 6:
					raise ModifyError(_('Group "%s" does not exist.') % identifier)
				if exit_code == 9:
					raise ValueError(_('Groupname "%s" is already in use.') % groupname)
				if exit_code:
					MODULE.error('Processing "%s" failed and returned %s' % (str(command), str(exit_code)))
					raise ModifyError(_('Could not modify group. See log for more information.'))
			except (ValueError, ModifyError) as e:
				messages += [str(e)]
			else:
				messages += ['']
		self.finished(request.id, messages)
	
	def groups_remove(self, request):
		if not type(request.options) == list:
			raise UMC_OptionTypeError(_('Options have to be given as list of strings.'))

		messages = []
		user_cache = self._parse_users()
		for group in request.options:
			identifier = group.get('object', '').replace('&lt;', '<') # frontend converts '<' to '&lt' for some reasons (undo that)
			gid = None
			primary_users = []
			command = ['/usr/sbin/groupdel']
			exit_code = None

			try:
				if not type(identifier) == str:
					raise ValueError(_('ID has to be given as string.'))

				# iterate over all users to check if one of them has the group as primary group
				for cached_user in user_cache:
					if cached_user['gid'] == gid:
						primary_users += [cached_user['username']]
				if primary_users: # users found wich have the group as primary group?
					raise ModifyError(_('Can not remove the primary group of user(s): %s.') % ', '.join(primary_users))

				command += [identifier]

				# execute "groupdel"
				exit_code = self.process(command)
				if exit_code == 6:
					raise ModifyError(_('Group "%s" does not exist.') % identifier)
				if exit_code:
					raise ModifyError(_('Could not delete group "%s". See log for more informaton.') % identifier)
					MODULE.error('Processing "%s" failed and returned %s' % (str(command), str(exit_code)))
			except (ValueError, ModifyError) as e:
				messages += ['%s: %s' % (identifier, str(e))]
			else:
				messages += ['']
		self.finished(request.id, messages)



