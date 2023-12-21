#!/usr/share/ucs-test/runner python3
## desc: Check ucs-sso A record on AD server
## tags: [admember]
## exposure: safe
## packages: [univention-samba]
## roles: [domaincontroller_master,domaincontroller_backup]
## bugs: [39574]

import sys

import dns.resolver

import univention.lib.admember
from univention.config_registry import ucr
from univention.config_registry.interfaces import Interfaces
from univention.testing.codes import Reason


if not univention.lib.admember.is_localhost_in_admember_mode():
    sys.exit(int(Reason.SKIP))

ad_domain_info = univention.lib.admember.lookup_adds_dc()
ad_ip = ad_domain_info['DC IP']
my_ip = Interfaces().get_default_ip_address().ip
domainname = ucr.get('domainname')
fqdn = ucr.get('ucs/server/sso/fqdn', 'ucs-sso.' + domainname)

resolver = dns.resolver.Resolver()
resolver.nameservers = [ad_ip]
resolver.lifetime = 10
response = resolver.query(fqdn, 'A')
ret_val = Reason.OKAY if any(str(data) == str(my_ip) for data in response) else Reason.FAIL
sys.exit(int(ret_val))
