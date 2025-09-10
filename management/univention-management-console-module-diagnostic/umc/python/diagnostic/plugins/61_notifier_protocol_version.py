#!/usr/bin/python3
# SPDX-FileCopyrightText: 2016-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from collections.abc import Callable
from subprocess import call

from univention.config_registry import handler_set, ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Critical, Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

UCS = (4, 3, 3, 428)
UCR = "notifier/protocol/version"
UDN = 3
BUTTON = {
    "label": _("Update protocol version"),
    "action": "set_protocol_version",
}

title = _('Check of the protocol version of the Univention Directory Notifier')
description = _('Starting with UCS {ucs[0]}.{ucs[1]}-{ucs[2]} erratum {ucs[3]}, the minimum protocol version should be set to {udn}.').format(ucs=UCS, udn=UDN)
run_descr = [f'This can be checked by running: ucr get {UCR}']
umc_modules = [{'module': 'ucr'}]

invalid_msg = _('The UCR variable <tt>{ucr}</tt> is not configured or invalid.')


def run(_umc_instance: Instance) -> None:
    server_role = ucr.get('server/role')
    if server_role not in ('domaincontroller_master', 'domaincontroller_backup'):
        return

    problems: list[str] = []

    var = "version/version"
    ucs_version = ucr.get(var, "")
    maj_str, _, min_str = ucs_version.partition(".")
    try:
        major, minor = int(maj_str), int(min_str)
    except ValueError:
        problems.append(invalid_msg.format(ucr=var))

    var = "version/patchlevel"
    ucs_patchlevel = ucr.get_int(var, -1)
    if ucs_patchlevel < 0:
        problems.append(invalid_msg.format(ucr=var))

    var = "version/erratalevel"
    ucs_erratalevel = ucr.get_int(var, -1)
    if ucs_erratalevel < 0:
        problems.append(invalid_msg.format(ucr=var))

    np_version = ucr.get_int(UCR, -1)
    if np_version < 0:
        problems.append(invalid_msg.format(ucr=UCR))

    if problems:
        text = "\n".join(problems)
        MODULE.error(text)
        raise Critical(text)

    if (major, minor, ucs_patchlevel, ucs_erratalevel) >= (4, 3, 3, 428) and np_version < UDN:
        MODULE.error(description)
        raise Warning(description, buttons=[BUTTON])


def set_protocol_version(umc: Instance) -> None:
    MODULE.process("Setting UDN protocol version %s", UDN)
    handler_set(["%s=%d" % (UCR, UDN)])
    call(["systemctl", "try-restart", "univention-directory-notifier.service"])
    return run(umc)


actions: dict[str, Callable[[Instance], None]] = {
    "set_protocol_version": set_protocol_version,
}


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
