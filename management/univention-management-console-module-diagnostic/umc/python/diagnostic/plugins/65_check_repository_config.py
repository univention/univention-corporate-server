#!/usr/bin/python3
# SPDX-FileCopyrightText: 2022-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Check the correctness of the repository configuration. A warning is
issued in case any UCR variable exist defining
username, password, port, prefix or path.
"""

import re
from collections import defaultdict
from re import Pattern

import univention.config_registry_info as cri
from univention.config_registry import handler_set as ucr_set, handler_unset as ucr_unset, ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.appcenter.util import create_url, scheme_is_http
from univention.management.console.modules.diagnostic import MODULE, Instance, ProblemFixed, Warning, main  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

umc_modules: list[dict[str, str]] = [
    {
        "module": "appcenter",
        "flavor": "components",
    },
    {
        "module": "ucr",
    },
]
run_desc = ["Checking repository configuration for correctness."]
title = _('Check repository configuration for correctness')
description = "\n".join((
    _("Some UCR variables for the repository configuration are deprecated."),
    _("As these variables should be no longer used, this check has been added to check for the existence of these variables."),
    _("Use the {appcenter:components} to correct these values by once saving the General repository settings "),
    _("as well as saving the settings for all Additional repositories or press the Button ADJUST ALL COMPONENTS "),
    _("to correct these settings and delete the obsolete variables."),
    _('Furthermore, it is checked if the scheme of the server variable is either http or https'),
))

ONLINE_BASE = 'repository/online'
COMPONENT_BASE = f'{ONLINE_BASE}/component'
DEPRECATED_VARS = ['prefix', 'username', 'password', 'port']
DEPRECATED_GEN = [f'{ONLINE_BASE}/{dep}' for dep in DEPRECATED_VARS]
RE_KEY = re.compile(f'{COMPONENT_BASE}/([^/]+)/({"|".join(DEPRECATED_VARS)})')

cleanup_vars: list[tuple[str, str]] = []


def run_cleanup_deprecated(umc_instance: Instance) -> None:

    msg = _('Cleanup of deprecated variables is executed !')
    MODULE.warn(msg)
    sorted_vars = defaultdict(list)
    for name, value in cleanup_vars:
        match = RE_KEY.fullmatch(name)
        component = match.group(1) if match else "$$BASE"
        sorted_vars[component].append((name, value))
    for var_list in sorted_vars.values():
        values: dict[str, str] = dict.fromkeys(DEPRECATED_VARS, "")
        for name, value in var_list:
            base, _dummy, key = name.rpartition("/")
            if key not in DEPRECATED_VARS:
                raise LookupError(f'Unexpected key found: {key}')
            values[key] = value
        server = ucr.get(f'{base}/server')
        server = create_url(server, values['prefix'], values['username'], values['password'], values['port'])
        ucr_set([f'{base}/server={server}'])
        ucr_unset([name[0] for name in var_list])
    raise ProblemFixed(buttons=[], description=_("After fixing the problem please use the Repository Settings module to check the changes made"))


actions = {
    'run_cleanup_deprecated': run_cleanup_deprecated,
}


def _get_config_registry_info() -> cri.ConfigRegistryInfo:
    cri.set_language('en')
    return cri.ConfigRegistryInfo(install_mode=False)


def _repo_relevant(name: str, reg: Pattern) -> bool:
    if name in DEPRECATED_GEN:
        return True
    return bool(reg.fullmatch(name))


def run(_umc_instance: Instance) -> None:
    error_descriptions: list[str] = []

    buttons = [{
        'action': 'run_cleanup_deprecated',
        'label': _('Adjust all components'),
    }]

    info = _get_config_registry_info()

    ignore_scheme_check = ucr.get("diagnostic/check/65_check_repository_config/ignore", "")
    for name in info.variables.keys():
        if _repo_relevant(name, RE_KEY):
            value = ucr.get(name, "")
            if value:
                if name == 'repository/online/port' and value == '80':
                    continue
                cleanup_vars.append((name, value))
                msg = _('The variable %(name)r is deprecated and should no longer be used.') % {'name': name}
                MODULE.warn(msg)
                error_descriptions.append(msg)
        elif not ignore_scheme_check and name.startswith(ONLINE_BASE) and name.endswith("server"):
            value = ucr.get(name, "")
            if not scheme_is_http(value):
                msg = "\n".join((
                    _('No http/https used as scheme in %(name)r: %(value)r.') % {'name': name, 'value': value},
                    _('This can be fixed only manually using the Repository Settings module or the UCR module.'),
                ))
                MODULE.warn(msg)
                error_descriptions.append(msg)
    if error_descriptions:
        raise Warning(f"{description}\n" + "\n".join(error_descriptions), buttons=buttons)


if __name__ == '__main__':
    main()
