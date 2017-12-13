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
from univention.admin.handlers.users.user import _password_is_locked, _get_locked_password, _get_unlocked_password, check_prohibited_username

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
		syntax=univention.admin.syntax.boolean,
		multivalue=False,
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

	def open(self):
		super(object, self).open()
		if self.exists():
			self.info['disabled'] = _password_is_locked(self['password'])
		self.save()

	def _ldap_pre_ready(self):
		super(object, self)._ldap_pre_ready()

		if not self.exists() or self.hasChanged('username'):
			check_prohibited_username(self.lo, self['username'])

		# get lock for username
		if not self.exists() or self.hasChanged('username'):
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

		# The order here is important!
		if self.hasChanged('password'):
			# 1. a new plaintext password is supplied
			# make a crypt password out of it
			self['password'] = "{crypt}%s" % (univention.admin.password.crypt(self['password']),)

		if self['disabled']:
			self['password'] = _get_locked_password(self['password'])
		else:
			self['password'] = _get_unlocked_password(self['password'])

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
