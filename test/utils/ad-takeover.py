#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2015-2017 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.
import subprocess
import threading
import socket
from optparse import OptionParser
from sys import exit
from ldap.dn import escape_dn_chars

from univention.lib.umc import Client

from time import sleep
from univention.config_registry import ConfigRegistry
ucr = ConfigRegistry()
client = None
finished = False

parser = OptionParser()
parser.add_option('-H', '--host', dest='host', default='localhost', help='host to connect to', metavar='HOST')
parser.add_option('-u', '--user', dest='username', help='username', metavar='UID', default='administrator')
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


client = Client(options.host, options.username, options.password, language='en-US')
request_options = {
	"ip": options.domain_host,
	"username": options.domain_admin,
	"password": options.domain_password
}

response = client.umc_command("adtakeover/connect", request_options)
print response.result
assert response.status==200

thread = threading.Thread(target=get_progress, args=(client,))
thread.start()

response = client.umc_command("adtakeover/run/copy", request_options)
assert response.status==200

#net -U Administrator%Univention.98  rpc share migrate files sysvol \
#   -S 10.200.7.132 --destination=10.200.7.150 --acls -vvvv
result = subprocess.call(["net", "-U", "%s%%%s" % (options.domain_admin, options.domain_password), "rpc", "share", "migrate", "files", "sysvol", "-S", options.domain_host, "--destination=%s" % (options.host), "--acls", "-vvvv"])
print result
assert result==0

response = client.umc_command("adtakeover/check/sysvol", request_options)
assert response.status==200


result = subprocess.call(["net", "rpc", "shutdown", "-I", options.domain_host, "-U", "%s%%%s" % (options.domain_admin, options.domain_password),])

finished = True

while not domainhost_unreachable(options.domain_host):
   # print "check if old domain is offline"
    sleep(2)

#waiting one last time to ensure winpc is off
sleep(5)

response = client.umc_command("adtakeover/run/takeover", request_options)
print response.status

#command = 'adtakeover/connect
#command = 'adtakeover/run/copy'
#command = 'adtakeover/check/sysvol'
#command = 'adtakeover/run/takeover'; 				}
# <command name="adtakeover/progress" function="poll" /> 		
# <command name="adtakeover/check/status" function="check_status" /
# <command name="adtakeover/status/done" function="set_status_done" /> 		
# <command name="adtakeover/connect" function="connect" /> 		
# <command name="adtakeover/run/copy" function="copy_domain_data" /> 		
# <command name="adtakeover/sysvol_info" function="sysvol_info" /> 		
# <command name="adtakeover/check/sysvol" function="check_sysvol" /> 		
# <command name="adtakeover/run/takeover" function="take_over_domain" />
