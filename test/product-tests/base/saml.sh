#!/bin/bash

set -x
set -e

test_saml () {

	eval "$(ucr shell ldap/base windows/domain)"

	# check winrm
	if ! dpkg -l python-winrm | grep ^ii 1>/dev/null; then
		( . utils.sh && install_winrm )
	fi

	# get windows client info/name
	python shared-utils/ucs-winrm.py run-ps --cmd ipconfig
	python shared-utils/ucs-winrm.py run-ps --cmd "(gwmi win32_operatingsystem).caption"
	winclient_name="$(python shared-utils/ucs-winrm.py run-ps  --cmd '$env:computername' --loglevel error | head -1 | tr -d '\r')"
	test -n "$winclient_name"

	# Join des Clients
	python shared-utils/ucs-winrm.py domain-join --dnsserver "$UCS"  --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"

	# Auf core prüfen: find /var -name core
	test -z "$(find /var -name core)"

	# In der UMC anlegen: Benutzer
	udm users/user create --position "cn=users,$ldap_base" --set username="newuser01" \
		--set lastname="newuser01" --set password="Univention.99"
	#udm groups/group modify --dn "cn=Domain Admins,cn=groups,$ldap_base" --append users="uid=newuser01,cn=users,$ldap_base"
	sleep 15

	# Login als Domänen-Administrator am Windows-Client
	python shared-utils/ucs-winrm.py domain-user-validate-password --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py domain-user-validate-password --domainuser "newuser01" --domainpassword "Univention.99"

	# Java + Selenium installieren
	python shared-utils/ucs-winrm.py run-ps --cmd "Invoke-WebRequest -Uri https://bit.ly/2TlkRyu -OutFile C:\\selenium-server.jar" # hopefully stable link
	python shared-utils/ucs-winrm.py run-ps --cmd "Invoke-WebRequest -Uri https://javadl.oracle.com/webapps/download/AutoDL?BundleId=236885_42970487e3af4f5aa5bca3f542482c60 -OutFile C:\\javasetup.exe" # probably not a stable link
	python shared-utils/ucs-winrm.py run-ps --cmd "C:\\javasetup.exe /s" # silent installation

	# Auf core prüfen: find /var -name core
	test -z "$(find /var -name core)"

	echo "Success"

}
