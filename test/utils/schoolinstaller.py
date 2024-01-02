#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2024 Univention GmbH
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

from __future__ import print_function

import sys
import time
import traceback
from argparse import ArgumentParser, Namespace  # noqa: F401


try:
    from typing import Any, Dict  # noqa: F401
except ImportError:
    pass

try:
    from univention.config_registry import ucr
except ImportError:
    from univention.config_registry import ConfigRegistry
    ucr = ConfigRegistry()
    ucr.load()

from univention.lib.umc import Client, ConnectionError, HTTPError


# we need python2.7 compatibility as this is also
# used to setup school in UCS 4 (update tests, ...)


def parse_args():  # type: () -> Namespace
    parser = ArgumentParser()
    parser.add_argument(
        '-H', '--host',
        default='%(hostname)s.%(domainname)s' % ucr,
        help='UMC host to connect to',
    )
    parser.add_argument(
        '-u', '--user',
        dest='username',
        required=True,
        help='UMC username',
        metavar='UID',
        default='Administrator',
    )
    parser.add_argument(
        '-p', '--password',
        required=True,
        help='UMC password',
    )
    parser.add_argument(
        '-o', '--ou',
        help='OU name of the school',
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-S', '--single-server',
        dest='setup',
        action='store_const',
        const='singlemaster',
        help='install a single server setup on a Primary',
    )
    group.add_argument(
        '-M', '--multi-server',
        dest='setup',
        action='store_const',
        const='multiserver',
        help='install a multi server setup',
    )

    parser.add_argument(
        '-E', '--educational-server-name',
        dest='name_edu_server',
        help='name of the educational server',
        metavar='EDU-HOST',
    )

    group = parser.add_mutually_exclusive_group(required=ucr['server/role'] == 'domaincontroller_slave')
    parser.add_argument(
        '-e', '--educational-server',
        dest='server_type',
        action='store_const',
        const='educational',
        help='install a DC Replica in educational network (DEFAULT)',
    )
    parser.add_argument(
        '-a', '--administrative-server',
        dest='server_type',
        action='store_const',
        const='administrative',
        help='install a DC Replica in administrative network',
    )

    parser.add_argument(
        '-m', '--master-host',
        dest='master',
        default=ucr['ldap/master'],
        required=ucr['server/role'] != 'domaincontroller_master',
        help='on a Replica the Primary host needs to be specified',
        metavar='HOST',
    )
    parser.add_argument(
        '-s', '--samba-version',
        dest='samba',
        default='4',
        choices=("3", "4"),
        help='the version of Samba, either 3 or 4',
    )

    options = parser.parse_args()

    if ucr['server/role'] == 'domaincontroller_slave' and options.server_type == 'administrative' and not options.name_edu_server:
        parser.error('Please specify the name of the educational slave when installing an administrative slave (-E)!')

    if not options.ou:
        if ucr['server/role'] == 'domaincontroller_slave' or options.setup == 'singlemaster':
            parser.error('Please specify a school OU (-o)!')
        options.ou = ''

    return options


options = parse_args()
client = Client(options.host, options.username, options.password, language='en-US')

params = {
    'setup': options.setup,
    'username': options.username,
    'password': options.password,
    'master': options.master,
    'samba': options.samba,
    'schoolOU': options.ou,
}

if options.server_type:
    params['server_type'] = options.server_type
if options.name_edu_server:
    params['nameEduServer'] = options.name_edu_server

result = client.umc_command('schoolinstaller/install', params).result
if result and not result.get('success', True):  # backwards compatibility
    print('ERROR: Failed to run installer!')
    print('output: %s' % result)
    sys.exit(1)

print('=== INSTALLATION STARTED ===')
status = {'finished': False}  # type: Dict[str, Any]
failcount = 0
last_message = None
while not status['finished']:
    if failcount >= 1200:
        print('ERROR: %d failed attempts - committing suicide' % (failcount, ))
        sys.exit(1)
    try:
        status = client.umc_command('schoolinstaller/progress').result
        failcount = 0
    except (HTTPError, ConnectionError):
        failcount += 1
        print('TRACEBACK %d in client.umc_command("schoolinstaller/progress"):\n%s' % (failcount, traceback.format_exc()))
        time.sleep(1)
    message = '%(component)s - %(info)s' % status
    if last_message != message:
        last_message = message
        print(message)
    else:
        print('.', end=' ')

if len(status['errors']) > 0:
    print('ERROR: installation failed!')
    print('output: %s' % status)
    sys.exit(1)

result = client.umc_command('lib/server/restart').result
if not result:
    print('ERROR: Failed to restart UMC')
    print('output: %s' % result)
    sys.exit(1)

# https://forge.univention.org/bugzilla/show_bug.cgi?id=42305
print('UMC will be restarted on the system. Waiting for 20 seconds.')
time.sleep(20)

sys.exit(0)
