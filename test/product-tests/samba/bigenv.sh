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

set_MaxConnIdleTime () {

	echo "dn: CN=Default Query Policy,CN=Query-Policies,CN=Directory Service,CN=Windows NT,CN=Services,CN=Configuration,DC=bigenv,DC=local
changetype: modify
delete: lDAPAdminLimits
lDAPAdminLimits: MaxConnIdleTime=900
-
add: lDAPAdminLimits
lDAPAdminLimits: MaxConnIdleTime=9000" | ldbmodify -H /var/lib/samba/private/sam.ldb --cross-ncs
	/etc/init.d/samba restart
}

clone_copy_samdb () {
	cp /usr/lib/python2.7/dist-packages/samba/join.py /usr/lib/python2.7/dist-packages/samba/join.py.bak
	sed -i 's/    ctx.do_join()/    ctx.plaintext_secrets=True\n    ctx.do_join()/' /usr/lib/python2.7/dist-packages/samba/join.py
	samba-tool drs clone-dc-database "$(dnsdomainname)" --server=master -UAdministrator%univention --targetdir /var/tmp/master --include-secrets
	sed -i 's/    ctx.plaintext_secrets=True//' /usr/lib/python2.7/dist-packages/samba/join.py
	echo univention > /tmp/pw
	univention-ssh-rsync /tmp/pw -a /var/tmp/master/ master:/var/tmp/master/
}

replace_samdb_and_upgrade () {
	ucr set dns/backend='ldap'
	/etc/init.d/bind9 restart
	/etc/init.d/samba stop

	local ridsetldif=$(ldbsearch -H /var/lib/samba/private/sam.ldb -b  "CN=RID Set,CN=$(hostname),OU=Domain Controllers,$(ucr get connector/s4/ldap/base)")
	local nextrid=$(sed -n 's/^rIDNextRID: //p' <<<"$ridsetldif")
	local prevpool=$(sed -n 's/^rIDPreviousAllocationPool: //p' <<<"$ridsetldif")

	# Important: Backup the Samba private data directory:
	cp -a /var/lib/samba/private/ /var/lib/samba/private.backup

	rsync -a /var/tmp/master/private/sam.ldb /var/lib/samba/private/
	rsync -a /var/tmp/master/private/sam.ldb.d/*.ldb /var/lib/samba/private/sam.ldb.d/

	if [ -f /var/tmp/master/private/encrypted_secrets.key ]; then
		rsync -a /var/tmp/master/private/encrypted_secrets.key /var/lib/samba/private/
	fi

	# Next update samba to make ldbedit work against the new Database format:
	univention-upgrade --noninteractive --updateto=4.3-4 --disable-app-updates
	/etc/init.d/samba stop

   #  Finally restore the local RID Set state:
echo -e "dn: CN=RID Set,CN=$(hostname),OU=Domain Controllers,$(ucr get connector/s4/ldap/base)
changetype: modify
replace: rIDNextRID
rIDNextRID: $nextrid
-
replace: rIDPreviousAllocationPool
rIDPreviousAllocationPool: $prevpool" | ldbmodify -H /var/lib/samba/private/sam.ldb

	/etc/init.d/samba start
	# give samba some time to repair drs
	sleep 180
}

restart_connector_and_bind () {
	/etc/init.d/univention-s4-connector start
	ucr set dns/backend='samba4'
	/etc/init.d/bind9 restart
}

bigenv_settings () {
	# some settings for setups with a big database
	ucr set directory/manager/user/primarygroup/update=false
	ucr set connector/s4/mapping/group/syncmode=read
	ucr set nss/group/cachefile/invalidate_interval=disabled
	ucr set ldap/database/mdb/maxsize='4294967296'
	ucr set listener/cache/mdb/maxsize='4294967296'
	ucr set slapd/backup=disbaled
	ucr unset samba4/backup/cron
}
