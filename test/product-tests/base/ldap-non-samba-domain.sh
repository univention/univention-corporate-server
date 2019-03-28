#!/bin/bash

set -x
set -e

test_ldap_non_samba_domain () {

	. product-tests/base/utils.sh
	eval "$(ucr shell ldap/base)"


	#### Produktest start


	### TODO

	# userpassword change
	password=univention
	users="test1 test2 test3"
	clients="$UCS"
	for user in $users; do
		udm users/user create --ignore_exists \
	    	--set password=$password --set lastname=$user --set username=$user
		udm users/user modify \
			--dn "$(univention-ldapsearch -LLL uid=$user dn |  sed -n 's/^dn: //p')" \
			--set password=$password --set overridePWHistory=1
	done
	sleep 10
	# check password
	echo $password > /tmp/.usertest
	kinit --password-file=/tmp/.usertest $user

	# password change
	password=Univention.98
	for user in $users; do
		echo $password > /tmp/.usertest
		kinit --password-file=/tmp/.usertest $user
	done
	sleep 10
	# check password
	for user in $users; do
		for client in $clients; do
			## TODO: check also remote?
		done
		echo $password > /tmp/.usertest
		kinit --password-file=/tmp/.usertest $user
	done
	
	echo "Success"

}
