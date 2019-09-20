# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the mail domain objects
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

import ldap

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.allocators
import univention.admin.localization
from univention.admin.handlers.dns import stripDot

translation = univention.admin.localization.translation('univention.admin.handlers.mail')
_ = translation.translate

module = 'mail/domain'
operations = ['add', 'edit', 'remove', 'search', 'move']
childs = 0
short_description = _('Mail domain')
object_name = _('Mail domain')
object_name_plural = _('Mail domains')
long_description = ''

module_search_filter = univention.admin.filter.conjunction('&', [
	univention.admin.filter.expression('objectClass', 'univentionMailDomainname'),
])
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionMailDomainname'],
	),
}

property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Mail domain name'),
		long_description='',
		syntax=univention.admin.syntax.dnsName,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('Mail domain description'), layout=[
			"name",
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', stripDot, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_dn(self):
		dn = ldap.dn.str2dn(super(object, self)._ldap_dn())
		dn[0] = [(dn[0][0][0], dn[0][0][1].lower(), dn[0][0][2])]
		return ldap.dn.dn2str(dn)

	def _ldap_modlist(self):
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
		ml = [(a, b, c.lower()) if a == "cn" else (a, b, c) for (a, b, c) in ml]
		return ml


lookup = object.lookup
identify = object.identify
