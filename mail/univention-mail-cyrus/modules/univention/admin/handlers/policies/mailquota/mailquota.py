# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the mail quota
#
# Copyright 2004-2015 Univention GmbH
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

try:
	from univention.admin.policy import (
		register_policy_mapping, policy_object_tab,
		requiredObjectClassesProperty, prohibitedObjectClassesProperty,
		fixedAttributesProperty, emptyAttributesProperty, ldapFilterProperty
	)
	UDMPolicyAPIVersion = 1
except ImportError:
	# Bug #39004: UDMPolicyAPIVersion is a workaround for registerLDAPExtension problems #39010 and #39011
	# it may be removed if those bugs are fixed or all systems in UCS domain have UCS version 4.0-3 or higher
	UDMPolicyAPIVersion = 0

import univention.debug

translation=univention.admin.localization.translation('univention.admin.handlers.policies.mailquota')
_=translation.translate

class mailquotaFixedAttributes(univention.admin.syntax.select):
	name='mailquotaFixedAttributes'
	choices=[
		('univentionMailQuotaMB', _('Quota limit (MB)')),
		]

module='policies/mailquota'
operations=['add','edit','remove','search']

policy_oc='univentionMailQuota'
policy_apply_to=["users/user"]
policy_position_dn_prefix="cn=mail"

childs=0
short_description=_('Policy: Mail quota')
policy_short_description=_('Mail quota')
long_description=''
options={
}
property_descriptions={
	'name': univention.admin.property(
			short_description=_('Name'),
			long_description='',
			syntax=univention.admin.syntax.policyName,
			multivalue=0,
			include_in_default_search=1,
			options=[],
			required=1,
			may_change=0,
			identifies=1,
		),
	'MailQuota': univention.admin.property(
			short_description=_('Quota limit (MB)'),
			long_description='',
			syntax=univention.admin.syntax.integer,
			multivalue=0,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	}

if UDMPolicyAPIVersion == 0:
	property_descriptions.update({
		'requiredObjectClasses': univention.admin.property(
			short_description=_('Required object class'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
		'prohibitedObjectClasses': univention.admin.property(
			short_description=_('Excluded object class'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
		'fixedAttributes': univention.admin.property(
			short_description=_('Fixed attribute'),
			long_description='',
			syntax=mailquotaFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
		'emptyAttributes': univention.admin.property(
			short_description=_('Empty attribute'),
			long_description='',
			syntax=mailquotaFixedAttributes,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
	})

	object_tab = Tab(_('Object'),_('Object'), advanced = True, layout = [
		[ 'requiredObjectClasses' , 'prohibitedObjectClasses' ],
		[ 'fixedAttributes', 'emptyAttributes' ]
	])
else:
	property_descriptions.update(dict([
		requiredObjectClassesProperty(),
		prohibitedObjectClassesProperty(),
		fixedAttributesProperty(syntax=mailquotaFixedAttributes),
		emptyAttributesProperty(syntax=mailquotaFixedAttributes),
		ldapFilterProperty(),
	]))
	object_tab = policy_object_tab()

layout = [
	Tab(_('General'),_('Mail quota'), layout = [
		Group( _( 'General mail quota settings' ), layout = [
			'name',
			'MailQuota'
		] ),
	] ),
	object_tab,
]

mapping=univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('MailQuota', 'univentionMailQuotaMB', None, univention.admin.mapping.ListToString)
if UDMPolicyAPIVersion == 0:
	mapping.register('requiredObjectClasses', 'requiredObjectClasses')
	mapping.register('prohibitedObjectClasses', 'prohibitedObjectClasses')
	mapping.register('fixedAttributes', 'fixedAttributes')
	mapping.register('emptyAttributes', 'emptyAttributes')
else:
	register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		univention.admin.handlers.simplePolicy.__init__(self, co, lo, position, dn, superordinate, attributes )

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('name'), mapping.mapValue('name', self.info['name']), self.position.getDn())

	def _ldap_addlist(self):
		return [ ('objectClass', ['top', 'univentionPolicy', 'univentionMailQuota']) ]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionMailQuota')
		])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	try:
		for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
			res.append( object( co, lo, None, dn, attributes = attrs ) )
	except:
		pass
	return res

def identify(dn, attr, canonical=0):
	return 'univentionMailQuota' in attr.get('objectClass', [])
