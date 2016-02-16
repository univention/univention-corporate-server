#!/usr/share/ucs-test/runner bash
## desc: "Run samba self test"
## exposure: dangerous
## packages:
##  - ldb-tools
## bugs: [40558]

. "$TESTLIBPATH/base.sh" || exit 137

RETVAL=100
IGNORE="
^ldb.python.*
^samba.tests.source.*
^samba.tests.docs.*
^samba3.blackbox.dfree_quota
^samba3.blackbox.smbclient_s3.crypt
^samba3.blackbox.smbclient_s3.plain
^samba3.blackbox.smbclient_s3.sign
^samba3.local.nss
^samba3.rap.basic
^samba3.raw.acls
^samba3.raw.samba3closeerr
^samba3.raw.samba3hide
^samba3.raw.streams
^samba3.smb2.acls
^samba3.smb2.create
^samba3.smb2.delete-on-close-perms
^samba3.smb2.getinfo
^samba4.blackbox.dbcheck
^samba4.blackbox.demote-saveddb
^samba4.blackbox.samba_tool_demote
^samba4.blackbox.upgradeprovision.alpha13
^samba4.blackbox.upgradeprovision.current
^samba4.blackbox.upgradeprovision.release-4-0-0
^samba4.drs.delete_object.python
^samba4.drs.fsmo.python
^samba4.drs.replica_sync.python
^samba4.drs.repl_schema.python
^samba4.krb5.kdc
^samba.blackbox.wbinfo
^samba.tests.blackbox.samba_tool_drs
^samba.tests.kcc
^samba4.ntvfs.cifs.krb5.base.deny2
^samba3.raw.notify.tree
^samba4.dlz_bind9.update01
^samba3.smb2.notify.*
^samba3.smb2.oplock.*"


ucr set update/secure_apt='no' repository/online/sources='yes' repository/online/unmaintained='yes'

section "running smbtorture"
# univention-install -y samba-testsuite
# smbtorture //"$(hostname -f)"/sysvol -W $(ucr get windows/domain) --option="realm=$(hostname -d)" -UAdministrator%univention ALL

section "running build self tests"

# setup
univention-install -y build-essential dpkg-dev
cd /opt
apt-get -y source samba
cd samba-*
apt-get -y build-dep samba
sed -i 's/$(conf_args)/$(conf_args) --enable-selftest/' debian/rules
for i in $IGNORE; do
	echo $i >> selftest/skip
done
debian/rules override_dh_auto_configure

# tests
TDB_NO_FSYNC=1 make -j test FAIL_IMMEDIATELY=1 SOCKET_WRAPPER_KEEP_PCAP=1 TESTS="samba3.raw.composite" || fail_fast 110
TDB_NO_FSYNC=1 make -j test FAIL_IMMEDIATELY=1 SOCKET_WRAPPER_KEEP_PCAP=1 || fail_fast 110

exit 100
