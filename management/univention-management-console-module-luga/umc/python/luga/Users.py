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
from copy import deepcopy

from univention.lib.i18n import Translation
from univention.management.console.modules import UMC_OptionTypeError, UMC_CommandError, UMC_OptionMissing, Base
from univention.management.console.modules.decorators import *
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

_ = Translation( 'univention-management-console-module-luga' ).translate

class Users:
	def _gid2name(self, gid):
		"""
			return groupname of a group id or empty string if no group was found
		"""
		ret = self._search_groups('gid', gid)
		return ret.pop().get('groupname') if len(ret) < 1 else ''

	def _parse_users(self, category='username', pattern='*'):
		""" parse /etc/passwd and /etc/shadow
			param category: one of [username, uid, gid, fullname, gecos, homedir, shell, group]
			param pattern: a searchpattern
			returns a list of dicts
			return [ { 'username': <username>, 'uid': <user id>, 'gid': <group id>', 'group': <primary group>, 'groups': <additional groups>, 'homedir': <home directory>, 'shell': <user shell>,
						'fullname': <full name>, 'miscellaneous': <misc>, 'roomnumber': <room number>, 'tel_business': <telephone business>, 'tel_private': <telephone private>, 
						'pw_last_change': <>, 'pw_mindays': <>, 'pw_maxdays': <>, 'pw_warndays': <>, 'pw_disabledays': <>, 'disabled_since': <>, 'lock': <>, 'pw_is_expired': <>, 'pw_is_empty': <>
					}, ... ]
		"""

		users = []
		shadows = {}

		try:
			# Parse /etc/shadow
			with open('/etc/shadow') as shadow:
				for user in shadow:
					user = user[:-1].split(':')
					user.pop()
					shadows[ user.pop(0) ] = user

			# Parse /etc/passwd
			with open('/etc/passwd') as passwd:
				for user in passwd:
					# remove trailing newline, split by ':' seperator
					(username, password, uid, gid, gecos, homedir, shell) = user[:-1].split(':')

					# Groups
					group = self._gid2name(gid) # primary group
					groups = self._get_additional_groups(username)
					groups_mixin = groups + [group]

					# Filter
					value = { 'username': username, 'uid': uid, 'gid': gid, 'gecos': gecos.split(','), 'fullname': gecos.split(',').pop(0), 'homedir': homedir, 'shell': shell, 'group': groups_mixin }.get(category, 'username')
					if list is type(value):
						for val in value:
							if fnmatch(str(value), pattern):
								break
						else:
							continue
					elif not fnmatch(str(value), pattern):
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

					for i in (1, 2, 3, 4):
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

		except (KeyError, IndexError, ValueError):
			raise UMC_CommandError(_('passwd/shadow file is corrupt'))
		except IOError:
			# no permissions, file does not exists
			raise UMC_CommandError(_('Could not open passwd/shadow file'))
		return users

	def _change_user_password(self, username, password, options={}):
		"""
			change the userpassword and options for <username>
			raises ValueError on error
		"""
		errors = {
			1: _('permission denied'),
			2: _('invalid combination of options'),
			3: _('unexpected failure, nothing done'),
			4: _('unexpected failure, passwd file missing'),
			5: _('passwd file busy, try again'),
			6: _('invalid argument to option'),
		}
		cmd = ['/usr/bin/passwd', '-q']

		if options.get('delete'):
			cmd.append('-d')
		if options.get('expire'):
			cmd.append('-e')
		if options.get('keep_tokens'):
			cmd.append('-k')
		if options.get('lock'):
			cmd.append('-l')
		# if no password is set you can not unlock a user
		elif options.get('unlock') and password:
			cmd.append('-u')

		inactive = options.get('disabledays')
		if inactive:
			cmd += ['-i', self.sanitize_int(inactive)]

		mindays = options.get('mindays')
		if mindays:
			cmd += ['-n', self.sanitize_int(mindays)]

		warndays = options.get('warndays')
		if warndays:
			cmd += ['-w', self.sanitize_int(warndays)]
			
		maxdays = options.get('maxdays')
		if maxdays:
			cmd += ['-x', self.sanitize_int(maxdays)]

		# Change password
		if password:
			pwd = ['/usr/bin/passwd', '-q', self.sanitize_arg(username)]
			returncode = self.process(pwd, '%s\n%s' % (password, password))
			if 0 != returncode:
				MODULE.error("cmd '%s' failed with returncode %d" % (pwd, returncode)) 
				error = errors.get(returncode, _('unknown error with statuscode %d') % (returncode))
				raise ValueError( _('an error accured while changing password: %s') % (error) )

		# Change options
		if len(cmd) > 2:
			cmd.append(self.sanitize_arg(username))
			returncode = self.process(cmd)
			if 0 != returncode:
				MODULE.error("cmd '%s' failed with returncode %d" % (cmd, returncode)) 
				error = errors.get(returncode, _('unknown error with statuscode %d') % (returncode))
				raise ValueError( _('an error accured while changing password options: %s') % (error) )

		return True

	@check_request_options()
	@log_request_options()
	@simple_response
	def users_query( self, category = 'username', pattern = '*'):
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

		response = self._parse_users( category, pattern )
		MODULE.info( 'luga.users_query: results: %s' % response )
		return response

	@log_request_options()
	#@check_request_options()
	@simple_response
	def users_get_users(self, category = 'username', pattern = '*'):
		"""
			returns a shorten list containing a dict for each user
			[ {'id': <username>, 'label': <username>}, ... ]
		"""
#		response = [ {'id': u['username'], 'label': u['username']} for u in self._parse_users(category, pattern) ]
		response = [ u['username'] for u in self._parse_users(category, pattern) ]

		MODULE.info( 'luga.users_query: results: %s' % str(response) )
		return response

	def _get_group_members(self, groupname):
		"""
			returns a list containing all users which are in <groupname> as strings
			[ <username>, <username2>, ... ]
		"""
		return map( lambda u: u['username'], self._parse_users('groupname', groupname) )

	@log_request_options()
	@check_request_options(list)
	def users_get( self, request ):
		"""
			returns a list of dicts containing user information from requested usernames
			param request.options = [ <username>, <username2>, ... ]
			return [ {<user>}, {<user2>}, ... ]
		"""
		userdict = {}
		for user in self._parse_users():
			if user['username'] in request.options:
				userdict[user['username']] = user
		response = [ userdict.get(username) for username in request.options ]

		MODULE.info( 'luga.users_get: results: %s' % str(response) )
		self.finished(request.id, response, status=SUCCESS)

	def _get_common_args( self, options, pwoptions={} ):
		"""
			get args which are equal for put and add
			can also modify an dict with password options
			return string
		"""

		cmd = []

		# Gecos
		gecos = [options.get('fullname'), options.get('roomnumber'), options.get('tel_business'), options.get('tel_private'), options.get('miscellaneous')]
		gecos = set([None]) != set(gecos)

		if gecos:
			keys = ['fullname', 'roomnumber', 'tel_business', 'tel_private', 'miscellaneous']
			gecos = map(lambda s: str(options.get(s, '')).replace(',', ''), keys)
			cmd += ['-c', self.sanitize_arg(','.join(gecos))]

		# Home directory
		homedir = options.get('homedir')
		if homedir:
			cmd += ['-d', self.sanitize_arg(homedir)]
			if options.get('create_home'):
				cmd.append('-m')

		# Shell
		shell = options.get('shell')
		if shell:
			cmd += ['-s', self.sanitize_arg(shell)]

		# User-ID
		uid = str(options.get('uid', ''))
		if uid.isdigit():
			cmd += ['-u', self.sanitize_int(uid)]

		# Additional groups
		groups = options.get('groups')
		if groups:
			cmd += ['-G', self.sanitize_arg( ','.join(list(groups))) ]

		# Primary Group
		group = options.get('group')
		if not options.get('create_usergroup') and group:
			cmd += ['-g', self.sanitize_arg( group )]

		# Password options
		if options.get('pw_remove'):
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

		inactive = options.get('pw_disabledays')
		if inactive:
			pwoptions['disabledays'] = inactive

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

	@log_request_options(['password'])
	@check_request_options((list, tuple,))
	def users_put( self, request ):
		"""
			modify a local user
		"""

		response = []
		errors = {
			# no information about returncodes, yet
		}

		for o in request.options:
			try:
				message = ''
				self.validate_type(o, dict)
				self.validate_type(o.get('object', {}), dict)
				option = o.get('object', {})

				# Username
				username = option.get('$username$')
				new_username = option.get('username')
				if not username:
					raise ValueError( _('No username given') )

				pwoptions = {}
				cmd = ['/usr/sbin/usermod']
				cmd += self._get_common_args( option, pwoptions )

				# Change username
				if new_username and username != new_username:
					self.validate_name(new_username)
					cmd += ['-l', self.sanitize_arg(new_username)]

				# Account deactivation
				if pwoptions.get('lock'):
					cmd.append('-L')

				elif option.get('unlock'):
					cmd.append('-U')

				# Password
				password = option.get('password')
				self._change_user_password(username, password, pwoptions)

				# Execute
				if len(cmd) > 1:
					cmd.append(self.sanitize_arg(username))
					returncode = self.process(cmd)
					if returncode != 0:
						MODULE.error("cmd '%s' failed with returncode %d" % (cmd, returncode))
						error = errors.get( returncode, _('unknown error with statuscode %d accured') % (returncode) )
						raise ValueError( error )

			except ValueError as e:
				message = (username + ': ' if type(username) is str else '') + str(e)
			finally:
				response.append( message )

		MODULE.info( 'luga.users_edit: results: %s' % str(response) )
		self.finished(request.id, response, status=SUCCESS)

	@log_request_options(['password'])
	@check_request_options((list, tuple,))
	def users_add(self, request):
		"""
			add a local user
		"""

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
				message = ''
				self.validate_type(o, dict)
				self.validate_type(o.get('object', {}), dict)
				option = o.get('object', {})

				# Username
				username = option.get('username')
				self.validate_name(username)

				pwoptions = {}
				cmd = ['/usr/sbin/useradd', '-r']

				if username == option.get('group'):
					option['create_usergroup'] = True
					cmd.append('-U')
				else:
					cmd.append('-N')

				cmd += self._get_common_args( option, pwoptions )

				# Execute
				cmd.append(self.sanitize_arg(username))
				returncode = self.process(cmd)
				if 0 != returncode:
					MODULE.error("cmd '%s' failed with returncode %d" % (cmd, returncode))
					error = errors.get( returncode, _('unknown error with statuscode %d occurred') % (returncode) )
					raise ValueError( error )

				# Change Password + options
				password = option.get('password')
				self._change_user_password(username, password, pwoptions)
			except ValueError as e:
				message = (username + ': ' if type(username) is str else '') + str(e)
			finally:
				response.append( message )

		MODULE.info( 'luga.users_add: results: %s' % str(response) )
		self.finished(request.id, response, status=SUCCESS)

	@log_request_options()
	@check_request_options((list, tuple,))
	def users_remove(self, request):
		"""
			remove a list of local users
			param request.options = [ { username: <string>, force: <bool>, remove: <bool> }, ...]
				force: force removal of files, even if not owned by user
				remove: remove home directory and mail spool
		"""

		response = []
		errors = {
			1: _('could not update password file'),
			2: _('invalid command syntax'),
			6: _('specified user doesnt exist'),
			8: _('user currently logged in'),
			10: _('could not update group file'),
			12: _('could not remove home directory or mail spool')
		}

		for option in request.options:
			try:
				message = ''
				if dict is not type(option):
					raise UMC_OptionTypeError( _("argument type has to be 'dict'") )

				cmd = ['/usr/sbin/userdel']

				username = option.get('object')
				if None is username:
					raise ValueError( _('No username given') )

				options = self.sanitize_dict(option.get('options', {}))
				if options.get('force'):
					cmd.append('-f')
				if options.get('remove'):
					cmd.append('-r')

				cmd.append(self.sanitize_arg(username))

				returncode = self.process(cmd)
				if returncode != 0:
					MODULE.error("cmd '%s' failed with returncode %d" % (cmd, returncode)) 
					error = errors.get( returncode, _('unknown error with statuscode %d accured') % (returncode) )
					raise ValueError( error )
			except ValueError as e:
				message = (username + ': ' if type(username) is str else '') + str(e)
			finally:
				response.append( message )

		MODULE.info( 'luga.users_remove: results: %s' % str(response) )
		self.finished(request.id, response, status=SUCCESS)

