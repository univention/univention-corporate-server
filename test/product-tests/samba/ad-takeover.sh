#!/bin/bash

set -x
set -e

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

check_user_in_ucs () {
	local username="$1"
	local password="$2"
	local binddn="$(univention-ldapsearch uid="$username" dn | sed -ne 's|dn: ||p')"
	# nss/pam
	getent passwd | grep -w "$username"
	su "$username" -c "exit"
	# kerberos
	echo "$password" > /tmp/pwdfile
	kinit --password-file=/tmp/pwdfile $1
	# ucs ldap
	univention-ldapsearch -D "$binddn" -w "$password" "uid=$username"
	# samba/ldap
	ldbsearch -U "$username"%"$password" -H ldap://127.0.0.1 "cn=$username"
	smbclient -U "$username"%"$password" //$(hostname)/sysvol -c exit
}

check_admin_umc () {
	local username="$1"
	local password="$2"
	local binddn="$(univention-ldapsearch uid="$username" dn | sed -ne 's|dn: ||p')"
	umc-command -U "$username" -P "$password" udm/get -f users/user -l -o "$binddn"
}

check_user_in_group () {
	local username="$1"
	local groupname="$2"
	udm groups/group list --filter name="$groupname" | grep "$username"
	local exitcode=$?
	if [ "$exitcode" -ne 0 ]; then
		printf '%s\n' 'user in group not found' >&2
		exit 1
	fi
}

. product-tests/samba/utils.sh
eval "$(ucr shell ldap/base)"

# Bug 46858 (missing samba restart) -> TODO
/etc/init.d/samba restart
sleep 20

# Login am übernommenen Windows-Client mit einem übernommenen Benutzer
# GPOs müssen korrekt angewendet werden.
# Login am übernommenen Windows-Client als "Domänen\Administrator"
python shared-utils/ucs-winrm.py check-applied-gpos --client "$WIN1" --username 'Administrator' --userpwd "$AD_PASSWORD" \
	--usergpo 'TestGPOUser' --usergpo 'Default Domain Policy' --computergpo 'TestGPOMachine' --computergpo 'Default Domain Policy'
for user in 1 3 150 1000 1500; do
	python shared-utils/ucs-winrm.py check-applied-gpos --client "$WIN1" --username "benutzer$user" --userpwd 'Univention@99' \
	--usergpo 'TestGPOUser' --usergpo 'Default Domain Policy'
	check_user_in_ucs "benutzer$user" "Univention@99"
done
for i in $(seq 1 40); do
	udm groups/group list --filter name="gruppe$i" | grep "^DN: "
done
for i in $(seq 1 1500); do
	udm users/user list --filter username="benutzer$i" | grep "^DN: "
	groupindex=$(($i % 40 + 1))
	check_user_in_group "benutzer$i" "gruppe$groupindex"
done
# TODO check group membership

# Passwortänderung muss funktionieren
new_password='üUnivention@90809098798'
python shared-utils/ucs-winrm.py change-user-password --domainuser benutzer11 --userpassword "$new_password" --client "$WIN1"
python shared-utils/ucs-winrm.py domain-user-validate-password --domainuser benutzer11 --domainpassword "$new_password" --client "$WIN1"
check_user_in_ucs benutzer11 "$new_password"

# Gruppenrichtlinienverwaltung (GPMC) starten, neue GPO anlegen.
# Name des Windows-Clients ändern, dann reboot
python shared-utils/ucs-winrm.py create-gpo --name NewGPO --comment "testing new GPO in domain" --client "$WIN1" --credssp
python shared-utils/ucs-winrm.py link-gpo --name NewGPO --target "$ldap_base" --client "$WIN1" --credssp
python shared-utils/ucs-winrm.py run-ps --client "$WIN1" --credssp \
	--cmd 'set-GPPrefRegistryValue -Name NewGPO -Context User -key "HKCU\Environment" -ValueName NewGPO -Type String -value NewGPO -Action Update' --client "$WIN1" --credssp
samba-tool gpo listall | grep NewGPO
python shared-utils/ucs-winrm.py rename-computer --name mycom --domainmode --credssp --client "$WIN1"
# AD Benutzer&Computer: Neuen Benutzer anlegen.
# Client-Anmeldung als neuer Benutzer: GPO Auswertung OK?
python shared-utils/ucs-winrm.py create-user --user-name "new1" --directory-entry --client "$WIN1" --credssp --user-password "Univention@99"
python shared-utils/ucs-winrm.py check-applied-gpos --client "$WIN1" --username 'new1' --userpwd "Univention@99" \
	--usergpo 'TestGPOUser' --usergpo 'Default Domain Policy' --usergpo 'NewGPO' \
	--computergpo 'TestGPOMachine' --computergpo 'Default Domain Policy'

# Login an UMC als weiteres Mitglied der AD-Gruppe "Domain Admins" / "Domänen Administratoren".
check_admin_umc benutzer1 "Univention@99"
check_admin_umc benutzer2 "Univention@99"

# Anlegen eines neuen Benutzers per UMC, Anmeldung mit dem neuen Benutzer am Windows Client
udm users/user create --position "cn=users,dc=adtakeover,dc=local" --set username="newuser01" --set firstname="Random" --set lastname="User" --set password="Univention.99"
python shared-utils/ucs-winrm.py check-applied-gpos --client "$WIN1" --username 'newuser01' --userpwd "Univention.99" \
	--usergpo 'TestGPOUser' --usergpo 'Default Domain Policy' --usergpo 'NewGPO' \
	--computergpo 'TestGPOMachine' --computergpo 'Default Domain Policy'

# Joinen eines weiteren Windows Clients in die (UCS-)Domäne
python shared-utils/ucs-winrm.py domain-join --dnsserver "$UCS" --client "$WIN2" --user "$WIN2_ADMIN" --password "$WIN2_PASSWORD" --domainpassword "$AD_PASSWORD" --domainuser "$AD_ADMIN"
# Anmeldung als übernommener Benutzer, GPO's?
python shared-utils/ucs-winrm.py check-applied-gpos --client "$WIN2" --username 'benutzer13' --userpwd "Univention@99" \
	--usergpo 'TestGPOUser' --usergpo 'Default Domain Policy' --usergpo 'NewGPO' \
	--computergpo 'TestGPOMachine' --computergpo 'Default Domain Policy'

echo "Success"

exit 0
