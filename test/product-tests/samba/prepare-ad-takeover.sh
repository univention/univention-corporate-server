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
prepare_ad_takeover () {

	set -x
	set -e

	. product-tests/samba/utils.sh
	eval "$(ucr shell ldap/base)"

	# Im AD sollten 1500 Benutzern und 40 Gruppen angelegt werden. Die Benutzer sollten auf die Gruppen verteilt werden.
	# in Benutzer sollte zusätzlich in die Gruppe "Domain Admins" / "Domänen Administratoren" aufgenommen werden.
	# Ein Benutzer sollte zusätzlich in die Gruppe "Domain Admins" / "Domänen Administratoren" aufgenommen werden.
	python shared-utils/ucs-winrm.py create-multiple-user --user-prefix benutzer --user-amount 1500 --user-password "Univention@99"
	python shared-utils/ucs-winrm.py create-multiple-adgroup --group-prefix gruppe --group-amount 40 --path "$ldap_base"
	python shared-utils/ucs-winrm.py add-modulo-user-in-group
	python shared-utils/ucs-winrm.py create-ou --name TestContainer --path "$ldap_base"
	python shared-utils/ucs-winrm.py add-user-to-domainadmin --username benutzer1
	python shared-utils/ucs-winrm.py add-user-to-domainadmin --username benutzer2

	# ein client vor dem takeover
	python shared-utils/ucs-winrm.py domain-join \
		--dnsserver "$AD" \
		--client "$WIN1" \
		--user "$WIN1_ADMIN" \
		--password "$WIN1_PASSWORD" \
		--domainpassword "$AD_PASSWORD" \
		--domainuser "$AD_ADMIN"

	# Im AD sollten jeweils eine GPO, mit Benutzer bzw. Windows-Client verknüpft werden
	python shared-utils/ucs-winrm.py create-gpo --name TestGPOUser --comment "testing new GPO in domain"
	python shared-utils/ucs-winrm.py run-ps --cmd \
		'set-GPPrefRegistryValue -Name TestGPOUser -Context User -key "HKCU\Environment" -ValueName TestGPOUser -Type String -value TestGPOUser -Action Update'
	python shared-utils/ucs-winrm.py link-gpo --name TestGPOUser --target "$ldap_base"

	python shared-utils/ucs-winrm.py create-gpo --name TestGPOMachine --comment "testing new GPO in domain"
	python shared-utils/ucs-winrm.py run-ps --cmd \
		'set-GPPrefRegistryValue -Name TestGPOMachine -Context Computer -key "HKLM\Environment" -ValueName TestGPOMachine -Type String -value TestGPOMachine -Action Update'
	python shared-utils/ucs-winrm.py link-gpo --name TestGPOMachine --target "$ldap_base"

	# Zusätzlich sollte etwas erkennbar an der AD Default-Domänen-Policy geändert werden
	python shared-utils/ucs-winrm.py run-ps --cmd \
		'set-GPPrefRegistryValue -Name "Default Domain Policy" -Context User -key "HKCU\Environment" -ValueName DefaultUserGPO -Type String -value TestGPOUser -Action Update'
	python shared-utils/ucs-winrm.py run-ps --cmd \
		'set-GPPrefRegistryValue -Name "Default Domain Policy" -Context Computer -key "HKLM\Environment" -ValueName DefaultMachineGPO -Type String -value TestMachineUser -Action Update'

	echo "Success"
}
