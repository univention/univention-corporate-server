#!/usr/bin/python2.6
import samba
from base64 import b64encode
from samba.samdb import SamDB
from samba.auth import system_session
from samba.param import LoadParm
from samba.provision import (
	secretsdb_setup_dns,
	ProvisionPaths,
	ProvisionNames,
	setup_add_ldif,
	setup_ldb,
	setup_path,
)

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
			dn = msg[0].dn
			samdb.delete(dn)
		except Exception:
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

		setup_add_ldif(samdb, setup_path("provision_dns_add_samba.ldif"), {
			"DNSDOMAIN": names.dnsdomain,
			"DOMAINDN": names.domaindn,
			"DNSPASS_B64": b64encode(dnspass.encode('utf-16-le')),
			"HOSTNAME" : names.hostname,
			"DNSNAME" : '%s.%s' % (
				names.netbiosname.lower(), names.dnsdomain.lower())
			})

