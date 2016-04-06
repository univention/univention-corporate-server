#!/bin/sh

if [ -n "$TEST_DATA_PREFIX" ]; then
	LDB_URL="$TEST_DATA_PREFIX/tdbtest.ldb"
else
	LDB_URL="tdbtest.ldb"
fi
export LDB_URL

PATH=bin:$PATH
export PATH

rm -f $LDB_URL*

if [ -z "$LDBDIR" ]; then
    LDBDIR=`dirname $0`/..
    export LDBDIR
fi

LDB_MODULES_PATH=$(pwd)/bin/modules/ldb/
export LDB_MODULES_PATH

cat <<EOF | $VALGRIND ldbadd || exit 1
dn: @MODULES
@LIST: univention_samaccountname_ldap_check
EOF

testaccount=Administrator

cat <<EOF | $VALGRIND ldbadd --controls="bypass_samaccountname_ldap_check:0" --trace || exit 1
dn: dc=bar
dc: bar
sAMAccountName: $testaccount
EOF

$VALGRIND ldbsearch "(sAMAccountName=$testaccount)" | grep "sAMAccountName: $testaccount" || exit 1

