#!/bin/bash

set -x
set -e

test_ldap_in_samba_domain () {

	. product-tests/ldap/utils.sh
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

	#### Produktest start


	### TODO
	# Login als Domänen-Administrator am Windows-Client
	python shared-utils/ucs-winrm.py domain-user-validate-password --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py domain-user-validate-password --domainuser "newuser01" --domainpassword "Univention.99"

	# userpassword change
	password=univention
	users="test1 test2 test3"
	clients="$WINRM_CLIENT $UCS"
	for user in $users; do
		udm users/user create --ignore_exists \
	    	--set password=$password --set lastname=$user --set username=$user
		udm users/user modify \
			--dn "$(univention-ldapsearch -LLL uid=$user dn |  sed -n 's/^dn: //p')" \
			--set password=$password --set overridePWHistory=1
	done
	sleep 10
	for client in $clients; do
		for user in $users; do
			smbclient "//$client/IPC$" -U "$user"%"$password" -c exit
		done
	done
	# password change via windows
	password=Univention.98
	for user in $users; do
		python shared-utils/ucs-winrm.py change-user-password --userpassword="$password" --domainuser "$user"
	done
	sleep 10
	# check password
	for user in $users; do
		for client in $clients; do
			smbclient //$client/IPC\$ -U "$user"%"$password" -c exit
		done
		echo $password > /tmp/.usertest
		kinit --password-file=/tmp/.usertest $user
	done
	
	echo "Success"

}
