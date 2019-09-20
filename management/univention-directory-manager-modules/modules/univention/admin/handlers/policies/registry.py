# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin policy for the registry configuration
#
# Copyright 2007-2019 Univention GmbH
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
import univention.admin.uexceptions

from univention.admin.policy import (
	register_policy_mapping, policy_object_tab,
	requiredObjectClassesProperty, prohibitedObjectClassesProperty,
	fixedAttributesProperty, emptyAttributesProperty, ldapFilterProperty
)


translation = univention.admin.localization.translation('univention.admin.handlers.policies')
_ = translation.translate


class registryFixedAttributes(univention.admin.syntax.select):
	name = 'registryFixedAttributes'
	choices = [
		('registry', _('UCR Variables'))
	]


module = 'policies/registry'
operations = ['add', 'edit', 'remove', 'search']

policy_oc = 'univentionPolicyRegistry'
policy_apply_to = ["computers/domaincontroller_master", "computers/domaincontroller_backup", "computers/domaincontroller_slave", "computers/memberserver", "computers/managedclient", "computers/mobileclient", "computers/thinclient", "computers/ucc"]
policy_position_dn_prefix = "cn=config-registry"
childs = 0
short_description = _('Policy: Univention Configuration Registry')
object_name = _('Univention Configuration Registry policy')
object_name_plural = _('Univention Configuration Registry policies')
policy_short_description = _('Univention Configuration Registry')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPolicy', 'univentionPolicyRegistry'],
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
	'registry': univention.admin.property(
		short_description=_('Configuration Registry'),
		long_description='',
		syntax=univention.admin.syntax.UCR_Variable,
		multivalue=True,
	),

}
property_descriptions.update(dict([
	requiredObjectClassesProperty(),
	prohibitedObjectClassesProperty(),
	fixedAttributesProperty(syntax=registryFixedAttributes),
	emptyAttributesProperty(syntax=registryFixedAttributes),
	ldapFilterProperty(),
]))

layout = [
	Tab(_('General'), _('These configuration settings will be set on the local UCS system.'), layout=[
		Group(_('General Univention Configuration Registry settings'), layout=[
			'name',
			'registry',
		]),
	]),
	policy_object_tab()
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
register_policy_mapping(mapping)


class object(univention.admin.handlers.simplePolicy):
	module = module

	def _post_unmap(self, info, values):
		info['registry'] = []
		for key, value in values.items():
			if key.startswith('univentionRegistry;entry-hex-'):
				key_name = key.split('univentionRegistry;entry-hex-', 1)[1].decode('hex')
				info['registry'].append([key_name, values[key][0].strip()])

		info['registry'].sort()

		return info

	def _post_map(self, modlist, diff):
		for key, old, new in diff:
			if key == 'registry':
				keys = [x[0] for x in new]
				duplicated = set([x for x in keys if keys.count(x) > 1])
				if duplicated:
					raise univention.admin.uexceptions.valueInvalidSyntax(_('Duplicated variables not allowed: %s') % (', '.join(map(repr, duplicated))), property='registry')

				old_dict = dict(old)
				new_dict = dict([k.strip(), v] for k, v in new)  # strip leading and trailing whitespace in variable names

				for var, value in old_dict.items():
					attr_name = 'univentionRegistry;entry-hex-%s' % var.encode('hex')
					if var not in new_dict:  # variable has been removed
						modlist.append((attr_name, value, None))
					elif value != new_dict[var]:  # value has been changed
						modlist.append((attr_name, value, new_dict[var]))

				for var, value in new_dict.items():
					attr_name = 'univentionRegistry;entry-hex-%s' % var.encode('hex')
					if var not in old_dict:  # variable has been added
						modlist.append((attr_name, None, new_dict[var]))
				break

		return modlist

	def _custom_policy_result_map(self):
		values = {}
		self.polinfo_more['registry'] = []
		for attr_name, value_dict in self.policy_attrs.items():
			values[attr_name] = value_dict['value']
			if attr_name.startswith('univentionRegistry;entry-hex-'):
				key_name = attr_name.split('univentionRegistry;entry-hex-', 1)[1].decode('hex')
				value_dict['value'].insert(0, key_name)
				self.polinfo_more['registry'].append(value_dict)
			elif attr_name:
				self.polinfo_more[self.mapping.unmapName(attr_name)] = value_dict

		self.polinfo = univention.admin.mapping.mapDict(self.mapping, values)
		self.polinfo = self._post_unmap(self.polinfo, values)


lookup = object.lookup
identify = object.identify
