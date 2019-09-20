# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DNS objects
#
# Copyright 2018-2019 Univention GmbH
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


import univention.admin.handlers
import univention.admin.handlers.settings.portal
import univention.admin.handlers.settings.portal_entry
import univention.admin.handlers.settings.portal_category
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/portal_all'
short_description = _('Portal: Settings')
long_description = _('Management of portals and their entries')

operations = ['search']
childmodules = ['settings/portal', 'settings/portal_entry', 'settings/portal_category']
virtual = True
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Internal name'),
		long_description='',
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'displayName': univention.admin.property(
		short_description=_('Display Name'),
		long_description='',
		syntax=univention.admin.syntax.LocalizedDisplayName,
		multivalue=True,
		required=True,
	),
}
layout = [Tab(_('General'), _('Basic settings'), layout=["name"])]
mapping = univention.admin.mapping.mapping()


class object(univention.admin.handlers.simpleLdap):
	module = module


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	res = []
	for child in childmodules:
		portal_module = univention.admin.modules.get(child)
		res.extend(portal_module.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit))

	return res


def identify(dn, attr, canonical=0):
	pass
