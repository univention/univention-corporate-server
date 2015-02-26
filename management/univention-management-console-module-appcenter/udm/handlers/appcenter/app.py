# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  direcory manager module for App Metadata
#
# Copyright 2013-2015 Univention GmbH
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

translation=univention.admin.localization.translation('univention.admin.handlers.appcenter')
_=translation.translate

OC = "univentionApp"

module='appcenter/app'
superordinate = 'settings/cn'
childs=0
operations=['add','edit','remove','search','move']
short_description=_('Appcenter: App Metadata')
long_description=''
options={}
property_descriptions={
	'id': univention.admin.property(
	        short_description=_('App ID'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			include_in_default_search=1,
			options=[],
			required=1,
			may_change=1,
			identifies=1
			),
	'name': univention.admin.property(
	        short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			include_in_default_search=1,
			options=[],
			required=1,
			may_change=1,
			identifies=0
			),
	'version': univention.admin.property(
	        short_description=_('Version'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
			),
	'shortDescription': univention.admin.property(
			short_description=_('Short description'),
			long_description='',
			syntax=univention.admin.syntax.TextArea,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'longDescription': univention.admin.property(
			short_description=_('Long description'),
			long_description='',
			syntax=univention.admin.syntax.TextArea,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'vendor': univention.admin.property(
			short_description=_('Vendor'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'contact': univention.admin.property(
			short_description=_('Contact'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'maintainer': univention.admin.property(
			short_description=_('Maintainer'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'website': univention.admin.property(
			short_description=_('Website'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'websiteVendor': univention.admin.property(
			short_description=_('Website Vendor'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'websiteMaintainer': univention.admin.property(
			short_description=_('Website Maintainer'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'screenshot': univention.admin.property(
			short_description=_('Screenshot'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			dontsearch=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'icon': univention.admin.property(
			short_description=_('Icon'),
			long_description='',
			syntax=univention.admin.syntax.Base64Upload,
			multivalue=0,
			dontsearch=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'category': univention.admin.property(
			short_description=_('Category'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'webInterface': univention.admin.property(
			short_description=_('Web Interface'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'webInterfaceName': univention.admin.property(
			short_description=_('Web Interface Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'conflictingApps': univention.admin.property(
			short_description=_('Conflicting Apps'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'conflictingSystemPackages': univention.admin.property(
			short_description=_('Conflicting System Packages'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'defaultPackages': univention.admin.property(
			short_description=_('Default Packages'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'defaultPackagesMaster': univention.admin.property(
			short_description=_('Default Master Packages'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'umcModuleName': univention.admin.property(
			short_description=_('UMC Module Name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'umcModuleFlavor': univention.admin.property(
			short_description=_('UMC Module Flavor'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'serverRole': univention.admin.property(
			short_description=_('Installable on Server Roles'),
			long_description='',
			syntax=univention.admin.syntax.UCSServerRole,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'server': univention.admin.property(
			short_description=_('Installed On Server'),
			long_description='',
			syntax=univention.admin.syntax.UCS_Server,
			multivalue=1,
			include_in_default_search=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	}

layout = [
	Tab(_('General'),_('App Definition'), layout = [
		Group( _( 'General' ), layout = [
			["id"],
			["name"],
			["version"],
			["shortDescription"],
			["longDescription"],
		] ),
		Group( _( 'About' ), layout = [
			["vendor"],
			["contact"],
			["maintainer"],
			["website"],
			["websiteVendor"],
			["websiteMaintainer"],
			["screenshot"],
		] ),
		Group( _( 'Metadata' ), layout = [
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
		] ),
	] ),
]

mapping=univention.admin.mapping.mapping()
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
mapping.register('screenshot', 'univentionAppScreenshot', None, univention.admin.mapping.ListToString)
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
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions
 		self.options=[]

		self.alloc=[]

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes)

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

	def _ldap_pre_create(self):		
		self.dn='univentionAppID=%s,%s' % ( mapping.mapValue('id', self.info['id']), self.position.getDn())

	def _ldap_addlist(self):
		ocs=['top', OC]		

		return [
			('objectClass', ocs),
		]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', OC),
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append( object( co, lo, None, dn, attributes = attrs ) )
	return res

def identify(dn, attr, canonical=0):
	return OC in attr.get('objectClass', [])

