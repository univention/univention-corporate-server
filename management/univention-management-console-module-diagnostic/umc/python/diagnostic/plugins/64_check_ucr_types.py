#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2022-2023 Univention GmbH
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

"""
Check correctness of UCR type definitions and type compatibility
of all defined variables.
"""

from typing import Dict, List

import univention.config_registry_info as cri
from univention.config_registry import ucr_live as ucr
from univention.config_registry.validation import Type
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning, main


_ = Translation('univention-management-console-module-diagnostic').translate

run_desc = ["Checking UCR variable values for correctness."]
title = _('Check UCR variable values for correctness')
description = "\n".join((
    _("Some UCR variables currently have invalid values."),
    _("This check has been added recently; some warning may be unproblematic."),
    _("Please investigate them if you experience any problems on this system."),
    _("Use the module {ucr} to correct their values."),
))
umc_modules: List[Dict[str, str]] = [
    {
        "module": "ucr",
    },
]


def _get_config_registry_info() -> cri.ConfigRegistryInfo:
    cri.set_language('en')
    return cri.ConfigRegistryInfo(install_mode=False)


def run(_umc_instance: Instance) -> None:
    error_descriptions: List[str] = []

    info = _get_config_registry_info()
    ignore = {typ for typ in (typ.strip() for typ in ucr.get("diagnostic/check/64_check_ucr_types/ignore", "").split(",")) if typ}
    for name, var in info.variables.items():
        try:
            validator = Type(var)
            if validator.vtype in ignore:
                continue
        except (TypeError, ValueError):
            msg = _('Invalid type %(type)r defined for variable %(variable)r.') % {'type': var.get('type'), 'variable': name}
            MODULE.error(msg)
            error_descriptions.append(msg)
        else:
            value = ucr.get(name)
            if value is not None and not validator.check(value):
                msg = _('The variable %(variable)r has the invalid value %(value)r.') % {'value': value, 'variable': name}
                MODULE.error(msg)
                error_descriptions.append(msg)

    if error_descriptions:
        raise Warning(description + '\n' + '\n'.join(error_descriptions))


if __name__ == '__main__':
    main()
