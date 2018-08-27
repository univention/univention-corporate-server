#!/bin/bash

set -x
set -e

create_and_print_testfile () {
	python shared-utils/ucs-winrm.py run-ps --cmd "New-Item .\\printest.txt -ItemType file"
	python shared-utils/ucs-winrm.py run-ps --cmd "Add-Content .\\printest.txt 'print this in PDF'"
	python shared-utils/ucs-winrm.py run-ps --cmd "copy .\\printest.txt \\\\$(hostname)\SambaPDFprinter"
}

check_windows_client_sid () {
	local ucs_sid="$(univention-ldapsearch cn=$WINCLIENT_NAME sambaSID | sed -n 's/^sambaSID: //p')"
	local samba_sid="$(univention-s4search cn=$WINCLIENT_NAME objectSid | sed -n 's/^objectSid: //p')"
	test -n "$ucs_sid"
	test "$ucs_sid" = "$samba_sid"
}

create_gpo () {
	local name=$1
	local ldap_base="$2"
	local context="$3"
	local key="$4"
	python shared-utils/ucs-winrm.py create-gpo --credssp --name "$name" --comment "testing new GPO in domain"
	python shared-utils/ucs-winrm.py link-gpo --name "$name" --target "$ldap_base" --credssp
	python shared-utils/ucs-winrm.py run-ps --credssp \
    	--cmd "set-GPPrefRegistryValue -Name $name -Context $context -key $key -ValueName "$name" -Type String -value "$name" -Action Update"
}
