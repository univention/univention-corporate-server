#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2013-2019 Univention GmbH
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

from univention.config_registry import ConfigRegistry
from univention.testing.strings import random_name, random_int
import ldap
import ldap.schema
import psutil
import subprocess
import time
import univention.uldap

WAIT_FOR_LDAP_TIME = 30  # seconds


def wait_for_ldap():
	print "\n** Waiting for slapd"
	for count in xrange(WAIT_FOR_LDAP_TIME):
		try:
			pinfo = [proc.name() for proc in psutil.process_iter() if proc.name() == 'slapd' and proc.ppid() == 1]
		except psutil.NoSuchProcess:
			pass
		else:
			if pinfo:
				print "(%s) process is running now.\n" % pinfo[0]
				break
			else:
				time.sleep(1)
				print count


def get_package_name():
	return random_name()


def get_schema_name():
	return random_name()


def get_acl_name():
	return '62%s' % random_name()


def get_container_name():
	return random_name()


def get_schema_attribute_id():
	return random_int() + random_int() + random_int() + random_int() + random_int()


def call_join_script(join_script_name):
	print 'call_join_script(%r)' % (join_script_name,)
	ucr = ConfigRegistry()
	ucr.load()

	join_script = '/usr/lib/univention-install/%s' % join_script_name

	return subprocess.call([join_script, '--binddn', ucr.get('tests/domainadmin/account'), '--bindpwdfile', ucr.get('tests/domainadmin/pwdfile')], shell=False)


def call_unjoin_script(unjoin_script_name):
	print 'call_unjoin_script(%r)' % (unjoin_script_name,)
	ucr = ConfigRegistry()
	ucr.load()

	join_script = '/usr/lib/univention-uninstall/%s' % unjoin_script_name

	return subprocess.call([join_script, '--binddn', ucr.get('tests/domainadmin/account'), '--bindpwdfile', ucr.get('tests/domainadmin/pwdfile')], shell=False)


def __fetch_schema_from_uri(ldap_uri):
	ucr = ConfigRegistry()
	ucr.load()

	retry = ucr.get('ldap/client/retry/count', 15)
	attempts = int(retry) + 1

	i = 0
	while i < attempts:
		try:
			return ldap.schema.subentry.urlfetch(ldap_uri)
		except ldap.SERVER_DOWN:
			if i >= (attempts - 1):
				raise
			time.sleep(1)
		i += 1


def fetch_schema_from_ldap_master():
	ucr = ConfigRegistry()
	ucr.load()

	ldap_uri = 'ldap://%(ldap/master)s:%(ldap/master/port)s' % ucr
	return __fetch_schema_from_uri(ldap_uri)


def fetch_schema_from_local_ldap():
	ucr = ConfigRegistry()
	ucr.load()

	ldap_uri = 'ldap://%(hostname)s:%(domainname)s' % ucr

	return __fetch_schema_from_uri(ldap_uri)


def get_ldap_master_connection(user_dn):
	ucr = ConfigRegistry()
	ucr.load()

	return univention.uldap.access(host=ucr.get('ldap/master'), port=int(ucr.get('ldap/master/port', '7389')), base=ucr.get('ldap/base'), binddn=user_dn, bindpw='univention')


def set_container_description(user_dn, container):
	print 'set_container_description(%r, %r)' % (user_dn, container)
	lo = get_ldap_master_connection(user_dn)
	lo.modify(container, [('description', '', random_name())])
