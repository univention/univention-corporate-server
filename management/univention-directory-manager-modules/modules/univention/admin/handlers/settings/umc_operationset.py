#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
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

from univention.admin.localization import translation
from univention.admin.handlers import simpleLdap

import univention.admin

_ = translation('univention.admin.handlers.settings').translate

module = 'settings/umc_operationset'
operations = ('add', 'edit', 'remove', 'search', 'move')
superordinate = 'settings/cn'

childs = 0
short_description = _('Settings: UMC operation set')
object_name = _('UMC operation set')
object_name_plural = _('UMC operation sets')
long_description = _('List of Operations for UMC')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'umcOperationSet'],
	),
}

property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=udm_syntax.string,
		include_in_default_search=True,
		required=True,
		identifies=True,
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=udm_syntax.string,
		include_in_default_search=True,
		dontsearch=True,
		required=True,
	),
	'operation': univention.admin.property(
		short_description=_('UMC commands'),
		long_description=_('List of UMC command names or patterns'),
		syntax=udm_syntax.UMC_CommandPattern,
		multivalue=True,
		dontsearch=True,
	),
	'flavor': univention.admin.property(
		short_description=_('Flavor'),
		long_description=_('Defines a specific flavor of the UMC module. If given the operations are permitted only if the flavor matches.'),
		syntax=udm_syntax.string,
		include_in_default_search=True,
		dontsearch=True,
	),
	'hosts': univention.admin.property(
		short_description=_('Restrict to host'),
		long_description=_('Defines on which hosts this operations are permitted on. The value can be either a host name (as filename pattern e.g. server1*), a server role (e.g. serverrole:domaincontroller_slave) or a service, which must run on the host, (e.g. service:LDAP). Leaving this empty causes all hosts to be allowed.'),
		syntax=udm_syntax.string,
		multivalue=True,
		dontsearch=True,
	),
}

layout = [
	Tab(_('General'), _('UMC Operation Set'), layout=[
		Group(_('General UMC operation set settings'), layout=[
			['name', 'description'],
			'operation',
			'flavor',
			'hosts',
		]),
	]),
]


def mapUMC_CommandPattern(value):
	return map(lambda x: ':'.join(x), value)


def unmapUMC_CommandPattern(value):
	unmapped = []
	for item in value:
		if item.find(':') >= 0:
			unmapped.append(item.split(':', 1))
		else:
			unmapped.append((item, ''))
	return unmapped


mapping = udm_mapping.mapping()
mapping.register('name', 'cn', None, udm_mapping.ListToString)
mapping.register('description', 'description', None, udm_mapping.ListToString)
mapping.register('operation', 'umcOperationSetCommand', mapUMC_CommandPattern, unmapUMC_CommandPattern)
mapping.register('flavor', 'umcOperationSetFlavor', None, udm_mapping.ListToString)
mapping.register('hosts', 'umcOperationSetHost')


class object(simpleLdap):
	module = module


lookup = object.lookup
identify = object.identify
