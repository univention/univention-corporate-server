# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager
#  UDM Virtual Machine Manager Information
#
# Copyright 2010-2019 Univention GmbH
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

import univention.admin
import univention.admin.mapping as udm_mapping
from univention.admin.handlers import simpleLdap
import univention.admin.syntax as udm_syntax
from univention.admin.localization import translation
from univention.admin.layout import Tab, Group


_ = translation('univention.admin.handlers.uvmm').translate

module = 'uvmm/info'
default_containers = ['cn=Information,cn=Virtual Machine Manager']

childs = False
short_description = _('UVMM: Machine information')
object_name = _('Machine information')
object_name_plural = _('Machine information')
long_description = ''
operations = ['search', 'edit', 'add', 'remove']


options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionVirtualMachine']
	)
}

# UDM properties
property_descriptions = {
	'uuid': univention.admin.property(
		short_description=_('UUID'),
		long_description=_('The unique identifier used by libvirt to identify the VM'),
		syntax=udm_syntax.string,
		required=True,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description=_('Description of virtual machine'),
		syntax=udm_syntax.TextArea,
	),
	'os': univention.admin.property(
		short_description=_('Operating system'),
		long_description=_('Name of the operation system'),
		syntax=udm_syntax.string,
	),
	'contact': univention.admin.property(
		short_description=_('Contact'),
		long_description=_('Name and/or email address of a contact person'),
		syntax=udm_syntax.string,
	),
	'profile': univention.admin.property(
		short_description=_('Profile'),
		long_description=_('Reference to the profile used for defining this VM'),
		syntax=udm_syntax.UvmmProfiles,
	),
}


# UDM web layout
layout = [
	Tab(_('General'), _('Virtual machine information'), layout=[
		Group(_('General'), layout=[
			"uuid",
			"description",
			"contact",
			"os",
			"profile",
		])
	])
]


# Mapping between UDM properties and LDAP attributes
mapping = udm_mapping.mapping()
mapping.register('uuid', 'univentionVirtualMachineUUID', None, udm_mapping.ListToString)
mapping.register('description', 'univentionVirtualMachineDescription', None, udm_mapping.ListToString)
mapping.register('os', 'univentionVirtualMachineOS', None, udm_mapping.ListToString)
mapping.register('contact', 'univentionVirtualMachineContact', None, udm_mapping.ListToString)
mapping.register('profile', 'univentionVirtualMachineProfileRef', None, udm_mapping.ListToString)


class object(simpleLdap):
	"""
	UDM module to handle UVMM VM info objects.
	"""
	module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
