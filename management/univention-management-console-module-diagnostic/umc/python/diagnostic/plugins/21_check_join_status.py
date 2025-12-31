#!/usr/bin/python3
# SPDX-FileCopyrightText: 2016-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from subprocess import PIPE, STDOUT, Popen

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Critical, Instance


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check join status')
description = _('The check for the join status was succsesful.')
links = [{
    'name': 'erroranalysis',
    'href': _('https://docs.software-univention.de/manual-5.2.html#domain:listenernotifier:erroranalysis'),
    'label': _('Manual: Analysis of listener/notifier problems'),
}]
umc_modules = [{'module': 'join'}]
run_descr = ['This can be checked by running: univention-check-join-status']


def run(_umc_instance: Instance) -> None:
    process = Popen(['univention-check-join-status'], stdout=PIPE, stderr=STDOUT)
    (stdout, stderr) = process.communicate()
    if process.returncode != 0:
        errors = [_('"univention-check-join-status" returned a problem with the domain join.')]
        if stdout:
            errors.append("\nSTDOUT:\n{}".format(stdout.decode('UTF-8', 'replace')))
        if stderr:
            errors.append("\nSTDERR:\n{}".format(stderr.decode('UTF-8', 'replace')))
        errors.append(_('See {erroranalysis} or run the join-scripts via {join}.'))
        MODULE.error('\n'.join(errors))
        raise Critical(description='\n'.join(errors))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
