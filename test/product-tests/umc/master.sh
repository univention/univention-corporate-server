#!/bin/bash

set -x
set -e

. product-tests/umc/lib.sh

# LDAP-Indizes
ucr set ldap/debug/level=257
/etc/init.d/slapd restart
tail -f /var/log/syslog | grep "not indexed" >> not_indexed.txt &

# make sure we have a large environment
[ "$(udm users/user list | grep ^DN | wc -l)" -gt 5000 ]
[ "$(udm groups/group list | grep ^DN | wc -l)" -gt 1000 ]
[ "$(udm shares/share list | grep ^DN | wc -l)" -gt 2000 ]
[ "$(udm shares/printer list | grep ^DN | wc -l)" -gt 1000 ]
[ "$(udm computers/memberserver list --filter 'service=Print' | grep ^DN | wc -l)" -gt 100 ]

# FIXME: UDM proucttests wants more than 10000 users, more than 3000 groups, one very large group

run_umc_tests

# LDAP-Indizes
cat not_indexed.txt
find -maxdepth 1 -name not_indexed.txt -empty | grep -q not_indexed.txt

exit 0
