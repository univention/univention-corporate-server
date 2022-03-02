# -*- coding: utf-8 -*-
#
# Copyright 2007-2022 Univention GmbH
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

"""
|UDM| module for the configuration registry policies
"""

import copy
import codecs

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
policy_apply_to = ["computers/domaincontroller_master", "computers/domaincontroller_backup", "computers/domaincontroller_slave", "computers/memberserver"]
policy_position_dn_prefix = "cn=config-registry"
childs = False
short_description = _('Policy: Univention Configuration Registry')
object_name = _('Univention Configuration Registry policy')
object_name_plural = _('Univention Configuration Registry policies')
policy_short_description = _('Univention Configuration Registry')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description=short_description,
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
	UCR_HEX = "univentionRegistry;entry-hex-"
	module = module

	def _post_unmap(self, info, oldattr):
		info['registry'] = sorted(
			[self._ucr_unhexlify(attr_name), ldap_value[0].decode('UTF-8').strip()]
			for attr_name, ldap_value in oldattr.items()
			if self._is_ucr_hex(attr_name)
		)
		return info

	def _post_map(self, modlist, diff):
		for key, old, new in diff:
			if key == 'registry':
				keys = [x[0] for x in new]
				duplicated = set(x for x in keys if keys.count(x) > 1)
				if duplicated:
					raise univention.admin.uexceptions.valueInvalidSyntax(_('Duplicated variables not allowed: %s') % (', '.join(map(repr, duplicated))), property='registry')

				old_dict = dict(old)
				new_dict = dict([k.strip(), v] for k, v in new)  # strip leading and trailing whitespace in variable names

				for key_name, old_value in old_dict.items():
					if key_name not in new_dict:  # UCR key has been removed
						attr_name = self._ucr_hexlify(key_name)
						modlist.append((attr_name, old_value.encode('UTF-8'), None))
					elif old_value != new_dict[key_name]:  # UCR variable has been changed
						attr_name = self._ucr_hexlify(key_name)
						modlist.append((attr_name, old_value.encode('UTF-8'), new_dict[key_name].encode('utf-8')))

				for key_name, new_value in new_dict.items():
					if key_name not in old_dict:  # UCR key has been added
						attr_name = self._ucr_hexlify(key_name)
						modlist.append((attr_name, None, new_value.encode('UTF-8')))
				break

		return modlist

	def _custom_policy_result_map(self):
		values = {}
		self.polinfo_more['registry'] = []
		for attr_name, value_dict in self.policy_attrs.items():
			value_dict = copy.deepcopy(value_dict)
			values[attr_name] = copy.copy(value_dict['value'])
			value_dict['value'] = [x.decode('UTF-8') for x in value_dict['value']]
			if self._is_ucr_hex(attr_name):
				key_name = self._ucr_unhexlify(attr_name)
				value_dict['value'].insert(0, key_name)
				self.polinfo_more['registry'].append(value_dict)
			elif attr_name:
				self.polinfo_more[self.mapping.unmapName(attr_name)] = value_dict

		self.polinfo = univention.admin.mapping.mapDict(self.mapping, values)
		self.polinfo = self._post_unmap(self.polinfo, values)

	def _ucr_hexlify(self, key_name):
		# type: (str) -> str
		return '%s%s' % (self.UCR_HEX, codecs.encode(key_name.encode('utf-8'), 'hex').decode('ASCII'))

	def _is_ucr_hex(self, attr_name):
		# type: (str) -> bool
		return attr_name.startswith(self.UCR_HEX)

	def _ucr_unhexlify(self, attr_name):
		# type: (str) -> str
		return codecs.decode(attr_name[len(self.UCR_HEX):], 'hex').decode('UTF-8')


lookup = object.lookup
identify = object.identify
