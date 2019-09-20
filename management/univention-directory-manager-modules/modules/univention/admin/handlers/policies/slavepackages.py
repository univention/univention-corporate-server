# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the DC Slave packages
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


class slavePackagesFixedAttributes(univention.admin.syntax.select):
	name = 'slavePackagesFixedAttributes'
	choices = [
		('univentionSlavePackages', _('Package installation list')),
		('univentionSlavePackagesRemove', _('Package removal list')),
	]


module = 'policies/slavepackages'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyPackagesSlave'
policy_apply_to = ["computers/domaincontroller_slave"]
policy_position_dn_prefix = "cn=packages,cn=update"

childs = 0
short_description = _('Policy: Slave packages')
object_name = _('Slave packages policy')
object_name_plural = _('Slave packages policies')
policy_short_description = _('Slave packages')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPolicy', 'univentionPolicyPackagesSlave'],
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
	'slavePackages': univention.admin.property(
		short_description=_('Package installation list'),
		long_description='',
		syntax=univention.admin.syntax.Packages,
		multivalue=True,
	),
	'slavePackagesRemove': univention.admin.property(
		short_description=_('Package removal list'),
		long_description='',
		syntax=univention.admin.syntax.PackagesRemove,
		multivalue=True,
	),

}
property_descriptions.update(dict([
	requiredObjectClassesProperty(),
	prohibitedObjectClassesProperty(),
	fixedAttributesProperty(syntax=slavePackagesFixedAttributes),
	emptyAttributesProperty(syntax=slavePackagesFixedAttributes),
	ldapFilterProperty(),
]))

layout = [
	Tab(_('General'), policy_short_description, layout=[
		Group(_('General slave packages settings'), layout=[
			'name',
			'slavePackages',
			'slavePackagesRemove'
		]),
	]),
	policy_object_tab()
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('slavePackages', 'univentionSlavePackages')
mapping.register('slavePackagesRemove', 'univentionSlavePackagesRemove')
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
	module = module


lookup = object.lookup
identify = object.identify
