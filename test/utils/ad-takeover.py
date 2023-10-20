#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2015-2023 Univention GmbH
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
import subprocess
import sys
import traceback
from argparse import ArgumentParser
from time import sleep

import univention.lib.umc
from univention.lib.umc import Client


client = None
finished = False

parser = ArgumentParser()
parser.add_argument('-H', '--host', default='localhost', help='host to connect to',)
parser.add_argument('-u', '--user', dest='username', help='username', metavar='UID', default='Administrator',)
parser.add_argument('-p', '--password', default='univention', help='password',)
parser.add_argument('-D', '--domain_host', default=None, help='domain controller to connect to', required=True,)
parser.add_argument('-A', '--domain_admin', help='domain admin username', metavar='DOMAIN_UID', default='administrator',)
parser.add_argument('-P', '--domain_password', default='Univention@99', help='domain admin password',)

options = parser.parse_args()


def domainhost_unreachable(client: Client,) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM,)
    s.settimeout(2)
    try:
        s.connect((client, 53))
        return False
    except socket.error:
        return True


def get_progress(client: Client,) -> None:
    while not finished:
        client.umc_command('adtakeover/progress')
        sleep(1)


def wait(client: Client,) -> None:
    path = 'adtakeover/progress'
    waited = 0
    result = None
    while waited <= 1800:
        sleep(10)
        waited += 1
        try:
            result = client.umc_command(path).result
        except univention.lib.umc.ConnectionError:
            print('... Apache down? Ignoring...')
            continue
        print(result)
        if result.get('finished', False,):
            break
    else:
        raise Exception("wait timeout")
    print(result)
    assert not result['errors']


client = Client(options.host, options.username, options.password, language='en-US',)
request_options = {
    "ip": options.domain_host,
    "username": options.domain_admin,
    "password": options.domain_password,
}

print('starting connect')
response = client.umc_command("adtakeover/connect", request_options,)
print(response.result)
assert response.status == 200

try:
    print('starting copy')
    response = client.umc_command("adtakeover/run/copy", request_options,)
except Exception:
    pass
wait(client)

print('starting rpc copy')
result = subprocess.call(["net", "-U", "%s%%%s" % (options.domain_admin, options.domain_password), "rpc", "share", "migrate", "files", "sysvol", "-S", options.domain_host, "--destination=%s" % (options.host), "--acls", "-vvvv"])
assert result == 0

print('starting sysvol check')
response = client.umc_command("adtakeover/check/sysvol", request_options,)
assert response.status == 200

print('starting shutdown')
result = subprocess.call(["net", "rpc", "shutdown", "-I", options.domain_host, "-U", "%s%%%s" % (options.domain_admin, options.domain_password)])
assert result == 0
finished = True

while not domainhost_unreachable(options.domain_host):
    sleep(2)

sleep(10)

# This works for "normal" ad-takeover, but if we ad-takeover from an
# ad-member mode there seems to be an issue with the umc connection
# .../run/takeover|.../status/done in this case fail (not sure why),
# so as a fallback adtakeover/check/status until finished or fail
try:
    print('starting takeover')
    response = client.umc_command("adtakeover/run/takeover", request_options,)
    print(response.status)
    assert response.status == 200

    print('starting done')
    response = client.umc_command("adtakeover/status/done", request_options,)
    print(response.status)
    assert response.status == 200

    print('OK - finished')
    sys.exit(0)
except Exception:
    print(traceback.format_exc())

# wait until finished
for _i in range(90):
    sleep(10)
    response = client.umc_command("adtakeover/check/status", request_options,)
    print(f'waiting got finished - {response.data}')
    if response.result == 'finished':
        print('OK - finished')
        sys.exit(0)

print(f"FAIL - not finished - {response.data}")
sys.exit(1)
