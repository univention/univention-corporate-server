#!/usr/bin/python3
# SPDX-FileCopyrightText: 2016-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Critical, Instance, ProblemFixed, util


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check local AD database for errors')
description = _('No errors found.')
run_descr = ['This can be checked by running: samba-tool dbcheck']


def run_samba_tool_dbcheck_fix(umc_instance: Instance) -> None:
    if not util.is_service_active('Samba 4'):
        return

    cmd = ['samba-tool', 'dbcheck', '--fix', '--cross-ncs', '--yes']
    (_success, output) = util.run_with_output(cmd)

    cmd_string = ' '.join(cmd)
    MODULE.process('Output of %s:\n%s', cmd_string, output)
    fix_log = [_('Output of `{cmd}`:').format(cmd=cmd_string)]

    fix_log.append(output)
    run(umc_instance, rerun=True, fix_log='\n'.join(fix_log))


actions = {
    'run_samba_tool_dbcheck_fix': run_samba_tool_dbcheck_fix,
}


def run(_umc_instance: Instance, rerun: bool = False, fix_log: str = '') -> None:
    if not util.is_service_active('Samba 4'):
        return

    error_descriptions = []
    if rerun and fix_log:
        error_descriptions.append(fix_log)

    buttons = [{
        'action': 'run_samba_tool_dbcheck_fix',
        'label': _('Run `samba-tool dbcheck --fix --cross-ncs --yes`'),
    }]

    cmd = ['samba-tool', 'dbcheck']
    (_success, output) = util.run_with_output(cmd)
    if [x for x in output.split('\n') if x.startswith("ERROR:")]:
        error = _('`samba-tool dbcheck` found an error in the local AD database.')
        error_descriptions.append(error)
        error_descriptions.append(output)
        if not rerun:
            fix = _('You can run `samba-tool dbcheck --fix` to fix the issue.')
            error_descriptions.append(fix)
        raise Critical(description='\n'.join(error_descriptions), buttons=buttons)

    if rerun:
        fixed = _('`samba-tool dbcheck` found no errors in the local AD database.')
        error_descriptions.append(fixed)
        MODULE.error('\n'.join(error_descriptions))
        raise ProblemFixed(description='\n'.join(error_descriptions))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
