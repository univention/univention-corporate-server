#!/usr/bin/python3
# SPDX-FileCopyrightText: 2016-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import subprocess

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check for modified UCR templates')
description = _('No problems found with modified UCR templates')
run_descr = ['This can be checked by running: univention-check-templates']


def run(_umc_instance: Instance) -> None:
    cmd = ['univention-check-templates']
    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError as error:
        error_description = [
            _('Errors found by `univention-check-templates`.'),
            _('The following UCR files are modified locally.'),
            _('Updated versions will be named FILENAME.dpkg-*.'),
            _('The files should be checked for differences.'),
        ]
        if error.output:
            MODULE.error('\n'.join(error_description))
            error_description.extend(('\n\n', error.output.decode('UTF-8', 'replace')))
        raise Warning(' '.join(error_description))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
