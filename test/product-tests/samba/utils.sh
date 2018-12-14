#!/bin/bash

set -x
set -e

create_and_print_testfile () {
	python shared-utils/ucs-winrm.py run-ps --cmd "New-Item .\\printest.txt -ItemType file"
	python shared-utils/ucs-winrm.py run-ps --cmd "Add-Content .\\printest.txt 'print this in PDF'"
	python shared-utils/ucs-winrm.py run-ps --cmd "copy .\\printest.txt \\\\$(hostname)\SambaPDFprinter"
}

check_windows_client_sid () {
	local name="$1"
	local ucs_sid="$(univention-ldapsearch cn="$name" sambaSID | sed -n 's/^sambaSID: //p')"
	local samba_sid="$(univention-s4search cn="$name" objectSid | sed -n 's/^objectSid: //p')"
	test -n "$ucs_sid"
	test "$ucs_sid" = "$samba_sid"
}

create_gpo () {
	local name="$1"; shift
	local ldap_base="$1"; shift
	local context="$1"; shift
	local key="$1"; shift
	python shared-utils/ucs-winrm.py create-gpo --credssp --name "$name" --comment "testing new GPO in domain" "$@"
	python shared-utils/ucs-winrm.py link-gpo --name "$name" --target "$ldap_base" --credssp "$@"
	python shared-utils/ucs-winrm.py run-ps --credssp --cmd "set-GPPrefRegistryValue -Name $name -Context $context -key $key -ValueName "$name" -Type String -value "$name" -Action Update" "$@"
}

create_gpo_on_server () {
	local name="$1"; shift
	local ldap_base="$1"; shift
	local context="$1"; shift
	local key="$1"; shift
	local server="$1"; shift
	python shared-utils/ucs-winrm.py create-gpo-server --credssp --name "$name" --comment "testing new GPO in non-master" --server $server "$@"
	python shared-utils/ucs-winrm.py run-ps --credssp --cmd "New-GPLink -Name \"$name\" -Target \"$ldap_base\" -order 1 -enforced yes -Server $server" "$@"
	python shared-utils/ucs-winrm.py run-ps --credssp --cmd "set-GPPrefRegistryValue -Server $server -Name $name -Context $context -key $key -ValueName $name -Type String -value $name -Action Update" "$@"
}

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

run_on_ucs_hosts () {
	for ip in $1; do
		sshpass -p "$UCS_PASSWORD" ssh -o StrictHostKeyChecking=no "$UCS_ROOT"@"$ip" "$2"
	done
}
