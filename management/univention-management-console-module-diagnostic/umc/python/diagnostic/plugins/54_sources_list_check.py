#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import glob
import re
import subprocess
from collections.abc import Iterator

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check errors in sources.list files')
description = _('All files ok.')
run_descr = ['Looking for Python exceptions in /etc/apt/sources.list.d/*']

TRACEBACK_REGEX = re.compile(
    r'(?P<start>#\s+)Traceback \(most recent call last\):\n'  # start of exception
    '(?:(?P=start).*\n)+?'  # irrelevant lines of detail
    r'(?P=start)(?P<exception>[^\s].*)\n')  # extract exception


def run_ucr_commit(umc_instance: Instance) -> None:
    cmd = [
        'ucr', 'commit',
        '/etc/apt/sources.list.d/15_ucs-online-version.list',
        '/etc/apt/sources.list.d/20_ucs-online-component.list',
    ]
    subprocess.call(cmd)
    run(umc_instance, rerun=True)


actions = {
    'run_ucr_commit': run_ucr_commit,
}


class TracebackFound(Exception):
    def __init__(self, path: str, exception: str) -> None:
        super().__init__(path, exception)
        self.path = path
        self.exception = exception

    def __str__(self) -> str:
        msg = _('Found exception in {path!r}: {exception}')
        return msg.format(path=self.path, exception=self.exception)


def find_tracebacks(path: str) -> Iterator[str]:
    with open(path) as fob:
        content = fob.read()
        for match in TRACEBACK_REGEX.finditer(content):
            yield match.group('exception')


def check_for_tracebacks() -> Iterator[TracebackFound]:
    for path in glob.glob('/etc/apt/sources.list.d/*'):
        for exception in find_tracebacks(path):
            yield TracebackFound(path, exception)


def run(_umc_instance: Instance, rerun: bool = False) -> None:
    error_descriptions = [str(exc) for exc in check_for_tracebacks()]

    buttons = [{
        'action': 'run_ucr_commit',
        'label': _('Regenerate sources.list'),
    }]

    if error_descriptions:
        error_descriptions.append(_('Please check the files for more details.'))
        if not rerun:
            error_descriptions.append(_('The error might be fixable by regenerating the sources.list.'))
            MODULE.error('\n'.join(error_descriptions))
            raise Warning(description='\n'.join(error_descriptions), buttons=buttons)
        raise Warning(description='\n'.join(error_descriptions))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
