#!/bin/bash

set -x
set -e

. product-tests/samba/utils.sh


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

# get windows client name
#create new user, shares and PDFprinter in master
udm users/user create --position "cn=users,dc=sambatest,dc=local" --set username="newuser01" --set firstname="Random" --set lastname="User" --set password="Univention.99"
udm groups/group modify --dn "cn=Domain Admins,cn=groups,dc=sambatest,dc=local" --append users="uid=newuser01,cn=users,dc=sambatest,dc=local"
udm shares/share create --position "cn=shares,dc=sambatest,dc=local" --set name="testshare" --set host="ucs-master.sambatest.local" --set path="/home/testshare"
udm shares/printer create --position "cn=printers,dc=sambatest,dc=local" --set name="Masterprinter" --set spoolHost=$(hostname -A) --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
	
python shared-utils/ucs-winrm.py domain-join --domain sambatest.local --dnsserver "$UCS" --domainuser "administrator" --domainpassword "$ADMIN_PASSWORD"
	
python shared-utils/ucs-winrm.py domain-user-validate-password --domainuser "Administrator" --domainpassword "$ADMIN_PASSWORD"
 #service smdb restart
 python shared-utils/ucs-winrm.py create-gpo --credssp --name NewGPO --comment "testing new GPO in domain"
python shared-utils/ucs-winrm.py link-gpo --name NewGPO --target "dc=sambatest,dc=local" --credssp
python shared-utils/ucs-winrm.py run-ps --credssp --cmd 'set-GPPrefRegistryValue -Name NewGPO -Context User -key "HKCU\Environment" -ValueName NewGPO -Type String -value NewGPO -Action Update'
sleep 150
  
#TODO A better check on client for applied GPOs
python shared-utils/ucs-winrm.py create-share-file --server $UCS --share "testshare" --filename "testfile.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD"
#echo "halli hallo" > /home/testshare/testfile.txt
#python shared-utils/ucs-winrm.py check-share --server $UCS --sharename "testshare" --filename "testfile.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD" --driveletter P
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

python shared-utils/ucs-winrm.py check-applied-gpos --client "$WINCLIENT" --username 'administrator' --userpwd "$ADMIN_PASSWORD" --usergpo 'Default Domain Policy' --usergpo 'NewGPO' --computergpo 'Default Domain Policy'
python shared-utils/ucs-winrm.py check-applied-gpos --client "$WINCLIENT" --username 'newuser01' --userpwd "Univention.99" --usergpo 'Default Domain Policy' --usergpo 'NewGPO' --computergpo 'Default Domain Policy'

python shared-utils/ucs-winrm.py setup-printer --printername Masterprinter --server "$UCS"
rpcclient  -UAdministrator%"$ADMIN_PASSWORD" localhost -c enumprinters
sleep 20
rpcclient  -UAdministrator%"$ADMIN_PASSWORD" localhost -c enumprinters

python shared-utils/ucs-winrm.py print-on-printer --printername Masterprinter --server "$UCS" --impersonate --run-as-user Administrator
stat /var/spool/cups-pdf/administrator/job_1-document.pdf
python shared-utils/ucs-winrm.py print-on-printer --printername Masterprinter --server "$UCS" --impersonate --run-as-user newuser01 --run-as-password "Univention.99"
stat /var/spool/cups-pdf/newuser01/job_2-document.pdf

#password change
python shared-utils/ucs-winrm.py change-user-password --domainuser newuser01 --userpassword "Univention123!"
	
python shared-utils/ucs-winrm.py run-ps --cmd hostname > WINCLIENTNAME
host $(cat WINCLIENTNAME | grep WIN | cut -c 1-15)

test -z "$(find /var -name core)"

echo "Success"
exit 0



