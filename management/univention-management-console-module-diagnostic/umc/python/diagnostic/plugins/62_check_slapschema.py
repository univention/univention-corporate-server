#!/usr/bin/python3
# SPDX-FileCopyrightText: 2022-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
from subprocess import PIPE, Popen

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Validating the LDAP configuration and schema files.')
description = _('LDAP configuration files are valid.')


def run(_umc_instance: Instance) -> None:
    if not os.path.exists('/usr/sbin/slapschema'):
        return

    process = Popen(['/usr/sbin/slapschema', '-f', '/etc/ldap/slapd.conf'], stdout=PIPE, stderr=PIPE, env={'LANG': 'C'}, shell=True)
    _stdout, stderr_ = process.communicate()
    stderr = stderr_.decode('UTF-8', 'replace')

    if stderr:
        raise Warning(_('The LDAP schema validation failed with the following errors or warnings:\n') + stderr)


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main

    main()
