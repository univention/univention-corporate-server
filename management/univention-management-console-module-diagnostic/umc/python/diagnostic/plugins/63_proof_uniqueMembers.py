#!/usr/bin/python3
# SPDX-FileCopyrightText: 2022-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import shlex

from univention.config_registry import ucr
from univention.lib.i18n import Translation
from univention.management.console.log import MODULE
from univention.management.console.modules.diagnostic import Instance, ProblemFixed, Warning, util  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check LDAP database for inconsistencies in group memberships.')
description = _('Check the LDAP database for inconsistencies in group membership attributes.')
run_descr = ['This can be checked by running: /usr/share/univention-directory-manager-tools/proof_uniqueMembers -c']


def run_proof_uniqueMembers_fix(umc_instance: Instance) -> None:
    cmd = ['/usr/share/univention-directory-manager-tools/proof_uniqueMembers']
    (_success, output) = util.run_with_output(cmd)

    cmd_string = ' '.join(shlex.quote(x) for x in cmd)
    MODULE.process('Output of %s: %r', cmd_string, output)
    fix_log = [_('Output of `{cmd}`:').format(cmd=cmd_string)]

    fix_log.append(output)
    run(umc_instance, rerun=True, fix_log='\n'.join(fix_log))


actions = {
    'run_proof_uniqueMembers_fix': run_proof_uniqueMembers_fix,
}


def run(_umc_instance: Instance, rerun: bool = False, fix_log: str = '') -> None:
    if ucr.get('server/role') != 'domaincontroller_master':
        return
    error_descriptions = []
    if rerun and fix_log:
        error_descriptions.append(fix_log)

    buttons = [{
        'action': 'run_proof_uniqueMembers_fix',
        'label': _('Run `/usr/share/univention-directory-manager-tools/proof_uniqueMembers`'),
    }]

    cmd = ['/usr/share/univention-directory-manager-tools/proof_uniqueMembers', '-c']
    (success, output) = util.run_with_output(cmd)
    if not success:
        error = _('`/usr/share/univention-directory-manager-tools/proof_uniqueMembers -c` found an error with the LDAP database group membership attributes.')
        error_descriptions.append(error)
        error_descriptions.append(output)
        if not rerun:
            fix = _('You can run `/usr/share/univention-directory-manager-tools/proof_uniqueMembers` to fix the issue.')
            error_descriptions.append(fix)
        raise Warning(description='\n'.join(error_descriptions), buttons=buttons)

    if rerun:
        fixed = _('`/usr/share/univention-directory-manager-tools/proof_uniqueMembers -c` found no errors with the LDAP database group membership attributes.')
        error_descriptions.append(fixed)
        MODULE.error('\n'.join(error_descriptions))
        raise ProblemFixed(description='\n'.join(error_descriptions))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
