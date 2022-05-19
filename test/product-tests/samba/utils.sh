#!/bin/bash

set -e -x

ucs-winrm () {  # <args..>
	local image='docker.software-univention.de/ucs-winrm'
	docker run --rm -v /etc/localtime:/etc/localtime:ro -v "$HOME/.ucs-winrm.ini:/root/.ucs-winrm.ini:ro" "$image" "$@"
}

create_and_print_testfile () {
	ucs-winrm run-ps --cmd "New-Item .\\printest.txt -ItemType file"
	ucs-winrm run-ps --cmd "Add-Content .\\printest.txt 'print this in PDF'"
	ucs-winrm run-ps --cmd "copy .\\printest.txt \\\\$(hostname)\SambaPDFprinter"
}

check_windows_client_sid () {  # <name>
	local name="$1" ucs_sid samba_sid
	ucs_sid="$(univention-ldapsearch cn="$name" sambaSID | sed -n 's/^sambaSID: //p')"
	samba_sid="$(univention-s4search cn="$name" objectSid | sed -n 's/^objectSid: //p')"
	test -n "$ucs_sid"
	test "$ucs_sid" = "$samba_sid"
}

create_gpo () {  # <name> <ldap_base> <context> <key> [args..]
	local name="$1" ldap_base="$2" context="$3" key="$4"
	shift 4 || shift $#
	ucs-winrm create-gpo --credssp --name "$name" --comment "testing new GPO in domain" "$@"
	ucs-winrm link-gpo --name "$name" --target "$ldap_base" --credssp "$@"
	ucs-winrm run-ps --credssp --cmd "set-GPPrefRegistryValue -Name $name -Context $context -key $key -ValueName $name -Type String -value $name -Action Update" "$@"
}

create_gpo_on_server () {  # <name> <ldap_base> <context> <key> <server> [args..]
	local name="$1" ldap_base="$2" context="$3" key="$4" server="$5"
	shift 5 || shift $#
	ucs-winrm create-gpo-server --credssp --name "$name" --comment "testing new GPO in non-master" --server "$server" "$@"
	ucs-winrm run-ps --credssp --cmd "New-GPLink -Name \"$name\" -Target \"$ldap_base\" -order 1 -enforced yes -Server $server" "$@"
	ucs-winrm run-ps --credssp --cmd "set-GPPrefRegistryValue -Server $server -Name $name -Context $context -key $key -ValueName $name -Type String -value $name -Action Update" "$@"
}

check_user_in_ucs () {  # <username> <password>
	local username="$1" password="$2" binddn
	binddn="$(univention-ldapsearch uid="$username" dn | sed -ne 's|dn: ||p')"
	# nss/pam
	getent passwd "$username"
	su -c "exit" "$username"
	# kerberos
	echo -n "$password" > /tmp/pwdfile
	kinit --password-file=/tmp/pwdfile "$username"
	# ucs ldap
	univention-ldapsearch -D "$binddn" -w "$password" "uid=$username"
	# samba/ldap
	ldbsearch -U "${username}%${password}" -H ldap://127.0.0.1 "cn=$username"
	smbclient -U "${username}%${password}" "//$(hostname)/sysvol" -c exit
}

check_admin_umc () {  # <username> <password>
	local username="$1" password="$2" binddn
	binddn="$(univention-ldapsearch uid="$username" dn | sed -ne 's|dn: ||p')"
	umc-command -U "$username" -P "$password" udm/get -f users/user -l -o "$binddn"
}

check_user_in_group () {  # <username> <groupname>
	local username="$1" groupname="$2"
	if ! udm groups/group list --filter name="$groupname" | grep "$username"
	then
		echo 'user in group not found' >&2
		exit 1
	fi
}

run_on_ucs_hosts () {  # <IPs> <cmd>
	local ip
	for ip in $1  # IFS
	do
		sshpass -p "$UCS_PASSWORD" ssh -o StrictHostKeyChecking=no "$UCS_ROOT"@"$ip" "$2"
	done
}

assert_no_core_files () {
	find /var -name core -exec false {} +
}
