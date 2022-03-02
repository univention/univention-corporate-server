#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  Upgrade script for gPLink
#
# Copyright 2012-2022 Univention GmbH
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
import sys
import ldap
from argparse import ArgumentParser
import univention.config_registry
import univention.admin.uldap
import univention.admin.uexceptions
import univention.s4connector.s4


def _connect_ucs(configRegistry, binddn, bindpwdfile):
	''' Connect to OpenLDAP '''

	if not (binddn or bindpwdfile):
		bindpwdfile = configRegistry.get('connector/ldap/bindpw', '/etc/ldap.secret')
		binddn = configRegistry.get('connector/ldap/binddn', 'cn=admin,' + configRegistry['ldap/base'])

	bindpw = open(bindpwdfile).read().strip()

	host = configRegistry.get('connector/ldap/server', configRegistry.get('ldap/master'))

	try:
		port = int(configRegistry.get('connector/ldap/port', configRegistry.get('ldap/master/port', 7389)))
	except ValueError:
		port = 7389

	try:
		lo = univention.admin.uldap.access(host=host, port=port, base=configRegistry['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=2, follow_referral=True)
	except univention.admin.uexceptions.authFail:
		print('Authentication failed')
		exit(1)

	return lo


def search_s4(s4):
	''' Search all S4 objects with gPLink attribute and return a
			dictonary with dn as key and gPLink as result. The gPLink
			will only be set on containers, OUs and DCs, therefore
			is a mapping not necessary.
	'''

	return dict((x[0], x[1]['gPLink'][0]) for x in s4.lo_s4.search('gPLink=*', attr=['gPLink']) if x[0] is not None)


def search_ucs(s4):
	''' Search all UCS objects with msGPOLink attribute and return a
			dictonary with dn as key and msGPOLink as result
	'''

	return dict((x[0], x[1]['msGPOLink'][0]) for x in s4.lo.search('msGPOLink=*', attr=['msGPOLink']))


def write_to_s4(lo_s4, configRegistry, ucs_result):
	''' Write the result from search_ucs to Samba LDAP '''
	s4_ldap_base = configRegistry.get('connector/s4/ldap/base').lower()
	ucs_ldap_base = configRegistry.get('ldap/base').lower()
	for ucs_dn in ucs_result.keys():
		s4_dn = ucs_dn.lower().replace(ucs_ldap_base, s4_ldap_base)

		ml = [('gPLink', [b'OLD'], ucs_result[ucs_dn])]
		try:
			lo_s4.modify(s4_dn, ml)
		except (ldap.LDAPError, univention.admin.uexceptions.base) as exc:
			print('Failed to set gPLink for Samba 4 object (%s): %s' % (s4_dn, exc))
		else:
			print('Set gPLink for Samba 4 object (%s)' % (s4_dn))


def write_to_ucs(lo, configRegistry, s4_result, only_override_empty=False, binddn=None, bindpwdfile=None):
	''' Write the result from search_s4 to UCS LDAP '''

	lo = _connect_ucs(configRegistry, binddn, bindpwdfile)

	s4_ldap_base = configRegistry.get('connector/s4/ldap/base').lower()
	ucs_ldap_base = configRegistry.get('ldap/base').lower()
	for s4_dn in s4_result.keys():
		ucs_dn = s4_dn.lower().replace(s4_ldap_base, ucs_ldap_base)
		ml = []
		try:
			for dn, attributes in lo.search(base=ucs_dn, scope=ldap.SCOPE_BASE):
				if only_override_empty and attributes.get('msGPOLink'):
					continue
				if b'msGPO' not in attributes.get('objectClass'):
					ml.append(('objectClass', attributes.get('objectClass'), attributes.get('objectClass') + [b'msGPO']))
				ml.append(('msGPOLink', attributes.get('msGPOLink'), s4_result[s4_dn]))
			if ml:
				lo.modify(ucs_dn, ml)
				print('Set msGPOLink for UCS object (%s)' % (ucs_dn))
		except univention.admin.uexceptions.noObject:
			pass
		except univention.admin.uexceptions.permissionDenied:
			print('Permission denied for object %s. Please specify a binddn and a bindpwdfile of a Domain Administrator' % (ucs_dn,))
		except Exception as e:
			print('Failed to set msGPOLink for UCS object %s. Error message was (%s)' % (ucs_dn, e))


if __name__ == '__main__':
	parser = ArgumentParser(usage='msgpo.py (--write2ucs|--write2samba4)')
	parser.add_argument("--write2ucs", action="store_true", help="Write MS GPO settings from Samba 4 to UCS", default=False)
	parser.add_argument("--write2samba4", action="store_true", help="Write MS GPO settings from UCS to Samba 4", default=False)
	parser.add_argument("--only-override-empty", action="store_true", help="The parameter controls that the attribute is only overwritten in case it is empty. This can only be used in write2ucs mode.", default=False)
	parser.add_argument("--binddn", help="Binddn for UCS LDAP connection")
	parser.add_argument("--bindpwdfile", help="Password file for UCS LDAP connection")
	options = parser.parse_args()

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	s4 = univention.s4connector.s4.s4.main()
	s4.init_ldap_connections()

	if options.write2ucs:
		write_to_ucs(s4.lo, configRegistry, search_s4(s4), options.only_override_empty, options.binddn, options.bindpwdfile)
	elif options.write2samba4:
		write_to_s4(s4.lo_s4, configRegistry, search_ucs(s4))
	else:
		parser.print_help()
		sys.exit(1)

	sys.exit(0)
