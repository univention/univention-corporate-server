#!/bin/bash

set -x
set -e

create_and_print_testfile () {
	python shared-utils/ucs-winrm.py run-ps --cmd "New-Item .\\printest.txt -ItemType file"
	python shared-utils/ucs-winrm.py run-ps --cmd "Add-Content .\\printest.txt 'print this in PDF'"
	python shared-utils/ucs-winrm.py run-ps --cmd "copy .\\printest.txt \\\\$(hostname)\SambaPDFprinter"
}

check_windows_client_sid () {
	local ucs_sid="$(univention-ldapsearch cn=$WINCLIENT_NAME sambaSID | sed -n 's/^sambaSID: //p')"
	local samba_sid="$(univention-s4search cn=$WINCLIENT_NAME objectSid | sed -n 's/^objectSid: //p')"
	test -n "$ucs_sid"
	test "$ucs_sid" = "$samba_sid"
}

run_singleserver_samba_test () {

	. env_vars
	# get windows client name
	local name="$(python shared-utils/ucs-winrm.py run-ps  --cmd '$env:computername' --loglevel error | head -1 | tr -d '\r')"
	echo "export WINCLIENT_NAME='$name'" >> ./env_vars
	. env_vars

	# Join des Clients
	python shared-utils/ucs-winrm.py domain-join --dnsserver "$UCS"  --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
	# Auf core prüfen: find /var -name core
	test -z "$(find /var -name core)"
	# SID des Windows-Clients in OpenLDAP prüfen Bug #39804
	check_windows_client_sid "$WINCLIENT"

	# In der UMC anlegen: Benutzer, Drucker, Dateifreigabe
	udm users/user create --position "cn=users,dc=sambatest,dc=local" --set username="newuser01" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	udm groups/group modify --dn "cn=Domain Admins,cn=groups,dc=sambatest,dc=local" --append users="uid=newuser01,cn=users,dc=sambatest,dc=local"
	udm shares/share create --position "cn=shares,dc=sambatest,dc=local" --set name="testshare" --set host="ucs-samba.sambatest.local" --set path="/home/testshare"
	udm shares/printer create --position "cn=printers,dc=sambatest,dc=local" --set name="printer1" --set spoolHost=$(hostname -A) --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
	sleep 15

	# Login als Domänen-Administrator am Windows-Client
	# TODO Netzwerkumgebung sichtbar?
	python shared-utils/ucs-winrm.py domain-user-validate-password --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
	python shared-utils/ucs-winrm.py domain-user-validate-password --domainuser "newuser01" --domainpassword "Univention.99"


	# Benutzer-Login am Windows7 Client
	# * Zugriff auf Homeshare, Datei anlegen
	# * Dateirechte aus Homeshare prüfen:
	#  ** Windows: Rechte Maustaste, Eigenschaften..
	#  ** Server: getfacl
	python shared-utils/ucs-winrm.py create-share-file --server $UCS --filename test-admin.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share Administrator
	stat /home/Administrator/test-admin.txt
	getfacl /home/Administrator/test-admin.txt | grep "Domain.*Admin"
	python shared-utils/ucs-winrm.py create-share-file --server $UCS --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention.99" --share newuser01
	stat /home/newuser01/test-newuser01.txt
	getfacl /home/newuser01/test-newuser01.txt | grep "Domain.*Users"
	python shared-utils/ucs-winrm.py create-share-file --server $UCS --filename test-admin.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share testshare
	stat /home/testshare/test-admin.txt
	# this should fail
	python shared-utils/ucs-winrm.py create-share-file --server $UCS --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention.99" --share testshare --debug 2>&1 | grep 'is denied.'
	python shared-utils/ucs-winrm.py create-share-file --server $UCS --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention.99" --share Administrator --debug 2>&1 | grep 'is denied.'
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $UCS --filename test-newuser01.txt --username 'newuser01' --userpwd "Univention.99" --share newuser01 --debug | grep "Group.*Domain Users"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $UCS --filename test-admin.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share Administrator --debug | grep "Group.*Domain Admins"
	# create files on samba and check share
	su newuser01 -c "touch /home/newuser01/newfile.txt"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $UCS --filename newfile.txt --username 'newuser01' --userpwd "Univention.99" --share newuser01 --debug | grep "Group.*Domain Users"
	su Administrator -c "touch /home/Administrator/newfile.txt"
	python shared-utils/ucs-winrm.py get-acl-for-share-file --server $UCS --filename newfile.txt --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --share Administrator --debug | grep "Group.*Domain Admins"
	# * GPO's
	python shared-utils/ucs-winrm.py create-gpo --credssp --name NewGPO --comment "testing new GPO in domain"
	python shared-utils/ucs-winrm.py link-gpo --name NewGPO --target "$LDAP_BASE" --credssp
	python shared-utils/ucs-winrm.py run-ps --credssp \
		--cmd 'set-GPPrefRegistryValue -Name NewGPO -Context User -key "HKCU\Environment" -ValueName NewGPO -Type String -value NewGPO -Action Update'
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'Administrator' --userpwd "$ADMIN_PASSWORD" --usergpo 'Default Domain Policy' --usergpo 'NewGPO' --computergpo 'Default Domain Policy'
	python shared-utils/ucs-winrm.py check-applied-gpos --username 'newuser01' --userpwd "Univention.99" --usergpo 'Default Domain Policy' --usergpo 'NewGPO' --computergpo 'Default Domain Policy'
	# * Zugriff auf Drucker
	# TODO install network printer
	##python shared-utils/ucs-winrm.py check-printer --server $UCS --printername "printer1" --username 'Administrator' --userpwd "$ADMIN_PASSWORD"
	##python shared-utils/ucs-winrm.py check-printer --server $UCS --printername "printer1" --username 'newuser01' --userpwd "Univention.99"
	# . samba-utils.sh; create_and_print_testfile
	# cat '/var/spool/cups-pdf/ANONYMOUS/job_1-smbprn_00000003_Remote_Downlevel_Document_.pdf'

	# host $windows_client muss die IPv4-Adresse liefern.
	nslookup "$WINCLIENT_NAME" | grep "$WINCLIENT"

	# IP-Adresse am Windows-Client ändern (statisch) DNS-Record auf dem Server überprüfen, DNS-Auflösung per host testen
	# TODO, geht nicht so einfach in ec2

	# Auf core prüfen: find /var -name core
	test -z "$(find /var -name core)"

	echo "Success"
	exit 0
}

