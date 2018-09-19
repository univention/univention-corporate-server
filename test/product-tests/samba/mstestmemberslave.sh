#!/bin/bash

set -x
set -e

#mount network share of slave and member server from windows client
python shared-utils/ucs-winrm.py check-share --server $MEMBER --sharename "testshareMember" --driveletter R --filename "test.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD"
python shared-utils/ucs-winrm.py check-share --server $SLAVE --sharename "testshareSlave" --driveletter Q --filename "test.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD"
#map printer driver names to network printers
#python shared-utils/ucs-winrm.py setup-printer --printername Slaveprinter --server "$SLAVE"
#python shared-utils/ucs-winrm.py setup-printer --printername Memberprinter --server "$MEMBER"
python shared-utils/ucs-winrm.py run-ps --cmd "Add-Printer -Connectionname \\\\$SLAVE\Slaveprinter" --impersonate --run-as-user Administrator
python shared-utils/ucs-winrm.py run-ps --cmd "Add-Printer -Connectionname \\\\$MEMBER\Memberprinter" --impersonate --run-as-user Administrator
sleep 20
#test printer
python shared-utils/ucs-winrm.py print-on-printer --printername Memberprinter --server $MEMBER --impersonate --run-as-user Administrator 
python shared-utils/ucs-winrm.py print-on-printer --printername Slaveprinter --server $SLAVE --impersonate --run-as-user Administrator
#check sysvol of backup and slave
sshpass -p "$ADMIN_PASSWORD" rsync -ne ssh /var/lib/samba/sysvol/$WINRM_DOMAIN/Policies root@$SLAVE:/var/lib/samba/sysvol/$WINRM_DOMAIN/Policies
sshpass -p "$ADMIN_PASSWORD" rsync -ne ssh /var/lib/samba/sysvol/$WINRM_DOMAIN/Policies root@$BACKUP:/var/lib/samba/sysvol/$WINRM_DOMAIN/Policies
samba-tool ntacl sysvolreset || true
