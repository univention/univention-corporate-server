#!/bin/bash

set -x
set -e

function create_gpo {
    samba-tool gpo create $1 -U $2 --password=$3
}

function check_gpos {
	echo "WIP"
}

function link_gpo_to_container {
    gpo=$(samba-tool gpo listall | grep $1 -B 1 | grep GPO | grep -oE "[^ ]+$")
    samba-tool gpo setlink $2 $gpo -U $3 --password=$4
}

function check_user_in_winclient {
	python shared-utils/ucs-winrm.py domain-user-validate-password --domain sambatest.local --domainuser $1 --domainpassword $2
}

function create_and_print_testfile {
	 python shared-utils/ucs-winrm.py run-ps --cmd "New-Item .\\printest.txt -ItemType file"
	 python shared-utils/ucs-winrm.py run-ps --cmd "Add-Content .\\printest.txt 'print this in PDF'"
	 python shared-utils/ucs-winrm.py run-ps --cmd "copy .\\printest.txt \\\\ucs-samba\SambaPDFprinter"
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
