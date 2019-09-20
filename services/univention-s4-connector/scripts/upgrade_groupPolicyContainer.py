#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Added groupPolicyContainer objects to rejected table
#
# Copyright 2012-2019 Univention GmbH
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
import univention.config_registry


def search_s4(filter, attribute):
	''' Search all S4 objects with objectClass=groupPolicyContainer
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


if __name__ == '__main__':

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	# Add CN=System to the reject list
	result = search_s4('-s base -b CN=System,%s' % configRegistry.get('connector/s4/ldap/base'), 'uSNChanged')
	add_to_sqlite(result)

	# Add CN=Policies,CN=System to the reject list
	result = search_s4('-s base -b CN=Policies,CN=System,%s' % configRegistry.get('connector/s4/ldap/base'), 'uSNChanged')
	add_to_sqlite(result)

	# Add all GPO containers to the reject list
	result = search_s4('objectClass=groupPolicyContainer', 'uSNChanged')
	add_to_sqlite(result)

	sys.exit(0)
