#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Trigger Synchronization of msWMI-Som objects
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

import sqlite3 as lite
import subprocess
import sys
import ldap
from optparse import OptionParser
import univention.config_registry
import univention.admin.uldap
import univention.admin.uexceptions


def _connect_ucs(configRegistry, binddn, bindpwd):
	''' Connect to OpenLDAP '''

	if binddn and bindpwd:
		bindpw = bindpwd
	else:
		bindpw_file = configRegistry.get('connector/ldap/bindpw', '/etc/ldap.secret')
		binddn = configRegistry.get('connector/ldap/binddn', 'cn=admin,' + configRegistry['ldap/base'])
		bindpw = open(bindpw_file).read()
		if bindpw[-1] == '\n':
			bindpw = bindpw[0:-1]

	host = configRegistry.get('connector/ldap/server', configRegistry.get('ldap/master'))

	try:
		port = int(configRegistry.get('connector/ldap/port', configRegistry.get('ldap/master/port')))
	except:
		port = 7389

	lo = univention.admin.uldap.access(host=host, port=port, base=configRegistry['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=2, follow_referral=True)

	return lo


def search_s4(filter, attribute):
	''' Search all S4 objects with objectClass=msWMI-Som
			and return a dictonary with dn as key and uSNChanged as result.
	'''

	p1 = subprocess.Popen(['ldbsearch -H /var/lib/samba/private/sam.ldb %s %s | ldapsearch-wrapper' % (filter, attribute)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	(stdout, stderr) = p1.communicate()

	if p1.returncode != 0:
		print stderr
		sys.exit(p1.returncode)

	result = {}
	dn = None

	for line in stdout.split('\n'):
		line = line.strip()
		if line.startswith('dn: '):
			dn = line[4:]
		if line.startswith('%s: ' % attribute):
			attr = line[len('%s: ' % attribute):]
			result[dn] = attr
			dn = None

	return result


def add_to_sqlite(result):
	dbcon = lite.connect('/etc/univention/connector/s4internal.sqlite')
	cur = dbcon.cursor()
	for dn in result.keys():
		print 'Add (%s) to the Samba 4 reject list.' % (dn)
		cur.execute("""
			INSERT OR REPLACE INTO '%(table)s' (key,value)
				VALUES (  '%(key)s', '%(value)s'
			);""" % {'key': result[dn], 'value': dn, 'table': 'S4 rejected'})
	dbcon.commit()
	cur.close()
	dbcon.close()


def trigger_ldap2sd(configRegistry, binddn, bindpwd):
	''' Touch all UCS objects with objectClass=msWMISom.
	'''

	lo = _connect_ucs(configRegistry, binddn, bindpwd)

	result = {}
	ldap_result = lo.search('(objectClass=msWMISom)')
	for dn, attributes in ldap_result:
		msWMIID = attributes.get('msWMIID', [])[0]
		ml = [(ldap.MOD_REPLACE, 'msWMIID', msWMIID)]
		try:
			print 'Touch UCS object %s' % (dn)
			lo.lo.modify_s(dn, ml)
		except ldap.NO_SUCH_OBJECT, ex:
			pass
		except ldap.LDAPError, ex:
			print 'Failure touching UCS object %s (%s)' % (dn, str(ex))


def trigger_sd2ldap(configRegistry):
	# Add CN=System to the reject list
	result = search_s4('-s base -b CN=System,%s' % configRegistry.get('connector/s4/ldap/base'), 'uSNChanged')
	add_to_sqlite(result)

	# Add CN=WMIPolicy,CN=System to the reject list
	result = search_s4('-s base -b CN=WMIPolicy,CN=System,%s' % configRegistry.get('connector/s4/ldap/base'), 'uSNChanged')
	add_to_sqlite(result)

	# Add CN=SOM,CN=WMIPolicy,CN=System to the reject list
	result = search_s4('-s base -b CN=SOM,CN=WMIPolicy,CN=System,%s' % configRegistry.get('connector/s4/ldap/base'), 'uSNChanged')
	add_to_sqlite(result)

	# Add all WMI filters to the reject list
	result = search_s4('objectClass=msWMI-Som', 'uSNChanged')
	add_to_sqlite(result)


if __name__ == '__main__':

	parser = OptionParser(usage='msGPOWQLFilter.py (--write2ucs|--write2samba4)')
	parser.add_option("--write2ucs", dest="write2ucs", action="store_true", help="Trigger synchronization of WMI filter objects from Samba 4 to UCS", default=False)
	parser.add_option("--write2samba4", dest="write2samba4", action="store_true", help="Trigger synchronization of WMI filter objects from UCS to Samba 4", default=False)
	parser.add_option("--binddn", dest="binddn", action="store", help="Binddn for UCS LDAP connection")
	parser.add_option("--bindpwd", dest="bindpwd", action="store", help="Password for UCS LDAP connection")
	(options, args) = parser.parse_args()

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	if options.write2ucs:
		trigger_sd2ldap(configRegistry)
	elif options.write2samba4:
		trigger_ldap2sd(configRegistry, options.binddn, options.bindpwd)
	else:
		parser.print_help()
		sys.exit(1)

	sys.exit(0)
