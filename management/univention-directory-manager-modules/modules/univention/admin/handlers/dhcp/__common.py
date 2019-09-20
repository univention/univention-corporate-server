# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP subnet
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

import sys

import univention.admin.localization
from univention.admin.layout import Tab
from univention.admin.handlers import simpleLdap

translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

_properties = {
	'option': univention.admin.property(
		short_description=_('DHCP options'),
		long_description=_('Additional options for DHCP'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=['options'],
	),
	'statements': univention.admin.property(
		short_description=_('DHCP Statements'),
		long_description=_('Additional statements for DHCP'),
		syntax=univention.admin.syntax.TextArea,
		multivalue=True,
		options=['options'],
	)
}
_options = {
	'options': univention.admin.option(
		short_description=_('Allow custom DHCP options'),
		long_description=_("Allow adding custom DHCP options. Experts only!"),
		default=False,
		editable=True,
		objectClasses=['dhcpOptions'],
	),
}
_mappings = (
	('option', 'dhcpOption', None, None),
	('statements', 'dhcpStatements', None, None),
)


def rangeMap(value):
	return [' '.join(x) for x in value]


def rangeUnmap(value):
	return [x.split() for x in value]


def add_dhcp_options(module_name):
	module = sys.modules[module_name]

	options = getattr(module, "options")
	options.update(_options)

	properties = getattr(module, "property_descriptions")
	properties.update(_properties)

	mapping = getattr(module, "mapping")
	for item in _mappings:
		mapping.register(*item)

	layout = getattr(module, "layout")
	layout.append(Tab(
		_('Low-level DHCP configuration'),
		_('Custom DHCP options'),
		advanced=True,
		layout=['option', 'statements']
	))


class DHCPBase(simpleLdap):
	pass
