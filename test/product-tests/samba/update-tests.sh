#!/bin/bash

set -x
set -e

#    Lizenz einspielen OK (im CFG Datei)
#    Per UDM eine Druckerfreigabe anlegen (z.B. Generic/Postscript mit file://-backend)
#    Neu booten(VMs werden durch Skripte neu gestarteVMs werden durch Skripte neu gestartett)
#    Snapshot der Umgebung. (In VMs keine möglichkeit)

test_printers () {
	set -x
	set -e

	. product-tests/samba/utils.sh
	# printing

	## unstable, deactivated check later
	# Druckerzugriff mit serverseitig hinterlegten Druckertreibern:
	#  Anlegen eines Druckers auf dem DC Slave und auf dem Memberserver
	#  Zugriff als Domänen-Administrator vom Windowsclient aus
	#  serverseitig einen Druckertreiber hinterlegen, am einfachsten von 32bit XP aus (Windows 7 ist ein bisschen anders, 64bit ist zusätzlich hakelig ).
	#  Verbinden eines Druckers als unpriviligierter Benutzer vom Windowsclient aus
	#  Testdruck von wordpad aus auf den verbundenen Drucker
	python shared-utils/ucs-winrm.py setup-printer --printername Masterprinter --server "$MASTER"
	sleep 20
	rpcclient  -UAdministrator%"$ADMIN_PASSWORD" localhost -c enumprinters
	python shared-utils/ucs-winrm.py print-on-printer --printername Masterprinter --server "$MASTER" --impersonate --run-as-user Administrator
	python shared-utils/ucs-winrm.py print-on-printer --printername Masterprinter --server "$MASTER" --impersonate --run-as-user newuser02 --run-as-password "Univention.99"
	sleep 60
	stat /var/spool/cups-pdf/administrator/job_1-document.pdf
	stat /var/spool/cups-pdf/newuser02/job_2-document.pdf
	# Druckerzugriff ohne serverseitige Druckertreiber
	#  Anlegen eines Druckers auf dem DC Slave und auf dem Memberserver
	#  Verbinden zum Drucker als unpriviligierter Benutzer vom Windowsclient aus
	#  Testdruck von wordpad aus auf den verbundenen Drucker
	python shared-utils/ucs-winrm.py setup-printer --printername Memberprinter --server "$MEMBER"
	python shared-utils/ucs-winrm.py setup-printer --printername Memberprinter --server "ucs-member.sambatest.local" --client $WIN2016
	sleep 20
	python shared-utils/ucs-winrm.py print-on-printer --printername Memberprinter --server $MEMBER \
		--impersonate --run-as-user Administrator
	python shared-utils/ucs-winrm.py print-on-printer --printername Memberprinter --server "$MEMBER" \
		--impersonate --run-as-user newuser02 --run-as-password "Univention.99"
	python shared-utils/ucs-winrm.py print-on-printer --printername Memberprinter --server "ucs-member.sambatest.local" \
		--impersonate --run-as-user newuser02 --run-as-password "Univention.99" --client $WIN2016
	sleep 60
	run_on_ucs_hosts $MEMBER 'stat /var/spool/cups-pdf/administrator/job_1-document.pdf'
	run_on_ucs_hosts $MEMBER 'stat /var/spool/cups-pdf/newuser02/job_2-document.pdf'
	run_on_ucs_hosts $MEMBER 'stat /var/spool/cups-pdf/newuser02/job_3-document.pdf'
	# printer GPO's TODO
}

test_before_update () {

	set -x
	set -e

	. product-tests/samba/utils.sh

	eval "$(ucr shell ldap/base windows/domain)"
	# Der Wert der UCR Variable samba/share/home muss "yes" sein OK
	ucr set samba/share/home='yes'
	export UCS_ROOT="root" UCS_PASSWORD="$ADMIN_PASSWORD"

	# Auf allen Systemen sollte einmal server-password-change aufgerufen werden

	# get windows client info/name
	python shared-utils/ucs-winrm.py run-ps --cmd ipconfig
	python shared-utils/ucs-winrm.py run-ps --cmd "(gwmi win32_operatingsystem).caption"

	# get hostname for check in dns of server from client
	# Auf UCS-Seite "host windowsclient" testen: Funktioniert der DNS-Lookup?
	local win2012_name="$(python shared-utils/ucs-winrm.py run-ps --client $WIN1 --cmd '$env:computername' --loglevel error | head -1 | tr -d '\r')"
	test -n "$win2012_name"

	# Per UDM ein paar Benutzer und/in Gruppen anlegen (lieber nicht nur einen, falls man später einen Bug frisch testen muss..) OK
	udm users/user create --position "cn=users,$ldap_base" --set username="testuser01" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	udm users/user create --position "cn=users,$ldap_base" --set username="testuser02" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	udm users/user create --position "cn=users,$ldap_base" --set username="testuser03" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	udm users/user create --position "cn=users,$ldap_base" --set username="testuser04" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	udm users/user create --position "cn=users,$ldap_base" --set username="testuser05" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	udm groups/group modify --dn "cn=Domain Admins,cn=groups,dc=sambatest,dc=local" --append users="uid=testuser01,cn=users,dc=sambatest,dc=local"
	udm groups/group create --position "cn=groups,$ldap_base" --set name="testgruppe1"
	udm groups/group create --position "cn=groups,$ldap_base" --set name="testgruppe2"
	udm groups/group create --position "cn=groups,$ldap_base" --set name="testgruppe3"
	udm groups/group create --position "cn=groups,$ldap_base" --set name="testgruppe4"
	udm groups/group create --position "cn=groups,$ldap_base" --set name="testgruppe5"
	udm groups/group modify --dn "cn=testgruppe1,cn=groups,$ldap_base" --append users="uid=testuser01,cn=users,$ldap_base"
	udm groups/group modify --dn "cn=testgruppe2,cn=groups,$ldap_base" --append users="uid=testuser02,cn=users,$ldap_base"
	udm groups/group modify --dn "cn=testgruppe3,cn=groups,$ldap_base" --append users="uid=testuser03,cn=users,$ldap_base"
	udm groups/group modify --dn "cn=testgruppe4,cn=groups,$ldap_base" --append users="uid=testuser04,cn=users,$ldap_base"
	udm groups/group modify --dn "cn=testgruppe5,cn=groups,$ldap_base" --append users="uid=testuser05,cn=users,$ldap_base"

	# Per UDM eine Dateifreigabe auf Slave anlegen, schreibbar für eine Gruppe in der Testuser1 Mitglied ist.
	udm shares/share create --position "cn=shares,$ldap_base" --set name="testshareSlave" --set host="ucs-slave.sambatest.local" --set path="/home/testshare"
	udm shares/share modify --dn "cn=testshareSlave,cn=shares,dc=sambatest,dc=local" --set group=5074 --set directorymode=0770 --set sambaDirectoryMode=0770
	
	udm shares/printer create --position "cn=printers,$ldap_base" --set name="Slaveprinter" --set spoolHost="ucs-slave.sambatest.local" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"

	# join windows clients
	# Sind alle UCS-Samba-Server in der Netzwerkumgebung der Clients zu sehen? unter windows net computer list
	# Windows 7 oder Windows 8 Client in die Domäne joinen
	for client in $WIN1; do
		python shared-utils/ucs-winrm.py domain-join --client $client --dnsserver "$MASTER" --domainuser "$ADMIN" --domainpassword "$ADMIN_PASSWORD"
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "testuser01" --domainpassword "Univention.99"
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "testuser02" --domainpassword "Univention.99"
	done
	for ucs in ucs-master ucs-backup ucs-slave ucs-member; do
		python shared-utils/ucs-winrm.py run-ps --client $WIN1 --cmd "nbtstat -a $ucs" # does not work with $WIN2016
	done

	# Einem Testuser1 als "Windows home path" den UNC-Pfad "\\memberserver\homes" eintragen (z.B. auf Laufwerk Z:). OK
	run_on_ucs_hosts $SLAVE "! stat /home/testuser01"
	udm users/user modify  --dn "uid=testuser01,cn=users,$ldap_base" --set homedrive='Y:' --set sambahome='\\ucs-slave\testuser01'
	check_user_in_ucs testuser01 "Univention.99"
	# Als Testuser1 anmelden
	python shared-utils/ucs-winrm.py logon-as --username testuser01 --userpwd 'Univention.99' --client $WIN1 
	# Ist das Homeverzeichnis automatisch eingebunden?
	run_on_ucs_hosts $SLAVE "touch /home/testuser01/testfile.txt"
	python shared-utils/ucs-winrm.py check-share --server ucs-slave --sharename "testuser01" --driveletter V --filename "testfile.txt" --username 'testuser01' --userpwd "Univention.99" --client $WIN1
	
	# Drucker verbinden (Druckertests wird erstaml ausgelassen, da auch im multi server test Drucker nicht stabil ist)
	# die Testseite drucken kommt eine PS-Datei raus? (z.B. per ssh wegkopieren und mit okular ansehen, falls der "Text-only" Treiber ausgewählt wurde, ist der Text abgeschnitten ).
	# ein Dokument aus wordpad heraus drucken: Es ist zu erwarten, dass keine PS-Datei angelegt wird. (Bug in UCS3.0-2)
	
	# Active Directory-Benutzer und -Computer öffnen, zum RODC wechseln und versuchen etwas zu ändern (sollte nicht funktionieren)
	# Abmeldung des Testuser1 vom Windows-Client.
	python shared-utils/ucs-winrm.py logon-as --username testuser01 --userpwd 'Univention.99' --client $WIN1

	# GPO's

	# Als Administrator einloggen und per "Gruppenrichtlinienverwaltung" (Remote Server Administration Tools" (RSAT) installieren) zwei GPOs anlegen 
	# und z.B. mit der Domänenwurzel verknüpfen, siehe https://hutten.knut.univention.de/mediawiki/index.php/Produkttests_UCS_3.2_Samba_4#GPO
	udm container/ou create --set name=gpo1
	udm container/ou create --set name=gpo2
	create_gpo GPO5 "$ldap_base" User 'HKCU\Environment' --client $WIN1
	create_gpo_on_server GPO4 "$ldap_base" Computer 'HKLM\Environment' $SLAVE --client $WIN1
	create_gpo_on_server GPO3 "$ldap_base" User 'HKCU\Environment' $BACKUP --client $WIN1
	create_gpo GPO1 "ou=gpo1,$ldap_base" User 'HKCU\Environment'
	create_gpo GPO2 "ou=gpo2,$ldap_base" Computer 'HKLM\Environment'
	udm users/user move --dn "uid=testuser05,cn=users,$ldap_base" --position "ou=gpo1,$ldap_base"
	udm computers/windows move --dn "cn=$win2012_name,cn=computers,$ldap_base" --position "ou=gpo2,$ldap_base"
	sleep 360 # wait for sysvol sync
	# reboot system to apply gpo's
	python shared-utils/ucs-winrm.py reboot --client $WIN1
	sleep 30
	#python shared-utils/ucs-winrm.py run-ps --cmd 'gpupdate /force' --client $WIN1  --credssp
	# Werden die GPOs ausgewertet?
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --client $WIN1 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --client $WIN1 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'GPO2' --computergpo 'Default Domain Policy'
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'testuser01' --userpwd "Univention.99" --client $WIN1 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'testuser05' --userpwd "Univention.99" --client $WIN1 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' --usergpo 'GPO1' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'
	# Vergleich /var/lib/samba/sysvol/$domainname/Policies auf DC Master und DC Backup mit dem DC Slave
	local sysvol="$(find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print $1}')"
	test $sysvol = "$(run_on_ucs_hosts $SLAVE "find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print \$1}'")"
	test $sysvol = "$(run_on_ucs_hosts $BACKUP "find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print \$1}'")"
	#test $sysvol = "$(run_on_ucs_hosts $SLAVE_RODC "find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print \$1}'")"

	# Freigaben

	# Login als Benutzer, Heimatverzeichnis sollte verbunden sein. Datei anlegen.
	run_on_ucs_hosts $MEMBER "! stat /home/testuser04"
	udm users/user modify  --dn "uid=testuser04,cn=users,$ldap_base" --set homedrive='M:' --set sambahome='\\ucs-slave\testuser04'
	python shared-utils/ucs-winrm.py logon-as --username testuser04 --userpwd 'Univention.99' --client $WIN1

	run_on_ucs_hosts $SLAVE "stat /home/testuser04"
	run_on_ucs_hosts $SLAVE "stat /home/testuser01"
	# Anlegen eines Shares auf dem DC Slave und auf dem Memberserver :DONE
	#   Sind die Shares vom Win7 und Win8.1 / W2012 Client erreichbar und verwendbar?
	#	Verschiedenen Optionen an Share testen (siehe Handbuch) DONE
	#	Funktioniert Schreib- und Lesezugriff DONE
	#	Rechtevergabe prüfen DONE (simuliert durch Zugriff mit anderen Benutzer)
	run_on_ucs_hosts $SLAVE "touch /home/testshare/test.txt"
	python shared-utils/ucs-winrm.py check-share --server ucs-slave --sharename "testshareSlave" --driveletter F --filename "test.txt" --username 'Administrator' --userpwd "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename test-admin01.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share testshareSlave
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename test-testuser01.txt --username 'testuser01' --userpwd "Univention.99" --share testshareSlave
	run_on_ucs_hosts $SLAVE "stat /home/testshare/test-admin01.txt"
	run_on_ucs_hosts $SLAVE "stat /home/testshare/test-testuser01.txt"
	#python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename testuser03-test.txt \
	#	--username 'testuser03' --userpwd "Univention.99" --share testshareSlave --debug 2>&1 | grep -i PermissionDenied
	python shared-utils/ucs-winrm.py create-share-file --server $MASTER --filename test-admin.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share Administrator
	stat /home/Administrator/test-admin.txt
	getfacl /home/Administrator/test-admin.txt | grep "Domain.*Admin"
	python shared-utils/ucs-winrm.py create-share-file --server ucs-master.sambatest.local --filename test-testuser02.txt --username 'testuser02' --userpwd "Univention.99" --share testuser02 --client $WIN1
	#stat /home/testuser02/test-testuser02.txt
	getfacl /home/testuser02/test-testuser02.txt | grep "Domain.*Users"
	# this should fail
	#python shared-utils/ucs-winrm.py create-share-file --server ucs-master.sambatest.local --filename test-testuser02.txt --username 'testuser02' --userpwd "Univention.99" \
	#	--share testshare --client $WIN1 --debug 2>&1 | grep -i PermissionDenied
	#python shared-utils/ucs-winrm.py create-share-file --server ucs-master.sambatest.local --filename test-testuser01.txt --username 'testuser01' --userpwd "Univention.99" \
	#	--share Administrator --client $WIN1 --debug 2>&1 | grep -i PermissionDenied
	# check windows acl's
	#  ACL-Vergabe unter Windows testen(rechte Maustaste/Eigenschaften.. Hinzufügen und Entfernen von ACLs) DONE
	#  Serverseitig: getfacl DONE
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $MASTER --filename test-testuser02.txt --username 'testuser02' --userpwd "Univention.99" \
		--share testuser02 --debug | grep "Group.*Domain Users"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $MASTER --filename test-admin.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" \
		--share Administrator --debug | grep "Group.*Domain Admins"
	# create files on samba and check share
	su testuser01 -c "touch /home/testuser01/newfile.txt"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $MASTER --filename newfile.txt --username 'testuser01' --userpwd "Univention.99" \
		--share testuser01 --debug | grep "Group.*Domain Users"
	su Administrator -c "touch /home/Administrator/newfile.txt"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $MASTER --filename newfile.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" \
		--share Administrator --debug | grep "Group.*Domain Admins"

	# printing
	test_printers

	# Im nächsten Schritt (Update) ein System kurzfristig noch auf UCS 4.3 lassen, 
	# um zwischendurch die DRS-Replikation zu testen (z.B. Benutzer anlegen und schauen ob das Objekt auf den alten System ankommt). OK (im cfg datei)
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
	# Windows-Heimatverzeichnis" am Benutzer auf \\memberserver\homes setzen, "Laufwerk für das Windows-Heimatverzeichnis" muss vermutlich auch gesetzt werden.
	# Login als Benutzer, Heimatverzeichnis sollte verbunden sein. Datei anlegen.
	#    Anmeldung als Testuser1 am Windows-Client
	# Zweiten/Neuen Windows-Client joinen (ggf. vorher Zeit manuell setzen, sonst zwei mal neu Booten, DNS record prüfen)
	for client in $WIN2; do
		python shared-utils/ucs-winrm.py domain-join --client $client --dnsserver "$MASTER" --domainuser "$ADMIN" --domainpassword "$ADMIN_PASSWORD"
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "testuser01" --domainpassword "Univention.99"
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "testuser02" --domainpassword "Univention.99"
	done
	python shared-utils/ucs-winrm.py logon-as --username testuser01 --userpwd 'Univention.99' --client $WIN1 
	#        Ist das Homeverzeichnis automatisch eingebunden?
	run_on_ucs_hosts $SLAVE "touch /home/testuser01/test.txt"
	python shared-utils/ucs-winrm.py check-share --server ucs-slave --sharename "testuser01" --driveletter G --filename "test.txt" --username 'testuser01' --userpwd "Univention.99" --client $WIN1
	#        Kann eine Datei dort angelegt werden?
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename test-user01.txt --username 'testuser01' --userpwd "Univention.99" --share testuser01 --client $WIN1
	#        Wurden die GPOs ausgewertet?
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'testuser01' --userpwd "Univention.99" --client $WIN2 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'
	#        Schreibzugriff auf share am Slave?
	python shared-utils/ucs-winrm.py check-share --server ucs-slave --sharename "testshareSlave" --driveletter Q --filename "test.txt" --username 'testuser01' --userpwd "Univention.99" --client $WIN1
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename testuser01.txt --username 'testuser01' --userpwd "Univention.99" --share testshareSlave --client $WIN1
	#        Passwort ändern am Windows-Client (per Alt-Ctrl-Del)
	#        Danach neues Passwort unter UCS mit "kinit testuser1" testen.
	#        Abmeldung des Testuser1 vom Windows-Client.
	# Unter UDM neuen Testuser2 anlegen, als Home-share "\\memberserver\homes" eintragen (z.B. auf Laufwerk Z:), gleiche Gruppe wie Testuser1. "Passwort bei nächster Anmeldung ändern" auswählen.
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
	# Anmeldung als Administrator am Windows-Client
	# Eine sichtbare Einstellung an den GPOs ändern
	# Eine neue GPO anlegen
	create_gpo GPO6 "$ldap_base" User 'HKCU\Environment' --client $WIN1
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

