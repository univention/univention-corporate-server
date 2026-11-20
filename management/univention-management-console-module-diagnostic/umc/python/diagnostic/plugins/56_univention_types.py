#!/usr/bin/python3
# SPDX-FileCopyrightText: 2016-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess

from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Instance, ProblemFixed, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('LDAP objects')
description = '\n'.join([
    _('Several services rely on the attribute "univentionObjectType" to search and identify objects in LDAP.'),
    _('Objects that implicitly satisfy the standards of a Univention Object but lack this attribute should be migrated.'),
])


def run(_umc_instance: Instance) -> None:
    if ucr.get('server/role') != 'domaincontroller_master':
        return

    process = subprocess.Popen(
        ['/usr/share/univention-directory-manager-tools/univention-object-type-migrate', '--no-action'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    stdout, _stderr = process.communicate()
    stdout = stdout.decode('UTF-8', 'replace')
    if process.returncode or 'Would modify' in stdout:
        raise Warning(f'{description}\n\n{stdout}', buttons=[{
            'action': 'migrate_objects',
            'label': _('Migrate LDAP objects'),
        }])


def migrate_objects(_umc_instance: Instance) -> None:
    cmd = ['/usr/share/univention-directory-manager-tools/univention-object-type-migrate', '--action']
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise Warning(exc.output.decode('UTF-8', 'replace')) from exc
    raise ProblemFixed(buttons=[])


actions = {
    'migrate_objects': migrate_objects,
}


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
