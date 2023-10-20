#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2016-2023 Univention GmbH
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

from subprocess import call
from typing import Callable, Dict, List

from univention.config_registry import handler_set, ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Critical, Instance, Warning


_ = Translation('univention-management-console-module-diagnostic').translate

UCS = (4, 3, 3, 428)
UCR = "notifier/protocol/version"
UDN = 3
BUTTON = {
    "label": _("Update protocol version"),
    "action": "set_protocol_version",
}

title = _('Check of the protocol version of the Univention Directory Notifier')
description = _('Starting with UCS {ucs[0]}.{ucs[1]}-{ucs[2]} erratum {ucs[3]}, the minimum protocol version should be set to {udn}.').format(ucs=UCS, udn=UDN,)
run_descr = [f'This can be checked by running: ucr get {UCR}']
umc_modules = [{'module': 'ucr'}]

invalid_msg = _('The UCR variable <tt>{ucr}</tt> is not configured or invalid.')


def run(_umc_instance: Instance,) -> None:
    server_role = ucr.get('server/role')
    if server_role not in ('domaincontroller_master', 'domaincontroller_backup'):
        return

    problems: List[str] = []

    var = "version/version"
    ucs_version = ucr.get(var, "",)
    maj_str, _, min_str = ucs_version.partition(".")
    try:
        major, minor = int(maj_str), int(min_str)
    except ValueError:
        problems.append(invalid_msg.format(ucr=var))

    var = "version/patchlevel"
    ucs_patchlevel = ucr.get_int(var, -1,)
    if ucs_patchlevel < 0:
        problems.append(invalid_msg.format(ucr=var))

    var = "version/erratalevel"
    ucs_erratalevel = ucr.get_int(var, -1,)
    if ucs_erratalevel < 0:
        problems.append(invalid_msg.format(ucr=var))

    np_version = ucr.get_int(UCR, -1,)
    if np_version < 0:
        problems.append(invalid_msg.format(ucr=UCR))

    if problems:
        text = "\n".join(problems)
        MODULE.error(text)
        raise Critical(text)

    if (major, minor, ucs_patchlevel, ucs_erratalevel) >= (4, 3, 3, 428) and np_version < UDN:
        MODULE.error(description)
        raise Warning(description, buttons=[BUTTON],)


def set_protocol_version(umc: Instance,) -> None:
    MODULE.process(f"Setting UDN protocol version {UDN}")
    handler_set(["%s=%d" % (UCR, UDN)])
    call(["systemctl", "try-restart", "univention-directory-notifier.service"])
    return run(umc)


actions: Dict[str, Callable[[Instance], None]] = {
    "set_protocol_version": set_protocol_version,
}


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
