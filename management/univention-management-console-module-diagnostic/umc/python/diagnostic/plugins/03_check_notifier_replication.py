#!/usr/bin/python3
# SPDX-FileCopyrightText: 2016-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import socket

from univention.config_registry import ucr_live as configRegistry
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate
run_descr = ["Checks if the output of /usr/share/univention-directory-listener/get_notifier_id.py and the value in /var/lib/univention-directory-listener/notifier_id are the same"]
title = _('Check for problems with UDN replication')
description = _('No problems found with UDN replication.')

links = [{
    'name': 'sdb',
    'href': 'https://help.univention.com/t/troubleshooting-listener-notifier/6430',
    'label': _('Univention Support Database - Troubleshooting: Listener-/Notifier'),
}]


def get_id(master: str, cmd: str = 'GET_ID') -> str:
    sock = socket.create_connection((master, 6669), 60.0)

    sock.send(b'Version: 3\nCapabilities: \n\n')
    sock.recv(100)

    sock.send(f'MSGID: 1\n{cmd}\n\n'.encode('ASCII'))
    notifier_result = sock.recv(100).strip().decode('ASCII')

    (_msg_id, notifier_id) = notifier_result.split('\n', 1)
    return notifier_id


def run(_umc_instance: Instance) -> None:
    try:
        notifier_id = get_id(configRegistry.get('ldap/master'))
    except OSError:
        MODULE.error('Error retrieving notifier ID from the UDN.')
        raise Warning(_('Error retrieving notifier ID from the UDN.'))
    else:
        with open('/var/lib/univention-directory-listener/notifier_id') as fob:
            id_from_file = fob.read().strip()

        if notifier_id != id_from_file:
            ed = [
                _('Univention Directory Notifier ID and the locally stored version differ.'),
                _('This might indicate an error or still processing transactions.'),
            ]
            MODULE.error('\n'.join(ed))
            raise Warning('\n'.join(ed))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
