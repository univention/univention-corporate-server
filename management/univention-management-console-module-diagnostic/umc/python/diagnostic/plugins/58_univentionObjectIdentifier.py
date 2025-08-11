#!/usr/bin/python3
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess

from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Instance, ProblemFixed, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Validate all objects have Univention Object Identifier set')
description = '\n'.join([
    _('All objects of class "univentionObject" should have the attribute "univentionObjectIdentifier" in OpenLDAP.'),
])


def run(_umc_instance: Instance) -> None:
    if ucr.get('server/role') != 'domaincontroller_master':
        return

    process = subprocess.Popen(
        ['/usr/share/univention-ldap/univention-update-univention-object-identifier', '--dry-run'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    stdout, _stderr = process.communicate()
    stdout = stdout.decode('UTF-8', 'replace')
    if process.returncode == 2:
        raise Warning(f'{description}\n\n{stdout}', buttons=[{
            'action': 'update_objects',
            'label': _('Update LDAP objects'),
        }])


def update_objects(_umc_instance: Instance) -> None:
    cmd = "/usr/share/univention-ldap/univention-update-univention-object-identifier"
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise Warning(exc.output.decode('UTF-8', 'replace')) from exc
    raise ProblemFixed(buttons=[])


actions = {
    'update_objects': update_objects,
}


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
