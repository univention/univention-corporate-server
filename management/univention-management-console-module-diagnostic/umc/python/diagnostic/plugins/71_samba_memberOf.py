#!/usr/bin/python3
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path

import ldap

from univention.config_registry import handler_set as ucr_set, ucr_live as ucr
from univention.lib.i18n import Translation
from univention.lib.misc import custom_username
from univention.management.console.modules.diagnostic import MODULE, Instance, ProblemFixed, Warning, util  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate
admin_user = custom_username('Administrator', ucr)

title = _('Check visibility of the memberOf attribute in Samba/AD')
description = _('No errors found.')
run_descr = [f'This can be checked by running: univention-s4search sAMAccountName={admin_user} memberOf']
links = [
    {
        'name': 'sdb',
        'href': 'https://help.univention.com/t/problem-no-memberof-attributes-in-samba-after-update-to-ucs-5/18673',
        'label': 'Univention Support Database - Some attributes in Samba like memberOf are missing',
    },
]


def run_samba_tool_group_addmembers_with_authenticated_users(umc_instance: Instance) -> None:
    if not util.is_service_active('Samba 4'):
        return

    cmd = ['samba-tool', 'group', 'addmembers', 'Pre-Windows 2000 Compatible Access', '--member-dn=CN=S-1-5-11,CN=ForeignSecurityPrincipals,%s' % ucr['ldap/base']]
    (_success, output) = util.run_with_output(cmd)

    cmd_string = ' '.join(cmd)
    MODULE.process('Output of %s:\n%s', cmd_string, output)
    fix_log = [_('Output of `{cmd}`:').format(cmd=cmd_string)]

    fix_log.append(output)
    run(umc_instance, rerun=True, fix_log='\n'.join(fix_log))


def run_samba_tool_group_addmembers_with_enterprise_domain_controllers(umc_instance: Instance) -> None:
    if not util.is_service_active('Samba 4'):
        return

    cmd = ['samba-tool', 'group', 'addmembers', 'Pre-Windows 2000 Compatible Access', '--member-dn=CN=S-1-5-9,CN=ForeignSecurityPrincipals,%s' % ucr['ldap/base']]
    (_success, output) = util.run_with_output(cmd)

    cmd_string = ' '.join(cmd)
    MODULE.process('Output of %s:\n%s', cmd_string, output)
    fix_log = [_('Output of `{cmd}`:').format(cmd=cmd_string)]

    fix_log.append(output)
    run(umc_instance, rerun=True, fix_log='\n'.join(fix_log))


def deactivate_test(umc_instance: Instance) -> None:
    ucr_set([f'diagnostic/check/disable/{Path(__file__).stem}=yes'])


actions = {
    'deactivate_test': deactivate_test,
    'run_samba_tool_group_addmembers_with_authenticated_users': run_samba_tool_group_addmembers_with_authenticated_users,
    'run_samba_tool_group_addmembers_with_enterprise_domain_controllers': run_samba_tool_group_addmembers_with_enterprise_domain_controllers,
}


def run(_umc_instance: Instance, rerun: bool = False, fix_log: str = '') -> None:
    if not util.is_service_active('Samba 4'):
        return

    error_descriptions = []
    if rerun and fix_log:
        error_descriptions.append(fix_log)

    buttons = [
        {
            'action': 'deactivate_test',
            'label': _('Deactivate test permanently'),
        },
        {
            'action': 'run_samba_tool_group_addmembers_with_authenticated_users',
            'label': _('Add "Authenticated Users" to "Pre-Windows 2000 Compatible Access"'),
        },
        {
            'action': 'run_samba_tool_group_addmembers_with_enterprise_domain_controllers',
            'label': _('Add "Enterprise Domain Controllers" to "Pre-Windows 2000 Compatible Access"'),
        },
    ]

    cmd = ['univention-s4search', ldap.filter.filter_format('sAMAccountName=%s', [admin_user]), 'memberOf']
    (_success, output) = util.run_with_output(cmd)
    if not [x for x in output.split('\n') if x.startswith('memberOf:')]:
        error = _('univention-s4search did not show any memberOf values for sAMAccountName=%s.') % admin_user
        error_descriptions.append(error)

        cmd = ['samba-tool', 'group', 'listmembers', 'Pre-Windows 2000 Compatible Access']
        (_success, output) = util.run_with_output(cmd)
        if not [x for x in output.split('\n') if x in ('S-1-5-11', 'S-1-5-9')]:
            error = '\n' + _('Typically either "Authenticated Users" or "Enterprise Domain Controllers" are member of "Pre-Windows 2000 Compatible Access".')
            error_descriptions.append(error)
            error = _('But here neither of these groups is member of "Pre-Windows 2000 Compatible Access". This is probably the cause of this behavior.')
            error_descriptions.append(error)
            error = _('By default Active Directory has "Authenticated Users" (S-1-5-11) in "Pre-Windows 2000 Compatible Access", but this can also pose some security issue.')
            error_descriptions.append(error)
            error = _(
                'As an alternative, depending on the use case, one can make "Enterprise Domain Controllers" (S-1-5-9) member of "Pre-Windows 2000 Compatible Access", which makes the "memberOf" attribute only visible for domain controllers (e.g. for univention-s4search).',
            )
            error_descriptions.append(error)

        if not rerun:
            fix = _('Please chose an action.')
            error_descriptions.append(fix)
        raise Warning(description='\n'.join(error_descriptions), buttons=buttons)

    if rerun:
        fixed = _('OK, fix worked, "univention-s4search sAMAccountName=%s memberOf" shows group memberships.') % admin_user
        error_descriptions.append(fixed)
        MODULE.error('\n'.join(error_descriptions))
        raise ProblemFixed(description='\n'.join(error_descriptions))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main

    main()
