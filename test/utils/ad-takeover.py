#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2015-2017 Univention GmbH
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

import subprocess
import socket
import univention.lib.umc

from optparse import OptionParser
from univention.lib.umc import Client
from time import sleep
from univention.config_registry import ConfigRegistry

ucr = ConfigRegistry()
client = None
finished = False

parser = OptionParser()
parser.add_option('-H', '--host', dest='host', default='localhost', help='host to connect to', metavar='HOST')
parser.add_option('-u', '--user', dest='username', help='username', metavar='UID', default='Administrator')
parser.add_option('-p', '--password', dest='password', default='univention', help='password', metavar='PASSWORD')
parser.add_option('-D', '--domain_host', dest='domain_host', default=None, help='domain controller to connect to', metavar='DOMAIN_HOST')
parser.add_option('-A', '--domain_admin', dest='domain_admin', help='domain admin username', metavar='DOMAIN_UID', default='administrator')
parser.add_option('-P', '--domain_password', dest='domain_password', default='Univention@99', help='domain admin password', metavar='DOMAIN_PASSWORD')

(options, args) = parser.parse_args()

if not options.domain_host:
	parser.error('Please specify an AD DC host address!')


def domainhost_unreachable(client):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(2)
	try:
		s.connect((client, 53))
		return False
	except socket.error:
		return True


def get_progress(client):
	while not finished:
		client.umc_command('adtakeover/progress')
		sleep(1)


def wait(client):
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
	"password": options.domain_password
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

sleep(5)

print('starting takeover')
response = client.umc_command("adtakeover/run/takeover", request_options)
print(response.status)
assert response.status == 200

print('starting done')
response = client.umc_command("adtakeover/status/done", request_options)
print(response.status)
assert response.status == 200
