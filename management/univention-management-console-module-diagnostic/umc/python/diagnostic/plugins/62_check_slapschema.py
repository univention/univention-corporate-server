#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2022-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

import os
import re
from subprocess import DEVNULL, PIPE, Popen

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Instance, Warning


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Validating the LDAP configuration and schema files.')
description = _('LDAP configuration is valid.')

RE_LINE = re.compile("^[0-9a-f]{8} (.+)")


def run(_umc_instance: Instance) -> None:
    if not os.path.exists('/usr/sbin/slapschema'):
        return

    process = Popen(['/usr/sbin/slapschema', '-f', '/etc/ldap/slapd.conf'], stdout=DEVNULL, stderr=PIPE, env=dict(os.environ, LANG='C'))
    assert process.stderr is not None
    errors = [
        m.group(1)
        for m in (RE_LINE.match(line.decode().strip()) for line in process.stderr)
        if m
    ]
    if not errors:
        return
    errors.insert(0, _('LDAP schema validation failed:'))
    msg = "\n".join(errors)
    raise Warning(
        description=msg,
        links=[
            {
                "name": "sdb",
                "href": "https://help.univention.com/t/problem-after-a-ldap-schema-was-removed-there-are-still-some-references-in-your-ldap/11810",
                "label": "Univention Help: After removing an LDAP schema, there are still some references in LDAP ",
            },
        ],
    )


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main

    main()
