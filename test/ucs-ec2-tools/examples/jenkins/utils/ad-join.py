#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2013 Univention GmbH
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

from optparse import OptionParser
import sys

try:
	# with 3.1
	from univention.management.console.modules.appcenter.util import UMCConnection
except ImportError:
	# with 3.2
	from univention.lib.umc_connection import UMCConnection

from time import sleep
from univention.config_registry import ConfigRegistry
ucr = ConfigRegistry()
ucr.load()

parser = OptionParser()
parser.add_option('-H', '--host', dest='host', default='localhost',
	help='host to connect to', metavar='HOST')
parser.add_option('-u', '--user', dest='username',
	help='username', metavar='UID', default='administrator')
parser.add_option('-p', '--password', dest='password', default='univention',
	help='password', metavar='PASSWORD')
parser.add_option('-D', '--domain_host', dest='domain_host', default=None,
	help='domain controller to connect to', metavar='DOMAIN_HOST')
parser.add_option('-A', '--domain_admin', dest='domain_admin',
	help='domain admin username', metavar='DOMAIN_UID', default='administrator')
parser.add_option('-P', '--domain_password', dest='domain_password', default='Univention@99',
	help='domain admin password', metavar='DOMAIN_PASSWORD')

(options, args) = parser.parse_args()

if not options.domain_host:
	parser.error('Please specify a domain controller host address!')


def join_ad():
	connection = UMCConnection(options.host)
	connection.auth(options.username, options.password)

	send_data = {
		'ad_server_address': options.domain_host,
		'password': options.domain_password,
		'username': options.domain_admin
		}

	result = connection.request("adconnector/admember/join", data=send_data)

	if not result:
		print 'ERROR: Failed to join ad domain!'
		print 'output: %s' % result
		sys.exit(1)

	progress_id = result['id']
	progress_data = {
			'progress_id':progress_id
			}

	print '=== AD-JOIN STARTED ==='
	status = {'finished': False}
	while not status['finished']:
		status = connection.request('adconnector/admember/progress', data=progress_data)
		percentage = status['percentage']
		print percentage
		sleep(2)

	if not status['result']['success']:
		print status['result']['error']
		print '=== AD-JOIN FINISHED WITH ERROR ==='
		sys.exit(1)

	print '=== AD-JOIN FINISHED ==='


def correct_passwords():
	"""Check domain password and admin name saved for ucs-test and
	correct them if needed"""

	print '=== Correcting ucs-test passwords ==='

	ucr_domainadmin = ucr['tests/domainadmin/account']
	ucr_domainadminparts = ucr_domainadmin.split(',')
	if ucr_domainadminparts[0].split('=')[1] != options.domain_admin:
		ucr_domainadminparts[0] = 'uid=%s' % options.domain_admin
		ucr['tests/domainadmin/account'] = ','.join(ucr_domainadminparts)


	ucr_domain_pw = ucr['tests/domainadmin/pwd']
	if  ucr_domain_pw != options.domain_password:
		ucr['tests/domainadmin/pwd']=options.domain_password

	ucr.save()

	with open ("/var/lib/ucs-test/pwdfile", "r") as pwfile:
		pwfile_pw = pwfile.read().replace('\n', '')
	if pwfile_pw != options.domain_password:
		with open ("/var/lib/ucs-test/pwdfile", "w") as pwfile:
			pwfile.write(options.domain_password)



join_ad()
correct_passwords()

sys.exit(0)
