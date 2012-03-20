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

import uuid
from fnmatch import fnmatch

from univention.lib.i18n import Translation
from univention.management.console.modules import UMC_OptionTypeError, Base
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

_ = Translation( 'univention-management-console-module-luga' ).translate

class Users():

	def gid2name(self, gid):
		"""
			get the groupname of a group id
		"""
		ret = self.groups_parse('gid', gid)
		if len(ret) != 1: # 0|1 other should be impossible
			return '' # important!
		return ret.pop().get('groupname')

	def users_parse(self, category='username', pattern='*'):
		""" parse /etc/passwd and /etc/shadow
			param category: one of [username, uid, gid, gecos, homedir, shell, group]
			param pattern: a searchpattern
			return a list of dicts
			return [ {  'gid': <group id>', 'homedir': <home directory>, 'password': <password>, 'shell': <user shell>, 'uid': <user id>, 'username': <username>, 
						'fullname': <full name>, 'miscellaneous': <misc>, 'roomnumber': <room number>, 'tel_business': <telephone business>, 'tel_private': <telephone private>, 
						[.TODO.], ... ] 
		"""
		# Load /etc/shadow into dict
		shadows = {}
		f = open('/etc/shadow', 'r')

		for user in f:
			user = user[0:-1].split(':')
			user.pop()
			shadows[ user.pop(0) ] = user
		f.close()

		# Parse /etc/passwd
		users = []
		f = open('/etc/passwd', 'r')
		for user in f:
			# remove trailing newline, split by ':' seperator
			(username, password, uid, gid, gecos, homedir, shell) = user[0:-1].split(':')

			# Groups
			group = self.gid2name(gid) # primary group
			groups = self.groups_getAdditionalGroups(username)
			groups_mixin = groups + [group]

			# Filter
			value = { 'username': username, 'uid': uid, 'gid': gid, 'gecos': gecos.split(','), 'homedir': homedir, 'shell': shell, 'group': groups_mixin }.get(category, 'username')
			if list is type(value):
				match = False
				for val in value:
					if fnmatch(str(value), pattern):
						match = True
			else:
				match = fnmatch(str(value), pattern)
			if not match:
				continue

			# Shadow
			shadow = shadows.get(username, [password, '', '', '', '', '', ''])
			password = shadow.pop(0)

			locked = ('!' == password[0]) or ('*' == password[0]) or ('LK' == password)
			expired = (password == '!!')
			empty_password = password in ('NP', '!', '')

			# Gecos
			gecos = gecos.split(',')
			while len(gecos) < 5:
				gecos.append('')

			users.append( {
				'username': username,
				'uid': int(uid),
				'gid': int(gid),
				'group': group,
				'groups': groups,
				'homedir': homedir,
				'shell': shell,
				'fullname': gecos[0],
				'roomnumber': gecos[1],
				'tel_business': gecos[2],
				'tel_private': gecos[3],
				'miscellaneous': gecos[4],
				# TODO
				'days_since_epoch_of_last_pw_change': shadow[0],
				'days_until_change_allowed': shadow[1],
				'days_before_change_required': shadow[2],
				'days_warning_for_expiration': shadow[3],
				'days_before_account_inactive': shadow[4],
				'days_since_epoch_when_account_expires': shadow[5],
				'locked': locked,
				'expired': expired,
				'empty_password': empty_password
			} )
		f.close()
		return users

	def users_changePassword(self, username, password):
		"""
			change the userpassword for <username>
			returns (<success>, <errormessage|None>)
			TODO: test special characters
		"""

		success = True
		message = None

		exit = self.process('/usr/bin/passwd %s' % username, '%s\n%s' % (password, password))
		if 0 != exit['returncode']:
			message = {
				'1': _('permission denied'),
				'2': _('invalid combination of options'),
				'3': _('unexpected failure, nothing done'),
				'4': _('unexpected failure, passwd file missing'),
				'5': _('passwd file busy, try again'),
				'6': _('invalid argument to option'),
			}.get( str(exit['returncode']), _('error') )
			success = False
		return (success, message)

	def users_query( self, request ):
		"""
			returns a list containing dicts of all users filtered by category with bash-like-pattern
			the following wildcars can be used in request.options.pattern:
				*       matches everything
				?       matches any single character
				[seq]   matches any character in seq
				[!seq]  matches any char not in seq
			request.options.category:
				one of [username, uid, gid, gecos, homedir, shell, group] default: username
		"""
		MODULE.info( 'luga.users_query: options: %s' % str( request.options ) )

		if dict is not type(request.options):
			request.status = BAD_REQUEST_INVALID_OPTS
			self.finished( request.id, False)
			return

		category = request.options.get('category', 'username')
		pattern = request.options.get('pattern', '*')

		# TODO: which exceptions can be raised by open()?
		try:
			request.status = SUCCESS
			response = self.users_parse( category, pattern )
		except:
			request.status = MODULE_ERR
			response = False
			pass # TODO

		MODULE.info( 'luga.users_query: results: %s' % str( response ) )
		self.finished( request.id, response )

	def users_getUsers(self, request):
		"""
			returns a shorten list containing a dict for each user
			[ {'id': <username>, 'label': <username>}, ... ]
		"""
		MODULE.info( 'luga.users_getUsers: options: %s' % str( request.options ) )

		response = []
		for user in self.users_parse():
			response.append( {'id': user['username'], 'label': user['username']} )

		MODULE.info( 'luga.users_query: results: %s' % str( response ) )
		self.finished(request.id, response)

	def users_getUsersByGroup(self, groupname):
		"""
			returns a list containing all users which are in <groupname> as strings
			[ <username>, <username2>, ... ]
		"""

		response = []
		users = self.users_parse('groupname', groupname)
		for user in users:
			response.append(user['username'])
		return response

	def users_get( self, request ):
		"""
			returns a list of dicts containing user information from requested usernames
			param request.options = [ <username>, <username2>, ... ]
		"""
		MODULE.info( 'luga.users_get: options: %s' % str( request.options ) )

		if list is not type(request.options):
			request.status = BAD_REQUEST_INVALID_OPTS
			self.finished( request.id, False, _("argument type has to be 'list'") )
			return

		response = []

		i = len(request.options)
		c = 0
		for user in self.users_parse():
			if user['username'] in request.options:
				response.append(user)
				c += 1
				if c == i:
					break

		MODULE.info( 'luga.users_get: results: %s' % str( response ) )
		self.finished( request.id, response )

	def users_put( self, request ):
		MODULE.info( 'luga.users_put: options: %s' % str( request.options ) )
		"""
			modify a local user

			TODO: two usernames
			TODO: parameter:
				-e, --expiredate ABL_DATUM	Ablaufdatum auf ABL_DATUM setzen
				-f, --inactive INAKTIV		Passwort nach Ablauf von INAKTIV deaktivieren
		"""

		if list is not type(request.options):
			request.status = BAD_REQUEST_INVALID_OPTS
			self.finished( request.id, False, _("argument type has to be 'list'") )
			return

		request.status = SUCCESS
		failures = []
		errors = {} # no information about returncodes, yet

		for option in request.options:
			o = option.get('object', {})
			options = option.get('options', {})

			# Username
			username = options.get('username')
			if not username:
				request.status = MODULE_ERR
				failures.append( ('', _('No username-option given')) )
				continue

			cmd = '/usr/sbin/usermod '

			# Change username
			if o.get('username'):
				cmd += ' -l "%s"' % o['username']

			# Gecos
			# TODO: emptiing entries?
			gecos = ( o.get('fullname', ''), o.get('roomnumber', ''), o.get('tel_business', ''), o.get('tel_private', ''), o.get('miscellaneous', '') )
			if not (gecos[0] or gecos[1] or gecos[2] or gecos[3] or gecos[4]):
				gecos = None

			if None != gecos:
				gecos = '%s,%s,%s,%s,%s' % gecos
				cmd += ' -c "%s"' % gecos

			# Home directory
			homedir = o.get('homedir')
			if homedir:
				cmd += ' -d "%s"' % homedir
				if True == options.get('move_home_folder'):
					cmd += ' -m '

			# Loginshell
			shell = o.get('shell')
			if shell:
				cmd += ' -s "%s"' % shell

			# Change User-ID
			uid = str(o.get('uid', ''))
			if uid.isdigit():
				cmd += ' -u "%d"' % uid

			# Primary Group
			if o.get('gid'): #TODO: rename to group
				cmd += ' -g "%s"' % o['gid']

			# Additional Groups
			groups = o.get('groups')
			if groups:
				cmd += ' -G "%s"' % ','.join( list(groups) )

			# Account deactivation
			if None != options.get('lock'):
				cmd += ' -L'
			elif None != options.get('unlock'):
				cmd += ' -U'

			# Password
			password = o.get('password')
			if password:
				# TODO
				pw = self.users_changePassword(username, password)
				if not pw[0]:
					request.status = MODULE_ERR
					message = pw[1]

			cmd += ' "%s"' % username

			# Execute
			exit = self.process(cmd)
			if exit['returncode'] != 0:
				request.status = MODULE_ERR
				error = errors.get( str(exit['returncode']), _('Could not edit user') )
				failures.append( (username, error, ) )
				continue

		response = 0 < len(failures)
		MODULE.info( 'luga.users_edit: results: %s' % str( response ) )
		self.finished( request.id, response, str(failures) )

	def users_add(self, request):
		"""
			add a local user

			TODO: remove gid, replace by groupname
			TODO: gecos
			TODO: Password changing
		"""
		MODULE.info( 'luga.users_add: options: %s' % str( request.options ) )
	
		if list is not type(request.options):
			request.status = BAD_REQUEST_INVALID_OPTS
			self.finished( request.id, False, _("argument type has to be 'list'") )
			return

		request.status = SUCCESS
		failures = []
		errors = {
			'1': _('could not update password file'),
			'2': _('invalid command syntax'),
			'3': _('invalid argument to option'),
			'4': _('UID already in use (and no -o)'),
			'6': _('specified group doesnt exist'),
			'9': _('username already in use'),
			'10': _('could not update group file'),
			'12': _('could not create home directory'),
			'13': _('could not create mail spool'),
		}

		for option in request.options:
			if dict is not type(option):
				failures.append( ('', _('No username given')) )
				continue

			o = option.get('object', {})
			options = option.get('options', {})

			# Username
#			username = o.get('username')
			username = options.get('username')
			if not username:
				request.status = MODULE_ERR
				failures.append( ('', _('No username-option given')) )
				continue

			cmd = '/usr/sbin/useradd '

			# Gecos
			# TODO: emptiing entries?
			gecos = ( o.get('fullname', ''), o.get('roomnumber', ''), o.get('tel_business', ''), o.get('tel_private', ''), o.get('miscellaneous', '') )
			if not (gecos[0] or gecos[1] or gecos[2] or gecos[3] or gecos[4]):
				gecos = None

			if None != gecos:
				gecos = '%s,%s,%s,%s,%s' % gecos
				cmd += ' -c "%s"' % gecos

			# Homedir
			if o.get('homedir'):
				cmd += ' -d "%s"' % o['homedir']
			if options.get('create_home'):
				cmd += ' -m'
			else:
				cmd += ' -M'

			# Shell
			if o.get('shell'):
				cmd += ' -s "%s"' % o['shell']

			# User ID
			if o.get('uid'):
				cmd += ' -u "%d"' % o['uid']

			# Create an own Usergroup as primary group?
			if options.get('create_usergroup'):
				cmd += ' -U'
			else:
				cmd += ' -N'
				# Primary Group
				if o.get('gid'): # TODO: rename to group
					cmd += ' -g "%s"' % o['gid']

			# Additional groups
			groups = o.get('groups')
			if groups:
				cmd += ' -G "%s"' % ','.join( list(groups) )

			# Password inactivity, expiration
			if o.get('inactive'):
				cmd += ' -f "%s"' % o['inactive']

			cmd += ' "%s"' % username

			# Execute
			exit = self.process(cmd)
			if 0 != exit['returncode']:
				request.status = MODULE_ERR
				error = errors.get( str(exit['returncode']), _('error') )
				failures.append( (username, error, ) )
				continue
			# TODO: TODO: TODO
			else:
				password = o.get('password')
				if None != password:
					pw = self.users_changePassword(username, password)
					if not pw[0]:
						request.status = MODULE_ERR
						response = pw[1]

		response = 0 < len(failures)

		MODULE.info( 'luga.users_add: results: %s' % str( response ) )
		self.finished( request.id, response, str(failures) )

	def users_remove(self, request):
		"""
			remove a list of local users
			param request.options = [ { username: <string>, force: <bool>, remove: <bool> }, ...]
				force: force removal of files, even if not owned by user
				remove: remove home directory and mail spool
		"""
		MODULE.info( 'luga.users_delete: options: %s' % str( request.options ) )

		if list is not type(request.options):
			request.status = BAD_REQUEST_INVALID_OPTS
			self.finished( request.id, False, _("argument type has to be 'list'") )
			return

		cmd = '/usr/sbin/userdel '
		request.status = SUCCESS
		failures = []
		errors = {
			'1': _('could not update password file'),
			'2': _('invalid command syntax'),
			'6': _('specified user doesnt exist'),
			'8': _('user currently logged in'),
			'10': _('could not update group file'),
			'12': _('could not remove home directory')
		}

		for option in request.options:
			# TODO: o is a string, not dict...
			# where to get options foreach user?
			# can i hack in JS? alerting user?
			if dict is not type(option):
				failures.append( ('', _('No username given')) )
				continue

			username = option.get('username')

			if None == username:
				failures.append( ('', _('No username given')) )
				continue
			if option.get('force'):
				cmd += ' -f'
			if option.get('remove'):
				cmd += ' -r'

			cmd += ' "%s"' % username

			exit = self.process(cmd)
			if exit['returncode'] != 0:
				request.status = MODULE_ERR
				error = errors.get( str(exit['returncode']), _('error') )
				failures.append( (username, error, ) )

		response = 0 < len(failures)

		MODULE.info( 'luga.users_delete: results: %s' % str( response ) )
		self.finished( request.id, response, str(failures) )
