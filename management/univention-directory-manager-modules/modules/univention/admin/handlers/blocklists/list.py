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

"""|UDM| module for all |blocklist| objects"""


import univention.admin.blocklist
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.blocklists')
_ = translation.translate

module = 'blocklists/list'
operations = ['add', 'edit', 'remove', 'search']
childs = False
childmodules = ['blocklists/entry']
short_description = _('Blocklist')
object_name = _('Blocklist')
object_name_plural = _('Blocklists')
long_description = _('Blocklist for certain UDM properties')
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionBlocklist'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'blockingProperties': univention.admin.property(
        short_description=_('Properties to block'),
        long_description=_('Property values removed from a UDM object can be automatically blocked for future use. This is achieved by adding the properties to a blocklist. The properties must be specified according to the following schema: "udm/module property". An example configuration would be "users/user mailPrimaryAddress". If multiple properties are assigned to the same blocklist, the blocking value applies for multiple properties.'),
        syntax=univention.admin.syntax.UDM_PropertySelect,
        required=True,
        multivalue=True,
    ),
    'retentionTime': univention.admin.property(
        short_description=_('Retention time for objects in this blocklist'),
        long_description=_('Property values removed from a UDM object can be automatically blocked for future use. Each blocklist can be assigned a retention period. Once this retention period has elapsed, the blocking object is automatically deleted, and the property value can be reassigned. The retention period is set using the following schema "1y6m3d" (which equals one year, six months and three days).'),
        syntax=univention.admin.syntax.string,
    ),
}

layout = [
    Tab(_('General'), _('Blocklist settings'), layout=[
        Group(_('General settings'), layout=[
            ['name'],
            ['retentionTime'],
            ['blockingProperties'],
        ]),
    ]),
]


def mapBlockingProperty(vals, encoding=()):
    return [u' '.join(val).encode(*encoding) for val in vals]


def unmapBlockingProperty(vals, encoding=()):
    return [val.decode(*encoding).split(u' ', 1) for val in vals]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('blockingProperties', 'univentionBlockingProperties', mapBlockingProperty, unmapBlockingProperty)
mapping.register('retentionTime', 'univentionBlocklistRetentionTime', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
    module = module
    ldap_base = univention.admin.blocklist.BLOCKLIST_BASE

    @classmethod
    def identify(cls, dn, attr, canonical=False):
        return b'univentionBlocklist' in attr.get('objectClass', [])


lookup_filter = object.lookup_filter
lookup = object.lookup
identify = object.identify
