#!/usr/bin/python3
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

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
parser.add_argument('-H', '--host', default='localhost', help='host to connect to')
parser.add_argument('-u', '--user', dest='username', help='username', metavar='UID', default='Administrator')
parser.add_argument('-p', '--password', default='univention', help='password')
parser.add_argument('-D', '--domain_host', default=None, help='domain controller to connect to', required=True)
parser.add_argument('-A', '--domain_admin', help='domain admin username', metavar='DOMAIN_UID', default='administrator')
parser.add_argument('-P', '--domain_password', default='Univention@99', help='domain admin password')

options = parser.parse_args()


def domainhost_unreachable(client: Client) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((client, 53))
        return False
    except OSError:
        return True


def get_progress(client: Client) -> None:
    while not finished:
        client.umc_command('adtakeover/progress')
        sleep(1)


def wait(client: Client) -> None:
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
        if result.get('finished', False):
            break
    else:
        raise Exception("wait timeout")
    print(result)
    assert not result['errors']


client = Client(options.host, options.username, options.password, language='en-US')
request_options = {
    "ip": options.domain_host,
    "username": options.domain_admin,
    "password": options.domain_password,
}

print('starting connect')
response = client.umc_command("adtakeover/connect", request_options)
print(response.result)
assert response.status == 200

try:
    print('starting copy')
    response = client.umc_command("adtakeover/run/copy", request_options)
except Exception:
    pass
wait(client)

print('starting rpc copy')
result = subprocess.call(["net", "-U", "%s%%%s" % (options.domain_admin, options.domain_password), "rpc", "share", "migrate", "files", "sysvol", "-S", options.domain_host, "--destination=%s" % (options.host), "--acls", "-vvvv"])
assert result == 0

print('starting sysvol check')
response = client.umc_command("adtakeover/check/sysvol", request_options)
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
    response = client.umc_command("adtakeover/run/takeover", request_options)
    print(response.status)
    assert response.status == 200

    print('starting done')
    response = client.umc_command("adtakeover/status/done", request_options)
    print(response.status)
    assert response.status == 200

    print('OK - finished')
    sys.exit(0)
except Exception:
    print(traceback.format_exc())

# wait until finished
for _i in range(90):
    sleep(10)
    response = client.umc_command("adtakeover/check/status", request_options)
    print(f'waiting got finished - {response.data}')
    if response.result == 'finished':
        print('OK - finished')
        sys.exit(0)

print(f"FAIL - not finished - {response.data}")
sys.exit(1)
