# -*- coding: utf-8 -*-
#
# Univention Directory Manager Modules
#  admin module for the admin modules
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


class adminFixedAttributes(univention.admin.syntax.select):
	name = 'adminFixedAttributes'
	choices = [
		('univentionAdminListModules', _('List of Univention Directory Manager modules')),
	]


module = 'policies/admin_container'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyAdminContainerSettings'
policy_apply_to = []
policy_position_dn_prefix = "cn=container,cn=admin"

childs = 0
short_description = _('Policy: Univention Directory Manager container settings')
object_name = _('Univention Directory Manager container settings policy')
object_name_plural = _('Univention Directory Manager container settings policies')
policy_short_description = _('Univention Directory Manager container settings')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPolicy', 'univentionPolicyAdminContainerSettings'],
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
	'listModules': univention.admin.property(
		short_description=_('Available Univention Directory Manager modules'),
		long_description='',
		syntax=univention.admin.syntax.univentionAdminModules,
		multivalue=True,
	),
}
property_descriptions.update(dict([
	requiredObjectClassesProperty(),
	prohibitedObjectClassesProperty(),
	fixedAttributesProperty(syntax=adminFixedAttributes),
	emptyAttributesProperty(syntax=adminFixedAttributes),
	ldapFilterProperty(),
]))

layout = [
	Tab(_('General'), _('Univention Directory Manager settings'), layout=[
		Group(_('General Univention Directory Manager container settings'), layout=[
			'name',
			'listModules',
		]),
	]),
	policy_object_tab(),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('listModules', 'univentionAdminListModules')
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
	module = module


lookup = object.lookup
identify = object.identify
