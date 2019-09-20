# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the ldap servers
#
# Copyright 2004-2019 Univention GmbH
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
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

from univention.admin.policy import (
	register_policy_mapping, policy_object_tab,
	requiredObjectClassesProperty, prohibitedObjectClassesProperty,
	fixedAttributesProperty, emptyAttributesProperty, ldapFilterProperty
)


translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


class ldapServerFixedAttributes(univention.admin.syntax.select):
	name = 'updateFixedAttributes'
	choices = [
		('univentionLDAPServer', _('LDAP Server')),
	]


module = 'policies/ldapserver'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyLDAPServer'
policy_apply_to = ["computers/memberserver", "computers/managedclient", "computers/mobileclient", "computers/thinclient"]
policy_position_dn_prefix = "cn=ldap"

childs = 0
short_description = _('Policy: LDAP server')
object_name = _('LDAP server policy')
object_name_plural = _('LDAP server policies')
policy_short_description = _('LDAP server')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPolicy', 'univentionPolicyLDAPServer'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.policyName,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True,
	),
	'ldapServer': univention.admin.property(
		short_description=_('LDAP server'),
		long_description='',
		syntax=univention.admin.syntax.DomainController,
		multivalue=True,
	),

}
property_descriptions.update(dict([
	requiredObjectClassesProperty(),
	prohibitedObjectClassesProperty(),
	fixedAttributesProperty(syntax=ldapServerFixedAttributes),
	emptyAttributesProperty(syntax=ldapServerFixedAttributes),
	ldapFilterProperty(),
]))

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General LDAP server settings'), layout=[
			'name',
			'ldapServer'
		]),
	]),
	policy_object_tab()
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('ldapServer', 'univentionLDAPServer')
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
	module = module


lookup = object.lookup
identify = object.identify
