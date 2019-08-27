#!/bin/bash

set -x
set -e

test_printers () {
	set -x
	set -e

	. product-tests/samba/utils.sh
	# unstable, deactivated check later
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
	python shared-utils/ucs-winrm.py setup-printer --printername Memberprinter --server "$MEMBER" --client $WIN2016
	sleep 20
	python shared-utils/ucs-winrm.py print-on-printer --printername Memberprinter --server $MEMBER \
		--impersonate --run-as-user Administrator
	python shared-utils/ucs-winrm.py print-on-printer --printername Memberprinter --server "$MEMBER" \
		--impersonate --run-as-user newuser02 --run-as-password "Univention.99"
	python shared-utils/ucs-winrm.py print-on-printer --printername Memberprinter --server "$MEMBER" \
		--impersonate --run-as-user newuser02 --run-as-password "Univention.99" --client $WIN2016
	sleep 60
	run_on_ucs_hosts $MEMBER 'stat /var/spool/cups-pdf/administrator/job_1-document.pdf'
	run_on_ucs_hosts $MEMBER 'stat /var/spool/cups-pdf/newuser02/job_2-document.pdf'
	run_on_ucs_hosts $MEMBER 'stat /var/spool/cups-pdf/newuser02/job_3-document.pdf'
}

test_master () {

	# Es sollte eine größere UCS Domäne aufgesetzt werden, also DC Master, DC Backup, DC Slave und Memberserver
	# zusätzlich sollte ein RODC installiert werden, siehe Produkttests UCS 3.2 Samba 4#Read-Only-DC. Auf allen Systemen
	# sollte Samba4 (optional Printserver) im Installer ausgewählt werden. Auf dem Memberserver Samba 3. Done: see cfg file
	#
	# Die folgenden Client-Systeme sollten der UCS-Samba4 Domäne beitreten:
	#  Windows 8 TODO
	#  Windows 7 TODO
	#  Windows 2008R2 TODO
	#  Windows 2012
	#  Windows 10/2016

	set -x
	set -e

	. product-tests/samba/utils.sh

	eval "$(ucr shell ldap/base windows/domain)"

	export UCS_ROOT="root" UCS_PASSWORD="$ADMIN_PASSWORD"

	# Auf allen Systemen sollte einmal server-password-change aufgerufen werden
	run_on_ucs_hosts "$MASTER $BACKUP $SLAVE $MEMBER" "ucr set server/password/interval='0' && /usr/lib/univention-server/server_password_change"

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
		# check time, give it a 5min threshold
		wintime=$(python shared-utils/ucs-winrm.py run-ps --client $client --credssp --cmd 'Get-Date -Format t')
		wintime_epoch="$(date -u -d $wintime +%s)"
		ucstime_epoch="$(date -u +%s)"
		diff=$(($wintime_epoch-$ucstime_epoch))
		test ${diff#-} -lt 300
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "newuser01" --domainpassword "Univention.99"
		python shared-utils/ucs-winrm.py domain-user-validate-password --client $client --domainuser "newuser02" --domainpassword "Univention.99"
	done
	for ucs in ucs-master ucs-backup ucs-slave ucs-member; do
		python shared-utils/ucs-winrm.py run-ps --client $WIN2012 --cmd "nbtstat -a $ucs" # does not work with $WIN2016
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
	create_gpo GPO2 "ou=gpo2,$ldap_base" Computer 'HKLM\Environment'
	udm users/user move --dn "uid=newuser05,cn=users,$ldap_base" --position "ou=gpo1,$ldap_base"
	udm computers/windows move --dn "cn=$win2016_name,cn=computers,$ldap_base" --position "ou=gpo2,$ldap_base"
	sleep 360 # wait for sysvol sync
	# reboot system to apply gpo's
	python shared-utils/ucs-winrm.py reboot --client $WIN2016
	sleep 120
	python shared-utils/ucs-winrm.py run-ps --cmd 'gpupdate /force' --client $WIN2016  --credssp
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --client $WIN2012 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --client $WIN2016 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'GPO2' --computergpo 'Default Domain Policy'
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'newuser01' --userpwd "Univention.99" --client $WIN2012 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'newuser05' --userpwd "Univention.99" --client $WIN2012 \
		--usergpo 'GPO5' --usergpo 'GPO3' --usergpo 'Default Domain Policy' --usergpo 'GPO1' \
		--computergpo 'GPO4' --computergpo 'Default Domain Policy'
	# Vergleich /var/lib/samba/sysvol/$domainname/Policies auf DC Master und DC Backup mit dem DC Slave
	local sysvol="$(find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print $1}')"
	test $sysvol = "$(run_on_ucs_hosts $SLAVE "find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print \$1}'")"
	test $sysvol = "$(run_on_ucs_hosts $BACKUP "find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print \$1}'")"
	test $sysvol = "$(run_on_ucs_hosts $SLAVE_RODC "find /var/lib/samba/sysvol/sambatest.local/ | md5sum | awk '{print \$1}'")"

	# Freigaben

	# Windows-Heimatverzeichnis" am Benutzer auf \\memberserver\homes setzen, "Laufwerk für das Windows-Heimatverzeichnis" muss vermutlich auch gesetzt werden.
	# Login als Benutzer, Heimatverzeichnis sollte verbunden sein. Datei anlegen.
	run_on_ucs_hosts $MEMBER "! stat /home/newuser04"
	udm users/user modify  --dn "uid=newuser04,cn=users,$ldap_base" --set homedrive='M:' --set sambahome='\\ucs-member\newuser04'
	python shared-utils/ucs-winrm.py logon-as --username newuser04 --userpwd 'Univention.99'
	run_on_ucs_hosts $MEMBER "stat /home/newuser04"
	# Anlegen eines Shares auf dem DC Slave und auf dem Memberserver :DONE
	#   Sind die Shares vom Win7 und Win8.1 / W2012 Client erreichbar und verwendbar?
	#	Verschiedenen Optionen an Share testen (siehe Handbuch) DONE
	#	Funktioniert Schreib- und Lesezugriff DONE
	#	Rechtevergabe prüfen DONE (simuliert durch Zugriff mit anderen Benutzer)
	run_on_ucs_hosts $MEMBER "touch /home/testshare/test.txt"
	run_on_ucs_hosts $SLAVE "touch /home/testshare/test.txt"
	udm shares/share modify --dn "cn=testshareMember,cn=shares,dc=sambatest,dc=local" --set group=5000 --set directorymode=0770 --set sambaDirectoryMode=0770
	udm shares/share modify --dn "cn=testshareSlave,cn=shares,dc=sambatest,dc=local" --set group=5000 --set directorymode=0770 --set sambaDirectoryMode=0770
	udm shares/share modify --dn "cn=testshare,cn=shares,dc=sambatest,dc=local" --set group=5000 --set directorymode=0770 --set sambaDirectoryMode=0770
	python shared-utils/ucs-winrm.py check-share --server ucs-member --sharename "testshareMember" --driveletter R --filename "test.txt" --username 'Administrator' --userpwd "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py check-share --server ucs-slave --sharename "testshareSlave" --driveletter Q --filename "test.txt" --username 'Administrator' --userpwd "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py create-share-file --server ucs-member --filename test-admin01.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share testshareMember
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename test-admin01.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share testshareSlave
	python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention.99" --share testshareSlave
	run_on_ucs_hosts $MEMBER "stat /home/testshare/test-admin01.txt"
	run_on_ucs_hosts $SLAVE "stat /home/testshare/test-admin01.txt"
	run_on_ucs_hosts $SLAVE "stat /home/testshare/test-newuser01.txt"
	# check invalid write access
	! python shared-utils/ucs-winrm.py create-share-file --server ucs-slave --filename newuser03-test.txt --username 'newuser03' --userpwd "Univention.99" --share testshareSlave --debug
	! run_on_ucs_hosts $SLAVE "stat /home/testshare/newuser03-test.txt"
	python shared-utils/ucs-winrm.py create-share-file --server $MASTER --share "testshare" --filename "testfile.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py create-share-file --server $MASTER --filename test-admin.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share Administrator
	stat /home/Administrator/test-admin.txt
	getfacl /home/Administrator/test-admin.txt | grep "Domain.*Admin"
	python shared-utils/ucs-winrm.py create-share-file --server ucs-master.sambatest.local --filename test-newuser02.txt --username 'newuser02' --userpwd "Univention.99" --share newuser02 --client $WIN2016
	stat /home/newuser02/test-newuser02.txt
	getfacl /home/newuser02/test-newuser02.txt | grep "Domain.*Users"
	python shared-utils/ucs-winrm.py create-share-file --server ucs-master.sambatest.local --filename test-admin.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share testshare --client $WIN2016
	stat /home/testshare/test-admin.txt
	# this should fail
	python shared-utils/ucs-winrm.py create-share-file --server ucs-master.sambatest.local --filename test-newuser02.txt --username 'newuser02' --userpwd "Univention.99" \
		--share testshare --client $WIN2016 --debug 2>&1 | grep -i PermissionDenied
	python shared-utils/ucs-winrm.py create-share-file --server ucs-master.sambatest.local --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention.99" \
		--share Administrator --client $WIN2016 --debug 2>&1 | grep -i PermissionDenied
	# check windows acl's
	#  ACL-Vergabe unter Windows testen(rechte Maustaste/Eigenschaften.. Hinzufügen und Entfernen von ACLs) DONE
	#  Serverseitig: getfacl DONE
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $MASTER --filename test-newuser02.txt --username 'newuser02' --userpwd "Univention.99" \
		--share newuser02 --debug | grep "Group.*Domain Users"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $MASTER --filename test-admin.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" \
		--share Administrator --debug | grep "Group.*Domain Admins"
	# create files on samba and check share
	su newuser01 -c "touch /home/newuser01/newfile.txt"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $MASTER --filename newfile.txt --username 'newuser01' --userpwd "Univention.99" \
		--share newuser01 --debug | grep "Group.*Domain Users"
	su Administrator -c "touch /home/Administrator/newfile.txt"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $MASTER --filename newfile.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" \
		--share Administrator --debug | grep "Group.*Domain Admins"
	# können Samba-Freigaben auch als MSDFS-Freigaben exportiert werden ? TODO
	#   Dafür muss auf dem Samba-Server die UCR-Variable samba/enable-msdfs=yes gesetzt werden TODO
	# in UMC Gruppenberechtigungen vergeben (valid users = @Gruppe) und prüfen TODO

	# printing
	test_printers
	# printer GPO's TODO

	# Passworte

	# Änderung
	#  Kann man anschließend per kinit für den Benutzer auf UCS-Seite ein Ticket bekommen?
	#  Kann das Passwort per STRG-ALT-ENTF an den unterschiedlichen Windows-Systemen geändert werden? Not possible : simulated with LDAP pw change
	python shared-utils/ucs-winrm.py change-user-password --domainuser newuser01 --userpassword "Univention123!"
	sleep 30
	check_user_in_ucs newuser01 "Univention123!"
	python shared-utils/ucs-winrm.py logon-as --username newuser01 --userpwd "Univention123!" --client $WIN2012
	python shared-utils/ucs-winrm.py logon-as --username newuser01 --userpwd "Univention123!" --client $WIN2016
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
	python shared-utils/ucs-winrm.py run-ps --cmd "net user newuser01 /domain" --impersonate --run-as-user Administrator | grep $(date -d "+2 days" +"%d.%m.%Y")
	python shared-utils/ucs-winrm.py change-user-password --domainuser newuser01 --userpassword "Univ" --debug 2>&1 | grep Exception
	python shared-utils/ucs-winrm.py change-user-password --domainuser newuser01 --userpassword "Univ!"
	sleep 10
	check_user_in_ucs newuser01 "Univ!"
	python shared-utils/ucs-winrm.py change-user-password --domainuser newuser01 --userpassword 'Univention123!'
	sleep 10
	check_user_in_ucs newuser01 'Univention123!'
	udm users/user modify --dn "uid=newuser01,cn=users,$ldap_base" --set pwdChangeNextLogin=1
	sleep 10
	python shared-utils/ucs-winrm.py run-ps --cmd 'ls' --credssp --run-as-user newuser01 --run-as-password 'Univention123!' --client $WIN2012 --debug 2>&1 | grep AccessDenied
	python shared-utils/ucs-winrm.py run-ps --cmd 'ls' --credssp --run-as-user newuser01 --run-as-password 'Univention123!' --client $WIN2016 --debug 2>&1 | grep AccessDenied
	! samba-tool user password -U newuser01 --password='Univention123!' --newpassword='Univention123!'
	samba-tool user password -U newuser01 --password='Univention123!' --newpassword='Ünivention999!'
	python shared-utils/ucs-winrm.py logon-as --username newuser01 --userpwd "Ünivention999!" --client $WIN2012
	python shared-utils/ucs-winrm.py logon-as --username newuser01 --userpwd "Ünivention999!" --client $WIN2016
	check_user_in_ucs newuser01 "Ünivention999!"

	run_on_ucs_hosts "$MASTER $BACKUP $SLAVE $SLAVE_RODC" 'test -z "$(find /var -name core)"'

	# Kerberos Interoperabilität TODO

	# DC Failover TODO
}
