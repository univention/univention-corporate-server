# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for license handling
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

from univention.admin.layout import Tab, Group
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

import univention.debug

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/license'
superordinate = 'settings/cn'
operations = ['remove', 'search']

childs = 0
short_description = _('Settings: License')
long_description = _('Univention License')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionLicense'],
	),
	'Version 1': univention.admin.option(
		short_description=_('Version 1 license'),
		editable=False,
		default=0
	),
	'Version 2': univention.admin.option(
		short_description=_('Version 2 license'),
		editable=False,
		default=1
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description=_('Name'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=False,
		identifies=True,
	),
	'expires': univention.admin.property(
		short_description=_('Expiry date'),
		long_description=_('License Expiration Date'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=True,
		may_change=False,
		identifies=False,
	),
	'module': univention.admin.property(
		short_description=_('Module'),
		long_description=_('Module the license is valid for'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 1'],
		required=True,
		may_change=False,
		identifies=False,
	),
	'base': univention.admin.property(
		short_description=_('Base DN'),
		long_description=_('Base DN the license is valid for'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=False,
		identifies=False,
	),
	'signature': univention.admin.property(
		short_description=_('Signature'),
		long_description=_('This Signature is used to verify the authenticity of the license.'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=True,
		may_change=False,
		identifies=False,
	),
	'accounts': univention.admin.property(
		short_description=_('Max. user accounts'),
		long_description=_('Maximum number of user accounts managed with the UCS infrastructure'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 1'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'clients': univention.admin.property(
		short_description=_('Max. clients'),
		long_description=_('Maximum number of client hosts managed with the UCS infrastructure'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 1'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'groupwareaccounts': univention.admin.property(
		short_description=_('Max. groupware accounts'),
		long_description=_('Maximum number of groupware accounts managed with the UCS infrastructure'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 1'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'desktops': univention.admin.property(
		short_description=_('Max. desktops'),
		long_description=_('Maximum number of Univention desktop accounts managed with the UCS infrastructure'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 1'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'productTypes': univention.admin.property(
		short_description=_('Valid product types'),
		long_description=_('Product types this license allows.'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=['Version 1'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'oemProductTypes': univention.admin.property(
		short_description=_('Valid OEM product types'),
		long_description=_('OEM Product types this license allows.'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=False,
		identifies=False,
	),
	'product': univention.admin.property(
		short_description=_('Product type'),
		long_description=_('Product type this license allows.'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=False,
		identifies=False,
	),
	'keyID': univention.admin.property(
		short_description=_('Key ID'),
		long_description=_('Key ID of this license.'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 2'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'servers': univention.admin.property(
		short_description=_('Servers'),
		long_description=_('Maximum number of servers this license allows.'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 2'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'support': univention.admin.property(
		short_description=_('Servers with standard support'),
		long_description=_('Servers with standard support.'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 2'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'premiumsupport': univention.admin.property(
		short_description=_('Premium Support'),
		long_description=_('Servers with premium support.'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 2'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'managedclients': univention.admin.property(
		short_description=_('Managed Clients'),
		long_description=_('Maximum number of managed clients this license allows.'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 2'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'users': univention.admin.property(
		short_description=_('Users'),
		long_description=_('Maximum number of users this license allows.'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 2'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'virtualdesktopusers': univention.admin.property(
		short_description=_('DVS users'),
		long_description=_('Maximum number of DVS users this license allows.'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 2'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'virtualdesktopclients': univention.admin.property(
		short_description=_('DVS clients'),
		long_description=_('Maximum number of DVS clients this license allows.'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 2'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'corporateclients': univention.admin.property(
		short_description=_('Corporate clients'),
		long_description=_('Maximum number of corporate clients this license allows.'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 2'],
		required=False,
		may_change=False,
		identifies=False,
	),
	'version': univention.admin.property(
		short_description=_('Version'),
		long_description=_('Version format of this license.'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['Version 2'],
		required=False,
		may_change=False,
		identifies=False,
	),

}

layout = [
	Tab(_('License'), _('Licensing Information'), layout=[
		Group(_('General license settings'), layout=[
			'name',
			'module',
			'expires',
			'base',
			'oemProductTypes',
			'signature',
		]),
		Group(_('Version 1 license informations'), layout=[
			'productTypes',
			['accounts', 'groupwareaccounts'],
			['clients', 'desktops'],
		]),
		Group(_('Version 2 license informations'), layout=[
			'keyID',
			['users', 'servers'],
			['corporateclients', 'managedclients'],
			['virtualdesktopusers', 'virtualdesktopclients'],
			['support', 'premiumsupport'],
			'version',
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('expires', 'univentionLicenseEndDate', None, univention.admin.mapping.ListToString)
mapping.register('module', 'univentionLicenseModule', None, univention.admin.mapping.ListToString)
mapping.register('base', 'univentionLicenseBaseDN', None, univention.admin.mapping.ListToString)
mapping.register('signature', 'univentionLicenseSignature', None, univention.admin.mapping.ListToString)
mapping.register('accounts', 'univentionLicenseAccounts', None, univention.admin.mapping.ListToString)
mapping.register('groupwareaccounts', 'univentionLicenseGroupwareAccounts', None, univention.admin.mapping.ListToString)
mapping.register('clients', 'univentionLicenseClients', None, univention.admin.mapping.ListToString)
mapping.register('desktops', 'univentionLicenseuniventionDesktops', None, univention.admin.mapping.ListToString)
mapping.register('productTypes', 'univentionLicenseType')
mapping.register('oemProductTypes', 'univentionLicenseOEMProduct')
mapping.register('product', 'univentionLicenseProduct', None, univention.admin.mapping.ListToString)
mapping.register('keyID', 'univentionLicenseKeyID', None, univention.admin.mapping.ListToString)
mapping.register('servers', 'univentionLicenseServers', None, univention.admin.mapping.ListToString)
mapping.register('support', 'univentionLicenseSupport', None, univention.admin.mapping.ListToString)
mapping.register('premiumsupport', 'univentionLicensePremiumSupport', None, univention.admin.mapping.ListToString)
mapping.register('managedclients', 'univentionLicenseManagedClients', None, univention.admin.mapping.ListToString)
mapping.register('users', 'univentionLicenseUsers', None, univention.admin.mapping.ListToString)
mapping.register('virtualdesktopusers', 'univentionLicenseVirtualDesktopUsers', None, univention.admin.mapping.ListToString)
mapping.register('virtualdesktopclients', 'univentionLicenseVirtualDesktopClients', None, univention.admin.mapping.ListToString)
mapping.register('corporateclients', 'univentionLicenseCorporateClients', None, univention.admin.mapping.ListToString)
mapping.register('version', 'univentionLicenseVersion', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		if self.oldattr.get('univentionLicenseVersion', []) == ['2']:
			self.options = ['Version 2']
		else:
			self.options = ['Version 1']

		self.save()


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):

	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionLicense')
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	return object.lookup(co, lo, filter, base, superordinate, scope, unique, required, timeout, sizelimit)


def identify(dn, attr, canonical=0):
	return 'univentionLicense' in attr.get('objectClass', [])
