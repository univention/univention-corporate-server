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
	local win2012_name="$(python shared-utils/ucs-winrm.py run-ps --client $WIN1 --cmd '$env:computername' --loglevel error | head -1 | tr -d '\r')"
	test -n "$win2012_name"

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
	udm shares/share modify --dn "cn=testshareSlave,cn=shares,dc=sambatest,dc=local" --set group=5074 --set directorymode=0770 --set sambaDirectoryMode=0770

	# Windows 7 oder Windows 8 Client in die Domäne joinen
	python shared-utils/ucs-winrm.py domain-join --client $WIN1 --dnsserver "$MASTER" --domainuser "$ADMIN" --domainpassword "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN1 --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN1 --domainuser "testuser01" --domainpassword "Univention.99"
	for ucs in ucs-master ucs-backup ucs-slave ucs-member; do
		python shared-utils/ucs-winrm.py run-ps --client $WIN1 --cmd "nbtstat -a $ucs" # does not work with $WIN2016
	done

	# Als Administrator einloggen und per "Gruppenrichtlinienverwaltung" (Remote Server Administration Tools" RSAT installieren)
	# zwei GPOs anlegen und z.B. mit der Domänenwurzel verknüpfen
	udm container/ou create --set name=gpo1
	udm container/ou create --set name=gpo2
	create_gpo GPO1 "$ldap_base" User 'HKCU\Environment'
	create_gpo GPO2 "$ldap_base" Computer 'HKLM\Environment'
	sleep 360 # wait for sysvol sync
	# reboot system to apply gpo's
	python shared-utils/ucs-winrm.py reboot --client $WIN1
	sleep 120

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
	# Drucker verbinden (Druckertests wird erstaml ausgelassen, da auch im multi server test Drucker nicht stabil ist)
	# die Testseite drucken kommt eine PS-Datei raus? (z.B. per ssh wegkopieren und mit okular ansehen, falls der "Text-only" Treiber ausgewählt wurde, ist der Text abgeschnitten ).
	# ein Dokument aus wordpad heraus drucken: Es ist zu erwarten, dass keine PS-Datei angelegt wird. (Bug in UCS3.0-2)
	# TODO

}

#    Snapshot der Umgebung. In VMs nicht möglich bzw. macht kein Sinn
#    univention-run-join-scripts (Generell: Hinweise aus Release-notes beachten!) OK(in cfg datei)
#    Funktioniert Anmeldung / DRS Replikation auch, wenn erst ein oder zwei UCS Systeme von UCS 4.3 auf UCS 4.4 aktualisiert wurden.
#
#
#
#    Samba4 auf dem Logonserver anhalten
#    Anmeldung von Testuser2 am Windows-Client
#        Ist das Homeverzeichnis am Windows-Client automatisch eingebunden?
#        Wurden die GPOs ausgewertet?
#        Passwort ändern am Windows-Client (per Alt-Ctrl-Del)
#    Einen frisch installierten UCS 4.4 Samba4 Slave joinen (vorher Samba4 wieder starten).
#    Kann noch ein UCS 4.3 DC mit Samba 4 in die Domäne gejoint werden?

#        Ein Dokument aus wordpad heraus drucken: kommt eine (andere) PS-Datei raus? (z.B. per ssh wegkopieren und mit okular ansehen). (Powershell kann nur Dateien zu Netzwerkdrucker senden/pipe)
test_after_update () {

	set -x
	set -e

	. product-tests/samba/utils.sh

	eval "$(ucr shell ldap/base windows/domain)"

	export UCS_ROOT="root" UCS_PASSWORD="$ADMIN_PASSWORD"

	# Auf einigen Systemen sollte einmal server-password-change aufgerufen werden
	run_on_ucs_hosts "$MASTER $BACKUP" "ucr set server/password/interval='0' && /usr/lib/univention-server/server_password_change"


	# Anmeldung als Testuser1 am Windows-Client
	python shared-utils/ucs-winrm.py logon-as --username testuser01 --userpwd 'Univention.99' --client $WIN1
	#   Ist das Homeverzeichnis automatisch eingebunden?
	run_on_ucs_hosts $MEMBER "touch /home/testuser01/test2.txt"
	python shared-utils/ucs-winrm.py check-share --server ucs-member --sharename "testuser01" --driveletter G --filename "test.txt" --username 'testuser01' --userpwd "Univention.99" --client $WIN1
	#   Kann eine Datei dort angelegt werden?
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename test-user01.txt --username 'testuser01' --userpwd "Univention.99" --share testuser01 --client $WIN1
	#   Wurden die GPOs ausgewertet?
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'testuser01' --userpwd "Univention.99" --client $WIN2 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'
	#   Schreibzugriff auf share am Slave?
	python shared-utils/ucs-winrm.py check-share --server ucs-slave --sharename "testshareSlave" --driveletter Q --filename "test.txt" --username 'testuser01' --userpwd "Univention.99" --client $WIN1
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename testuser01.txt --username 'testuser01' --userpwd "Univention.99" --share testshareSlave --client $WIN1
	#   Passwort ändern am Windows-Client (per Alt-Ctrl-Del) TODO
	#   Danach neues Passwort unter UCS mit "kinit testuser1" testen. TODO
	#   Abmeldung des Testuser1 vom Windows-Client. TODO

	# Anmeldung als Administrator am Windows-Client
	#   Eine sichtbare Einstellung an den GPOs ändern TODO
	#   Eine neue GPO anlegen
	create_gpo GPO6 "$ldap_base" User 'HKCU\Environment' --client $WIN1
    python shared-utils/ucs-winrm.py check-applied-gpos --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --client $WIN1 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'GPO6' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'

	# Zweiten/Neuen Windows-Client joinen (ggf. vorher Zeit manuell setzen, sonst zwei mal neu Booten, DNS record prüfen)
	python shared-utils/ucs-winrm.py domain-join --client $WIN2 --dnsserver "$MASTER" --domainuser "$ADMIN" --domainpassword "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN2 --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN2 --domainuser "testuser01" --domainpassword "Univention.99"
	python shared-utils/ucs-winrm.py domain-user-validate-password --client $WIN2 --domainuser "testuser02" --domainpassword "Univention.99"

	# Unter UDM neuen Testuser2 anlegen, als Home-share "\\memberserver\homes" eintragen (z.B. auf Laufwerk Z:),
	# gleiche Gruppe wie Testuser1. "Passwort bei nächster Anmeldung ändern" auswählen.
	udm users/user modify  --dn "uid=testuser02,cn=users,$ldap_base" --set homedrive='Z:' --set sambahome='\\ucs-slave\testuser02'
	check_user_in_ucs testuser01 "Univention.99"
	# Anmeldung am neuen Windows-Client als Testuser2.
	python shared-utils/ucs-winrm.py logon-as --username testuser02 --userpwd 'Univention.99' --client $WIN2 
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename test-testuser02.txt --username 'testuser02' --userpwd "Univention.99" --share testuser02
	# Passwortänderung verlangt? Funktioniert?
	# "kinit testuser2" auf UDM geht mit neuem Passwort?
	# Ist das Homeverzeichnis am Windows-Client automatisch eingebunden?
	#run_on_ucs_hosts $SLAVE "touch /home/testuser02/test.txt"
	python shared-utils/ucs-winrm.py check-share --server ucs-slave --sharename "testuser02" --driveletter R --filename "test-testuser02.txt" --username 'testuser02' --userpwd "Univention.99" --client $WIN2
	# Kann eine Datei dort angelegt werden?
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename test-admin02.txt --username 'testuser02' --userpwd "Univention.99" --share testuser02 --client $WIN2
	# Wurden die GPOs ausgewertet?
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'testuser02' --userpwd "Univention.99" --client $WIN2 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'
	# Sieht man die Server der Domäne unter Explorer->Netzwerkumgebung?
	# Windows Kommando ausfüren: echo %LOGONSERVER%
	# Abmeldung des Testuser2 vom Windows-Client.
	run_on_ucs_hosts $MEMBER "! stat /home/testuser04"
	python shared-utils/ucs-winrm.py logon-as --username testuser04 --userpwd 'Univention.99' --client $WIN1 
	#run_on_ucs_hosts $MEMBER "stat /home/testuser04"
	# Passworte

	# Check Minimales Passwortalter bei "samba-tool domain passwordsettings show"
	# (Anpassung Minimales Passwortalter auf 0 per
	#"samba-tool domain passwordsettings set -min-pwg-age 0")
	# Änderung
	#  Kann man anschließend per kinit für den Benutzer auf UCS-Seite ein Ticket bekommen?
	#  Kann das Passwort per STRG-ALT-ENTF an den unterschiedlichen Windows-Systemen geändert werden? Not possible : simulated with LDAP pw change
	python shared-utils/ucs-winrm.py change-user-password --domainuser testuser01 --userpassword "Univention123!"
	sleep 30
	check_user_in_ucs testuser01 "Univention123!"
	python shared-utils/ucs-winrm.py logon-as --username testuser01 --userpwd "Univention123!" --client $WIN1
	python shared-utils/ucs-winrm.py logon-as --username testuser01 --userpwd "Univention123!" --client $WIN2
	# In UDM am Samba Domänenobjekt folgende Einstellungen treffen
	#  Maximales Passwortalter: 2 Tage (wegen Bug #44226) DONE
	#  Passwort History: 2 (wegen Bug #46557) DONE
	#  Minimale Passwortlänge auf 5 Buchstaben setzen. DONE
	udm policies/pwhistory modify --dn "cn=default-settings,cn=pwhistory,cn=users,cn=policies,$ldap_base" --set expiryInterval=2
	udm policies/pwhistory modify --dn "cn=default-settings,cn=pwhistory,cn=users,cn=policies,$ldap_base" --set pwLength=5
	udm policies/pwhistory modify --dn "cn=default-settings,cn=pwhistory,cn=users,cn=policies,$ldap_base" --set length=2
	samba-tool domain passwordsettings set --min-pwd-length=5 --max-pwd-age=2 --history-length=2
	sleep 15
	# change pw after policies changes
	#  Mit Benutzer am Windows7-Client anmelden und Passwort auf "Ünivention123" ändern.
	#  Die Samba4/Heimdal-Passwortkomplexitätsprüfung sollte das akzeptieren. DONE
	#  Uhrzeit auf den UCS DCs eine Stunde vorstellen und neu booten. (Oder Zeit sinnvoll anders nutzen..) Simulated by fetching information from Samba DB and comparing with a date
	#  Benutzer-Konto Option "Passwort bei der nächsten Anmeldung ändern" im UDM wählen und an jedem Windows System testen, ob das Passwort geändert werden muss.
	#  Mit Benutzer am Windows7-Client anmelden -> Windows muss Passwortänderung verlangen. Passwort ändern:
	#  Man sollte nicht wieder das alte Passwort setzen können. Man sollte ein Passwort mit 5 Buchstaben setzen können. DONE
	#  Kann man jetzt wieder "Ünivention123" setzen? DONE
	python shared-utils/ucs-winrm.py run-ps --cmd "net user testuser01 /domain" --impersonate --run-as-user Administrator | grep $(date -d "+2 days" +"%d.%m.%Y")
	python shared-utils/ucs-winrm.py change-user-password --domainuser testuser01 --userpassword "Univ" --debug 2>&1 | grep Exception
	python shared-utils/ucs-winrm.py change-user-password --domainuser testuser01 --userpassword "Univ!"
	sleep 10
	check_user_in_ucs testuser01 "Univ!"
	python shared-utils/ucs-winrm.py change-user-password --domainuser testuser01 --userpassword 'Univention123!'
	sleep 10
	check_user_in_ucs testuser01 'Univention123!'
	udm users/user modify --dn "uid=testuser01,cn=users,$ldap_base" --set pwdChangeNextLogin=1
	sleep 10
	python shared-utils/ucs-winrm.py run-ps --cmd 'ls' --credssp --run-as-user testuser01 --run-as-password 'Univention123!' --client $WIN1 --debug 2>&1 | grep AccessDenied
	python shared-utils/ucs-winrm.py run-ps --cmd 'ls' --credssp --run-as-user testuser01 --run-as-password 'Univention123!' --client $WIN2 --debug 2>&1 | grep AccessDenied
	! samba-tool user password -U testuser01 --password='Univention123!' --newpassword='Univention123!'
	samba-tool user password -U testuser01 --password='Univention123!' --newpassword='Ünivention999!'
	python shared-utils/ucs-winrm.py logon-as --username testuser01 --userpwd "Ünivention999!" --client $WIN2
	python shared-utils/ucs-winrm.py logon-as --username testuser01 --userpwd "Ünivention999!" --client $WIN2
	check_user_in_ucs testuser01 "Ünivention999!"

	run_on_ucs_hosts "$MASTER $BACKUP $SLAVE" 'test -z "$(find /var -name core)"'

}

