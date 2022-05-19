#!/bin/bash

set -e -x

check_trust () {
	# shellcheck source=utils.sh
	. product-tests/samba/utils.sh
	eval "$(ucr shell)"

	# create some ucs/windows users
	udm users/user create --set username=ucs1 --set lastname=ucs1 --set password=univention
	udm users/user create --set username=ucs2 --set lastname=ucs2 --set password=univention
	udm users/user create --set username=ucs3 --set lastname=ucs3 --set password=univention
	udm users/user create --set username=ucs-admin --set lastname=ucs-admin --set password=univention --append groups="cn=Domain Admins,cn=groups,$ldap_base"
	ucs-winrm create-user --user-password Univention@99  --user-name=win1
	ucs-winrm create-user --user-password Univention@99  --user-name=win2
	ucs-winrm create-user --user-password Univention@99  --user-name=win3

	# join clients into AD and UCS
	ucs-winrm domain-join --client "$WINCLIENT_AD" --dnsserver "$WINAD" --domainpassword "$WINAD_PASSWORD" --domainuser "$WINAD_ADMIN"
	# shellcheck disable=SC2154
	ucs-winrm domain-join --client "$WINCLIENT_UCS" --dnsserver "$UCS" --domain "$domainname" --domainpassword "$UCS_PASSWORD" --domainuser "$UCS_ADMIN"

	# create some GPO's
	# in AD
	create_gpo UserGPO1 "dc=adtest,dc=local" User 'HKCU\Environment'
	create_gpo MachineGPO1 "dc=adtest,dc=local" Computer 'HKLM\Environment'
	# in UCS
	create_gpo UCSUserGPO1 "$ldap_base" User 'HKCU\Environment' --client "$WINCLIENT_UCS" --domain "$domainname"
	create_gpo UCSMachineGPO1 "$ldap_base" Computer 'HKLM\Environment' --client "$WINCLIENT_UCS" --domain "$domainname"

	# check GPO's in AD and UCS
	ucs-winrm check-applied-gpos --username 'Administrator' --userpwd "$WINRM_PASSWORD" --usergpo 'UserGPO1' --computergpo 'MachineGPO1'
	ucs-winrm check-applied-gpos --client "$WINCLIENT_AD" --username 'win1' --userpwd "Univention@99" --usergpo 'UserGPO1' --computergpo 'MachineGPO1'
	ucs-winrm check-applied-gpos --client "$WINCLIENT_UCS" --username 'ucs1' --userpwd "univention" --usergpo UCSUserGPO1 --computergpo UCSMachineGPO1 --domain "$domainname"

	# dns forward in UCS
	local win_hostname win_fqdn ucs_ip ucs_fqdn
	# shellcheck disable=SC2016
	win_hostname="$(ucs-winrm run-ps  --cmd '$env:computername' --loglevel error | head -1 | tr -d '\r')"
	win_fqdn="$win_hostname.$WINRM_DOMAIN"
	ucs_ip=$(ucr get interfaces/eth0/address)
	ucs_fqdn=$(hostname -f)
cat > /etc/bind/local.conf.samba4 <<%EOR
zone "$WINRM_DOMAIN" {
type forward;
forwarders { $WINRM_CLIENT; };
};
%EOR
	service bind9 restart
	ping -c 2 "$win_fqdn"
	# and AD
	ucs-winrm run-ps --cmd "Add-DnsServerConditionalForwarderZone -Name $domainname -MasterServers $ucs_ip"
	ucs-winrm run-ps --cmd "Get-DnsServerZone"
	ucs-winrm run-ps --cmd "ping -n 2 $ucs_fqdn"

	# create trust
	samba-tool domain trust create "$WINRM_DOMAIN" -k no -U"${WINAD_NBDOM}\\${WINRM_USER}%${WINRM_PASSWORD}" --type=external
	samba-tool domain trust list
	wbinfo --check-secret --domain="$WINRM_DOMAIN"

	# add ucs domain users to remote group on winclient for later logon tests
	# shellcheck disable=SC2154
	ucs-winrm run-ps --client "$WINCLIENT_AD" --cmd "Add-LocalGroupMember -Group \"Remotedesktopbenutzer\" -Member \"$windows_domain\\Domain Users\""

	# ucs user in windows
	ucs-winrm domain-user-validate-password --domain "$WINRM_DOMAIN" --domainpassword univention --domainuser ucs1
	ucs-winrm domain-user-validate-password --domain "$WINRM_DOMAIN" --domainpassword wrong_password --domainuser ucs1 && return 1
	ucs-winrm domain-user-validate-password --domain INVALID_DOMAIN --domainpassword univention --domainuser ucs1 && return 1
	ucs-winrm domain-user-validate-password --domain "$WINRM_DOMAIN" --domainpassword univention --domainuser "ucs1@${domainname}"

	# new GPO's in AD
	create_gpo UserGPO2 "dc=adtest,dc=local" User 'HKCU\Environment'
	create_gpo MachineGPO2 "dc=adtest,dc=local" Computer 'HKLM\Environment'

	# new GPO's in UCS
	create_gpo UCSUserGPO2 "$ldap_base" User 'HKCU\Environment' --client "$WINCLIENT_UCS" --domain "$domainname"
	create_gpo UCSMachineGPO2 "$ldap_base" Computer 'HKLM\Environment' --client "$WINCLIENT_UCS" --domain "$domainname"

	# AD - check old and new GPO's in ad server and client, for windows and ucs user
	ucs-winrm check-applied-gpos --username 'Administrator' --userpwd "$WINRM_PASSWORD" \
		--usergpo 'UserGPO1' --usergpo 'UserGPO2' --computergpo 'MachineGPO1' --computergpo 'MachineGPO2'
	ucs-winrm check-applied-gpos --client "$WINCLIENT_AD" --username 'win1' --userpwd "Univention@99" \
		--usergpo 'UserGPO1' --usergpo 'UserGPO2' --computergpo 'MachineGPO1' --computergpo 'MachineGPO2'
	ucs-winrm check-applied-gpos --client "$WINCLIENT_AD" --username 'win2' --userpwd "Univention@99" \
		--usergpo 'UserGPO1' --usergpo 'UserGPO2' --computergpo 'MachineGPO1' --computergpo 'MachineGPO2'
	ucs-winrm check-applied-gpos --client "$WINCLIENT_AD" --username 'ucs1' --userpwd "univention" \
		--usergpo 'UserGPO1' --usergpo 'UserGPO2' --computergpo 'MachineGPO1' --computergpo 'MachineGPO2' --domain "$domainname"

	# UCS - check old and new GPO's for UCS user
	ucs-winrm check-applied-gpos --client "$WINCLIENT_UCS" --username 'ucs1' --userpwd 'univention' --domain "$domainname" \
		--usergpo UCSUserGPO1 --usergpo UCSUserGPO2 --computergpo UCSMachineGPO1 --computergpo UCSMachineGPO2
	ucs-winrm check-applied-gpos --client "$WINCLIENT_UCS" --username 'ucs2' --userpwd 'univention' --domain "$domainname" \
		--usergpo UCSUserGPO1 --usergpo UCSUserGPO2 --computergpo UCSMachineGPO1 --computergpo UCSMachineGPO2
}
