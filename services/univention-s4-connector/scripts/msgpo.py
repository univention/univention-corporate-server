#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Upgrade script for gPLink
#
# Copyright 2012-2020 Univention GmbH
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

from __future__ import print_function
import subprocess
import sys
import ldap
from argparse import ArgumentParser
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
		port = int(configRegistry.get('connector/ldap/port', configRegistry.get('ldap/master/port', 7389)))
	except ValueError:
		port = 7389

	lo = univention.admin.uldap.access(host=host, port=port, base=configRegistry['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=2, follow_referral=True)

	return lo


def search_s4():
	''' Search all S4 objects with gPLink attribute and return a
			dictonary with dn as key and gPLink as result. The gPLink
			will only be set on containers, OUs and DCs, therefore
			is a mapping not necessary.
	'''

	p1 = subprocess.Popen(['ldbsearch -H /var/lib/samba/private/sam.ldb gPLink=* dn gPLink | ldapsearch-wrapper'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	(stdout, stderr) = p1.communicate()

	if p1.returncode != 0:
		print(stderr.decode('UTF-8', 'replace'))
		sys.exit(p1.returncode)

	result = {}
	dn = None

	for line in stdout.decode('UTF-8').split('\n'):
		line = line.strip()
		if line.startswith('dn: '):
			dn = line[4:]
		if line.startswith('gPLink: '):
			gPLink = line[len('gPLink: '):]
			result[dn] = gPLink
			dn = None

	return result


def write_to_s4(configRegistry, ucs_result):
	''' Write the result from search_ucs to Samba LDAP '''
	s4_ldap_base = configRegistry.get('connector/s4/ldap/base').lower()
	ucs_ldap_base = configRegistry.get('ldap/base').lower()
	for ucs_dn in ucs_result.keys():
		s4_dn = ucs_dn.lower().replace(ucs_ldap_base, s4_ldap_base)

		if True:
			mod_str = 'dn: %s\nchangetype: modify\n' % s4_dn
			mod_str += 'replace: gPLink\ngPLink: %s\n' % ucs_result[ucs_dn]
			mod_str += '\n'
			p1 = subprocess.Popen(['ldbmodify', '-H', '/var/lib/samba/private/sam.ldb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=False)
			(stdout, stderr) = p1.communicate(mod_str)
			if p1.returncode != 0:
				print('Failed to set gPLink for Samba 4 object (%s)' % (s4_dn))
			else:
				print('Set gPLink for Samba 4 object (%s)' % (s4_dn))


def search_ucs(configRegistry, binddn, bindpwd):
	''' Search all UCS objects with msGPOLink attribute and return a
			dictonary with dn as key and msGPOLink as result
	'''

	lo = _connect_ucs(configRegistry, binddn, bindpwd)

	result = {}
	ldap_result = lo.search('(msGPOLink=*)')
	for dn, attributes in ldap_result:
		result[dn] = attributes.get('msGPOLink', [])[0]

	return result


def write_to_ucs(configRegistry, s4_result, binddn, bindpwd, only_override_empty=False):
	''' Write the result from search_s4 to UCS LDAP '''

	lo = _connect_ucs(configRegistry, binddn, bindpwd)

	s4_ldap_base = configRegistry.get('connector/s4/ldap/base').lower()
	ucs_ldap_base = configRegistry.get('ldap/base').lower()
	for s4_dn in s4_result.keys():
		ucs_dn = s4_dn.lower().replace(s4_ldap_base, ucs_ldap_base)
		ml = []
		try:
			for dn, attributes in lo.search(base=ucs_dn, scope=ldap.SCOPE_BASE):
				if only_override_empty and attributes.get('msGPOLink'):
					continue
				if 'msGPO' not in attributes.get('objectClass'):
					ml.append(('objectClass', attributes.get('objectClass'), attributes.get('objectClass') + ['msGPO']))
				ml.append(('msGPOLink', attributes.get('msGPOLink'), s4_result[s4_dn]))
			if ml:
				print('Set msGPOLink for UCS object (%s)' % (ucs_dn))
				lo.modify(ucs_dn, ml)
		except univention.admin.uexceptions.noObject:
			pass
		except Exception:
			print('Failed to set msGPOLink for UCS object (%s)' % (ucs_dn))


if __name__ == '__main__':
	parser = ArgumentParser(usage='msgpo.py (--write2ucs|--write2samba4)')
	parser.add_argument("--write2ucs", action="store_true", help="Write MS GPO settings from Samba 4 to UCS", default=False)
	parser.add_argument("--write2samba4", action="store_true", help="Write MS GPO settings from UCS to Samba 4", default=False)
	parser.add_argument("--only-override-empty", action="store_true", help="The parameter controls that the attribute is only overwritten in case it is empty. This can only be used in write2ucs mode.", default=False)
	parser.add_argument("--binddn", help="Binddn for UCS LDAP connection")
	parser.add_argument("--bindpwd", help="Password for UCS LDAP connection")
	parser.add_argument("--bindpwdfile", help="Password file for UCS LDAP connection")
	options = parser.parse_args()
	if options.bindpwdfile:
		with open(options.bindpwdfile) as fd:
			options.bindpwd = fd.readline().strip()

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	if options.write2ucs:
		result = search_s4()
		write_to_ucs(configRegistry, result, options.binddn, options.bindpwd, options.only_override_empty)
	elif options.write2samba4:
		result = search_ucs(configRegistry, options.binddn, options.bindpwd)
		write_to_s4(configRegistry, result)
	else:
		parser.print_help()
		sys.exit(1)

	sys.exit(0)
