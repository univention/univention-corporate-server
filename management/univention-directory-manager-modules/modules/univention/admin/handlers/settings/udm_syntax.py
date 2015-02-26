# -*- coding: utf-8 -*-
#
# Univention Directory Manager Syntax Extensions
#  direcory manager module for UDM syntax extensions
#
# Copyright 2013-2014 Univention GmbH
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

import os

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization
import apt

translation=univention.admin.localization.translation('univention.admin.handlers.settings')
_=translation.translate

OC = "univentionUDMSyntax"

module='settings/udm_syntax'
superordinate='settings/cn'
childs=0
operations=['add','edit','remove','search','move']
short_description=_('Settings: UDM Syntax')
long_description=''
options={}
property_descriptions={
	'name': univention.admin.property(
	        short_description=_('UDM syntax name'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			include_in_default_search=1,
			options=[],
			required=1,
			may_change=1,
			identifies=1
			),
	'filename': univention.admin.property(
			short_description=_('UDM syntax file name'),
			long_description='',
			syntax=univention.admin.syntax.BaseFilename,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			default = '',
			identifies=0
			),
	'data': univention.admin.property(
			short_description=_('UDM syntax data'),
			long_description='',
			syntax=univention.admin.syntax.Base64Bzip2Text,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'active': univention.admin.property(
			short_description=_('Active'),
			long_description='',
			syntax=univention.admin.syntax.TrueFalseUp,
			default = 'FALSE',
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'appidentifier': univention.admin.property(
			short_description=_('App identifier'),
			long_description='',
			syntax=univention.admin.syntax.TextArea,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'package': univention.admin.property(
			short_description=_('Software package'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'packageversion': univention.admin.property(
			short_description=_('Software package version'),
			long_description='',
			syntax=univention.admin.syntax.DebianPackageVersion,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'ucsversionstart': univention.admin.property(
			short_description=_('Minimal UCS version'),
			long_description='',
			syntax=univention.admin.syntax.UCSVersion,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	'ucsversionend': univention.admin.property(
			short_description=_('Maximal UCS version'),
			long_description='',
			syntax=univention.admin.syntax.UCSVersion,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	}

layout = [
	Tab(_('General'),_('Basic values'), layout = [
		Group( _( 'General UDM syntax settings' ), layout = [
			["name"],
			["filename"],
			["data"],
		] ),
		Group( _( 'Metadata' ), layout = [
			["package"],
			["packageversion"],
			["appidentifier"],
		] ),
		Group( _( 'UCS Version Dependencies' ), layout = [
			["ucsversionstart"],
			["ucsversionend"],
		] ),
		Group( _( 'Activated' ), layout = [
			["active"],
		] ),
	] ),
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('filename', 'univentionUDMSyntaxFilename', None, univention.admin.mapping.ListToString)
mapping.register('data', 'univentionUDMSyntaxData', univention.admin.mapping.mapBase64, univention.admin.mapping.unmapBase64)
mapping.register('active', 'univentionUDMSyntaxActive', None, univention.admin.mapping.ListToString)
mapping.register('appidentifier', 'univentionAppIdentifier')
mapping.register('package', 'univentionOwnedByPackage', None, univention.admin.mapping.ListToString)
mapping.register('packageversion', 'univentionOwnedByPackageVersion', None, univention.admin.mapping.ListToString)
mapping.register('ucsversionstart', 'univentionUCSVersionStart', None, univention.admin.mapping.ListToString)
mapping.register('ucsversionend', 'univentionUCSVersionEnd', None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions
 		self.options=[]

		self.alloc=[]

		univention.admin.handlers.simpleLdap.__init__(self, co, lo,  position, dn, superordinate, attributes = attributes )

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

	def _ldap_pre_create(self):		
		self.dn='cn=%s,%s' % ( mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		ocs=['top', 'univentionObjectMetadata', OC]		

		return [
			('objectClass', ocs),
		]

	def _ldap_pre_modify(self):
		diff_keys = [ key for key in self.info.keys() if self.info.get(key) != self.oldinfo.get(key) and key not in ('active', 'appidentifier') ]
		if not diff_keys: ## check for trivial change
			return
		if not self.hasChanged('package'):
			old_version = self.oldinfo.get('packageversion','0')
			if not  apt.apt_pkg.version_compare(self['packageversion'], old_version) > -1:
				raise univention.admin.uexceptions.valueInvalidSyntax, _('packageversion: Version must not be lower than the current one.')

	
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

