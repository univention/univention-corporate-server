#!/bin/bash

set -x
set -e

revert_to_samba47 () {
	set -x
	set -e
	/etc/init.d/univention-s4-connector stop
	ucr set dns/backend='ldap'
	/etc/init.d/bind9 restart
	/etc/init.d/samba stop
	OLD_PKG_VERSION_SAMBA='2:4.7.8-1A~4.3.0.201905081755'
	OLD_PKG_VERSION_LDB='2:1.2.3-1A~4.3.0.201801031047'
	OLD_PKG_VERSION_TDB='1.3.15-2A~4.3.0.201712121753'
	OLD_PKG_VERSION_TALLOC='2.1.11-1A~4.3.0.201802090138'
	OLD_PKG_VERSION_TEVENT='0.9.36-1A~4.3.0.201808081834'
	univention-install --allow-downgrades -y \
		libsmbclient="$OLD_PKG_VERSION_SAMBA" \
		libwbclient0="$OLD_PKG_VERSION_SAMBA" \
		python-samba="$OLD_PKG_VERSION_SAMBA" \
		samba="$OLD_PKG_VERSION_SAMBA" \
		samba-common="$OLD_PKG_VERSION_SAMBA" \
		samba-common-bin="$OLD_PKG_VERSION_SAMBA" \
		samba-dsdb-modules="$OLD_PKG_VERSION_SAMBA" \
		samba-libs="$OLD_PKG_VERSION_SAMBA" \
		samba-vfs-modules="$OLD_PKG_VERSION_SAMBA" \
		smbclient="$OLD_PKG_VERSION_SAMBA" \
		winbind="$OLD_PKG_VERSION_SAMBA" \
		ldb-tools="$OLD_PKG_VERSION_LDB" \
		libldb1="$OLD_PKG_VERSION_LDB" \
		python-ldb="$OLD_PKG_VERSION_LDB" \
		libtdb1="$OLD_PKG_VERSION_TDB" \
		python-tdb="$OLD_PKG_VERSION_TDB" \
		tdb-tools="$OLD_PKG_VERSION_TDB" \
		libtalloc2="$OLD_PKG_VERSION_TALLOC" \
		python-talloc="$OLD_PKG_VERSION_TALLOC" \
		libtevent0="$OLD_PKG_VERSION_TEVENT"
	/etc/init.d/samba start
	/etc/init.d/univention-s4-connector start
	ucr set dns/backend='samba4'
	/etc/init.d/bind9 restart
}
