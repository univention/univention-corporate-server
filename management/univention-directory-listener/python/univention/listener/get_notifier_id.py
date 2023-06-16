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


def get_nid(master: str, cmd: str = "GET_ID") -> int:
    """Retrieve current Univention Directory Notifier transaction or schema ID."""
    sock = socket.create_connection((master, 6669), 60.0)

    sock.send(b'Version: 3\nCapabilities: \n\n')
    sock.recv(100)

    sock.send(b'MSGID: 1\n%s\n\n' % (cmd.encode('UTF-8'),))
    answer = sock.recv(100)
    text = answer.decode()
    lines = text.splitlines()
    return int(lines[1])


def main() -> None:
    """Retrieve current Univention Directory Notifier transaction ID."""
    options = parse_args()
    try:
        print(get_nid(options.master, options.cmd))
    except (OSError, UnicodeDecodeError, IndexError, ValueError) as ex:
        sys.exit('Error: %s' % (ex,))


if __name__ == '__main__':
    main()
