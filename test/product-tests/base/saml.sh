#!/bin/bash

set -e -x

test_saml () {
	eval "$(ucr shell ldap/base windows/domain)"

	# get windows client info/name
	# shellcheck source=utils.sh
	. utils.sh || return $?
	ucs-winrm run-ps --cmd ipconfig
	ucs-winrm run-ps --cmd "(gwmi win32_operatingsystem).caption"
	# shellcheck disable=SC2016
	winclient_name="$(ucs-winrm run-ps  --cmd '$env:computername' --loglevel error | head -1 | tr -d '\r')"
	test -n "$winclient_name"

	# Join des Clients
	ucs-winrm domain-join --dnsserver "$UCS"  --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"

	assert_no_core_files

	# In der UMC anlegen: Benutzer
	# shellcheck disable=SC2154
	udm users/user create --position "cn=users,$ldap_base" --set username="newuser01" \
		--set lastname="newuser01" --set password="Univention.99"
	#udm groups/group modify --dn "cn=Domain Admins,cn=groups,$ldap_base" --append users="uid=newuser01,cn=users,$ldap_base"
	sleep 15

	# Login als Domänen-Administrator am Windows-Client
	ucs-winrm domain-user-validate-password --domainuser 'Administrator' --domainpassword "$ADMIN_PASSWORD"
	ucs-winrm domain-user-validate-password --domainuser 'newuser01' --domainpassword 'Univention.99'

	# Java + Selenium installieren
	ucs-winrm run-ps --cmd "Invoke-WebRequest -Uri https://bit.ly/2TlkRyu -OutFile C:\\selenium-server.jar" # hopefully stable link
	ucs-winrm run-ps --cmd "Invoke-WebRequest -Uri https://javadl.oracle.com/webapps/download/AutoDL?BundleId=236885_42970487e3af4f5aa5bca3f542482c60 -OutFile C:\\javasetup.exe" # probably not a stable link
	ucs-winrm run-ps --cmd "C:\\javasetup.exe /s" # silent installation

	assert_no_core_files

	echo "Success"
}
