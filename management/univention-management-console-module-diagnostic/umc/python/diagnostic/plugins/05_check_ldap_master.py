#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2016-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path

import univention.uldap
from univention.config_registry import handler_set as ucr_set, ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Critical, Instance, ProblemFixed, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Primary LDAP server check')
description = ['Check the UCR variable `ldap/master` for correctness.']
run_descr = ["Checking Primary LDAP server"]
umc_modules = [{'module': 'ucr'}]


def deactivate_test(umc_instance: Instance) -> None:
    ucr_set([f'diagnostic/check/disable/{Path(__file__).stem}=yes'])


def fix_ldap_master(umc_instance: Instance) -> None:
    master_fqdn = lookup_master()
    ucr_set([f'ldap/master={master_fqdn}'])
    run(umc_instance, retest=True)


actions = {
    'fix_ldap_master': fix_ldap_master,
    'deactivate_test': deactivate_test,
}


def lookup_master() -> str:
    lo = univention.uldap.getMachineConnection()
    master = lo.search(base=ucr['ldap/base'], filter='(univentionServerRole=master)', attr=['cn'])
    try:
        master_cn = master[0][1].get('cn')[0].decode('UTF-8')
    except IndexError:
        raise Critical(f'Could not find the Primary Directory Node {master}')

    return f"{master_cn}.{ucr['domainname']}"


def run(_umc_instance: Instance, retest: bool = False) -> None:
    buttons = [
        {
            "action": "fix_ldap_master",
            "label": _("Fix Primary LDAP server configuration"),
        },
        {
            'action': 'deactivate_test',
            'label': _('Deactivate test'),
        },
    ]

    master_fqdn = lookup_master()
    if master_fqdn != ucr['ldap/master']:
        warn = (_('The primary LDAP Server of this System (UCR ldap/master) is not set to the Primary Directory Node of this UCS domain (%s).') % (master_fqdn,))
        raise Warning(warn, buttons=buttons)

    if retest:
        raise ProblemFixed(buttons=[])


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
