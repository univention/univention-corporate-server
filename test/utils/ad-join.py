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

from optparse import OptionParser
from sys import exit
from ldap.dn import escape_dn_chars

from univention.lib.umc import Client

from time import sleep
from univention.config_registry import ConfigRegistry
ucr = ConfigRegistry()
client = None

parser = OptionParser()
parser.add_option('-H', '--host', dest='host', default='localhost', help='host to connect to', metavar='HOST')
parser.add_option('-u', '--user', dest='username', help='username', metavar='UID', default='administrator')
parser.add_option('-p', '--password', dest='password', default='univention', help='password', metavar='PASSWORD')
parser.add_option('-D', '--domain_host', dest='domain_host', default=None, help='domain controller to connect to', metavar='DOMAIN_HOST')
parser.add_option('-A', '--domain_admin', dest='domain_admin', help='domain admin username', metavar='DOMAIN_UID', default='administrator')
parser.add_option('-P', '--domain_password', dest='domain_password', default='Univention@99', help='domain admin password', metavar='DOMAIN_PASSWORD')
parser.add_option('-S', '--sync_mode', dest='sync_mode', action="store_true", default=False, help='join in synchronization mode (instead of read by default)', metavar='SYNC_MODE')

(options, args) = parser.parse_args()

if not options.domain_host:
	parser.error('Please specify an AD DC host address!')


def join_sync_mode():
	""" Join in bi-directional sync mode via UMC requests """

	# check domain / get configuration:
	print '=== AD-JOIN STARTED ==='
	request_options = {
		"ad_server_address": options.domain_host,
		"username": options.domain_admin,
		"password": options.domain_password,
		"mode": "adconnector"
	}
	result = client.umc_command("adconnector/check_domain", request_options).result

	# configure / save options:
	print '=== AD-JOIN CONFIGURATION ==='
	try:
		kerberos_domain = result['Domain']
		ad_ldap_base = result['LDAP_Base']
		ad_dc_name = result['DC_DNS_Name']
	except KeyError as exc:
		print "\nAn Error while reading the AD Domain configuration: %r" % exc
		exit(1)

	request_options = {
		'Host_IP': options.domain_host,
		'KerberosDomain': kerberos_domain,
		'LDAP_Base': ad_ldap_base,
		'LDAP_BindDN': "cn=" + escape_dn_chars(options.domain_admin) + ",cn=users," + ad_ldap_base,
		'LDAP_Host': ad_dc_name,
		'LDAP_Password': options.domain_password,
		'MappingSyncMode': "sync"
	}

	conf_result = client.umc_command("adconnector/adconnector/save", request_options).result
	if not conf_result['success']:
		print "\nThe AD Connector configuration was not saved successfully: %s" % conf_result
		exit(1)

	# start AD connector:
	print '=== AD-JOIN STARTING CONNECTOR ==='
	start_result = client.umc_command("adconnector/service", {'action': "start"}).result
	if not start_result['success']:
		print "\nThe AD Connector was not started successfully: %s" % start_result
		exit(1)

	print '=== AD-JOIN FINISHED ==='


def join_read_mode():
	""" Join in read mode via UMC requests """

	send_data = {
		'ad_server_address': options.domain_host,
		'password': options.domain_password,
		'username': options.domain_admin
	}

	result = client.umc_command("adconnector/admember/join", send_data).result

	if not result:
		print 'ERROR: Failed to join ad domain!'
		exit(1)

	progress_id = result['id']
	progress_data = {'progress_id': progress_id}

	print '=== AD-JOIN STARTED ==='
	status = {'finished': False}
	while not status['finished']:
		# FIXME: this might loop forever?
		status = client.umc_command('adconnector/admember/progress', progress_data).result
		percentage = status['percentage']
		print percentage
		sleep(2)

	if not status['result']['success']:
		print status['result']['error']
		print '=== AD-JOIN FINISHED WITH ERROR ==='
		exit(1)

	print '=== AD-JOIN FINISHED ==='


def join_ad():
	""" Function for joining an AD domain, mimicking a join from umc"""

	global client
	client = Client(options.host, options.username, options.password, language='en-US')

	if options.sync_mode:
		# join in sync mode:
		print '=== AD-JOIN SYNC MODE SELECTED ==='
		join_sync_mode()
	else:
		# join in read mode:
		print '=== AD-JOIN READ MODE SELECTED ==='
		join_read_mode()


def check_correct_passwords():
	"""Check domain password saved for ucs-test and
	correct if needed"""

	print '=== Checking / Correcting ucs-test passwords ==='

	ucr.load()
	ucr_domain_pw = ucr['tests/domainadmin/pwd']
	if ucr_domain_pw != options.domain_password:
		ucr['tests/domainadmin/pwd'] = options.domain_password

	ucr.save()

	with open("/var/lib/ucs-test/pwdfile", "r") as pwfile:
		pwfile_pw = pwfile.read().replace('\n', '')
	if pwfile_pw != options.domain_password:
		with open("/var/lib/ucs-test/pwdfile", "w") as pwfile:
			pwfile.write(options.domain_password)


def check_correct_domain_admin():
	"""Check domain administrator saved for ucs-test and
	correct if needed"""

	print '=== Checking / Correcting ucs-test domain administrator ==='

	ucr.load()
	ucr_domain_admin = ucr['tests/domainadmin/account']
	if ucr_domain_admin:
		# FIXME: https://hutten.knut.univention.de/mediawiki/index.php/Sicherheits-Richtlinien#LDAP_DN.27s_Escapen
		ucr_domain_admin_parts = ucr_domain_admin.split(',')
		if ucr_domain_admin_parts[0].split('=')[1] != options.domain_admin:
			ucr_domain_admin_parts[0] = 'uid=%s' % options.domain_admin
			ucr['tests/domainadmin/account'] = ','.join(ucr_domain_admin_parts)
	else:
		print "=== tests/domainadmin/account is not set, trying to create it ==="
		ucr_domain_name = ucr['domainname']
		if ucr_domain_name:
			ucr_domain_parts = ucr_domain_name.split('.')
			ucr_domain_admin_parts = ['uid=%s' % options.domain_admin, 'cn=users']
			for part in ucr_domain_parts:
				ucr_domain_admin_parts.append('dc=%s' % part)
			ucr['tests/domainadmin/account'] = ','.join(ucr_domain_admin_parts)

	ucr.save()


join_ad()

# don't do that, why?
# tests/domainadmin/account and tests/domainadmin/pwd is the UCS account, why settings this to the windows account?
#check_correct_passwords()
#check_correct_domain_admin()

exit(0)
