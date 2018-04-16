#!/bin/bash

set -x
set -e

#  done:  Der AD Takeover sollte mit Windows Server 2003 R2 und Windows Server 2008R2 getestet werden
#    Folgende Testumgebung wird jeweils benötigt:
#  done:      UCS-Domäne bestehend aus DC Master, und einem weiteren DC
#  done:      AD-Domäne im gleichen IPv4-Netz mit identischem Domännennamen, bestehend aus mindestens einem AD-DC und einem gejointen Windows 7 Client
#  done:  Hostnamen und IP-Adressen sollten domänenübergreifend einzigartig gewählt sein. done
#  done:  Beide Domänen sollten sich DNS-technisch zunächst nicht "sehen", d.h. im AD z.B. sollte nicht das UCS-DNS eingetragen sein.
#  done:  Im AD sollten 1500 Benutzern und 40 Gruppen angelegt werden. Die Benutzer sollten auf die Gruppen verteilt werden.
#  done:  Ein Benutzer sollte zusätzlich in die Gruppe "Domain Admins" / "Domänen Administratoren" aufgenommen werden.
#  done:  Im AD sollten jeweils eine GPO, mit Benutzer bzw. Windows-Client verknüpft werden, z.B.: done
#  done:      Benutzerkonfiguration -> Administrative Vorlagen -> Startmenü und Taskleiste -> Lautstärkesymbol entfernen -> aktivieren/Ok
#        Computerkonfiguration -> Administrative Vorlagen -> System/Anmelden -> Diese Programme bei der Benutzeranmeldung ausführen -> Auszuführende Elemente -> notepad -> aktivieren/Ok
#    Zusätzlich sollte etwas erkennbar an der AD Default-Domänen-Policy geändert werden, z.B. done
#  done:      Benutzerkonfiguration -> Administrative Vorlagen -> "Liste "Alle Programme" aus dem Menü Start entfernen"


prepare_ad_takeover_product_test () {

	. env_vars

	# Im AD sollten 1500 Benutzern und 40 Gruppen angelegt werden. Die Benutzer sollten auf die Gruppen verteilt werden.
	# in Benutzer sollte zusätzlich in die Gruppe "Domain Admins" / "Domänen Administratoren" aufgenommen werden.
	# Ein Benutzer sollte zusätzlich in die Gruppe "Domain Admins" / "Domänen Administratoren" aufgenommen werden.
	python shared-utils/ucs-winrm.py create-multiple-user --user-prefix benutzer --user-amount 1500 --user-password "Univention@99"
	python shared-utils/ucs-winrm.py create-multiple-adgroup --group-prefix gruppe --group-amount 40 --path "$LDAP_BASE"
	python shared-utils/ucs-winrm.py random-user-in-group
	python shared-utils/ucs-winrm.py create-ou --name TestContainer --path "$LDAP_BASE"
	python shared-utils/ucs-winrm.py add-user-to-domainadmin --username benutzer1
	python shared-utils/ucs-winrm.py add-user-to-domainadmin --username benutzer2

	# ein client vor dem takeover
	python shared-utils/ucs-winrm.py domain-join --dnsserver "$AD" --client "$WIN1" --user "$WIN1_ADMIN" --password "$WIN1_PASSWORD" --domainpassword "$AD_PASSWORD" --domainuser "$AD_ADMIN"

	# Im AD sollten jeweils eine GPO, mit Benutzer bzw. Windows-Client verknüpft werden
	python shared-utils/ucs-winrm.py create-gpo --name TestGPOUser --comment "testing new GPO in domain"
	python shared-utils/ucs-winrm.py run-ps --cmd \
		'set-GPPrefRegistryValue -Name TestGPOUser -Context User -key "HKCU\Environment" -ValueName TestGPOUser -Type String -value TestGPOUser -Action Update'
	python shared-utils/ucs-winrm.py link-gpo --name TestGPOUser --target "$LDAP_BASE"
	python shared-utils/ucs-winrm.py create-gpo --name TestGPOMachine --comment "testing new GPO in domain"
	python shared-utils/ucs-winrm.py run-ps --cmd \
		'set-GPPrefRegistryValue -Name TestGPOMachine -Context Computer -key "HKLM\Environment" -ValueName TestGPOMachine -Type String -value TestGPOMachine -Action Update'
	python shared-utils/ucs-winrm.py link-gpo --name TestGPOMachine --target "$LDAP_BASE"
	# Zusätzlich sollte etwas erkennbar an der AD Default-Domänen-Policy geändert werden
	python shared-utils/ucs-winrm.py run-ps --cmd \
		'set-GPPrefRegistryValue -Name "Default Domain Policy" -Context User -key "HKCU\Environment" -ValueName DefaultUserGPO -Type String -value TestGPOUser -Action Update'
	python shared-utils/ucs-winrm.py run-ps --cmd \
		'set-GPPrefRegistryValue -Name "Default Domain Policy" -Context Computer -key "HKLM\Environment" -ValueName DefaultMachineGPO -Type String -value TestMachineUser -Action Update'
}

#    Nach der erfolgreichen Durchführung des AD Takeover, wie in der Wiki-Dokumentation beschrieben, sollten folgende Punkte geprüft werden:
#  done via WinRM:      Login am übernommenen Windows-Client mit einem übernommenen Benutzer
#  done(server side)          GPOs müssen korrekt angewendet werden.
#            Passwortänderung muss funktionieren.
#  done:      Login am übernommenen Windows-Client als "Domänen\Administrator"
#            Gruppenrichtlinienverwaltung (GPMC) starten, neue GPO anlegen.
#            AD Benutzer&Computer: Neuen Benutzer anlegen.
#            Name des Windows-Clients ändern, dann reboot, Client-Anmeldung als neuer Benutzer: GPO Auswertung OK?
#        Login an UMC als Administrator
#  done:      Login an UMC als weiteres Mitglied der AD-Gruppe "Domain Admins" / "Domänen Administratoren".
#  done:    Anlegen eines neuen Benutzers per UMC, Anmeldung mit dem neuen Benutzer am Windows Client
#  done:      Joinen eines weiteren Windows Clients in die (UCS-)Domäne, Anmeldung als übernommener Benutzer



check_ad_takeover_product_test () {

	. env_vars
 #. ad-takeover.sh; check_GPO TestGPO

 #udm users/user modify --dn uid=benutzer1,cn=users,dc=adtakeover,dc=local --set password='univention' --set overridePWHistory=1 --set overridePWLength=1
 #udm users/user create --position "cn=users,dc=adtakeover,dc=local" --set username="newuser01" --set firstname="Random" --set lastname="User" --set password="Univention.99"
 #python shared-utils/ucs-winrm.py reboot
 #python shared-utils/ucs-winrm.py wait_for_client
 #LOCAL sleep 150

 #python shared-utils/ucs-winrm.py domain-join --domain adtakeover.local --dnsserver [master231_IP] --domainuser benutzer2 --domainpassword 'Univention@99'

 #. ad-takeover.sh; check_user_in_ucs user10
 #. ad-takeover.sh; check_user_in_ucs user1
 #. ad-takeover.sh; check_user_in_ucs benutzer1
 #. ad-takeover.sh; check_user_in_ucs benutzer1500

 #. ad-takeover.sh; check_user_in_winclient newuser01 'Univention.99'

 #. ad-takeover.sh; check_GPO_for_user TestGPO user1
 #. ad-takeover.sh; check_GPO_for_user TestGPO1 user10
 #. ad-takeover.sh; check_GPO_for_user TestGPO user1
 #. ad-takeover.sh; check_GPO_for_user TestGPO1 user10
#TODO A better check on client for applied GPOs
}

function check_all_user {
    for value in {1..10}
    do
        python shared-utils/ucs-winrm.py domain_user_validate_password --domain adtakeover.local --domainuser user$value --domainpassword Univention@$value
    done
}

function check_user_in_winclient {
 python shared-utils/ucs-winrm.py domain_user_validate_password --domain adtakeover.local --domainuser $1 --domainpassword $2
}

function check_user_in_ucs {
command=`udm users/user list --filter uid=$1`
if echo "$command" | grep -q "username"
then
    echo "user in DC found"
else
    echo "user in DC not found"
    exit 1
fi
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
