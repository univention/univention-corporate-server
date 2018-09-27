#!/bin/bash

set -x
set -e

#mount network share of slave and member server from windows client
#    Sind die Shares vom Win7 und Win8.1 / W2012 Client erreichbar und verwendbar?
#	Verschiedenen Optionen an Share testen (siehe Handbuch) DONE
#	Funktioniert Schreib- und Lesezugriff DONE
#	Rechtevergabe prüfen TODO
python shared-utils/ucs-winrm.py check-share --server $MEMBER --sharename "testshareMember" --driveletter R --filename "test.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD"
python shared-utils/ucs-winrm.py check-share --server $SLAVE --sharename "testshareSlave" --driveletter Q --filename "test.txt" --username 'administrator' --userpwd "$ADMIN_PASSWORD"
#map printer driver names to network printers
#python shared-utils/ucs-winrm.py setup-printer --printername Slaveprinter --server "$SLAVE"
#python shared-utils/ucs-winrm.py setup-printer --printername Memberprinter --server "$MEMBER"
#    Druckerzugriff ohne serverseitige Druckertreiber DONE
python shared-utils/ucs-winrm.py run-ps --cmd "Add-Printer -Connectionname \\\\$SLAVE\Slaveprinter" --impersonate --run-as-user Administrator
python shared-utils/ucs-winrm.py run-ps --cmd "Add-Printer -Connectionname \\\\$MEMBER\Memberprinter" --impersonate --run-as-user Administrator
sleep 20
#test printer
#	Testdruck von wordpad aus auf den verbundenen Drucker DONE simulated with Powershell commands
python shared-utils/ucs-winrm.py print-on-printer --printername Memberprinter --server $MEMBER --impersonate --run-as-user Administrator 
python shared-utils/ucs-winrm.py print-on-printer --printername Slaveprinter --server $SLAVE --impersonate --run-as-user Administrator
#check sysvol of backup and slave
#    SYSVOL-Replikation nach >=(2 mal 5) Minuten
#	Vergleich /var/lib/samba/sysvol/$domainname/Policies auf DC Master und DC Backup mit dem DC Slave. DONE
sshpass -p "$ADMIN_PASSWORD" rsync -ne ssh /var/lib/samba/sysvol/$WINRM_DOMAIN/Policies root@$SLAVE:/var/lib/samba/sysvol/$WINRM_DOMAIN/Policies
sshpass -p "$ADMIN_PASSWORD" rsync -ne ssh /var/lib/samba/sysvol/$WINRM_DOMAIN/Policies root@$BACKUP:/var/lib/samba/sysvol/$WINRM_DOMAIN/Policies
#Sind alle UCS-Samba-Server in der Netzwerkumgebung der Clients zu sehen?
python shared-utils/ucs-winrm.py run-ps --cmd "ping ucs-master" --impersonate --run-as-user Administrator
python shared-utils/ucs-winrm.py run-ps --cmd "ping ucs-slave" --impersonate --run-as-user Administrator
python shared-utils/ucs-winrm.py run-ps --cmd "ping ucs-backup" --impersonate --run-as-user Administrator
python shared-utils/ucs-winrm.py run-ps --cmd "ping ucs-member" --impersonate --run-as-user Administrator
samba-tool ntacl sysvolreset || true
