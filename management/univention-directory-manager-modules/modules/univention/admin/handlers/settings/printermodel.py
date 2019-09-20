# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for printer modules
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

import shlex

from univention.admin.layout import Tab, Group
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/printermodel'
operations = ['add', 'edit', 'remove', 'search', 'move']
superordinate = 'settings/cn'

childs = 0
short_description = _('Settings: Printer Driver List')
object_name = _('Printer Driver List')
object_name_plural = _('Printer Driver Lists')
long_description = _('List of drivers for printers')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionPrinterModels'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description=_('Name'),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
		identifies=True,
	),
	'printmodel': univention.admin.property(
		short_description=_('Printer Model'),
		long_description=_('Printer Model'),
		syntax=univention.admin.syntax.printerModel,
		multivalue=True,
		include_in_default_search=True,
	),
}

layout = [
	Tab(_('General'), _('Printer List'), layout=[
		Group(_('General printer driver list settings'), layout=[
			'name',
			'printmodel',
		]),
	]),
]


def unmapDriverList(old):
	return map(lambda x: shlex.split(x), old)


def mapDriverList(old):
	str = []
	for i in old:
		str.append('"%s" "%s"' % (i[0], i[1]))
	return str


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('printmodel', 'printerModel', mapDriverList, unmapDriverList)


class object(univention.admin.handlers.simpleLdap):
	module = module

	@classmethod
	def rewrite_filter(cls, filter, mapping):
		if filter.variable == 'printmodel':
			filter.variable = 'printerModel'
		else:
			super(object, cls).rewrite_filter(filter, mapping)


lookup = object.lookup
identify = object.identify
