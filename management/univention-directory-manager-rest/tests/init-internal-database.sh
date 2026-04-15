#!/bin/bash

set -uo pipefail
mkdir -p /var/lib/univention-ldap/internal
echo "dn: cn=internal
objectClass: organizationalRole
" | slapadd -b cn=internal -f /etc/ldap/slapd.conf

echo "dn: cn=blocklists,cn=internal
cn: blocklists
objectClass: organizationalRole
objectClass: univentionObject
univentionObjectType: container/cn
" | slapadd -b cn=internal -f /etc/ldap/slapd.conf

exit 0
