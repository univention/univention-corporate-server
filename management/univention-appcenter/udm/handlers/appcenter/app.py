# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  directory manager module for App Metadata
#
# Copyright 2013-2019 Univention GmbH
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

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.appcenter')
_ = translation.translate

OC = "univentionApp"

module = 'appcenter/app'
superordinate = 'settings/cn'
default_containers = ['cn=apps,cn=univention']
childs = 0
operations = ['add', 'edit', 'remove', 'search', 'move']
short_description = _('Appcenter: App Metadata')
object_name = _('App Metadata')
object_name_plural = _('App Metadata')
long_description = ''
options = {}
property_descriptions = {
	'id': univention.admin.property(
		short_description=_('App ID'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=True
	),
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=False
	),
	'version': univention.admin.property(
		short_description=_('Version'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=True,
		may_change=True,
		identifies=False
	),
	'shortDescription': univention.admin.property(
		short_description=_('Short description'),
		long_description='',
		syntax=univention.admin.syntax.TextArea,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'longDescription': univention.admin.property(
		short_description=_('Long description'),
		long_description='',
		syntax=univention.admin.syntax.TextArea,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'vendor': univention.admin.property(
		short_description=_('Vendor'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'contact': univention.admin.property(
		short_description=_('Contact'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'maintainer': univention.admin.property(
		short_description=_('Maintainer'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'website': univention.admin.property(
		short_description=_('Website'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'websiteVendor': univention.admin.property(
		short_description=_('Website Vendor'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'websiteMaintainer': univention.admin.property(
		short_description=_('Website Maintainer'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'icon': univention.admin.property(
		short_description=_('Icon'),
		long_description='',
		syntax=univention.admin.syntax.Base64Upload,
		multivalue=False,
		dontsearch=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'category': univention.admin.property(
		short_description=_('Category'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'webInterface': univention.admin.property(
		short_description=_('Web Interface'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'webInterfaceName': univention.admin.property(
		short_description=_('Web Interface Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'conflictingApps': univention.admin.property(
		short_description=_('Conflicting Apps'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'conflictingSystemPackages': univention.admin.property(
		short_description=_('Conflicting System Packages'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'defaultPackages': univention.admin.property(
		short_description=_('Default Packages'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'defaultPackagesMaster': univention.admin.property(
		short_description=_('Default Master Packages'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'umcModuleName': univention.admin.property(
		short_description=_('UMC Module Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'umcModuleFlavor': univention.admin.property(
		short_description=_('UMC Module Flavor'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'serverRole': univention.admin.property(
		short_description=_('Installable on Server Roles'),
		long_description='',
		syntax=univention.admin.syntax.UCSServerRole,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'server': univention.admin.property(
		short_description=_('Installed On Server'),
		long_description='',
		syntax=univention.admin.syntax.UCS_Server,
		multivalue=True,
		include_in_default_search=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
}

layout = [
	Tab(_('General'), _('App Definition'), layout=[
		Group(_('General'), layout=[
			["id"],
			["name"],
			["version"],
			["shortDescription"],
			["longDescription"],
		]),
		Group(_('About'), layout=[
			["vendor"],
			["contact"],
			["maintainer"],
			["website"],
			["websiteVendor"],
			["websiteMaintainer"],
		]),
		Group(_('Metadata'), layout=[
			["icon"],
			["category"],
			["webInterface"],
			["webInterfaceName"],
			["conflictingApps"],
			["conflictingSystemPackages"],
			["defaultPackages"],
			["defaultPackagesMaster"],
			["umcModuleName"],
			["umcModuleFlavor"],
			["serverRole"],
			["server"],
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('id', 'univentionAppID', None, univention.admin.mapping.ListToString)
mapping.register('name', 'univentionAppName')
mapping.register('version', 'univentionAppVersion', None, univention.admin.mapping.ListToString)
mapping.register('shortDescription', 'univentionAppDescription')
mapping.register('longDescription', 'univentionAppLongDescription')
mapping.register('vendor', 'univentionAppVendor', None, univention.admin.mapping.ListToString)
mapping.register('contact', 'univentionAppContact', None, univention.admin.mapping.ListToString)
mapping.register('maintainer', 'univentionAppMaintainer', None, univention.admin.mapping.ListToString)
mapping.register('website', 'univentionAppWebsite')
mapping.register('websiteVendor', 'univentionAppWebsiteVendor')
mapping.register('websiteMaintainer', 'univentionAppWebsiteMaintainer')
mapping.register('icon', 'univentionAppIcon', None, univention.admin.mapping.ListToString)
mapping.register('category', 'univentionAppCategory')
mapping.register('webInterface', 'univentionAppWebInterface', None, univention.admin.mapping.ListToString)
mapping.register('webInterfaceName', 'univentionAppWebInterfaceName', None, univention.admin.mapping.ListToString)
mapping.register('conflictingApps', 'univentionAppConflictingApps')
mapping.register('conflictingSystemPackages', 'univentionAppConflictingSystemPackages')
mapping.register('defaultPackages', 'univentionAppDefaultPackages')
mapping.register('defaultPackagesMaster', 'univentionAppDefaultPackagesMaster')
mapping.register('umcModuleName', 'univentionAppUMCModuleName', None, univention.admin.mapping.ListToString)
mapping.register('umcModuleFlavor', 'univentionAppUMCModuleFlavor', None, univention.admin.mapping.ListToString)
mapping.register('serverRole', 'univentionAppServerRole')
mapping.register('server', 'univentionAppInstalledOnServer')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_addlist(self):
		ocs = ['top', OC]

		return [
			('objectClass', ocs),
		]


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
