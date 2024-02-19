# -*- coding: utf-8 -*-
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

"""|UDM| functions to check and create blocklist entries"""


import hashlib
import re
from datetime import datetime

import ldap
from dateutil.relativedelta import relativedelta

import univention.admin.uexceptions
import univention.admin.uldap
from univention.admin import configRegistry


translation = univention.admin.localization.translation('univention.admin.handlers')
_ = translation.translate

BLOCKLIST_BASE = 'cn=blocklists,cn=internal'


try:
    unicode  # noqa: B018
except NameError:
    unicode = str


def hash_blocklist_value(value):
    return 'sha256:%s' % hashlib.sha256(value.lower().encode('UTF-8')).hexdigest()


def parse_timedelta(timedelta_string):
    """
    Parse time delta.

    >>> parse_timedelta("1y10m340d")
    relativedelta(years=+1, months=+10, days=+340)
    """
    match = re.match(r'((?P<years>-?\d+)y)?((?P<months>-?\d+)m)?((?P<days>-?\d+)d)?', timedelta_string)
    if match:
        parts = {unit: int(value) for unit, value in match.groupdict().items() if value}
        return relativedelta(**parts)


@univention.admin._ldap_cache(ttl=120)
def get_blocklist_config(lo):
    config = {}
    for blist in univention.admin.handlers.blocklists.list.lookup(None, lo, 'entryUUID=*', base=BLOCKLIST_BASE, scope='one'):
        config[blist.dn] = blist.get('retentionTime', '30d')
        for mod, prop in blist.get('blockingProperties', []):
            if not config.get(mod):
                config[mod] = {}
            config[mod][prop] = blist.dn
    return config


def get_blocking_udm_properties(udm_obj):
    config = get_blocklist_config(udm_obj.lo_machine_primary)
    return config.get(udm_obj.module, {})


def get_blockeduntil(dn, lo):
    config = get_blocklist_config(lo)
    retention = config.get(dn, '30d')
    blocking_duration = parse_timedelta(retention)
    blocked_until = datetime.utcnow() + blocking_duration
    return datetime.strftime(blocked_until, '%Y%m%d%H%M%SZ')


def blocklist_enabled(udm_obj):
    return not udm_obj.module.startswith('blocklists/') and configRegistry.is_true('directory/manager/blocklist/enabled', False)


def get_blocklist_values_from_udm_property(udm_property_value, udm_property_name):
    if isinstance(udm_property_value, (str, unicode)):
        return [udm_property_value]
    if not isinstance(udm_property_value, list) or not all(isinstance(mem, (str, unicode)) for mem in udm_property_value):
        raise RuntimeError('The property %r uses a complex syntax. This is not supported for blocklist objects.' % udm_property_name)
    return udm_property_value


def create_blocklistentry(udm_obj):
    if not blocklist_enabled(udm_obj):
        return []
    blocklist_entries = []
    for attr, bl_dn in get_blocking_udm_properties(udm_obj).items():
        if (not udm_obj.exists() and udm_obj.oldinfo.get(attr)) or (udm_obj.hasChanged(attr) and udm_obj.oldinfo.get(attr)):
            blocklist_position = univention.admin.uldap.position(bl_dn)
            for value in get_blocklist_values_from_udm_property(udm_obj.oldinfo[attr], attr):
                blocklistentry = univention.admin.handlers.blocklists.entry.object(None, udm_obj.lo_machine_primary, blocklist_position)
                blocklistentry.open()
                blocklistentry['value'] = value
                blocklistentry['originUniventionObjectIdentifier'] = udm_obj.entry_uuid
                blocklistentry['blockedUntil'] = get_blockeduntil(bl_dn, udm_obj.lo_machine_primary)
                try:
                    blocklistentry.create()
                except univention.admin.uexceptions.objectExists:
                    pass
                else:
                    blocklist_entries.append(blocklistentry.dn)
    return blocklist_entries


def check_blocklistentry(udm_obj):
    if not blocklist_enabled(udm_obj):
        return
    for attr, bl_dn in get_blocking_udm_properties(udm_obj).items():
        if udm_obj.hasChanged(attr) and udm_obj.info.get(attr):
            for value in get_blocklist_values_from_udm_property(udm_obj.info[attr], attr):
                hashed_value = ldap.dn.escape_dn_chars(hash_blocklist_value(value))
                dn = 'cn=%s,%s' % (hashed_value, bl_dn)
                obj = udm_obj.lo_machine_primary.get(dn)
                if obj and obj['originUniventionObjectIdentifier'][0].decode('utf-8') != udm_obj.entry_uuid:
                    raise univention.admin.uexceptions.valueError(_('The value %r is blocked for the UDM property %r.') % (value, attr), property=attr)


def cleanup_blocklistentry(blocklist_entries, udm_obj):
    for entry in blocklist_entries:
        try:
            udm_obj.lo_machine_primary.delete(entry)
        except univention.admin.uexceptions.noObject:
            pass
