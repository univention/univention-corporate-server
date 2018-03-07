#!/bin/bash

set -x

function create_user {
    for value in {1..10}
    do
        python shared-utils/ucs-winrm.py create-user --user-name user$value --user-password Univention@$value
    done
}

function check_all_user {
    for value in {1..10}
    do
        python shared-utils/ucs-winrm.py domain_user_validate_password --domain adtakeover.local --domainuser user$value --domainpassword Univention@$value
    done
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

