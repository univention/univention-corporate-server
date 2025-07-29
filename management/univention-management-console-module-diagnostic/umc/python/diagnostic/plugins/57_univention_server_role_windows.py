#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


from univention.admin.uldap import access, getAdminConnection
from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Instance, ProblemFixed, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Server Role Windows')
description = '\n'.join([
    _('Several services rely on the attribute "univentionServerRole" to search and identify objects in OpenLDAP.'),
    _('Objects that implicitly satisfy the criteria of a Univention Object but lack this attribute should be migrated.'),
])

_WINDOWS_SERVER_ROLES = {
    'computers/windows_domaincontroller': 'windows_domaincontroller',
    'computers/windows': 'windows_client',
}


def udm_objects_without_ServerRole(lo: access) -> dict[str, list[str]]:
    objs: dict[str, list[str]] = {}
    result = lo.search('(&(objectClass=univentionWindows)(!(univentionServerRole=*)))', attr=['univentionObjectType'])
    if result:
        ldap_base = ucr.get('ldap/base')
        for dn, attrs in result:
            if dn.endswith(',cn=temporary,cn=univention,%s' % ldap_base):
                continue
            try:
                univentionObjectType = attrs['univentionObjectType'][0].decode('UTF-8')
            except KeyError:
                univentionObjectType = None

            server_role = _WINDOWS_SERVER_ROLES.get(univentionObjectType, "")
            objs.setdefault(server_role, []).append(dn)

    return objs


def run(_umc_instance: Instance) -> None:
    if ucr.get('server/role') != 'domaincontroller_master':
        return

    lo, _pos = getAdminConnection()
    objs = udm_objects_without_ServerRole(lo)
    details = '\n\n' + _('These objects were found:')

    total_objs = 0
    fixable_objs = 0
    for server_role in sorted(objs):
        num_objs = len(objs[server_role])
        if num_objs:
            total_objs += num_objs
            if server_role:
                fixable_objs += num_objs
                details += '\n· ' + _('Number of objects that should be marked as "%(server_role)s": %(num_objs)d') % {'server_role': server_role, 'num_objs': num_objs}
            else:
                details += '\n· ' + _("Number of unspecific Windows computer objects with inconsistent univentionObjectType: %d (Can't fix this automatically)") % (num_objs,)
    if total_objs:
        if fixable_objs:
            raise Warning(description + details, buttons=[{
                'action': 'migrate_objects',
                'label': _('Migrate %d LDAP objects') % fixable_objs,
            }])
        else:
            raise Warning(description + details, buttons=[])


def migrate_objects(_umc_instance: Instance) -> None:
    lo, _pos = getAdminConnection()
    objs = udm_objects_without_ServerRole(lo)
    for server_role in sorted(objs):
        if not server_role:
            continue
        for dn in objs[server_role]:
            changes = [('univentionServerRole', None, server_role)]
            lo.modify(dn, changes)
    raise ProblemFixed(buttons=[])


actions = {
    'migrate_objects': migrate_objects,
}


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
