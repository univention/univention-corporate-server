#!/usr/bin/python3
#
# Copyright 2023 Univention GmbH
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

"""Check Listener queues of installed apps for unprocessed files."""

from pathlib import Path

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Instance, Warning


_ = Translation('univention-management-console-module-diagnostic').translate

run_descr = ["Checks if there are unprocessed files in the Listener and Listener Converter queue directories of installed apps. Listener: /var/lib/univention-appcenter/listener/$AppName/ , Listener Converter: /var/lib/univention-appcenter/apps/$AppName/data/listener/"]
title = _('The app listener queues contain unprocessed files')
description = '\n'.join([
    _('This test checks whether there are unprocessed files in the App Listener directory /var/lib/univention-appcenter/listener/$AppName/ and Listener Converter directory /var/lib/univention-appcenter/apps/$AppName/data/listener/ of installed apps. '),
    _('Currently, there are unprocessed files in these directories. '),
    _('This could either mean that the affected app is currently processing these files or that there is some issue with the app queues. '),
    _('More information can be found in the app log files under /var/log/univention/.'),
])

APP_DIR = Path('/var/lib/univention-appcenter/apps/')
LISTENER_DIR = Path('/var/lib/univention-appcenter/listener/')


def run(_umc_instance: Instance) -> None:
    error_descriptions: list[str] = []

    for app_path in APP_DIR.glob("*"):
        converter_dir = LISTENER_DIR / app_path.name
        length = sum(1 for p in converter_dir.glob("*.json"))
        if length > 0:
            error_descriptions.append(_('The %(name)s Listener Converter has %(length)d unprocessed files.') % {'name': app_path.name, 'length': length})
        listener_path = app_path / "data/listener"
        if listener_path.exists():
            length = sum(1 for p in listener_path.glob("20*.json"))
            if length > 0:
                error_descriptions.append(_('The %(name)s Listener has %(length)d unprocessed files.') % {'name': app_path.name, 'length': length})

    if error_descriptions:
        raise Warning(f"{description}\n" + "\n".join(error_descriptions))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
