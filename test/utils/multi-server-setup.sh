#!/bin/bash
# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -e -x

setup_multi_server () {
	set -e -x

	# shellcheck source=utils.sh
	. product-tests/samba/utils.sh

	eval "$(ucr shell ldap/base windows/domain)"

	export UCS_ROOT="root" UCS_PASSWORD="$ADMIN_PASSWORD"

	# server password change on all UCS hosts
	run_on_ucs_hosts "$MASTER $BACKUP $SLAVE $MEMBER" \
		"ucr set server/password/interval='0' && /usr/lib/univention-server/server_password_change"

	# get windows client info
	ucs-winrm run-ps --cmd ipconfig
	ucs-winrm run-ps --cmd "(gwmi win32_operatingsystem).caption"

	local win2012_name win2016_name
	win2012_name="$(ucs-winrm run-ps --client "$WIN2012" --cmd '$env:computername' --loglevel error | head -1 | tr -d '\r')"
	win2016_name="$(ucs-winrm run-ps --client "$WIN2016" --cmd '$env:computername' --loglevel error | head -1 | tr -d '\r')"
	test -n "$win2012_name"
	test -n "$win2016_name"

	# create users
	for i in 1 2 3 4 5; do
		udm users/user create --position "cn=users,$ldap_base" \
			--set username="newuser0$i" --set firstname="Random" --set lastname="User" \
			--set password="Univention.99"
	done

	# add newuser01 to Domain Admins
	udm groups/group modify --dn "cn=Domain Admins,cn=groups,$ldap_base" \
		--append users="uid=newuser01,cn=users,$ldap_base"

	# create share directories on all hosts
	run_on_ucs_hosts "$MASTER" "mkdir -p /home/testshare"
	run_on_ucs_hosts "$MEMBER" "mkdir -p /home/testshare"
	run_on_ucs_hosts "$SLAVE" "mkdir -p /home/testshare"

	# create shares
	udm shares/share create --position "cn=shares,$ldap_base" --set name="testshare" \
		--set host="ucs-master.sambatest.test" --set path="/home/testshare"
	udm shares/share create --position "cn=shares,$ldap_base" --set name="testshareMember" \
		--set host="ucs-member.sambatest.test" --set path="/home/testshare"
	udm shares/share create --position "cn=shares,$ldap_base" --set name="testshareSlave" \
		--set host="ucs-slave.sambatest.test" --set path="/home/testshare"

	# set share permissions
	for share in testshare testshareMember testshareSlave; do
		udm shares/share modify --dn "cn=$share,cn=shares,$ldap_base" \
			--set group=5000 --set directorymode=0770 --set sambaDirectoryMode=0770
	done

	# create printers
	udm shares/printer create --position "cn=printers,$ldap_base" --set name="Masterprinter" \
		--set spoolHost="ucs-master.sambatest.test" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
	udm shares/printer create --position "cn=printers,$ldap_base" --set name="Memberprinter" \
		--set spoolHost="ucs-member.sambatest.test" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
	udm shares/printer create --position "cn=printers,$ldap_base" --set name="Slaveprinter" \
		--set spoolHost="ucs-slave.sambatest.test" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"

	# join windows clients to domain
	for client in $WIN2012 $WIN2016; do
		ucs-winrm domain-join --client "$client" --dnsserver "$MASTER" \
			--domainuser "$ADMIN" --domainpassword "$ADMIN_PASSWORD"
		sleep 120
	done

	# create OUs
	udm container/ou create --set name=gpo1
	udm container/ou create --set name=gpo2

	# create GPOs
	create_gpo GPO5 "$ldap_base" User 'HKCU\Environment' --client "$WIN2012"
	create_gpo_on_server GPO4 "$ldap_base" Computer 'HKLM\Environment' "$SLAVE" --client "$WIN2012"
	create_gpo_on_server GPO3 "$ldap_base" User 'HKCU\Environment' "$BACKUP" --client "$WIN2012"
	create_gpo GPO1 "ou=gpo1,$ldap_base" User 'HKCU\Environment'
	create_gpo GPO2 "ou=gpo2,$ldap_base" Computer 'HKLM\Environment'

	# move objects into OUs
	udm users/user move --dn "uid=newuser05,cn=users,$ldap_base" --position "ou=gpo1,$ldap_base"
	udm computers/windows move --dn "cn=$win2016_name,cn=computers,$ldap_base" --position "ou=gpo2,$ldap_base"

	# create test files on shares
	run_on_ucs_hosts "$MEMBER" "touch /home/testshare/test.txt"
	run_on_ucs_hosts "$SLAVE" "touch /home/testshare/test.txt"

	# set password policies
	udm policies/pwhistory modify --dn "cn=default-settings,cn=pwhistory,cn=users,cn=policies,$ldap_base" \
		--set expiryInterval=2
	udm policies/pwhistory modify --dn "cn=default-settings,cn=pwhistory,cn=users,cn=policies,$ldap_base" \
		--set pwLength=5
	udm policies/pwhistory modify --dn "cn=default-settings,cn=pwhistory,cn=users,cn=policies,$ldap_base" \
		--set length=2
	samba-tool domain passwordsettings set --min-pwd-length=5 --max-pwd-age=2 --history-length=2

	# wait for sysvol sync
	sleep 360

	# reboot windows clients to apply GPOs
	ucs-winrm reboot --client "$WIN2016"
	ucs-winrm reboot --client "$WIN2012"
	sleep 360
	ucs-winrm run-ps --cmd 'gpupdate /force' --client "$WIN2016" --credssp
	ucs-winrm run-ps --cmd 'gpupdate /force' --client "$WIN2012" --credssp
}
