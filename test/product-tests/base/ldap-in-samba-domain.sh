#!/bin/bash

set -x
set -e

test_ldap_in_samba_domain_master () {
	. product-tests/base/create_5000_users_in_1000_groups.sh
	measure_time_for_create_5000_users_distributed_in_1000_groups
	# measure_time_for_create_group_with_5000_members
}

test_ldap_in_samba_domain_backup () {

	. product-tests/base/utils.sh
	eval "$(ucr shell ldap/base windows/domain)"

	### Skalierungstests
	# TODO:
	#    An UMC anmelden: < 1 Sek
	#        users/user öffnen: ca. 3 Sek (Autosuche weitere 9 Sek)
	#        Benutzersuche mit 5000 Usern als Suchergebnis: 10 Sekunde
	#        Gruppe mit 5000 Mitgliedern öffnen: 4 Sekunden
	#        Anlegen der User 5001 bis 5010: 17 Sekunden
	#    Benutzer zu 5000er-Gruppe hinzufügen:
	#        Öffnen der Benutzerauswahl zum Hinzufügen:
	#            initiales Öffnen des Dialogs: 12 Sekunden
	#            erneutes Öffnen des Dialogs: < 1 Sekunde
	#        Suchen in der Benutzerauswahl zum Hinzufügen:
	#            abhängig von der Ergebnisanzahl:
	#            10 User → < 1 Sekunde
	#            100 User → ca. < 2 Sekunden
	#            5000 User → ca. 12 Sekunden
	#        Gruppe modifizieren/speichern: ca. 6 Sekunden

	measure_duration --limit=1 umc_login
	# measure_duration --limit=3  umc_open_users_user
	# measure_duration --limit=12 umc_open_users_user_autosearch
	# measure_duration --limit=10 umc_search_5000_users
	# measure_duration --limit=4  umc_open_group_with_5000_users
	# measure_duration --limit=17 umc_create_10_users
	# measure_duration --limit=12 umc_open_group_with_5000_users
	# measure_duration --limit=1  umc_open_group_with_5000_users    ## second time
	## TODO: Timing of user add select box
	# measure_duration --limit=6 umc_add_user_to_group_with_5000_users

	### Passwort-Tests
	# TODO:
	# https://hutten.knut.univention.de/mediawiki/index.php/Produkttests_UCS_4.4_LDAP#Passw.C3.B6rter.2FKonten

	### Replikation
	# TODO:
	# https://hutten.knut.univention.de/mediawiki/index.php/Produkttests_UCS_4.4_LDAP#Replikation
	# 	in Wesentlichen: failed.ldif

	### Unix-Konto / Home-Share
	# TODO:
	# https://hutten.knut.univention.de/mediawiki/index.php/Produkttests_UCS_4.4_LDAP#Unix-Konto_.28Home-Share.29

	### END - After this, the cfg file may run backup2master
}

test_ldap_in_samba_domain_windowsclient () {
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
