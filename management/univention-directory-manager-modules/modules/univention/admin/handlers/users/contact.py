# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the user objects
#
# Copyright 2018-2019 Univention GmbH
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

import univention.admin
from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.allocators
import univention.admin.localization
import univention.admin.uexceptions

import univention.debug as ud

from univention.admin.handlers.users.user import mapHomePostalAddress, unmapHomePostalAddress

translation = univention.admin.localization.translation('univention.admin.handlers.users')
_ = translation.translate

module = 'users/contact'
operations = ['add', 'edit', 'remove', 'search', 'move']

childs = 0
short_description = _('Contact')
object_name = _('Contact')
object_name_plural = _('Contact information')
long_description = _('Contact information')

options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'person', 'inetOrgPerson', 'organizationalPerson']
	)
}
property_descriptions = {
	'cn': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.TwoThirdsString,
		include_in_default_search=True,
		identifies=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'lastname': univention.admin.property(
		short_description=_('Last name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'firstname': univention.admin.property(
		short_description=_('First name'),
		long_description='',
		syntax=univention.admin.syntax.TwoThirdsString,
		include_in_default_search=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'title': univention.admin.property(
		short_description=_('Title'),
		long_description='',
		syntax=univention.admin.syntax.OneThirdString,
		readonly_when_synced=True,
		copyable=True,
	),
	'initials': univention.admin.property(
		short_description=_('Initials'),
		long_description='',
		syntax=univention.admin.syntax.string6,
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
	'displayName': univention.admin.property(
		short_description=_('Display name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		default='<firstname> <lastname><:strip>',
		readonly_when_synced=True,
		copyable=True,
	),
	'birthday': univention.admin.property(
		short_description=_('Birthdate'),
		long_description='',
		syntax=univention.admin.syntax.iso8601Date,
		copyable=True,
	),
	'jpegPhoto': univention.admin.property(
		short_description=_("Picture of the user (JPEG format)"),
		long_description=_('Picture for user account in JPEG format'),
		syntax=univention.admin.syntax.jpegPhoto,
		dontsearch=True,
		copyable=True,
	),
	'organisation': univention.admin.property(
		short_description=_('Organisation'),
		long_description='',
		syntax=univention.admin.syntax.string64,
		readonly_when_synced=True,
		copyable=True,
	),
	'employeeNumber': univention.admin.property(
		short_description=_('Employee number'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		copyable=True,
	),
	'employeeType': univention.admin.property(
		short_description=_('Employee type'),
		long_description='',
		syntax=univention.admin.syntax.string,
		copyable=True,
	),
	'secretary': univention.admin.property(
		short_description=_('Superior'),
		long_description='',
		syntax=univention.admin.syntax.UserDN,
		multivalue=True,
		copyable=True,
	),
	'e-mail': univention.admin.property(
		short_description=_('E-mail address'),
		long_description='',
		syntax=univention.admin.syntax.emailAddress,
		multivalue=True,
	),
	'phone': univention.admin.property(
		short_description=_('Telephone number'),
		long_description='',
		syntax=univention.admin.syntax.phone,
		multivalue=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'roomNumber': univention.admin.property(
		short_description=_('Room number'),
		long_description='',
		syntax=univention.admin.syntax.OneThirdString,
		multivalue=True,
		copyable=True,
	),
	'departmentNumber': univention.admin.property(
		short_description=_('Department number'),
		long_description='',
		syntax=univention.admin.syntax.OneThirdString,
		multivalue=True,
		copyable=True,
	),
	'street': univention.admin.property(
		short_description=_('Street'),
		long_description='',
		syntax=univention.admin.syntax.string,
		readonly_when_synced=True,
		copyable=True,
	),
	'postcode': univention.admin.property(
		short_description=_('Postal code'),
		long_description='',
		syntax=univention.admin.syntax.OneThirdString,
		readonly_when_synced=True,
		copyable=True,
	),
	'postOfficeBox': univention.admin.property(
		short_description=_('Post office box'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		copyable=True,
	),
	'preferredLanguage': univention.admin.property(
		short_description=_('Preferred language'),
		long_description='',
		syntax=univention.admin.syntax.string,
		copyable=True,
	),
	'city': univention.admin.property(
		short_description=_('City'),
		long_description='',
		syntax=univention.admin.syntax.TwoThirdsString,
		readonly_when_synced=True,
		copyable=True,
	),
	'country': univention.admin.property(
		short_description=_('Country'),
		long_description='',
		syntax=univention.admin.syntax.Country,
		readonly_when_synced=True,
		copyable=True,
	),
	'homeTelephoneNumber': univention.admin.property(
		short_description=_('Private telephone number'),
		long_description='',
		syntax=univention.admin.syntax.phone,
		multivalue=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'mobileTelephoneNumber': univention.admin.property(
		short_description=_('Mobile phone number'),
		long_description='',
		syntax=univention.admin.syntax.phone,
		multivalue=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'pagerTelephoneNumber': univention.admin.property(
		short_description=_('Pager telephone number'),
		long_description='',
		syntax=univention.admin.syntax.phone,
		multivalue=True,
		readonly_when_synced=True,
		copyable=True,
	),
	'homePostalAddress': univention.admin.property(
		short_description=_('Private postal address'),
		long_description='',
		syntax=univention.admin.syntax.postalAddress,
		multivalue=True,
		copyable=True,
	),
	'preferredDeliveryMethod': univention.admin.property(
		short_description=_('Preferred delivery method'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'physicalDeliveryOfficeName': univention.admin.property(
		short_description=_('Delivery office name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		copyable=True,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('User account'), layout=[
			['title', 'firstname', 'lastname'],
			['description'],
		]),
		Group(_('Personal information'), layout=[
			'displayName',
			'birthday',
			'jpegPhoto',
		]),
		Group(_('Organisation'), layout=[
			'organisation',
			['employeeNumber', 'employeeType'],
			'secretary',
		]),
	]),
	Tab(_('Contact'), _('Contact information'), layout=[
		Group(_('Business'), layout=[
			'e-mail',
			'phone',
			['roomNumber', 'departmentNumber'],
			['street', 'postcode', 'city', 'country'],
		]),
		Group(_('Private'), layout=[
			'homeTelephoneNumber',
			'mobileTelephoneNumber',
			'pagerTelephoneNumber',
			'homePostalAddress'
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('cn', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('lastname', 'sn', None, univention.admin.mapping.ListToString)
mapping.register('firstname', 'givenName', None, univention.admin.mapping.ListToString)
mapping.register('title', 'title', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('displayName', 'displayName', None, univention.admin.mapping.ListToString)
mapping.register('birthday', 'univentionBirthday', None, univention.admin.mapping.ListToString)
mapping.register('jpegPhoto', 'jpegPhoto', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('organisation', 'o', None, univention.admin.mapping.ListToString)
mapping.register('employeeNumber', 'employeeNumber', None, univention.admin.mapping.ListToString)
mapping.register('employeeType', 'employeeType', None, univention.admin.mapping.ListToString)
mapping.register('secretary', 'secretary')
mapping.register('e-mail', 'mail')
mapping.register('preferredLanguage', 'preferredLanguage', None, univention.admin.mapping.ListToString)
mapping.register('preferredDeliveryMethod', 'preferredDeliveryMethod', None, univention.admin.mapping.ListToString)
mapping.register('phone', 'telephoneNumber')
mapping.register('roomNumber', 'roomNumber')
mapping.register('departmentNumber', 'departmentNumber')
mapping.register('physicalDeliveryOfficeName', 'physicalDeliveryOfficeName', None, univention.admin.mapping.ListToString)
mapping.register('street', 'street', None, univention.admin.mapping.ListToString)
mapping.register('postcode', 'postalCode', None, univention.admin.mapping.ListToString)
mapping.register('postOfficeBox', 'postOfficeBox')
mapping.register('city', 'l', None, univention.admin.mapping.ListToString)
mapping.register('country', 'st', None, univention.admin.mapping.ListToString)
mapping.register('homeTelephoneNumber', 'homePhone')
mapping.register('mobileTelephoneNumber', 'mobile')
mapping.register('pagerTelephoneNumber', 'pager')
mapping.register('homePostalAddress', 'homePostalAddress', mapHomePostalAddress, unmapHomePostalAddress)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def description(self):
		description = '%s %s' % (self['firstname'] or '', self['lastname'])
		return description.strip()

	def get_candidate_dn(self):
		dn = self._ldap_dn()
		if self.exists():
			rdn = self.lo.explodeDn(dn)[0]
			dn = '%s,%s' % (rdn, self.lo.parentDn(self.dn))
		return dn

	def unique_dn(self):
		candidate_dn = self.get_candidate_dn()
		try:
			self.lo.searchDn(base=candidate_dn, scope='base')
		except univention.admin.uexceptions.noObject:
			return True
		else:
			return False

	def acquire_unique_dn(self):
		nonce = 1
		cn = '%s %s %d' % (self['firstname'] or '', self['lastname'], nonce,)
		self['cn'] = cn.strip()
		while not self.unique_dn():
			nonce += 1
			cn = '%s %s %d' % (self['firstname'] or '', self['lastname'], nonce,)
			self['cn'] = cn.strip()
		return self.get_candidate_dn()

	def _ldap_pre_ready(self):
		super(object, self)._ldap_pre_ready()

		if not self.exists() or self.hasChanged(('firstname', 'lastname',)):
			self.acquire_unique_dn()

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
		ml = self._modlist_display_name(ml)
		ml = self._modlist_univention_person(ml)
		return ml

	def _modlist_display_name(self, ml):
		# update displayName automatically if no custom value has been entered by the user and the name changed
		if self.info.get('displayName') == self.oldinfo.get('displayName') and (self.info.get('firstname') != self.oldinfo.get('firstname') or self.info.get('lastname') != self.oldinfo.get('lastname')):
			prop_displayName = self.descriptions['displayName']
			old_default_displayName = prop_displayName._replace(prop_displayName.base_default, self.oldinfo)
			# does old displayName match with old default displayName?
			if self.oldinfo.get('displayName', '') == old_default_displayName:
				# yes ==> update displayName automatically
				new_displayName = prop_displayName._replace(prop_displayName.base_default, self)
				ml.append(('displayName', self.oldattr.get('displayName', [''])[0], new_displayName))
		return ml

	def _modlist_univention_person(self, ml):
		if self.hasChanged('birthday'):
			# make sure that univentionPerson is set as objectClass when birthday is set
			if self['birthday'] and 'univentionPerson' not in self.oldattr.get('objectClass', []):
				ml.append(('objectClass', '', 'univentionPerson'))
			# remove univentionPerson as objectClass when birthday is unset
			elif not self['birthday'] and 'univentionPerson' in self.oldattr.get('objectClass', []):
				ml.append(('objectClass', 'univentionPerson', ''))
		return ml

	def _move(self, newdn, modify_childs=True, ignore_license=False):
		olddn = self.dn

		# acquire unique dn in new position
		self.dn = newdn
		newdn = self.acquire_unique_dn()
		self.dn = olddn

		self.lo.rename(self.dn, newdn)
		self.dn = newdn

		try:
			self._move_in_groups(olddn)  # can be done always, will do nothing if oldinfo has no attribute 'groups'
			self._move_in_subordinates(olddn)
			self._ldap_post_move(olddn)
		except:
			# move back
			ud.debug(ud.ADMIN, ud.WARN, 'simpleLdap._move: self._ldap_post_move failed, move object back to %s' % olddn)
			self.lo.rename(self.dn, olddn)
			self.dn = olddn
			raise
		return self.dn

	@classmethod
	def unmapped_lookup_filter(cls):
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'person'),
			univention.admin.filter.expression('objectClass', 'inetOrgPerson'),
			univention.admin.filter.expression('objectClass', 'organizationalPerson'),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'posixAccount')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'shadowAccount')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'sambaSamAccount')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'krb5Principal')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'krb5KDCEntry')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'univentionMail')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'simpleSecurityObject')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'uidObject')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'pkiUser')]),
		])


lookup = object.lookup


def identify(dn, attr, canonical=0):
	# FIXME is this if block needed? copy pasted from users/user
	if '0' in attr.get('uidNumber', []) or '$' in attr.get('uid', [''])[0] or 'univentionHost' in attr.get('objectClass', []) or 'functional' in attr.get('univentionObjectFlag', []):
		return False

	required_ocs = {'person', 'inetOrgPerson', 'organizationalPerson', }
	forbidden_ocs = {'posixAccount', 'shadowAccount', 'sambaSamAccount', 'krb5Principal', 'krb5KDCEntry', 'univentionMail', 'simpleSecurityObject', 'uidObject', 'pkiUser', }
	ocs = set(attr.get('objectClass', []))
	return (ocs & required_ocs == required_ocs) and not (ocs & forbidden_ocs)
