#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2016-2023 Univention GmbH
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

from typing import Any, Dict, List, Tuple

from univention.admin.modules import identify, update
from univention.admin.uldap import access, getAdminConnection
from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Instance, ProblemFixed, Warning


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('LDAP objects')
description = '\n'.join([
    _('Several services rely on the attribute "univentionObjectType" to search and identify objects in LDAP.'),
    _('Objects that implicitly satisfy the standards of a Univention Object but lack this attribute should be migrated.'),
])

_UPDATED = False
UdmModule = Any  # FIXME


def udm_objects_without_type(lo: access) -> List[Tuple[str, List[UdmModule], List[bytes]]]:
    global _UPDATED
    if not _UPDATED:
        update()
        _UPDATED = True
    objs = []
    query = lo.search('(!(univentionObjectType=*))')
    for dn, attrs in query:
        if dn.endswith(',cn=temporary,cn=univention,%s' % ucr.get('ldap/base')):
            continue
        modules = identify(dn, attrs)
        if modules:
            for module in modules:  # Bug #47846
                if module.module == 'kerberos/kdcentry':
                    break
            else:
                objs.append((dn, modules, attrs['objectClass']))
    return objs


def run(_umc_instance: Instance) -> None:
    if ucr.get('server/role') != 'domaincontroller_master':
        return

    lo, pos = getAdminConnection()
    objects = udm_objects_without_type(lo)
    if len(objects):
        counted_objects: Dict[str, int] = {}
        details = '\n\n' + _('These objects were found:')
        for _dn, modules, _object_classes in objects:
            for module in modules:
                counted_objects.setdefault(module.short_description, 0)
                counted_objects[module.short_description] += 1
        for module_name in sorted(counted_objects.keys()):
            num_objs = counted_objects[module_name]
            details += '\n· ' + _('%d objects should be "%s"') % (num_objs, module_name)
        raise Warning(description + details, buttons=[{
            'action': 'migrate_objects',
            'label': _('Migrate %d LDAP objects') % len(objects),
        }])


def migrate_objects(_umc_instance: Instance) -> None:
    lo, pos = getAdminConnection()
    objects = udm_objects_without_type(lo)
    for dn, modules, object_classes in objects:
        new_object_classes = object_classes[:]
        if b'univentionObject' not in object_classes:
            new_object_classes.append(b'univentionObject')
        changes = [
            ('objectClass', object_classes, new_object_classes),
            ('univentionObjectType', [], [module.module.encode('UTF-8') for module in modules]),
        ]
        lo.modify(dn, changes)
    raise ProblemFixed(buttons=[])


actions = {
    'migrate_objects': migrate_objects,
}


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
