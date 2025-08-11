#!/usr/bin/python3
# SPDX-FileCopyrightText: 2023-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Check Listener queues of installed apps for unprocessed files."""

from pathlib import Path

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Instance, Warning  # noqa: A004


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
