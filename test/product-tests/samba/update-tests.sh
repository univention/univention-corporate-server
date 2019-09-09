#!/bin/bash

set -x
set -e

test_before_update () {

	set -x
	set -e

	. product-tests/samba/utils.sh

	eval "$(ucr shell ldap/base windows/domain)"

	export UCS_ROOT="root" UCS_PASSWORD="$ADMIN_PASSWORD"

	# get windows client info/name
	python shared-utils/ucs-winrm.py run-ps --cmd ipconfig
	python shared-utils/ucs-winrm.py run-ps --cmd "(gwmi win32_operatingsystem).caption"

	# get hostname for check in dns of server from client
	# Auf UCS-Seite "host windowsclient" testen: Funktioniert der DNS-Lookup?
	local win1_name="$(python shared-utils/ucs-winrm.py run-ps --client $WIN1 --cmd '$env:computername' --loglevel error | head -1 | tr -d '\r')"
	test -n "$win1_name"

	# Per UDM ein paar Benutzer und/in Gruppen anlegen (lieber nicht nur einen, falls man später einen Bug frisch testen muss..) OK
	for i in $(seq 1 10); do
		udm users/user create --position "cn=users,$ldap_base" --set username="user$i" --set firstname="Random" --set lastname="User" --set password="Univention.99"
		udm groups/group create --position "cn=groups,$ldap_base" --set name="group$i"
		udm groups/group modify --dn "cn=group$i,cn=groups,$ldap_base" --append users="uid=user$i,cn=users,$ldap_base"
	done

	# Einem Testuser1 als "Windows home path" den UNC-Pfad "\\memberserver\homes" eintragen (z.B. auf Laufwerk Z:).
	udm users/user create --position "cn=users,$ldap_base" --set username="testuser01" --set firstname="Random" \
		--set lastname="User" --set password="Univention.99" --set sambahome='\\ucs-member\testuser01' --set homedrive='Y:'

	# Per UDM eine Druckerfreigabe anlegen (z.B. Generic/Postscript mit file://-backend)
	udm shares/printer create --position "cn=printers,$ldap_base" --set name="Memberprinter" --set spoolHost="ucs-member.sambatest.local" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
	udm shares/printer create --position "cn=printers,$ldap_base" --set name="Masterprinter" --set spoolHost="ucs-master.sambatest.local" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
	udm shares/printer create --position "cn=printers,$ldap_base" --set name="Slaveprinter" --set spoolHost="ucs-slave.sambatest.local" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"

	# Per UDM eine Dateifreigabe auf Slave anlegen, schreibbar für eine Gruppe in der Testuser1 Mitglied ist.
	udm shares/share create --position "cn=shares,$ldap_base" --set name="testshareSlave" --set host="ucs-slave.sambatest.local" --set path="/home/testshare"
	gid="$(id -g testuser01)"
	udm shares/share modify --dn "cn=testshareSlave,cn=shares,dc=sambatest,dc=local" --set group=$gid --set directorymode=0770 --set sambaDirectoryMode=0770

	# Windows 7 oder Windows 8 Client in die Domäne joinen
	python shared-utils/ucs-winrm.py domain-join --client $WIN1 --dnsserver "$MASTER" --domainuser "$ADMIN" --domainpassword "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN1 --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN1 --domainuser "testuser01" --domainpassword "Univention.99"
	for ucs in ucs-master ucs-backup ucs-slave ucs-member; do
		python shared-utils/ucs-winrm.py run-ps --client $WIN1 --cmd "nbtstat -a $ucs" # does not work with $WIN2016
	done

	# Als Administrator einloggen und per "Gruppenrichtlinienverwaltung" (Remote Server Administration Tools" RSAT installieren)
	# zwei GPOs anlegen und z.B. mit der Domänenwurzel verknüpfen
	create_gpo GPO1 "$ldap_base" User 'HKCU\Environment'
	create_gpo GPO2 "$ldap_base" Computer 'HKLM\Environment'
	sleep 360 # wait for sysvol sync
	# reboot system to apply gpo's
	python shared-utils/ucs-winrm.py reboot --client $WIN1
	sleep 120

	# Auf UCS-Seite "host windowsclient" testen: Funktioniert der DNS-Lookup?
	host $win1_name

	# Als Testuser1 anmelden
	python shared-utils/ucs-winrm.py logon-as --username testuser01 --userpwd 'Univention.99' --client $WIN1
	#   Ist das Homeverzeichnis automatisch eingebunden?
	run_on_ucs_hosts $MEMBER "stat /home/testuser01"
	#   Schreibzugriff auf Slave
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename testuser01.txt --username 'testuser01' --userpwd "Univention.99" --share testshareSlave
	run_on_ucs_hosts $SLAVE "stat /home/testshare/testuser01.txt"
	#    GPO's
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'testuser01' --userpwd "Univention.99" --client $WIN1 \
		--usergpo 'GPO1' --usergpo 'Default Domain Policy' --computergpo 'GPO2' --computergpo 'Default Domain Policy'
	#   Ein Dokument aus wordpad heraus drucken: kommt eine (andere) PS-Datei raus? TODO
	#   die Testseite drucken kommt eine PS-Datei raus? TODO

}

test_after_update () {

	set -x
	set -e

	. product-tests/samba/utils.sh

	eval "$(ucr shell ldap/base windows/domain)"

	export UCS_ROOT="root" UCS_PASSWORD="$ADMIN_PASSWORD"

	# Funktioniert Anmeldung / DRS Replikation auch, wenn erst ein oder zwei UCS Systeme von UCS 4.3 auf UCS 4.4 aktualisiert wurden. TODO

	# Auf einigen Systemen sollte einmal server-password-change aufgerufen werden
	run_on_ucs_hosts "$MASTER $BACKUP" "ucr set server/password/interval='0' && /usr/lib/univention-server/server_password_change"

	# Check Minimales Passwortalter bei "samba-tool domain passwordsettings show" TODO

	# Anmeldung als Testuser1 am Windows-Client
	python shared-utils/ucs-winrm.py logon-as --username testuser01 --userpwd 'Univention.99' --client $WIN1
	#   Ist das Homeverzeichnis automatisch eingebunden?
	run_on_ucs_hosts $MEMBER "/etc/init.d/samba restart"
	run_on_ucs_hosts $MEMBER "touch /home/testuser01/test2.txt"
	python shared-utils/ucs-winrm.py check-share --server ucs-member --sharename "testuser01" --driveletter G --filename "test2.txt" --username 'testuser01' --userpwd "Univention.99" --client $WIN1
	#   Kann eine Datei dort angelegt werden?
	python shared-utils/ucs-winrm.py create-share-file --server ucs-member --filename test3.txt --username 'testuser01' --userpwd "Univention.99" --share testuser01 --client $WIN1
	#   Wurden die GPOs ausgewertet?
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'testuser01' --userpwd "Univention.99" --client $WIN1 \
		--usergpo 'GPO1' --usergpo 'Default Domain Policy' --computergpo 'GPO2' --computergpo 'Default Domain Policy'
	#   Schreibzugriff auf share am Slave?
	python shared-utils/ucs-winrm.py check-share --server ucs-slave --sharename "testshareSlave" --driveletter Q --filename "testuser01.txt" --username 'testuser01' --userpwd "Univention.99" --client $WIN1
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename testuser02.txt --username 'testuser01' --userpwd "Univention.99" --share testshareSlave --client $WIN1
	python shared-utils/ucs-winrm.py check-share --server ucs-slave --sharename "testshareSlave" --driveletter Q --filename "testuser02.txt" --username 'testuser01' --userpwd "Univention.99" --client $WIN1
	#  Ein Dokument aus wordpad heraus drucken: kommt eine (andere) PS-Datei raus? TODO
	#  Passwort ändern am Windows-Client (per Alt-Ctrl-Del) TODO
	#  Danach neues Passwort unter UCS mit "kinit testuser1" testen. TODO

	# Anmeldung als Administrator am Windows-Client
	#   Eine sichtbare Einstellung an den GPOs ändern TODO
	#   Eine neue GPO anlegen
	create_gpo GPO3 "$ldap_base" User 'HKCU\Environment'
	create_gpo GPO4 "$ldap_base" Computer 'HKLM\Environment'

	# Zweiten/Neuen Windows-Client joinen (ggf. vorher Zeit manuell setzen, sonst zwei mal neu Booten, DNS record prüfen)
	python shared-utils/ucs-winrm.py domain-join --client $WIN2 --dnsserver "$MASTER" --domainuser "$ADMIN" --domainpassword "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN2 --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN2 --domainuser "testuser01" --domainpassword "Univention.99"

	# Unter UDM neuen Testuser2 anlegen, als Home-share "\\memberserver\homes" eintragen (z.B. auf Laufwerk Z:),
	# gleiche Gruppe wie Testuser1. "Passwort bei nächster Anmeldung ändern" auswählen.
	udm users/user create --position "cn=users,$ldap_base" --set username="testuser02" --set firstname="Random" --set pwdChangeNextLogin=1 \
		--set lastname="User" --set password="Univention.99" --set sambahome='\\ucs-member\testuser02' --set homedrive='Y:'
	sleep 30
	# Anmeldung am neuen Windows-Client als Testuser2.
	! python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN2 --domainuser "testuser02" --domainpassword "Univention.99"
	#   Passwortänderung verlangt? Funktioniert?
	python shared-utils/ucs-winrm.py change-user-password --client $WIN2 --domainuser testuser02 --userpassword "Univention123!"
	sleep 30
	python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN2 --domainuser "testuser02" --domainpassword "Univention123!"
	sleep 30
	#   "kinit testuser2" auf UDM geht mit neuem Passwort?
	check_user_in_ucs testuser02 "Univention123!"
	#   Ist das Homeverzeichnis am Windows-Client automatisch eingebunden?
	python shared-utils/ucs-winrm.py logon-as --username testuser02 --userpwd 'Univention123!' --client $WIN2
	python shared-utils/ucs-winrm.py run-ps --impersonate --run-as-user testuser02 --run-as-password 'Univention123!' --client $WIN2 \
		--cmd 'gwmi win32_mappedlogicaldisk -ComputerName localhost | select ProviderName, Name'
	python shared-utils/ucs-winrm.py run-ps --impersonate --run-as-user testuser02 --run-as-password 'Univention123!' --client $WIN2 \
		--cmd 'gwmi win32_mappedlogicaldisk -ComputerName localhost | select ProviderName, Name' | grep '\\\\ucs-member\\testuser02'
	#   Kann eine Datei dort angelegt werden?
	python shared-utils/ucs-winrm.py create-share-file --server ucs-member --filename test1.txt --username 'testuser02' --userpwd "Univention123!" --share testuser02 --client $WIN2
	run_on_ucs_hosts $MEMBER "stat /home/testuser02/test1.txt"
	#   Wurden die GPOs ausgewertet?
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'testuser02' --userpwd "Univention123!" --client $WIN2 \
		--usergpo 'GPO1' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO2' --computergpo 'GPO4' --computergpo 'Default Domain Policy'
	#   Sieht man die Server der Domäne unter Explorer->Netzwerkumgebung? TODO
	#   Windows Kommando ausfüren: echo %LOGONSERVER% TODO

	# Samba4 auf dem Logonserver anhalten TODO

	# Anmeldung von Testuser2 am Windows-Client
	python shared-utils/ucs-winrm.py logon-as --username testuser02 --userpwd 'Univention123!' --client $WIN1
	#   Ist das Homeverzeichnis am Windows-Client automatisch eingebunden?
	python shared-utils/ucs-winrm.py run-ps --impersonate --run-as-user testuser02 --run-as-password 'Univention123!' --client $WIN1 \
		--cmd 'gwmi win32_mappedlogicaldisk -ComputerName localhost | select ProviderName, Name'
	python shared-utils/ucs-winrm.py run-ps --impersonate --run-as-user testuser02 --run-as-password 'Univention123!' --client $WIN1 \
		--cmd 'gwmi win32_mappedlogicaldisk -ComputerName localhost | select ProviderName, Name' | grep '\\\\ucs-member\\testuser02'
	#   Wurden die GPOs ausgewertet?
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'testuser02' --userpwd "Univention123!" --client $WIN1 \
		--usergpo 'GPO1' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO2' --computergpo 'GPO4' --computergpo 'Default Domain Policy'
	#   Passwort ändern am Windows-Client (per Alt-Ctrl-Del)
	python shared-utils/ucs-winrm.py change-user-password --client $WIN1 --domainuser testuser02 --userpassword "newPassW0rd-"
	sleep 30
	python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN1 --domainuser "testuser02" --domainpassword "newPassW0rd-"
	sleep 30
	check_user_in_ucs testuser02 "newPassW0rd-"

	# Einen frisch installierten UCS 4.4 Samba4 Slave joinen (vorher Samba4 wieder starten). TODO
	# Kann noch ein UCS 4.3 DC mit Samba 4 in die Domäne gejoint werden? TODO
}
