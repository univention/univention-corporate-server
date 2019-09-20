#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Upgrade script for msGPOWQLFilter attributes
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


def search_s4():
	''' Search all S4 objects with gPCWQLFilter attribute and return a
			dictonary with dn as key and gPCWQLFilter as result.
			The corresponding msGPOWQLFilter
			will only be set on groupPolicyContainer objects.
	'''

	p1 = subprocess.Popen(['ldbsearch -H /var/lib/samba/private/sam.ldb gPCWQLFilter=* dn gPCWQLFilter | ldapsearch-wrapper'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
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
		if line.startswith('gPCWQLFilter: '):
			gPCWQLFilter = line[len('gPCWQLFilter: '):]
			result[dn] = gPCWQLFilter
			dn = None

	return result


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
				result[key] = []
	return result


def write_to_s4(configRegistry, ucs_result):
	''' Write the result from search_ucs to Samba LDAP '''
	s4_ldap_base = configRegistry.get('connector/s4/ldap/base').lower()
	ucs_ldap_base = configRegistry.get('ldap/base').lower()
	for ucs_dn in ucs_result.keys():
		s4_dn = ucs_dn.lower().replace(ucs_ldap_base, s4_ldap_base)

		# This search is not necessary at the moment
		# s4_object = _get_s4_object(s4_dn)
		# if s4_object:

		if True:
			mod_str = 'dn: %s\nchangetype: modify\n' % s4_dn
			mod_str += 'replace: gPCWQLFilter\ngPCWQLFilter: %s\n' % ucs_result[ucs_dn]
			mod_str += '\n'
			p1 = subprocess.Popen(['ldbmodify', '-H', '/var/lib/samba/private/sam.ldb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=False)
			(stdout, stderr) = p1.communicate(mod_str)
			if p1.returncode != 0:
				print 'Failed to set gPCWQLFilter for Samba 4 object (%s)' % (s4_dn)
			else:
				print 'Set gPCWQLFilter for Samba 4 object (%s)' % (s4_dn)


def search_ucs(configRegistry, binddn, bindpwd):
	''' Search all UCS objects with msGPOWQLFilter attribute and return a
			dictonary with dn as key and msGPOWQLFilter as result
	'''

	lo = _connect_ucs(configRegistry, binddn, bindpwd)

	result = {}
	ldap_result = lo.search('(msGPOWQLFilter=*)')
	for dn, attributes in ldap_result:
		result[dn] = attributes.get('msGPOWQLFilter', [])[0]

	return result


def write_to_ucs(configRegistry, s4_result, binddn, bindpwd):
	''' Write the result from search_s4 to UCS LDAP '''

	lo = _connect_ucs(configRegistry, binddn, bindpwd)

	s4_ldap_base = configRegistry.get('connector/s4/ldap/base').lower()
	ucs_ldap_base = configRegistry.get('ldap/base').lower()
	for s4_dn in s4_result.keys():
		ucs_dn = s4_dn.lower().replace(s4_ldap_base, ucs_ldap_base)
		ml = []
		try:
			for dn, attributes in lo.search(base=ucs_dn, scope=ldap.SCOPE_BASE):
				ml.append(('msGPOWQLFilter', attributes.get('msGPOWQLFilter'), s4_result[s4_dn]))
			if ml:
				print 'Set msGPOWQLFilter for UCS object (%s)' % (ucs_dn)
				lo.modify(ucs_dn, ml)
		except univention.admin.uexceptions.noObject:
			pass
		except:
			print 'Failed to set msGPOWQLFilter for UCS object (%s)' % (ucs_dn)


if __name__ == '__main__':

	parser = OptionParser(usage='msGPOWQLFilter.py (--write2ucs|--write2samba4)')
	parser.add_option("--write2ucs", dest="write2ucs", action="store_true", help="Write WMI filter links from Samba 4 to UCS", default=False)
	parser.add_option("--write2samba4", dest="write2samba4", action="store_true", help="Write WMI filter links from UCS to Samba 4", default=False)
	parser.add_option("--binddn", dest="binddn", action="store", help="Binddn for UCS LDAP connection")
	parser.add_option("--bindpwd", dest="bindpwd", action="store", help="Password for UCS LDAP connection")
	parser.add_option("--bindpwdfile", dest="bindpwdfile", action="store", help="Password file for UCS LDAP connection")
	(options, args) = parser.parse_args()
	if options.bindpwdfile:
		with open(options.bindpwdfile) as f:
			options.bindpwd = f.readline().strip()

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	if options.write2ucs:
		result = search_s4()
		write_to_ucs(configRegistry, result, options.binddn, options.bindpwd)
	elif options.write2samba4:
		result = search_ucs(configRegistry, options.binddn, options.bindpwd)
		write_to_s4(configRegistry, result)
	else:
		parser.print_help()
		sys.exit(1)

	sys.exit(0)
