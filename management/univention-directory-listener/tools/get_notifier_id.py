#!/usr/bin/python3
#
# Univention Directory Listener
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Read the notifier id from the Primary Directory Node"""


import argparse
import socket
import sys

from univention.config_registry import ucr


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-s', '--schema',
        action='store_const',
        const='GET_SCHEMA_ID',
        default='GET_ID',
        help='Fetch LDAP Schema ID',
        dest='cmd',
    )
    parser.add_argument(
        '--master',
        '-m',
        default=ucr.get("ldap/master"),
        help='LDAP Server address',
    )
    parser.add_argument(
        'master',
        nargs='?',
        default=argparse.SUPPRESS,
        help=argparse.SUPPRESS,
    )
    options = parser.parse_args()
    return options


def main() -> None:
    """Retrieve current Univention Directory Notifier transaction ID."""
    options = parse_args()
    try:
        sock = socket.create_connection((options.master, 6669), 60.0)

        sock.send(b'Version: 3\nCapabilities: \n\n')
        sock.recv(100)

        sock.send(b'MSGID: 1\n%s\n\n' % (options.cmd.encode('UTF-8'),))
        notifier_result = sock.recv(100)

        if notifier_result:
            print("%s" % notifier_result.decode('UTF-8', 'replace').splitlines()[1])
    except OSError as ex:
        print('Error: %s' % (ex,), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
