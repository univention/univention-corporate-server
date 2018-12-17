#!/bin/bash

set -x
set -e

test_master () {

	set -x
	set -e

	. product-tests/samba/utils.sh

	eval "$(ucr shell ldap/base windows/domain)"

	export UCS_ROOT="root" UCS_PASSWORD="$ADMIN_PASSWORD"

	# Auf allen Systemen sollte einmal server-password-change aufgerufen werden
	run_on_ucs_hosts "$MASTER $BACKUP $SLAVE $SLAVE_RODC $MEMBER" "ucr set server/password/interval='0' && /usr/lib/univention-server/server_password_change"

	# get windows client info/name
	python shared-utils/ucs-winrm.py run-ps --cmd ipconfig
	python shared-utils/ucs-winrm.py run-ps --cmd "(gwmi win32_operatingsystem).caption"

	# get hostname for check in dns of server from client
	local win2012_name="$(python shared-utils/ucs-winrm.py run-ps --client $WIN2012 --cmd '$env:computername' --loglevel error | head -1 | tr -d '\r')"
	local win2016_name="$(python shared-utils/ucs-winrm.py run-ps --client $WIN2016 --cmd '$env:computername' --loglevel error | head -1 | tr -d '\r')"
	test -n "$win2012_name"
	test -n "$win2016_name"

	# create new user, shares and PDFprinter in master
	udm users/user create --position "cn=users,$ldap_base" --set username="newuser01" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	udm users/user create --position "cn=users,$ldap_base" --set username="newuser02" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	udm users/user create --position "cn=users,$ldap_base" --set username="newuser03" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	udm users/user create --position "cn=users,$ldap_base" --set username="newuser04" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	udm users/user create --position "cn=users,$ldap_base" --set username="newuser05" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	udm groups/group modify --dn "cn=Domain Admins,cn=groups,dc=sambatest,dc=local" --append users="uid=newuser01,cn=users,dc=sambatest,dc=local"

	udm shares/share create --position "cn=shares,$ldap_base" --set name="testshare" --set host="ucs-master.sambatest.local" --set path="/home/testshare"
	udm shares/share create --position "cn=shares,$ldap_base" --set name="testshareMember" --set host="ucs-member.sambatest.local" --set path="/home/testshare"
	udm shares/share create --position "cn=shares,$ldap_base" --set name="testshareSlave" --set host="ucs-slave.sambatest.local" --set path="/home/testshare"

	udm shares/printer create --position "cn=printers,$ldap_base" --set name="Memberprinter" --set spoolHost="ucs-member.sambatest.local" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
	udm shares/printer create --position "cn=printers,$ldap_base" --set name="Masterprinter" --set spoolHost="ucs-master.sambatest.local" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
	udm shares/printer create --position "cn=printers,$ldap_base" --set name="Slaveprinter" --set spoolHost="ucs-slave.sambatest.local" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"

	# join windows clients
	# Uhrzeit prüfen: Sollte synchron zum DC Master sein (automatischer Abgleich per NTP)
	# Anmeldung auf dem System als Domänen-Benutzer (normales Mitglied von Domain Users)
	# Sind alle UCS-Samba-Server in der Netzwerkumgebung der Clients zu sehen? unter windows net computer list
	for client in $WIN2012 $WIN2016; do
		python shared-utils/ucs-winrm.py domain-join --client $client --dnsserver "$MASTER" --domainuser "$ADMIN" --domainpassword "$ADMIN_PASSWORD"
		python shared-utils/ucs-winrm.py run-ps --client $client --credssp --cmd 'Get-Date -Format t' > date
		wintime="$(sed -n 1p date | cut -c1-5)"
		ucstime="$(date -u +"%H:%M")"
		test "$wintime" = "$ucstime"
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "newuser01" --domainpassword "Univention.99"
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "newuser02" --domainpassword "Univention.99"
		for ucs in ucs-master ucs-backup ucs-slave ucs-member; do
			python shared-utils/ucs-winrm.py run-ps --client $client --cmd "nbtstat -a $ucs" | grep -i $ucs
			python shared-utils/ucs-winrm.py run-ps --client $client --cmd "nbtstat -a $ucs"
		done
	done

	# Alle DCs auf coredump prüfen: find /var -name core
	run_on_ucs_hosts "$MASTER $BACKUP $SLAVE $SLAVE_RODC" 'test -z "$(find /var -name core)"'

	# Read-Only-DC
    # Nach dem Join sollten auf dem RODC z.B. keine unicodePwd und supplementalCredentials repliziert sein.
	# Der folgende Aufruf sollte daher nur an dem Objekt des RODC selbst und an dem lokalen krbtgt_* Konto diese Passwortattribute finden:
    # Schreibzugriffe gegen den RODC sollten scheitern
	test 2 -eq $(run_on_ucs_hosts "$SLAVE_RODC" "ldbsearch -H /var/lib/samba/private/sam.ldb unicodePwd" | grep -i ^unicodePwd: | wc -l)
	test 2 -eq $(run_on_ucs_hosts "$SLAVE_RODC" "ldbsearch -H /var/lib/samba/private/sam.ldb supplementalcredentials" | grep -i ^supplementalcredentials: | wc -l)
	run_on_ucs_hosts "$SLAVE_RODC" '! samba-tool user add rodcuser1 Password.99'

	# GPO's

	# Per Gruppenrichtlineinverwaltung (GPMC) vom Client aus auf den DC Salve wechseln (Rechts-click auf Domäne, anderen DC auswählen)
	# Default Domain Policy anpassen und testen, ob sich diese korrekt auf Benutzer/Recher auswirkt, z.B.
	# Container/OU im Samba4-verzeichnisdienst anlegen, Benutzer-GPO (GPO1) anlegen und damit verknüpfen, Testbenutzer in den Container verschieben. GPO Beispiel:
	# Container/OU im Samba4-verzeichnisdienst anlegen, Rechner-GPO (GPO2) anlegen und damit verknüpfen, Test-Windows-client in den Container verschieben. GPO Beispiel:
	# Per Gruppenrichtlineinverwaltung (GPMC) vom Client aus auf den DC Backup wechseln (Rechts-click auf Domäne, anderen DC auswählen)
	udm container/ou create --set name=gpo1
	udm container/ou create --set name=gpo2
	create_gpo GPO5 "$ldap_base" User 'HKCU\Environment' --client $WIN2012
	create_gpo_on_server GPO4 "$ldap_base" Computer 'HKLM\Environment' $SLAVE --client $WIN2012
	create_gpo_on_server GPO3 "$ldap_base" User 'HKCU\Environment' $BACKUP --client $WIN2012
    create_gpo GPO1 "ou=gpo1,$ldap_base" User 'HKCU\Environment'
    create_gpo GPO2 "ou=gpo1,$ldap_base" Computer 'HKLM\Environment'
	udm users/user move --dn "uid=newuser05,cn=users,$ldap_base" --position "ou=gpo1,$ldap_base"
	udm computers/windows move --dn "cn=$win2016_name,cn=computers,$ldap_base" --position "ou=gpo2,$ldap_base"

	python shared-utils/ucs-winrm.py check-applied-gpos --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --client $WIN2012 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --client $WIN2016 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'GPO2' --computergpo 'Default Domain Policy'

	python shared-utils/ucs-winrm.py check-applied-gpos --username 'newuser01' --userpwd "Univention.99" \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'newuser05' --userpwd "Univention.99" \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' --usergpo 'GPO1' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'

	# Vergleich /var/lib/samba/sysvol/$domainname/Policies auf DC Master und DC Backup mit dem DC Slave
	local sysvol="$(find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print $1}')"
	test $sysvol = "$(run_on_ucs_hosts $SLAVE "find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print \$1}'")"
	test $sysvol = "$(run_on_ucs_hosts $BACKUP "find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print \$1}'")"
	test $sysvol = "$(run_on_ucs_hosts $SLAVE_RODC "find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print \$1}'")"

	# Freigaben

	python shared-utils/ucs-winrm.py create-share-file --server $UCS --share "testshare" --filename "testfile.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py create-share-file --server $UCS --filename test-admin.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share Administrator
	stat /home/Administrator/test-admin.txt
	getfacl /home/Administrator/test-admin.txt | grep "Domain.*Admin"
	python shared-utils/ucs-winrm.py create-share-file --server $UCS --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention.99" --share newuser01
	stat /home/newuser01/test-newuser01.txt
	getfacl /home/newuser01/test-newuser01.txt | grep "Domain.*Users"
	python shared-utils/ucs-winrm.py create-share-file --server $UCS --filename test-admin.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share testshare
	stat /home/testshare/test-admin.txt
	# this should fail
	python shared-utils/ucs-winrm.py create-share-file --server $UCS --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention.99" \
		--share testshare --debug 2>&1 | grep 'denied.'
	python shared-utils/ucs-winrm.py create-share-file --server $UCS --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention.99" \
		--share Administrator --debug 2>&1 | grep 'denied.'
	# check windows acl's
	#	    ACL-Vergabe unter Windows testen(rechte Maustaste/Eigenschaften.. Hinzufügen und Entfernen von ACLs) DONE
	#	    Serverseitig: getfacl DONE
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $UCS --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention.99" \
		--share newuser01 --debug | grep "Group.*Domain Users"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $UCS --filename test-admin.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" \
		--share Administrator --debug | grep "Group.*Domain Admins"
	# create files on samba and check share
	su newuser01 -c "touch /home/newuser01/newfile.txt"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $UCS --filename newfile.txt --username 'newuser01' --userpwd "Univention.99" \
		--share newuser01 --debug | grep "Group.*Domain Users"
	su Administrator -c "touch /home/Administrator/newfile.txt"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $UCS --filename newfile.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" \
		--share Administrator --debug | grep "Group.*Domain Admins"

	python shared-utils/ucs-winrm.py check-applied-gpos --client "$WINCLIENT" --username 'administrator' \
		--userpwd "$ADMIN_PASSWORD" --usergpo 'Default Domain Policy' --usergpo 'NewGPO' --computergpo 'Default Domain Policy'
	python shared-utils/ucs-winrm.py check-applied-gpos --client "$WINCLIENT" --username 'newuser01' \
		--userpwd "Univention.99" --usergpo 'Default Domain Policy' --usergpo 'NewGPO' --computergpo 'Default Domain Policy'

	#printertest network printer in master
	#	Zugriff als Domänen-Administrator vom Windowsclient aus DONE
	#	serverseitig einen Druckertreiber hinterlegen, am einfachsten von 32bit XP aus (Windows 7 ist ein bisschen anders, 64bit ist zusätzlich hakelig ).
	#	Verbinden eines Druckers als unpriviligierter Benutzer vom Windowsclient aus DONE
	#	Testdruck von wordpad aus auf den verbundenen Drucker DONE
	#    Druckerzugriff mit serverseitig hinterlegten Druckertreibern: DONE
	python shared-utils/ucs-winrm.py setup-printer --printername Masterprinter --server "$UCS"
	rpcclient  -UAdministrator%"$ADMIN_PASSWORD" localhost -c enumprinters
	sleep 20
	rpcclient  -UAdministrator%"$ADMIN_PASSWORD" localhost -c enumprinters
	python shared-utils/ucs-winrm.py print-on-printer --printername Masterprinter --server "$UCS" --impersonate --run-as-user Administrator
	sleep 20
	stat /var/spool/cups-pdf/administrator/job_1-document.pdf
	python shared-utils/ucs-winrm.py print-on-printer --printername Masterprinter --server "$UCS" --impersonate --run-as-user newuser01 --run-as-password "Univention.99"
	sleep 20
	stat /var/spool/cups-pdf/newuser01/job_2-document.pdf

	#    Kann man anschließend per kinit für den Benutzer auf UCS-Seite ein Ticket bekommen?
	#Samba Domänen Passwort Einstellungen:
	#password change
	#    Kann das Passwort per STRG-ALT-ENTF an den unterschiedlichen Windows-Systemen geändert werden? Not possible : simulated with LDAP pw change
	python shared-utils/ucs-winrm.py change-user-password --domainuser newuser01 --userpassword "Univention123!"

	#change pw policies
	#    In UDM am Samba Domänenobjekt folgende Einstellungen treffen
	#        Maximales Passwortalter: 2 Tage (wegen Bug #44226) DONE
	#        Passwort History: 2 (wegen Bug #46557) DONE
	#        Minimale Passwortlänge auf 5 Buchstaben setzen. DONE
	udm policies/pwhistory modify --dn 'cn=default-settings,cn=pwhistory,cn=users,cn=policies,dc=sambatest,dc=local' --set expiryInterval=2
	udm policies/pwhistory modify --dn 'cn=default-settings,cn=pwhistory,cn=users,cn=policies,dc=sambatest,dc=local' --set pwLength=5
	udm policies/pwhistory modify --dn 'cn=default-settings,cn=pwhistory,cn=users,cn=policies,dc=sambatest,dc=local' --set length=2
	samba-tool domain passwordsettings set --min-pwd-length=5 --max-pwd-age=2 --history-length=2
	sleep 150

	#python shared-utils/ucs-winrm.py run-ps --cmd hostname > WINCLIENTNAME
	#host $(cat WINCLIENTNAME | grep WIN | cut -c 1-15)

	test -z "$(find /var -name core)"

	# add share and printer to slave and member server
	# Windows-Heimatverzeichnis" am Benutzer auf \\memberserver\homes setzen, "Laufwerk für das Windows-Heimatverzeichnis" muss vermutlich auch gesetzt werden. TODO teilweise abgedeckt mit untere Fall
	#	Login als Benutzer, Heimatverzeichnis sollte verbunden sein. Datei anlegen. DONE: Shares on memberserver and slave are mounted and tested on Windowsclient
	#    Anlegen eines Shares auf dem DC Slave und auf dem Memberserver :DONE
	#	Anlegen eines Druckers auf dem DC Slave und auf dem Memberserver DONE

	# Check list
	#Es sollte eine größere UCS Domäne aufgesetzt werden, also DC Master, DC Backup, DC Slave und Memberserver zusätzlich sollte ein RODC installiert werden, siehe Produkttests UCS 3.2 Samba 4#Read-Only-DC. Auf allen Systemen sollte Samba4 (optional Printserver) im Installer ausgewählt werden. Auf dem Memberserver Samba 3. Done: see cfg file
	#Auf allen Systemen sollte einmal server-password-change aufgerufen werden Done: cfg file
	#
	#Alle DCs auf coredump prüfen: find /var -name core Done
	#Die folgenden Client-Systeme sollten der UCS-Samba4 Domäne beitreten:
	#Windows 8
	#Windows 7
	#Windows 2012 Done(Amazon has only this) cfg file
	#Windows 2008R2
	#Windows 10
	#
	#Es sollten die AD Tools auf einem Windows Client installiert werden: http://wiki.univention.de/index.php?title=UCS_3.0_Samba_4#Manage_users_with_Active_Directory_tools : As of now impossible beacuse WinRM cannot use AD Tools
	#(Achtung: "Administrator" ist nicht "MYDOM\Administrator"! Ersterer ist nur der lokale Administrator.).

	#GPO
	#Es sollten die Remote Administration Tools auf dem Windows Client installiert werden, siehe hier

	#SHARES
	#
	#    können Samba-Freigaben auch als MSDFS-Freigaben exportiert werden ? TODO
	#    Dafür muss auf dem Samba-Server die UCR-Variable samba/enable-msdfs=yes gesetzt werden TODO
	#
	#
	#
	#    In UMC Gruppenberechtigungen vergeben (valid users = @Gruppe) und prüfen TODO

	#PASSWORDS
	#Änderung

	#mount network share of slave and member server from windows client
	#    Sind die Shares vom Win7 und Win8.1 / W2012 Client erreichbar und verwendbar?
	#	Verschiedenen Optionen an Share testen (siehe Handbuch) DONE
	#	Funktioniert Schreib- und Lesezugriff DONE
	#	Rechtevergabe prüfen DONE (simuliert durch Zugriff mit anderen Benutzer)
	# give acces to DC Backup Hosts to share
	udm shares/share modify --dn "cn=testshareMember,cn=shares,dc=sambatest,dc=local" --set group=5005 --set directorymode=0770 --set sambaDirectoryMode=0770
	udm shares/share modify --dn "cn=testshareSlave,cn=shares,dc=sambatest,dc=local" --set group=5005 --set directorymode=0770 --set sambaDirectoryMode=0770
	python shared-utils/ucs-winrm.py check-share --server $MEMBER --sharename "testshareMember" --driveletter R --filename "test.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py check-share --server $SLAVE --sharename "testshareSlave" --driveletter Q --filename "test.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD"

	python shared-utils/ucs-winrm.py create-share-file --server $MEMBER --filename test-admin01.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" \
		--share testshareMember
	python shared-utils/ucs-winrm.py create-share-file --server $SLAVE --filename test-admin01.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" \
		--share testshareSlave

	python shared-utils/ucs-winrm.py create-share-file --server $MEMBER --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention123!" \
		--share testshareMember --debug 2>&1 | grep 'Exception'
	python shared-utils/ucs-winrm.py create-share-file --server $SLAVE --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention123!" \
		--share testshareSlave --debug 2>&1 | grep 'Exception'
	#map printer driver names to network printers
	python shared-utils/ucs-winrm.py setup-printer --printername Slaveprinter --server "$SLAVE"
	python shared-utils/ucs-winrm.py setup-printer --printername Memberprinter --server "$MEMBER"
	#    Druckerzugriff ohne serverseitige Druckertreiber DONE
	python shared-utils/ucs-winrm.py run-ps --cmd "Add-Printer -Connectionname \\\\$SLAVE\Slaveprinter" --impersonate --run-as-user Administrator
	python shared-utils/ucs-winrm.py run-ps --cmd "Add-Printer -Connectionname \\\\$MEMBER\Memberprinter" --impersonate --run-as-user Administrator
	sleep 20
	#test printer
	#	Testdruck von wordpad aus auf den verbundenen Drucker DONE simulated with Powershell commands
	python shared-utils/ucs-winrm.py print-on-printer --printername Memberprinter --server $MEMBER --impersonate --run-as-user Administrator
	python shared-utils/ucs-winrm.py print-on-printer --printername Slaveprinter --server $SLAVE --impersonate --run-as-user Administrator
	python shared-utils/ucs-winrm.py print-on-printer --printername Memberprinter --server "$MEMBER" --impersonate --run-as-user newuser01 --run-as-password "Univention123!"
	python shared-utils/ucs-winrm.py print-on-printer --printername Slaveprinter --server "$SLAVE" --impersonate --run-as-user newuser01 --run-as-password "Univention123!"
	#change pw after policiesw changes
	#    Mit Benutzer am Windows7-Client anmelden und Passwort auf "Ünivention123" ändern. Die Samba4/Heimdal-Passwortkomplexitätsprüfung sollte das akzeptieren. DONE
	#    Uhrzeit auf den UCS DCs eine Stunde vorstellen und neu booten. (Oder Zeit sinnvoll anders nutzen..) Simulated by fetching information from Samba DB and comparing with a date
	#    Benutzer-Konto Option "Passwort bei der nächsten Anmeldung ändern" im UDM wählen und an jedem Windows System testen, ob das Passwort geändert werden muss. Kann man jetzt wieder "Ünivention123" setzen? DONE
	python shared-utils/ucs-winrm.py change-user-password --domainuser newuser01 --userpassword "Univ!"
	python shared-utils/ucs-winrm.py change-user-password --domainuser newuser01 --userpassword "Univ" --debug 2>&1 | grep Exception
	python shared-utils/ucs-winrm.py change-user-password --domainuser newuser01 --userpassword "Univention123!"
	#check expiration date of PW
	#    Mit Benutzer am Windows7-Client anmelden -> Windows muss Passwortänderung verlangen. Passwort ändern: Man sollte nicht wieder das alte Passwort setzen können. Man sollte ein Passwort mit 5 Buchstaben setzen können. DONE
	python shared-utils/ucs-winrm.py run-ps --cmd "net user newuser01 /domain" --impersonate --run-as-user Administrator | grep $(date -d "+2 days" +"%d.%m.%Y")
}


test_slave () {
	set -e
	set -x
	stat /var/spool/cups-pdf/administrator/job_1-document.pdf
	stat /var/spool/cups-pdf/newuser01/job_2-document.pdf
}

test_backup() {
	set -e
	set -x
}

test_member () {
	set -e
	set -x
	stat /var/spool/cups-pdf/administrator/job_1-document.pdf
	stat /var/spool/cups-pdf/newuser01/job_2-document.pdf
}

# TODO
# drucken als unpriviligierter Benutzer DONE
