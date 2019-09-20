#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Upgrade script for samba domain password setting attributes
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


def _get_s4_object(dn):
	''' Search for a Samba 4 object and put it into one dictonary '''
	result = {}

	p1 = subprocess.Popen(['ldbsearch -H /var/lib/samba/private/sam.ldb -b "%s" -s base | ldapsearch-wrapper' % dn], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	(stdout, stderr) = p1.communicate()

	if p1.returncode == 0:
		for line in stdout.split('\n'):
			line = line.strip()
			if not line or line.startswith('#'):
				continue
			key = line.split(':')[0]
			value = line[len(key) + 2:]
			if result.get(key):
				result[key].append(value)
			else:
				result[key] = [value]
	return result


def write_to_s4(configRegistry, mod_str):
	''' Write the mod_str to Samba LDAP '''
	s4_ldap_base = configRegistry.get('connector/s4/ldap/base').lower()
	ucs_ldap_base = configRegistry.get('ldap/base').lower()
	p1 = subprocess.Popen(['ldbmodify', '-H', '/var/lib/samba/private/sam.ldb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=False)
	(stdout, stderr) = p1.communicate(mod_str)
	if p1.returncode != 0:
		print 'Failed to write to Samba 4: %s' % (mod_str)
	else:
		print 'Synchronization of password setting attributes from UCS to Samba 4 was successful.'


def search_ucs_sambadomain_object(configRegistry, lo, SID):
	''' Search all UCS samba domain object
	'''

	ldap_result = lo.search(filter='sambaSID=%s' % SID)
	if len(ldap_result) == 1:
		return ldap_result[0]
	elif len(ldap_result) > 0:
		print 'ERROR: Found more than one sambaDomain object with sambaSID %s' % SID
	else:
		print 'ERROR: Did not find a sambaDomain object with sambaSID %s' % SID

# Time interval in S4 / AD is often 100-nanosecond intervals:
# http://msdn.microsoft.com/en-us/library/windows/desktop/ms676863%28v=vs.85%29.aspx


def _s2nano(seconds):
	return seconds * 10000000


def _nano2s(nanoseconds):
	return nanoseconds / 10000000


if __name__ == '__main__':

	parser = OptionParser(usage='msgpo.py (--write2ucs|--write2samba4)')
	parser.add_option("--write2ucs", dest="write2ucs", action="store_true", help="Write Samba password settings from Samba 4 to UCS", default=False)
	parser.add_option("--write2samba4", dest="write2samba4", action="store_true", help="Write Samba password settings from UCS to Samba 4", default=False)
	parser.add_option("--binddn", dest="binddn", action="store", help="Binddn for UCS LDAP connection")
	parser.add_option("--bindpwd", dest="bindpwd", action="store", help="Password for UCS LDAP connection")
	parser.add_option("--bindpwdfile", dest="bindpwdfile", action="store", help="Password file for UCS LDAP connection")
	(options, args) = parser.parse_args()
	if options.bindpwdfile:
		with open(options.bindpwdfile) as f:
			options.bindpwd = f.readline().strip()

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	lo = _connect_ucs(configRegistry, options.binddn, options.bindpwd)

	if options.write2ucs:
		s4_object = _get_s4_object(configRegistry.get('samba4/ldap/base'))
		ucs_object_dn, ucs_object_attr = search_ucs_sambadomain_object(configRegistry, lo, s4_object.get('objectSid')[0])
		ml = []
		sync_times = [('sambaMaxPwdAge', 'maxPwdAge'), ('sambaMinPwdAge', 'minPwdAge'), ('sambaLockoutDuration', 'lockoutDuration')]
		for (ucs_attr, s4_attr) in sync_times:
			s4_time = _nano2s(long(s4_object.get(s4_attr, [0])[0]) * -1)
			ml.append((ucs_attr, ucs_object_attr.get(ucs_attr), [str(s4_time)]))
		sync_integers = [('sambaPwdHistoryLength', 'pwdHistoryLength'), ('sambaMinPwdLength', 'minPwdLength')]
		for (ucs_attr, s4_attr) in sync_integers:
			ml.append((ucs_attr, ucs_object_attr.get(ucs_attr), s4_object.get(s4_attr, [0])))
		lo.modify(ucs_object_dn, ml)
	elif options.write2samba4:
		s4_object = _get_s4_object(configRegistry.get('samba4/ldap/base'))
		ucs_object = search_ucs_sambadomain_object(configRegistry, lo, s4_object.get('objectSid')[0])

		# Convert UCS attributes to Samba 4 values
		mod_str = 'dn: %s\nchangetype: modify\n' % configRegistry.get('samba4/ldap/base')
		sync_times = [('sambaMaxPwdAge', 'maxPwdAge'), ('sambaMinPwdAge', 'minPwdAge'), ('sambaLockoutDuration', 'lockoutDuration')]
		for (ucs_attr, s4_attr) in sync_times:
			ucs_value = long(ucs_object[1].get(ucs_attr, [0])[0])
			new_value = str(_s2nano(ucs_value) * -1)
			mod_str += 'replace: %s\n%s: %s\n' % (s4_attr, s4_attr, new_value)
		sync_integers = [('sambaPwdHistoryLength', 'pwdHistoryLength'), ('sambaMinPwdLength', 'minPwdLength')]
		for (ucs_attr, s4_attr) in sync_integers:
			mod_str += 'replace: %s\n%s: %s\n' % (s4_attr, s4_attr, ucs_object[1].get(ucs_attr, [0])[0])
		mod_str += '\n'
		write_to_s4(configRegistry, mod_str)

	else:
		parser.print_help()
		sys.exit(1)

	sys.exit(0)
