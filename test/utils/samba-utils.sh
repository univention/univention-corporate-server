#!/bin/bash

set -x
set -e


function create_gpo {
    samba-tool gpo create $1 -U $2 --password=$3
}

function link_gpo_to_container {
    gpo=$(samba-tool gpo listall | grep $1 -B 1 | grep GPO | grep -oE "[^ ]+$")
    samba-tool gpo setlink $2 $gpo -U $3 --password=$4
}

function check_user_in_winclient {
	python shared-utils/ucs-winrm.py domain-user-validate-password --domain sambatest.local --domainuser $1 --domainpassword $2
}

function create_and_print_testfile {
	 python shared-utils/ucs-winrm.py run-ps --cmd "New-Item .\\printest.txt -ItemType file"
	 python shared-utils/ucs-winrm.py run-ps --cmd "Add-Content .\\printest.txt 'print this in PDF'"
	 python shared-utils/ucs-winrm.py run-ps --cmd "copy .\\printest.txt \\\\$(hostname)\SambaPDFprinter"
}
function check_GPO {
	command=`samba-tool gpo listall`
	if echo "$command" | grep -q "$1"
	then
		echo "GPO found"
	else
		echo "GPO not found"
		exit 1
	fi
}

function check_GPO_for_user {
	command=`samba-tool gpo list $2`
	if  echo $command | grep -q "$1"
	then
		echo "GPO for user found"
	else
		echo "GPO for user not found"
		exit 1
	fi
}

function run_singleserver_sambatest {
	. env_vars
	#In der UMC anlegen: Benutzer, Drucker, Dateifreigabe OK
	 udm users/user create --position "cn=users,dc=sambatest,dc=local" --set username="newuser01" --set firstname="Random" --set lastname="User" --set password="Univention.99"
	 udm groups/group modify --dn "cn=Domain Admins,cn=groups,dc=sambatest,dc=local" --append users="uid=newuser01,cn=users,dc=sambatest,dc=local"
	 udm shares/share create --position "cn=shares,dc=sambatest,dc=local" --set name="testshare" --set host="ucs-samba.sambatest.local" --set path="/home/testshare"
	 udm shares/printer create --position "cn=printers,dc=sambatest,dc=local" --set name="SambaPDFprinter" --set spoolHost=$(hostname -A) --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
	#service smdb restart
	 create_gpo newgpo administrator univention
	 link_gpo_to_container newgpo "DC=sambatest,DC=local" administrator univention
	#Join des Clients OK
	#Login als Domänen-Administrator am Windows7-Client: windows version ist server 2012 OK
	 python shared-utils/ucs-winrm.py domain-join-ucs --domain sambatest.local --dnsserver "$UCS" --client "$WINCLIENT" --user "Administrator" --password "$WINCLIENT_PASSWORD" --domainuser "administrator" --domainpassword "univention"
	 sleep 150
	 check_user_in_winclient newuser01 'Univention.99'
	 check_GPO_for_user newgpo newuser01
	#TODO A better check on client for applied GPOs
	#UCS Master DC und Shares in Netzwerkumgebung sichtbar? ok
	 python shared-utils/ucs-winrm.py create-share-file --server $UCS --filename testdir --username 'administrator' --userpwd 'univention'
	 echo "halli hallo" > /home/testshare/testdir/test.txt
	 python shared-utils/ucs-winrm.py check-share --server $UCS --driveletter P --sharename testshare --filename "testdir\\test.txt" --username 'administrator' --userpwd 'univention'
	
	#Verbinden des Druckers ok
	 python shared-utils/ucs-winrm.py check-printer --server $UCS --printername "SambaPDFprinter" --username 'administrator' --userpwd 'univention'
	#Zugriff auf Drucker ok
	 . samba-utils.sh; create_and_print_testfile
	
	 python shared-utils/ucs-winrm.py check-applied-gpos --client "$WINCLIENT" --username 'administrator' --userpwd "univention" --usergpo 'Default Domain Policy' --usergpo 'newgpo' --computergpo 'Default Domain Policy'
	 python shared-utils/ucs-winrm.py check-applied-gpos --client "$WINCLIENT" --username 'newuser01' --userpwd "Univention.99" --usergpo 'Default Domain Policy' --usergpo 'newgpo' --computergpo 'Default Domain Policy'
	 cat '/var/spool/cups-pdf/ANONYMOUS/job_1-smbprn_00000003_Remote_Downlevel_Document_.pdf' 
	
	#host $windows_client ok 
	#muss die IPv4-Adresse liefern. ok
	 python shared-utils/ucs-winrm.py run-ps --cmd hostname > WINCLIENTNAME
	 host $(cat WINCLIENTNAME | grep WIN | cut -c 1-15)
	
	#TODO/not possible yet
    	#Auf core prüfen: find /var -name core
	#SID des Windows-Clients in OpenLDAP prüfen Bug #39804
	#Benutzer-Login am Windows7 Client
	#    Dateirechte aus Homeshare prüfen:
	#        Windows: Rechte Maustaste, Eigenschaften..
	#        Server: getfacl
	#Auf core prüfen
	#IP-Adresse am Windows-Client ändern (statisch)
	#    DNS-Record auf dem Server überprüfen, DNS-Auflösung per host testen.
	#Auf core prüfen
}

