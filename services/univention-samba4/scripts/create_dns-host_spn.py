#!/usr/bin/python2.6
#
# Copyright 2012 Univention GmbH
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Add SAM account for dns-$hostname to create dns.keytab"""

import samba
import time
import sys
from base64 import b64encode
from samba.samdb import SamDB
from samba.auth import system_session
from samba.param import LoadParm
from samba.provision import (
	ProvisionPaths,
	ProvisionNames,
)
from samba.provision.common import (
	setup_path,
	setup_add_ldif,
	setup_ldb
)
from samba.provision.sambadns import secretsdb_setup_dns

if __name__ == '__main__':
	## most of this is extracted from source4/scripting/python/samba/provision/*

	lp = LoadParm()
	lp.load('/etc/samba/smb.conf')

	samdb = SamDB('/var/lib/samba/private/sam.ldb', session_info=system_session(lp), lp=lp)
	secretsdb = samba.Ldb('/var/lib/samba/private/secrets.ldb', session_info=system_session(lp), lp=lp)

	paths = ProvisionPaths()
	paths.private_dir = lp.get("private dir")

	names = ProvisionNames()
	# NT domain, kerberos realm, root dn, domain dn, domain dns name
	names.realm = lp.get("realm").upper()
	names.domain = lp.get("workgroup").upper()
	names.domaindn = samdb.domain_dn()
	names.dnsdomain = samba.ldb.Dn(samdb, names.domaindn).canonical_str().replace("/", "")
	basedn = samba.dn_from_dns_name(names.dnsdomain)

	# Get the netbiosname first (could be obtained from smb.conf in theory)
	res = secretsdb.search(expression="(flatname=%s)" %
		names.domain,base="CN=Primary Domains",
		scope=samba.ldb.SCOPE_SUBTREE, attrs=["sAMAccountName"])
	names.netbiosname = str(res[0]["sAMAccountName"]).replace("$","")

	# dns hostname and server dn
	res4 = samdb.search(expression="(CN=%s)" % names.netbiosname,
		base="OU=Domain Controllers,%s" % basedn,
		scope=samba.ldb.SCOPE_ONELEVEL, attrs=["dNSHostName"])
	names.hostname = str(res4[0]["dNSHostName"]).replace("." + names.dnsdomain,"")
	names.hostname = names.hostname.lower()

	dnspass = samba.generate_random_password(128, 255)

	dns_keytab_path='dns.keytab'

	## most of this is extraced from source4/scripting/bin/samba_upgradedns
	# Check if dns-HOSTNAME account exists and create it if required
	try:
		dn = 'samAccountName=dns-%s,CN=Principals' % names.hostname
		msg = secretsdb.search(expression='(dn=%s)' % dn, attrs=['secret'])
		dnssecret = msg[0]['secret'][0]
	except Exception:
		print "Adding dns-%s account" % names.hostname
	
		try:
			msg = samdb.search(base=names.domaindn, scope=samba.ldb.SCOPE_DEFAULT,
				expression='(sAMAccountName=dns-%s)' % (names.hostname),
				attrs=['clearTextPassword'])
			if msg:
				print "removing sAMAccountName=dns-%s" % (names.hostname)
				dn = msg[0].dn
				samdb.delete(dn)
		except Exception:
			print "exception while removing sAMAccountName=dns-%s" % (names.hostname)
			pass

		setup_add_ldif(secretsdb, setup_path("secrets_dns.ldif"), {
			"REALM": names.realm,
			"DNSDOMAIN": names.dnsdomain,
			"DNS_KEYTAB": dns_keytab_path,
			"DNSPASS_B64": b64encode(dnspass),
			"HOSTNAME": names.hostname,
			"DNSNAME" : '%s.%s' % (
				names.netbiosname.lower(), names.dnsdomain.lower())
			})

		account_created = False
		count = 0
		while not account_created:
			try:
				setup_add_ldif(samdb, setup_path("provision_dns_add_samba.ldif"), {
					"DNSDOMAIN": names.dnsdomain,
					"DOMAINDN": names.domaindn,
					"DNSPASS_B64": b64encode(dnspass.encode('utf-16-le')),
					"HOSTNAME" : names.hostname,
					"DNSNAME" : '%s.%s' % (
						names.netbiosname.lower(), names.dnsdomain.lower())
					})
				account_created = True
			except:
				count += 1
				if count > 300:
					print 'ERROR: failed to create dns-$hostname'
					sys.exit(1)
				print "Waiting for RID pool"
				time.sleep(1)
