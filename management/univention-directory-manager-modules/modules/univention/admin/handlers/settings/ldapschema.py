# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  direcory manager module for LDAP schema extensions
#
# Copyright 2013-2017 Univention GmbH
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
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization
import apt

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

OC = "univentionLDAPExtensionSchema"

module = 'settings/ldapschema'
superordinate = 'settings/cn'
childs = 0
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Settings: LDAP Schema Extension')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionObjectMetadata', OC],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Schema name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=True
	),
	'filename': univention.admin.property(
		short_description=_('Schema file name'),
		long_description='',
		syntax=univention.admin.syntax.BaseFilename,
		multivalue=False,
		options=[],
		required=True,
		may_change=True,
		default='',
		identifies=False
	),
	'data': univention.admin.property(
		short_description=_('Schema data'),
		long_description='',
		syntax=univention.admin.syntax.Base64Bzip2Text,
		multivalue=False,
		options=[],
		required=True,
		may_change=True,
		identifies=False
	),
	'active': univention.admin.property(
		short_description=_('Active'),
		long_description='',
		syntax=univention.admin.syntax.TrueFalseUp,
		default='FALSE',
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'appidentifier': univention.admin.property(
		short_description=_('App identifier'),
		long_description='',
		syntax=univention.admin.syntax.TextArea,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'package': univention.admin.property(
		short_description=_('Software package'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'packageversion': univention.admin.property(
		short_description=_('Software package version'),
		long_description='',
		syntax=univention.admin.syntax.DebianPackageVersion,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
}

layout = [
	Tab(_('General'), _('Basic values'), layout=[
		Group(_('General LDAP schema extension settings'), layout=[
			["name"],
			["filename"],
			["data"],
		]),
		Group(_('Metadata'), layout=[
			["package"],
			["packageversion"],
			["appidentifier"],
		]),
		Group(_('Activated'), layout=[
			["active"],
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('filename', 'univentionLDAPSchemaFilename', None, univention.admin.mapping.ListToString)
mapping.register('data', 'univentionLDAPSchemaData', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('active', 'univentionLDAPSchemaActive', None, univention.admin.mapping.ListToString)
mapping.register('appidentifier', 'univentionAppIdentifier')
mapping.register('package', 'univentionOwnedByPackage', None, univention.admin.mapping.ListToString)
mapping.register('packageversion', 'univentionOwnedByPackageVersion', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_pre_modify(self):
		diff_keys = [key for key in self.info.keys() if self.info.get(key) != self.oldinfo.get(key) and key not in ('active', 'appidentifier')]
		if not diff_keys:  # check for trivial change
			return
		if not self.hasChanged('package'):
			old_version = self.oldinfo.get('packageversion', '0')
			if not apt.apt_pkg.version_compare(self['packageversion'], old_version) > -1:
				raise univention.admin.uexceptions.valueInvalidSyntax(_('packageversion: Version must not be lower than the current one.'))


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):

	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', OC),
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):

	return OC in attr.get('objectClass', [])
