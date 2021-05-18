# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the simple authentication account objects
#
# Copyright 2004-2021 Univention GmbH
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

from __future__ import absolute_import

import ldap

import univention.admin
from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization
import univention.admin.uexceptions
from univention.admin.handlers.users.user import check_prohibited_username

translation = univention.admin.localization.translation('univention.admin.handlers.users')
_ = translation.translate

module = 'users/ldap'
operations = ['add', 'edit', 'remove', 'search', 'move', 'copy']

childs = False
short_description = _('Simple authentication account')
object_name = _('Simple authentication account')
object_name_plural = _('Simple authentication accounts')
long_description = _('This user object can only simply do an LDAP bind. It is intended for functional purposes and is not counted as user object in the license.')

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
		include_in_default_search=True,
		required=True,
		identifies=True,
		readonly_when_synced=True,
	),
	'lastname': univention.admin.property(
		short_description=_('Last name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
		default='<username><:umlauts,strip>',
		readonly_when_synced=True,
		copyable=True,
	),
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.TwoThirdsString,
		include_in_default_search=True,
		required=True,
		default='<username><:umlauts,strip>',
		readonly_when_synced=True,
		copyable=True,
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'disabled': univention.admin.property(
		short_description=_('Account deactivation'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		dontsearch=True,
		show_in_lists=True,
		copyable=True,
	),
	'password': univention.admin.property(
		short_description=_('Password'),
		long_description='',
		syntax=univention.admin.syntax.userPasswd,
		required=True,
		dontsearch=True,
		readonly_when_synced=True,
	),
	'locked': univention.admin.property(
		short_description=_('Reset lockout'),
		long_description=_('If the account is locked out due to too many login failures, this checkbox allows unlocking.'),
		syntax=univention.admin.syntax.locked,
		show_in_lists=True,
		default='0',
	),
	'overridePWHistory': univention.admin.property(
		short_description=_('Override password history'),
		long_description=_('No check if the password was already used is performed.'),
		syntax=univention.admin.syntax.boolean,
		dontsearch=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'overridePWLength': univention.admin.property(
		short_description=_('Override password check'),
		long_description=_('No check for password quality and minimum length is performed.'),
		syntax=univention.admin.syntax.boolean,
		dontsearch=True,
		readonly_when_synced=True,
		copyable=True,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('User account'), layout=[
			['username', 'description'],
			['password'],
			['overridePWHistory', 'overridePWLength'],
			['disabled'],
			['locked'],
		]),
	]),
]


def unmapLocked(oldattr):
	if isLDAPLocked(oldattr):
		return '1'
	return '0'


def isLDAPLocked(oldattr):
	return bool(oldattr.get('pwdAccountLockedTime', [''])[0])


mapping = univention.admin.mapping.mapping()
mapping.register('username', 'uid', None, univention.admin.mapping.ListToString)
mapping.register('lastname', 'sn', None, univention.admin.mapping.ListToString)
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('password', 'userPassword', univention.admin.mapping.dontMap(), univention.admin.mapping.ListToString)

mapping.registerUnmapping('locked', unmapLocked)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def open(self):
		super(object, self).open()
		if self.exists():
			self.info['disabled'] = '1' if univention.admin.password.is_locked(self['password']) else '0'
		self.save()

	def _ldap_pre_ready(self):
		super(object, self)._ldap_pre_ready()

		if not self.exists() or self.hasChanged('username'):
			check_prohibited_username(self.lo, self['username'])

			# get lock for username
			try:
				self.alloc.append(('uid', univention.admin.allocators.request(self.lo, self.position, 'uid', value=self['username'])))
			except univention.admin.uexceptions.noLock:
				raise univention.admin.uexceptions.uidAlreadyUsed(self['username'])

	def _ldap_post_create(self):
		self._confirm_locks()

	def _ldap_pre_modify(self):
		if self.hasChanged('username'):
			username = self['username']
			try:
				newdn = 'uid=%s,%s' % (ldap.dn.escape_dn_chars(username), self.lo.parentDn(self.dn))
				self._move(newdn)
			finally:
				univention.admin.allocators.release(self.lo, self.position, 'uid', username)

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

		ml = self._modlist_lastname(ml)
		ml = self._modlist_cn(ml)
		ml = self._modlist_pwd_account_locked_time(ml)
		ml = self._modlist_posix_password(ml)

		if self.hasChanged(['password']):
			pwhistoryPolicy = univention.admin.password.PasswortHistoryPolicy(self.loadPolicyObject('policies/pwhistory'))
			ml = self._check_password_history(ml, pwhistoryPolicy)
			self._check_password_complexity(pwhistoryPolicy)

		return ml

	# If you change anything here, please also check users/user.py
	def _modlist_posix_password(self, ml):
		if not self.exists() or self.hasChanged(['disabled', 'password']):
			old_password = self.oldattr.get('userPassword', [''])[0]
			password = self['password']

			if self.hasChanged('password') and univention.admin.password.RE_PASSWORD_SCHEME.match(password):
				# hacking attempt. user tries to change the password to e.g. {KINIT} or {crypt}$6$...
				raise univention.admin.uexceptions.valueError(_('Invalid password.'), property='password')

			if univention.admin.password.password_is_auth_saslpassthrough(old_password):
				# do not change {SASL} password, but lock it if necessary
				password = old_password

			password_hash = univention.admin.password.lock_password(password)
			if self['disabled'] != '1':
				password_hash = univention.admin.password.unlock_password(password_hash)
			ml.append(('userPassword', old_password, password_hash))
		return ml

	def _modlist_lastname(self, ml):
		if not self.exists() and not self['lastname']:
			prop = self.descriptions['lastname']
			sn = prop._replace(prop.base_default, self)
			ml.append(('sn', '', sn))
		return ml

	def _modlist_cn(self, ml):
		if not self.exists() and not self['name']:
			prop = self.descriptions['name']
			cn = prop._replace(prop.base_default, self)
			ml.append(('cn', '', cn))
		return ml

	def _modlist_pwd_account_locked_time(self, ml):
		# remove pwdAccountLockedTime during unlocking
		if self.hasChanged('locked') and self['locked'] == '0':
			pwdAccountLockedTime = self.oldattr.get('pwdAccountLockedTime', [''])[0]
			if pwdAccountLockedTime:
				ml.append(('pwdAccountLockedTime', pwdAccountLockedTime, ''))
		return ml

	# If you change anything here, please also check users/user.py
	def _check_password_history(self, ml, pwhistoryPolicy):
		if not self.hasChanged('password'):
			return ml
		if self['overridePWHistory'] == '1':
			return ml

		pwhistory = self.oldattr.get('pwhistory', [''])[0]

		if univention.admin.password.password_already_used(self['password'], pwhistory):
			raise univention.admin.uexceptions.pwalreadyused()

		if pwhistoryPolicy.pwhistoryLength is not None:
			newPWHistory = univention.admin.password.get_password_history(self['password'], pwhistory, pwhistoryPolicy.pwhistoryLength)
			ml.append(('pwhistory', self.oldattr.get('pwhistory', [''])[0], newPWHistory))

		return ml

	# If you change anything here, please also check users/user.py
	def _check_password_complexity(self, pwhistoryPolicy):
		if not self.hasChanged('password'):
			return
		if self['overridePWLength'] == '1':
			return

		password_minlength = max(0, pwhistoryPolicy.pwhistoryPasswordLength) or self.password_length
		if len(self['password']) < password_minlength:
			raise univention.admin.uexceptions.pwToShort(_('The password is too short, at least %d characters needed!') % (password_minlength,))

		if pwhistoryPolicy.pwhistoryPasswordCheck:
			pwdCheck = univention.password.Check(self.lo)
			pwdCheck.enableQualityCheck = True
			try:
				pwdCheck.check(self['password'], username=self['username'])
			except ValueError as e:
				raise univention.admin.uexceptions.pwQuality(str(e).replace('W?rterbucheintrag', 'Wörterbucheintrag').replace('enth?lt', 'enthält'))

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

	@classmethod
	def unmapped_lookup_filter(cls):
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'simpleSecurityObject'),
			univention.admin.filter.expression('objectClass', 'uidObject'),
			univention.admin.filter.expression('objectClass', 'person'),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'posixAccount')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('uidNumber', '0')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('uid', '*$')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('univentionObjectFlag', 'functional')]),
		])

	@classmethod
	def _ldap_attributes(cls):
		return ['*', 'pwdAccountLockedTime']


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn, attr, canonical=0):
	if '0' in attr.get('uidNumber', []) or '$' in attr.get('uid', [''])[0] or 'univentionHost' in attr.get('objectClass', []) or 'functional' in attr.get('univentionObjectFlag', []):
		return False

	required_ocs = {'person', 'simpleSecurityObject', 'uidObject', }
	forbidden_ocs = {'posixAccount', 'shadowAccount', 'sambaSamAccount', 'univentionMail', 'krb5Principal', 'krb5KDCEntry'}
	ocs = set(attr.get('objectClass', []))
	return (ocs & required_ocs == required_ocs) and not (ocs & forbidden_ocs)
