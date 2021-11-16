#!/bin/sh
set -e

test="$(dirname "$0")"
base="${test}/.."

export PATH="${base}/bin${PATH:+:$PATH}"
export LDBDIR="${LDBDIR:-${base}}"
export LDB_MODULES_PATH="${base}/bin/modules/ldb/"
export LDB_URL="${TEST_DATA_PREFIX:-.}/tdbtest.ldb"

rm -f "$LDB_URL"*

${VALGRIND:+$VALGRIND} ldbadd <<EOF
dn: @MODULES
@LIST: univention_samaccountname_ldap_check
EOF

testaccount=Administrator

${VALGRIND:+$VALGRIND} ldbadd --controls="bypass_samaccountname_ldap_check:0" --trace <<EOF
dn: dc=bar
dc: bar
sAMAccountName: $testaccount
EOF

${VALGRIND:+$VALGRIND} ldbsearch "(sAMAccountName=$testaccount)" | grep "sAMAccountName: $testaccount"

echo "SUCCESS"
