#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2022 Univention GmbH
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

# This script was adjusted from the Tests for ntacls manipulation
# Copyright (C) Matthieu Patou <mat@matws.net> 2009-2010
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from __future__ import print_function

import sys
import optparse

from ldap.filter import filter_format

from samba.samdb import SamDB
import ldb
import samba.getopt
from samba.auth import system_session
from univention import config_registry


parser = optparse.OptionParser("$prog [options] <host>")
sambaopts = samba.getopt.SambaOptions(parser)
parser.add_option_group(sambaopts)
parser.add_option_group(samba.getopt.VersionOptions(parser))
# use command line creds if available
credopts = samba.getopt.CredentialsOptions(parser)
parser.add_option_group(credopts)
parser.add_option("-H", "--url", dest="database_url")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
parser.add_option("--ignore-exists", action="store_true", dest="ignore_exists")
parser.add_option("--createsite", action="store_true", dest="createsite")
parser.add_option("--createsitelink", action="store_true", dest="createsitelink")
parser.add_option("--createsubnet", action="store_true", dest="createsubnet")
parser.add_option("--modifysubnet", action="store_true", dest="modifysubnet")
parser.add_option("--site", dest="site")
parser.add_option("--sitelink", dest="sitelink")
parser.add_option("--subnet", dest="subnet")
opts, args = parser.parse_args()

if not opts.database_url:
	print("Option -H or --url needed", file=sys.stderr)
	sys.exit(1)

if opts.createsitelink:
	if not opts.sitelink:
		print("Option --sitelink needed for sitelink creation", file=sys.stderr)
		sys.exit(1)

if opts.createsite:
	if not opts.site:
		print("Option --site needed for site creation", file=sys.stderr)
		sys.exit(1)

if opts.createsubnet or opts.modifysubnet:
	if not opts.subnet:
		print("Option --subnet needed for subnet creation", file=sys.stderr)
		sys.exit(1)
	if not opts.site:
		print("Option --site needed for subnet creation", file=sys.stderr)
		sys.exit(1)

if not (opts.createsitelink or opts.createsite or opts.createsubnet or opts.modifysubnet):
	parser.print_help()

lp = sambaopts.get_loadparm()
creds = credopts.get_credentials(lp)

configRegistry = config_registry.ConfigRegistry()
configRegistry.load()

samdb = SamDB(opts.database_url, credentials=creds, session_info=system_session(lp), lp=lp)

samba4_ldap_base = configRegistry.get('samba4/ldap/base')
ldif_dict = {
	'branchsite_name': opts.site,
	'sitelink': opts.sitelink,
	'branchsite_subnet': opts.subnet,
	'samba4_ldap_base': samba4_ldap_base
}

if opts.createsite:
	res = samdb.search("CN=Configuration,%s" % samba4_ldap_base, scope=ldb.SCOPE_SUBTREE, expression=filter_format("(&(objectClass=site)(cn=%s))", [opts.site]))
	if res:
		print("site %s already exists" % opts.site, file=sys.stderr)
		if not opts.ignore_exists:
			sys.exit(1)
		else:
			sys.exit(0)

	if opts.sitelink and not opts.createsitelink:
		res = samdb.search("CN=Configuration,%s" % samba4_ldap_base, scope=ldb.SCOPE_SUBTREE, expression=filter_format("(&(objectClass=siteLink)(cn=%s))", [opts.sitelink]))
		if not res:
			print("sitelink %s not found" % opts.sitelink, file=sys.stderr)
			sys.exit(1)

	site_add_ldif = '''
dn: CN=%(branchsite_name)s,CN=Sites,CN=Configuration,%(samba4_ldap_base)s
objectClass: site
cn: %(branchsite_name)s
showInAdvancedViewOnly: TRUE
name: %(branchsite_name)s
systemFlags: 1107296256
objectCategory: CN=Site,CN=Schema,CN=Configuration,%(samba4_ldap_base)s

dn: CN=NTDS Site Settings,CN=%(branchsite_name)s,CN=Sites,CN=Configuration,%(samba4_ldap_base)s
objectClass: nTDSSiteSettings
cn: NTDS Site Settings
showInAdvancedViewOnly: TRUE
name: NTDS Site Settings
objectCategory: CN=NTDS-Site-Settings,CN=Schema,CN=Configuration,%(samba4_ldap_base)s

dn: CN=Servers,CN=%(branchsite_name)s,CN=Sites,CN=Configuration,%(samba4_ldap_base)s
objectClass: serversContainer
cn: Servers
showInAdvancedViewOnly: TRUE
name: Servers
systemFlags: 33554432
objectCategory: CN=Servers-Container,CN=Schema,CN=Configuration,%(samba4_ldap_base)s
''' % ldif_dict

	samdb.add_ldif(site_add_ldif)
	print("created site %s" % opts.site)

	if opts.sitelink and not opts.createsitelink:
		# and add it to the sitelink
		sitelink_modify_ldif = '''
dn: CN=%(sitelink)s,CN=IP,CN=Inter-Site Transports,CN=Sites,CN=Configuration,%(samba4_ldap_base)s
changetype: modify
add: siteList
siteList: CN=%(branchsite_name)s,CN=Sites,CN=Configuration,%(samba4_ldap_base)s
''' % ldif_dict
		samdb.modify_ldif(sitelink_modify_ldif)
		print("added site %s to sitelink %s" % (opts.site, opts.sitelink))

elif opts.site:
	res = samdb.search("CN=Configuration,%s" % samba4_ldap_base, scope=ldb.SCOPE_SUBTREE, expression=filter_format("(&(objectClass=site)(cn=%s))", [opts.site]))
	if not res:
		print("site %s not found" % opts.site, file=sys.stderr)
		sys.exit(1)

if opts.createsitelink:
	res = samdb.search("CN=Configuration,%s" % samba4_ldap_base, scope=ldb.SCOPE_SUBTREE, expression=filter_format("(&(objectClass=siteLink)(cn=%s))", [opts.sitelink]))
	if res:
		print("sitelink %s already exists" % opts.sitelink, file=sys.stderr)
		if not opts.ignore_exists:
			sys.exit(1)

	sitelink_add_ldif = '''
dn: CN=%(sitelink)s,CN=IP,CN=Inter-Site Transports,CN=Sites,CN=Configuration,%(samba4_ldap_base)s
objectClass: siteLink
cn: %(sitelink)s
cost: 100
showInAdvancedViewOnly: TRUE
name: %(sitelink)s
systemFlags: 1073741824
objectCategory: CN=Site-Link,CN=Schema,CN=Configuration,%(samba4_ldap_base)s
replInterval: 180
siteList: CN=%(branchsite_name)s,CN=Sites,CN=Configuration,%(samba4_ldap_base)s
''' % ldif_dict

	samdb.add_ldif(sitelink_add_ldif)
	print("created sitelink %s" % opts.sitelink)

if opts.createsubnet:
	res = samdb.search("CN=Configuration,%s" % samba4_ldap_base, scope=ldb.SCOPE_SUBTREE, expression=filter_format("(&(objectClass=subnet)(cn=%s))", [opts.subnet]))
	if res:
		print("subnet %s already exists" % opts.subnet, file=sys.stderr)
		if not opts.ignore_exists:
			sys.exit(1)

	subnet_add_ldif = '''
dn: CN=%(branchsite_subnet)s,CN=Subnets,CN=Sites,CN=Configuration,%(samba4_ldap_base)s
objectClass: subnet
cn: %(branchsite_subnet)s
showInAdvancedViewOnly: TRUE
name: %(branchsite_subnet)s
systemFlags: 1073741824
siteObject: CN=%(branchsite_name)s,CN=Sites,CN=Configuration,%(samba4_ldap_base)s
objectCategory: CN=Subnet,CN=Schema,CN=Configuration,%(samba4_ldap_base)s
''' % ldif_dict

	samdb.add_ldif(subnet_add_ldif)
	print("created subnet %s for site %s" % (opts.subnet, opts.site))

elif opts.modifysubnet:
	res = samdb.search("CN=Configuration,%s" % samba4_ldap_base, scope=ldb.SCOPE_SUBTREE, expression=filter_format("(&(objectClass=subnet)(cn=%s))", [opts.subnet]))
	if not res:
		print("subnet %s not found" % opts.subnet, file=sys.stderr)
		sys.exit(1)

	res = samdb.search("CN=Configuration,%s" % samba4_ldap_base, scope=ldb.SCOPE_SUBTREE, expression=filter_format("(&(objectClass=site)(cn=%s))", [opts.site]))
	if not res:
		print("site %s not found" % opts.site, file=sys.stderr)
		sys.exit(1)

	site_dn = res[0]['dn']
	subnet_dn = "CN=$(branchsite_subnet)s,CN=Subnets,CN=Sites,CN=Configuration,%(samba4_ldap_base)s" % ldif_dict

	subnet_modify_ldif = '''
dn: %s
changetype: modify
replace: siteObject
siteObject: %s
''' % (subnet_dn, site_dn)

	samdb.modify_ldif(subnet_modify_ldif)
	print("associated subnet %s with site %s" % (opts.subnet, opts.site))
