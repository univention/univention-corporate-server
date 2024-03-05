# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2024 Univention GmbH
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

"""|UDM| module for |DNS| Name Server records"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.dns.forward_zone
import univention.admin.localization
from univention.admin.handlers.dns import (  # noqa: F401
    Attr, DNSBase, is_dns, is_not_handled_by_other_module_than, is_zone,
)
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate

module = 'dns/ns_record'
operations = ['add', 'edit', 'remove', 'search']
columns = ['nameserver']
superordinate = ['dns/forward_zone', 'dns/reverse_zone']
childs = False
short_description = 'DNS: NS Record'
object_name = 'Nameserver record'
object_name_plural = 'Nameserver records'
long_description = _('Delegate a subzone to other nameservers.')
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'dNSZone'],
    ),
}
property_descriptions = {
    'zone': univention.admin.property(
        short_description=_('Zone name'),
        long_description=_('The name of the subzone relative to the parent.'),
        syntax=univention.admin.syntax.dnsName,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'zonettl': univention.admin.property(
        short_description=_('Time to live'),
        long_description=_('The time this entry may be cached.'),
        syntax=univention.admin.syntax.UNIX_TimeInterval,
        default=(('22', 'hours'), []),
        dontsearch=True,
    ),
    'nameserver': univention.admin.property(
        short_description=_('Name servers'),
        long_description=_('The FQDNs of the hosts serving the named zone.'),
        syntax=univention.admin.syntax.dnsHostname,
        multivalue=True,
        required=True,
    ),
}

layout = [
    Tab(_('General'), _('Basic values'), layout=[
        Group(_('General NS record settings'), layout=[
            'zone',
            'nameserver',
            'zonettl',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('zone', 'relativeDomainName', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('nameserver', 'nSRecord', encoding='ASCII')
mapping.register('zonettl', 'dNSTTL', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)


class object(DNSBase):
    module = module

    @classmethod
    def unmapped_lookup_filter(cls):
        return univention.admin.filter.conjunction('&', [
            univention.admin.filter.expression('objectClass', 'dNSZone'),
            univention.admin.filter.expression('nSRecord', '*', escape=False),
            univention.admin.filter.conjunction('!', [univention.admin.filter.expression('sOARecord', '*', escape=False)]),
        ])


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn, attr, canonical=False):  # type: (str, Attr, bool) -> bool
    return bool(
        attr.get('nSRecord')
        and is_dns(attr)
        and not is_zone(attr)
        and is_not_handled_by_other_module_than(attr, module),
    )
