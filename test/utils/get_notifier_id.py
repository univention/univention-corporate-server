#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Directory Listener
"""Read the notifier id from the DC master"""
#
# Copyright 2004-2017 Univention GmbH
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

import socket
from univention.config_registry import ConfigRegistry
import sys


def main():
    """Retrieve current Univention Directory Notifier transaction ID."""
    configRegistry = ConfigRegistry()
    configRegistry.load()

    master = configRegistry.get('ldap/master')
    if not master:
        print >> sys.stderr, 'Error: ldap/master not set'
        sys.exit(1)

    try:
        sock = socket.create_connection((master, 6669), 60.0)

        sock.send('Version: 3\nCapabilities: \n\n')
        sock.recv(100)

        sock.send('MSGID: 1\nGET_ID\n\n')
        notifier_result = sock.recv(100)

        if notifier_result:
            print "%s" % notifier_result.splitlines()[1]
    except socket.error as ex:
        print >> sys.stderr, 'Error: %s' % (ex,)
        sys.exit(1)


if __name__ == '__main__':
    main()
