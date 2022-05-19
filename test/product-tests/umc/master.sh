#!/bin/bash

set -e -x

# shellcheck source=lib.sh
. product-tests/umc/lib.sh

# LDAP-Indizes
ucr set ldap/debug/level=257
/etc/init.d/slapd restart
tail -f /var/log/syslog | grep "not indexed" >> not_indexed.txt &
pid=$!

# make sure we have a large environment
[ "$(udm users/user list | grep -c ^DN)" -gt 5000 ]
[ "$(udm groups/group list | grep -c ^DN)" -gt 1000 ]
[ "$(udm shares/share list | grep -c ^DN)" -gt 2000 ]
[ "$(udm shares/printer list | grep -c ^DN)" -gt 1000 ]
[ "$(udm computers/memberserver list --filter 'service=Print' | grep -c ^DN)" -gt 100 ]

# FIXME: UDM proucttests wants more than 10000 users, more than 3000 groups, one very large group

run_umc_tests

# LDAP-Indizes
kill $pid
cat not_indexed.txt
[ ! -s not_indexed.txt ]

exit 0
