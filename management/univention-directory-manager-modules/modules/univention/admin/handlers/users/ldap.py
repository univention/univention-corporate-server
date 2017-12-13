# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the user objects
#
# Copyright 2004-2017 Univention GmbH
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

import ldap

import univention.admin
from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.groups.group
import univention.admin.password
import univention.admin.samba
import univention.admin.allocators
import univention.admin.localization
import univention.admin.uexceptions
import univention.admin.uldap
import univention.admin.handlers.settings.prohibited_username

import univention.debug
import univention.password

translation = univention.admin.localization.translation('univention.admin.handlers.users')
_ = translation.translate


module = 'users/ldap'
operations = ['add', 'edit', 'remove', 'search', 'move', 'copy']
uid_umlauts_mixedcase = 0

childs = False
short_description = _('Simple authentication Account')
long_description = ''

# {'person': (('sn', 'cn'), ('userPassword', 'telephoneNumber', 'seeAlso', 'description')), 'uidObject': (('uid',), ()), 'univentionPWHistory': ((), ('pwhistory',)), 'simpleSecurityObject': (('userPassword',), ())}
options = {
	'default': univention.admin.option(
		short_description=_('Simple authentication account'),
		default=True,
		objectClasses=['top', 'person', 'univentionPWHistory', 'simpleSecurityObject', 'uidObject'],
	)
}
property_descriptions = {
	'username': univention.admin.property(
		short_description=_('User name'),
		long_description='',
		syntax=univention.admin.syntax.uid_umlauts,
		multivalue=False,
		include_in_default_search=True,
		required=True,
		may_change=True,
		identifies=True,
		readonly_when_synced=True,
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		required=False,
		may_change=True,
		identifies=False,
		readonly_when_synced=True,
		copyable=True,
	),
	'disabled': univention.admin.property(
		short_description=_('Account deactivation'),
		long_description='',
		syntax=univention.admin.syntax.disabled,
		multivalue=False,
		options=['posix', 'samba', 'kerberos'],
		required=False,
		may_change=True,
		identifies=False,
		show_in_lists=True,
		copyable=True,
	),
	'password': univention.admin.property(
		short_description=_('Password'),
		long_description='',
		syntax=univention.admin.syntax.userPasswd,
		multivalue=False,
		options=['posix', 'samba', 'kerberos', 'ldap_pwd'],
		required=True,
		may_change=True,
		identifies=False,
		dontsearch=True,
		readonly_when_synced=True,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('User account'), layout=[
			['username', 'description'],
			'password',
			'disabled',
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('username', 'uid', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('password', 'userPassword', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def __pwd_is_locked(self, password):
		return password and (password.startswith('{crypt}!') or password.startswith('{LANMAN}!'))

	def __pwd_unlocked(self, password):
		if self.__pwd_is_locked(password):
			if password.startswith("{crypt}!"):
				return password.replace("{crypt}!", "{crypt}")
			elif password.startswith('{LANMAN}!'):
				return password.replace("{LANMAN}!", "{LANMAN}")
		return password

	def __pwd_locked(self, password):
		# cleartext password?
		if not password.startswith('{crypt}') and not password.startswith('{LANMAN}'):
			return "{crypt}!%s" % (univention.admin.password.crypt('password'))

		if not self.__pwd_is_locked(password):
			if password.startswith("{crypt}"):
				return password.replace("{crypt}", "{crypt}!")
			elif password.startswith("{LANMAN}"):
				return password.replace("{LANMAN}", "{LANMAN}!")
		return password

	def __pwd_is_auth_saslpassthrough(self, password):
		if password.startswith('{SASL}') and univention.admin.baseConfig.get('directory/manager/web/modules/users/user/auth/saslpassthrough', 'no').lower() == 'keep':
			return 'keep'
		return 'no'

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)
		if self.exists():
			self.modifypassword = 0
			self['password'] = '********'
			userPassword = self.oldattr.get('userPassword', [''])[0]
			if userPassword:
				self.info['password'] = userPassword
				self.modifypassword = 0
				if self.__pwd_is_locked(userPassword):
					self['locked'] = 'posix'
				self.is_auth_saslpassthrough = self.__pwd_is_auth_saslpassthrough(userPassword)
		self.save()

	def _ldap_pre_create(self):
		super(object, self)._ldap_pre_create()
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'users/user: dn was set to %s' % self.dn)
		if not self['password']:
			self['password'] = self.oldattr.get('password', [''])[0]
			self.modifypassword = 0
		else:
			self.modifypassword = 1

		prohibited_objects = univention.admin.handlers.settings.prohibited_username.lookup(self.co, self.lo, '')
		if prohibited_objects and len(prohibited_objects) > 0:
			for i in range(0, len(prohibited_objects)):
				if self['username'] in prohibited_objects[i]['usernames']:
					raise univention.admin.uexceptions.prohibitedUsername(': %s' % self['username'])
		try:
			uid = univention.admin.allocators.request(self.lo, self.position, 'uid', value=self['username'])
		except univention.admin.uexceptions.noLock:
			username = self['username']
			univention.admin.allocators.release(self.lo, self.position, 'uid', username)
			raise univention.admin.uexceptions.uidAlreadyUsed(': %s' % username)

		self.alloc.append(('uid', uid))

#	def _ldap_addlist(self):
#		return al

	def _ldap_post_create(self):
		self._confirm_locks()

	def _ldap_pre_modify(self):
		if self.hasChanged('username'):
			try:
				univention.admin.allocators.request(self.lo, self.position, 'uid', value=self['username'])
			except univention.admin.uexceptions.noLock:
				username = self['username']
				univention.admin.allocators.release(self.lo, self.position, 'uid', username)
				raise univention.admin.uexceptions.uidAlreadyUsed(': %s' % username)

			newdn = 'uid=%s,%s' % (ldap.dn.escape_dn_chars(self['username']), self.lo.parentDn(self.dn))
			self._move(newdn)
			univention.admin.allocators.release(self.lo, self.position, 'uid', self['username'])

		if self.hasChanged('password'):
			if not self['password']:
				self['password'] = self.oldattr.get('password', ['********'])[0]
				self.modifypassword = 0
			elif not self.info['password']:
				self['password'] = self.oldattr.get('password', ['********'])[0]
				self.modifypassword = 0
			else:
				self.modifypassword = 1

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

		disabled = "!" if self['disabled'] else ''

		if self.hasChanged('password'):
			password_crypt = "{crypt}%s%s" % (disabled, univention.admin.password.crypt(self['password']))
			ml.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_crypt))

		if self.hasChanged('locked'):
			if 'posix' in self.options or ('samba' in self.options and self['username'] == 'root'):
				# if self.modifypassword is set the password was already locked
				if not self.modifypassword:
					if self['locked'] in ['all', 'posix']:
						password_disabled = self.__pwd_locked(self['password'])
						ml.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_disabled))
					else:
						password_enabled = self.__pwd_unlocked(self['password'])
						ml.append(('userPassword', self.oldattr.get('userPassword', [''])[0], password_enabled))
						pwdAccountLockedTime = self.oldattr.get('pwdAccountLockedTime', [''])[0]
						if pwdAccountLockedTime:
							ml.append(('pwdAccountLockedTime', pwdAccountLockedTime, ''))

		return ml

	def _ldap_post_remove(self):
		univention.admin.allocators.release(self.lo, self.position, 'uid', self['username'])

		admin_settings_dn = 'uid=%s,cn=admin-settings,cn=univention,%s' % (ldap.dn.escape_dn_chars(self['username']), self.lo.base)
		# delete admin-settings object of user if it exists
		try:
			self.lo.delete(admin_settings_dn)
		except univention.admin.uexceptions.noObject:
			pass

	def _move(self, newdn, modify_childs=True, ignore_license=False):
		olddn = self.dn
		tmpdn = 'cn=%s-subtree,cn=temporary,cn=univention,%s' % (ldap.dn.escape_dn_chars(self['username']), self.lo.base)
		al = [('objectClass', ['top', 'organizationalRole']), ('cn', ['%s-subtree' % self['username']])]
		subelements = self.lo.search(base=self.dn, scope='one', attr=['objectClass'])  # FIXME: identify may fail, but users will raise decode-exception
		if subelements:
			try:
				self.lo.add(tmpdn, al)
			except:
				# real errors will be caught later
				pass
			try:
				moved = dict(self.move_subelements(olddn, tmpdn, subelements, ignore_license))
				subelements = [(moved[subdn], subattrs) for (subdn, subattrs) in subelements]
			except:
				# subelements couldn't be moved to temporary position
				# subelements were already moved back to self
				# stop moving and reraise
				raise
		try:
			dn = super(object, self)._move(newdn, modify_childs, ignore_license)
		except:
			# self couldn't be moved
			# move back subelements and reraise
			self.move_subelements(tmpdn, olddn, subelements, ignore_license)
			raise
		if subelements:
			try:
				moved = dict(self.move_subelements(tmpdn, newdn, subelements, ignore_license))
				subelements = [(moved[subdn], subattrs) for (subdn, subattrs) in subelements]
			except:
				# subelements couldn't be moved to self
				# subelements were already moved back to temporary position
				# move back self, move back subelements to self and reraise
				super(object, self)._move(olddn, modify_childs, ignore_license)
				self.move_subelements(tmpdn, olddn, subelements, ignore_license)
				raise
		return dn

	def cancel(self):
		for i, j in self.alloc:
			univention.admin.allocators.release(self.lo, self.position, i, j)


def lookup_filter(filter_s=None, lo=None):
	lookup_filter_obj = \
		univention.admin.filter.conjunction('&', [
			univention.admin.filter.conjunction('|', [
				univention.admin.filter.conjunction('&', [
					univention.admin.filter.expression('objectClass', 'posixAccount'),
					univention.admin.filter.expression('objectClass', 'shadowAccount'),
				]),
				univention.admin.filter.expression('objectClass', 'univentionMail'),
				univention.admin.filter.expression('objectClass', 'sambaSamAccount'),
				univention.admin.filter.expression('objectClass', 'simpleSecurityObject'),
				univention.admin.filter.expression('objectClass', 'inetOrgPerson'),
			]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('uidNumber', '0')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('uid', '*$')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('univentionObjectFlag', 'functional')]),
		])
	lookup_filter_obj.append_unmapped_filter_string(filter_s, univention.admin.mapping.mapRewrite, mapping)
	return lookup_filter_obj


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	filter = lookup_filter(filter_s)
	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):
	if isinstance(attr.get('uid', []), type([])) and len(attr.get('uid', [])) > 0 and ('$' in attr.get('uid', [])[0]):
		return False

	return (
		(
			('posixAccount' in attr.get('objectClass', []) and 'shadowAccount' in attr.get('objectClass', [])) or
			'univentionMail' in attr.get('objectClass', []) or
			'sambaSamAccount' in attr.get('objectClass', []) or
			'simpleSecurityObject' in attr.get('objectClass', []) or
			(
				'person' in attr.get('objectClass', []) and
				'organizationalPerson' in attr.get('objectClass', []) and
				'inetOrgPerson' in attr.get('objectClass', [])
			)
		) and
		'0' not in attr.get('uidNumber', []) and
		'$' not in attr.get('uid', []) and
		'univentionHost' not in attr.get('objectClass', []) and
		'functional' not in attr.get('univentionObjectFlag', [])
	)
