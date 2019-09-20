# -*- coding: utf-8 -*-
#
# Univention Management Console
#  admin module: policy defining access restriction for UMC
#
# Copyright 2011-2019 Univention GmbH
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
import univention.admin.syntax as udm_syntax
import univention.admin.mapping as udm_mapping

from univention.admin.handlers import simplePolicy
import univention.admin.localization

from univention.admin.policy import (
	register_policy_mapping, policy_object_tab,
	requiredObjectClassesProperty, prohibitedObjectClassesProperty,
	fixedAttributesProperty, emptyAttributesProperty, ldapFilterProperty
)


translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


class umcFixedAttributes(udm_syntax.select):
	choices = (
		('umcPolicyGrantedOperationSet', _('Allowed UMC operation sets')),
	)


module = 'policies/umc'
operations = ('add', 'edit', 'remove', 'search')

policy_oc = 'umcPolicy'
policy_apply_to = ['users/user', 'users/ldap', 'groups/group']
policy_position_dn_prefix = 'cn=UMC'

childs = 0
short_description = _('Policy: UMC')
object_name = _('UMC policy')
object_name_plural = _('UMC policies')
policy_short_description = _('Defines a set of allowed UMC operations')
long_description = ''

options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPolicy', 'umcPolicy'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=udm_syntax.policyName,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True,
	),
	'allow': univention.admin.property(
		short_description=_('List of allowed UMC operation sets'),
		long_description='',
		syntax=udm_syntax.UMC_OperationSet,
		multivalue=True,
	),
}
property_descriptions.update(dict([
	requiredObjectClassesProperty(),
	prohibitedObjectClassesProperty(),
	fixedAttributesProperty(syntax=umcFixedAttributes),
	emptyAttributesProperty(syntax=umcFixedAttributes),
	ldapFilterProperty(),
]))

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General UMC settings'), layout=[
			'name',
			'allow',
		]),
	]),
	policy_object_tab()
]

mapping = udm_mapping.mapping()
mapping.register('name', 'cn', None, udm_mapping.ListToString)
mapping.register('allow', 'umcPolicyGrantedOperationSet')
register_policy_mapping(mapping)


class object(simplePolicy):
	module = module


lookup = object.lookup
identify = object.identify
