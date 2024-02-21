# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2024 Univention GmbH
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

"""|UDM| module for blocklist settings"""

import univention.admin.blocklist
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
import univention.admin.uldap
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.blocklists')
_ = translation.translate

module = 'blocklists/entry'
operations = ['add', 'edit', 'remove', 'search']
childs = False
superordinate = 'blocklists/list'
short_description = _('Univention blocklist entries')
object_name = _('Univention blocklist entry')
object_name_plural = _('Univention blocklist entries')
long_description = ''
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionBlockingEntry'],
    ),
}
property_descriptions = {
    'value': univention.admin.property(
        short_description=_('Blocklist entry value'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'blockedUntil': univention.admin.property(
        short_description=_('Blocked until'),
        long_description=_('This blocklist entry is valid until timestamp (generalized time in LDAP-Syntax -> 21241212000000Z). Expired entries are deleted.'),
        syntax=univention.admin.syntax.GeneralizedTimeUTC,
        required=True,
    ),
    'originUniventionObjectIdentifier': univention.admin.property(
        short_description=_('Origin ID'),
        long_description=_('The ID of the UDM object that lead to this blocklist entry. The value of this blocklist entry can still be used on that UDM object.'),
        syntax=univention.admin.syntax.string,
        required=True,
        may_change=False,
    ),
}

layout = [
    Tab(_('General'), _('Blocklist entry settings'), layout=[
        Group(_('General settings'), layout=[
            ["value"],
            ["blockedUntil"],
            ["originUniventionObjectIdentifier"],
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('value', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('blockedUntil', 'blockedUntil', None, univention.admin.mapping.ListToString)
mapping.register('originUniventionObjectIdentifier', 'originUniventionObjectIdentifier', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
    module = module
    ldap_base = univention.admin.blocklist.BLOCKLIST_BASE

    @classmethod
    def rewrite_filter(cls, filter, mapping):
        super(object, cls).rewrite_filter(filter, mapping)
        if filter.variable == 'cn':
            filter.value = univention.admin.blocklist.hash_blocklist_value(filter.value.encode('UTF-8'))

    @classmethod
    def identify(cls, dn, attr, canonical=False):
        return b'univentionBlockingEntry' in attr.get('objectClass', [])

    def _ldap_pre_create(self):
        self['value'] = univention.admin.blocklist.hash_blocklist_value(self['value'].encode('UTF-8'))
        super(object, self)._ldap_pre_create()


lookup_filter = object.lookup_filter
lookup = object.lookup
identify = object.identify
