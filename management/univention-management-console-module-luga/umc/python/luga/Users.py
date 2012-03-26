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
from datetime import date

from univention.lib.i18n import Translation
from univention.management.console.modules import UMC_OptionTypeError, UMC_CommandError, UMC_OptionMissing, Base
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

_ = Translation( 'univention-management-console-module-luga' ).translate

class Users:
	def gid2name(self, gid):
		"""
			get the groupname of a group id
			return empty string if no group was found
		"""
		ret = self.group_search('gid', gid)
		if len(ret) != 1: # 0|1 other should be impossible
			return ''
		return ret.pop().get('groupname')

	def parse_users(self, category='username', pattern='*'):
		""" parse /etc/passwd and /etc/shadow
			param category: one of [username, uid, gid, gecos, homedir, shell, group]
			param pattern: a searchpattern
			return a list of dicts
			return [ {  'gid': <group id>', 'homedir': <home directory>, 'password': <password>, 'shell': <user shell>, 'uid': <user id>, 'username': <username>, 
						'fullname': <full name>, 'miscellaneous': <misc>, 'roomnumber': <room number>, 'tel_business': <telephone business>, 'tel_private': <telephone private>, 
						[.TODO.], ... ] 
		"""

		users = []
		shadows = {}

		try:
			shadow = open('/etc/shadow')
			passwd = open('/etc/passwd')

			# Parse /etc/shadow
			for user in shadow:
				user = user[:-1].split(':')
				user.pop()
				shadows[ user.pop(0) ] = user
			shadow.close()

			# Parse /etc/passwd
			for user in passwd:
				# remove trailing newline, split by ':' seperator
				(username, password, uid, gid, gecos, homedir, shell) = user[0:-1].split(':')

				# Groups
				group = self.gid2name(gid) # primary group
				groups = self.get_additional_groups(username)
				groups_mixin = groups + [group]

				# Filter
				value = { 'username': username, 'uid': uid, 'gid': gid, 'gecos': gecos.split(','), 'fullname': gecos.split(',').pop(0), 'homedir': homedir, 'shell': shell, 'group': groups_mixin }.get(category, 'username')
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

				pw_is_empty = password in ('NP', '!', '', '*')
				deactivated = (password != '') and (('!' == password[0]) or ('*' == password[0]) or ('LK' == password))
				pw_is_expired = (password == '!!' or shadow[5].isdigit())

				shadow[0] = date.isoformat(date.fromtimestamp(int(shadow[0]) * 86400))
				if shadow[5].isdigit():
					shadow[5] = date.isoformat(date.fromtimestamp(int(shadow[5]) * 86400))

				for i in [1, 2, 3, 4]:
					if not shadow[i].isdigit():
						shadow[i] = 0

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
					'pw_last_change': shadow[0],
					'pw_mindays': int(shadow[1]),
					'pw_maxdays': int(shadow[2]),
					'pw_warndays': int(shadow[3]),
					'pw_disabledays': int(shadow[4]),
					'disabled_since': shadow[5], 
					'lock': deactivated,
					'pw_is_expired': pw_is_expired,
					'pw_is_empty': pw_is_empty
				} )
			passwd.close()
		except (KeyError, IndexError):
			raise UMC_CommandError(_('passwd/shadow file is corrupt'))
		except IOError:
			raise UMC_CommandError(_('Could not open passwd/shadow file')) # no permissions, file does not exists
#		except:
#			raise UMC_CommandError(_('Could not parse passwd/shadow file'))
		return users

	def change_user_password(self, username, password, options={}):
		"""
			change the userpassword and options for <username>
			raises ValueError on error
		"""
		messages = {
			0: '',
			1: _('permission denied'),
			2: _('invalid combination of options'),
			3: _('unexpected failure, nothing done'),
			4: _('unexpected failure, passwd file missing'),
			5: _('passwd file busy, try again'),
			6: _('invalid argument to option'),
		}
		cmd = '/usr/bin/passwd -q '

		if options.get('delete'):
			cmd += '-d '
		if options.get('expire'):
			cmd += '-e '
		if options.get('keep_tokens'):
			cmd += '-k '
		if options.get('lock'):
			cmd += '-l '
		elif options.get('unlock') and password:
			cmd += '-u '

		inactive = options.get('disabledays')
		if inactive:
			cmd += '-i %d ' % self.sanitize_int(inactive)

		mindays = options.get('mindays')
		if mindays:
			cmd += '-n %d ' % self.sanitize_int(mindays)

		warndays = options.get('warndays')
		if warndays:
			cmd += '-w %d ' % self.sanitize_int(warndays)
			
		maxdays = options.get('maxdays')
		if maxdays:
			cmd += '-x %d ' % self.sanitize_int(maxdays)

		pwd = '/usr/bin/passwd -q %s' % self.sanitize_arg(username)
		cmd += self.sanitize_arg(username)
		if not (inactive or mindays or warndays or maxdays or options.get('delete') or options.get('expire') or options.get('keep_tokens') or options.get('lock') or (options.get('unlock') and password)):
			cmd = False

		# Change password
		if password:
			returncode = self.process(pwd, '%s\n%s' % (password, password))
			if 0 != returncode:
				MODULE.error('cmd "%s" failed with returncode %d' % (pwd, returncode)) 
				message = messages.get(returncode, _('unknown error with statuscode %d') % (returncode))
				raise ValueError( _('an error accured while changing password for %s: %s') % (username, message) )

		# Change options
		if cmd:
			returncode = self.process(cmd)
			if 0 != returncode:
				MODULE.error('cmd "%s" failed with returncode %d' % (cmd, returncode)) 
				message = messages.get(returncode, _('unknown error with statuscode %d accured while changing password options') % (returncode))
				raise ValueError( _('an error accured while changing password options for %s: %s') % (username, message) )

		return True

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
			raise UMC_OptionTypeError( _("argument type has to be 'dict'") )

		category = request.options.get('category', 'username')
		pattern = request.options.get('pattern', '*')

		request.status = SUCCESS
		response = self.parse_users( category, pattern )

		MODULE.info( 'luga.users_query: results: %s' % str( response ) )
		self.finished( request.id, response )

	def users_get_users(self, request):
		"""
			returns a shorten list containing a dict for each user
			[ {'id': <username>, 'label': <username>}, ... ]
		"""
		MODULE.info( 'luga.users_getUsers: options: %s' % str( request.options ) )

		response = []
		for user in self.parse_users():
			response.append( {'id': user['username'], 'label': user['username']} )

		MODULE.info( 'luga.users_query: results: %s' % str( response ) )
		self.finished(request.id, response)

	def get_group_members(self, groupname):
		"""
			returns a list containing all users which are in <groupname> as strings
			[ <username>, <username2>, ... ]
		"""

		response = []
		users = self.parse_users('groupname', groupname)
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
			raise UMC_OptionTypeError( _("argument type has to be 'list'") )

		response = []

		i = len(request.options)
		c = 0
		for user in self.parse_users():
			if user['username'] in request.options:
				response.append(user)
				c += 1
				if c == i:
					break

		MODULE.info( 'luga.users_get: results: %s' % str( response ) )
		self.finished( request.id, response )

	def get_common_args( self, options, pwoptions={} ):
		"""
			get args which are equal for put and add
			can also modify an dict with password options
			return string
		"""

		cmd = ' '

		# Gecos
		def sanitize_gecos(s):
			return str( options.get(s, '') ).replace(',', '')

		gecos = [options.get('fullname'), options.get('roomnumber'), options.get('tel_business'), options.get('tel_private'), options.get('miscellaneous')]
		gecos = set([None]) != set(gecos)

		if gecos:
			gecos = map(sanitize_gecos, ['fullname', 'roomnumber', 'tel_business', 'tel_private', 'miscellaneous'])
			cmd += '-c %s ' % self.sanitize_arg( ','.join(gecos) )

		# Home directory
		homedir = options.get('homedir')
		if homedir:
			cmd += '-d %s ' % self.sanitize_arg( homedir )
			if options.get('create_home'): # TODO: rename move/create_home
				cmd += '-m '

		# Shell
		shell = options.get('shell')
		if shell:
			cmd += '-s %s ' % self.sanitize_arg(shell)

		# User-ID
		uid = str(options.get('uid', ''))
		if uid.isdigit():
			cmd += '-u %d ' % self.sanitize_int(uid)

		# Additional groups
		groups = options.get('groups')
		if groups:
			cmd += '-G %s ' % self.sanitize_arg( ','.join(list(groups)) )

		# Primary Group
		group = options.get('group')
		if group:
			cmd += '-g %s ' % self.sanitize_arg( group )

		# Password options
		if options.get('pw_delete'):
			pwoptions['delete'] = True
		if options.get('pw_expire'):
			pwoptions['expire'] = True
		if options.get('pw_keep_tokens'):
			pwoptions['keep_tokens'] = True
		if options.get('lock'):
			pwoptions['lock'] = True
		else:
		#	if options.get('pw_unlock'):
		#	TODO: old state
			pwoptions['unlock'] = True

		inactive = options.get('pw_deactivatedays')
		if inactive:
			pwoptions['inactive'] = inactive

		mindays = options.get('pw_mindays')
		if mindays:
			pwoptions['mindays'] = mindays

		warndays = options.get('pw_warndays')
		if warndays:
			pwoptions['warndays'] = warndays

		maxdays = options.get('pw_maxdays')
		if maxdays:
			pwoptions['maxdays'] = maxdays

		return cmd

	def users_put( self, request ):
		MODULE.info( 'luga.users_put: options: %s' % str( request.options ) )
		"""
			modify a local user
		"""

		if list is not type(request.options):
			raise UMC_OptionTypeError( _("argument type has to be 'list'") )

		request.status = SUCCESS
		response = []
		errors = {
			# no information about returncodes, yet
		}

		for o in request.options:
			try:
				#if dict is not type(o) or dict is not type(o.get('object', {})) or dict is not type(o.get('options', {})):
				if dict is not type(o) or dict is not type(o.get('object', {})):
					raise UMC_OptionTypeError( _("argument type has to be 'dict'") )
				option = o.get('object', {})
#				options = o.get('options', {})

				# Username
				username = option.get('$username$')
				new_username = option.get('username')
				if not username:
					raise ValueError( _('No username given') )

				pwoptions = {}
				cmd = '/usr/sbin/usermod '
				cmd += self.get_common_args( option, pwoptions )

				# Change username
				if new_username and username != new_username:
					cmd += '-l %s ' % self.sanitize_arg( new_username )

				# Account deactivation
				if pwoptions.get('lock'):
					cmd += '-L '

				elif option.get('unlock'):
					cmd += '-U '

				cmd += self.sanitize_arg(username)

				# Password
				password = option.get('password')
				self.change_user_password(username, password, pwoptions)

				# Execute
				returncode = self.process(cmd)
				if returncode != 0:
					error = errors.get( returncode, _('unknown error with statuscode %d accured') % (returncode) )
					raise ValueError( _('%s: %s') % (username, error) )

			except ValueError as e:
				response.append( str(e) )

		MODULE.info( 'luga.users_edit: results: %s' % str( response ) )
		self.finished( request.id, response )

	def users_add(self, request):
		"""
			add a local user

			TODO: remove gid, replace by groupname
			TODO: gecos
			TODO: Password changing
		"""
		MODULE.info( 'luga.users_add: options: %s' % str( request.options ) )
	
		if list is not type(request.options):
			raise UMC_OptionTypeError( _("argument type has to be 'list'") )

		request.status = SUCCESS
		response = []
		errors = {
			1: _('could not update password file'),
			2: _('invalid command syntax'),
			3: _('invalid argument to option'),
			4: _('UID already in use (and no -o)'),
			6: _('specified group doesnt exist'),
			9: _('username already in use'),
			10: _('could not update group file'),
			12: _('could not create home directory'),
			13: _('could not create mail spool'),
		}

		for o in request.options:
			try:
				if dict is not type(o) or dict is not type(o.get('object', {})):
					raise UMC_OptionTypeError( _("argument type has to be 'dict'") )

				option = o.get('object', {})
#				options = o.get('options', {})

#				if dict is not type(option): # or dict is not type(options):
#					raise UMC_OptionTypeError( _("argument type has to be 'dict'") )

				# Username
				username = option.get('username')
				if not username:
					raise ValueError( _('No username given') )

				pwoptions = {}
				cmd = '/usr/sbin/useradd '
				cmd += self.get_common_args( option, pwoptions )

				# TODO: rename?
				# Create an own Usergroup as primary group?
				if option.get('create_usergroup'):
					cmd += ' -U'
				else:
					cmd += ' -N'

				cmd += ' %s' % self.sanitize_arg(username)

				# Execute
				returncode = self.process(cmd)
				if 0 != returncode:
					MODULE.error('cmd "%s" failed with returncode %d' % (cmd, returncode)) 
					error = errors.get( returncode, _('unknown error with statuscode %d accured') % (returncode) )
					raise ValueError( '%s: %s' % (username, error) )
				else:
					password = option.get('password')
					self.change_user_password(username, password, pwoptions)
			except UMC_OptionTypeError as e:
				if len(request.options) is 1:
					raise e
				else:
					response.append( str(e) )
			except ValueError as e:
				response.append( str(e) )

		MODULE.info( 'luga.users_add: results: %s' % str( response ) )
		self.finished( request.id, response )

	def users_remove(self, request):
		"""
			remove a list of local users
			param request.options = [ { username: <string>, force: <bool>, remove: <bool> }, ...]
				force: force removal of files, even if not owned by user
				remove: remove home directory and mail spool
		"""
		MODULE.info( 'luga.users_delete: options: %s' % str( request.options ) )

		if list is not type(request.options):
			raise UMC_OptionTypeError( _("argument type has to be 'list'") )

		cmd = '/usr/sbin/userdel '
		request.status = SUCCESS
		response = []
		errors = {
			1: _('could not update password file'),
			2: _('invalid command syntax'),
			6: _('specified user doesnt exist'),
			8: _('user currently logged in'),
			10: _('could not update group file'),
			12: _('could not remove home directory')
		}

		for option in request.options:
			try:
				# TODO: option is a string, not dict...
				# where to get options foreach user?
				# can i hack in JS? alerting user?
				if dict is not type(option):
					raise UMC_OptionTypeError( _("argument type has to be 'dict'") )

				username = option.get('username')

				if None is username:
					raise ValueError( _('No username given') )
				if option.get('force'):
					cmd += ' -f'
				if option.get('remove'):
					cmd += ' -r'

				cmd += ' %s' % self.sanitize_arg(username)

				returncode = self.process(cmd)
				if returncode != 0:
					MODULE.error('cmd "%s" failed with returncode %d' % (cmd, returncode)) 
					error = errors.get( returncode, _('unknown error with statuscode %d accured') % (returncode) )
					raise ValueError( '%s: %s' % (username, error) )
			except ValueError as e:
				response.append( str(e) )

		MODULE.info( 'luga.users_delete: results: %s' % str( response ) )
		self.finished( request.id, response )

