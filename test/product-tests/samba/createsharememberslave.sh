#!/bin/bash

set -x
set -e

#add share and printer to slave and member server
#Windows-Heimatverzeichnis" am Benutzer auf \\memberserver\homes setzen, "Laufwerk für das Windows-Heimatverzeichnis" muss vermutlich auch gesetzt werden. TODO teilweise abgedeckt mit untere Fall
#	Login als Benutzer, Heimatverzeichnis sollte verbunden sein. Datei anlegen. DONE: Shares on memberserver and slave are mounted and tested on Windowsclient
#    Anlegen eines Shares auf dem DC Slave und auf dem Memberserver :DONE
#	Anlegen eines Druckers auf dem DC Slave und auf dem Memberserver DONE
udm shares/printer create --position "cn=printers,dc=sambatest,dc=local" --set name="Memberprinter" --set spoolHost="ucs-member.sambatest.local" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
udm shares/share create --position "cn=shares,dc=sambatest,dc=local" --set name="testshareMember" --set host="ucs-member.sambatest.local" --set path="/home/testshare"
udm shares/printer create --position "cn=printers,dc=sambatest,dc=local" --set name="Slaveprinter" --set spoolHost="ucs-slave.sambatest.local" --set uri="cups-pdf:/" --set model="cups-pdf/CUPS-PDF.ppd"
udm shares/share create --position "cn=shares,dc=sambatest,dc=local" --set name="testshareSlave" --set host="ucs-slave.sambatest.local" --set path="/home/testshare"
#create gpo on Backup to check if change of DC is possible
#    Per Gruppenrichtlineinverwaltung (GPMC) vom Client aus auf den DC Salve wechseln (Rechts-click auf Domäne, anderen DC auswählen). DONE: simulated by creating a new GPO with Slave as DC
python shared-utils/ucs-winrm.py create-gpo-server --credssp --name NewGPOinSlave --comment "testing new GPO in domain" --server $SLAVE
python shared-utils/ucs-winrm.py link-gpo --name NewGPOinSlave --target "dc=sambatest,dc=local" --credssp
#	Per Gruppenrichtlineinverwaltung (GPMC) vom Client aus auf den DC Backup wechseln (Rechts-click auf Domäne, anderen DC auswählen) und dort z.B. die Benutzer-Richtlinie anpassen (z.B. einfach Lautstärkesymbol entfernen -> deaktivieren/Ok). Es sollte keine Fehlermeldung kommen. DONE : simulated by creating GPO with Backup as DC
python shared-utils/ucs-winrm.py create-gpo-server --credssp --name NewGPOinBackup --comment "testing new GPO in domain" --server $BACKUP
python shared-utils/ucs-winrm.py link-gpo --name NewGPOinBackup --target "dc=sambatest,dc=local" --credssp
