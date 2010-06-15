<?php

@%@BCWARNING=// @%@

@!@
if baseConfig.has_key("horde/hosteddomain"):
	domains = baseConfig["horde/hosteddomain"]
elif baseConfig.has_key("mail/hosteddomains"):
	domains = baseConfig["mail/hosteddomains"]
else:
	domains=baseConfig['domainname']

if domains.find( ' ' ) != -1:
	d = domains[ : domains.find( ' ' ) ]
else:
	d = domains

print "$conf['cookie']['domain'] = '%s.%s';" % (baseConfig['hostname'],d)
print "$conf['problems']['email'] = '%s';" % baseConfig['mail/alias/webmaster']
print "$conf['problems']['maildomain'] = '%s';" % d
print "$conf['kolab']['ldap']['basedn'] = '%s';" % baseConfig['ldap/base']
print "$conf['kolab']['imap']['server'] = '%s';" % baseConfig['horde/imapserver']
print "$conf['kolab']['imap']['maildomain'] = '%s';" % d
@!@
?>
