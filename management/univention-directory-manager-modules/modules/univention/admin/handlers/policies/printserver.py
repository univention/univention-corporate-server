# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the print server
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


class printServerFixedAttributes(univention.admin.syntax.select):
	name = 'updateFixedAttributes'
	choices = [
		('univentionPrintServer', _('Print server')),
	]


module = 'policies/printserver'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyPrintServer'
policy_apply_to = ["computers/memberserver", "computers/managedclient", "computers/mobileclient", "computers/domaincontroller_backup", "computers/domaincontroller_master", "computers/domaincontroller_slave"]
policy_position_dn_prefix = "cn=printservers"

childs = 0
short_description = _('Policy: Print server')
object_name = _('Print server policy')
object_name_plural = _('Print server policies')
policy_short_description = _('Print server')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPolicy', 'univentionPolicyPrintServer'],
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
	'printServer': univention.admin.property(
		short_description=_('Print server'),
		long_description='',
		syntax=univention.admin.syntax.ServicePrint_FQDN,
		include_in_default_search=True,
	),

}
property_descriptions.update(dict([
	requiredObjectClassesProperty(),
	prohibitedObjectClassesProperty(),
	fixedAttributesProperty(syntax=printServerFixedAttributes),
	emptyAttributesProperty(syntax=printServerFixedAttributes),
	ldapFilterProperty(),
]))

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General print server settings'), layout=[
			'name',
			'printServer'
		]),
	]),
	policy_object_tab()
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('printServer', 'univentionPrintServer', None, univention.admin.mapping.ListToString)
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
	module = module


lookup = object.lookup
identify = object.identify
