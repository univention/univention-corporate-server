#!/bin/bash

set -x

function create_user {
    for value in {1..10}
    do
        python shared-utils/ucs-winrm.py create-user --user-name user$value --user-password Univention@$value
    done
}

function prepare_AD_for_takeover {
     python shared-utils/ucs-winrm.py create-multiple-user --user-prefix benutzer --user-amount 1500 --user-password "Univention@99" 
     python shared-utils/ucs-winrm.py create-multiple-adgroup --group-prefix gruppe --group-amount 40 --path 'dc=adtakeover,dc=local'
     python shared-utils/ucs-winrm.py random-user-in-group
     python shared-utils/ucs-winrm.py create-newGPO --name TestGPO --comment "testing new GPO in domain"
     python shared-utils/ucs-winrm.py create-newGPO --name TestGPO1 --comment "testing new GPO in domain"
     python shared-utils/ucs-winrm.py get-GPO --name TestGPO
     python shared-utils/ucs-winrm.py new-OU  --name TestContainer --path 'dc=adtakeover,dc=local'
     python shared-utils/ucs-winrm.py new-user-in-ou --user-name user1 --user-password "Univention@99" --path 'ou=TestContainer,dc=adtakeover,dc=local'
     python shared-utils/ucs-winrm.py new-user-in-ou --user-name user10 --user-password "Univention@99" --path 'ou=TestContainer,dc=adtakeover,dc=local'
     python shared-utils/ucs-winrm.py link-GPO-withLDAPobject --name TestGPO --target 'ou=TestContainer,dc=adtakeover,dc=local' #TODO : link new GPOs with existing containers see Bug#46443
     python shared-utils/ucs-winrm.py link-GPO-withLDAPobject --name TestGPO1 --target 'ou=TestContainer,dc=adtakeover,dc=local'
     python shared-utils/ucs-winrm.py set-GPO-SSaverTimeout --name TestGPO --timeout 900
     python shared-utils/ucs-winrm.py hide-volumeicon-GPO --name TestGPO
     python shared-utils/ucs-winrm.py set-GPO-SSaverTimeout --guid 31B2F340-016D-11D2-945F-00C04FB984F9 --timeout 60
     python shared-utils/ucs-winrm.py hideprograms-startmenu-GPO --guid 31B2F340-016D-11D2-945F-00C04FB984F9
     python shared-utils/ucs-winrm.py apply-GPO-on-user --name TestGPO --username user1
     python shared-utils/ucs-winrm.py apply-GPO-on-user --name TestGPO --username user10
     python shared-utils/ucs-winrm.py add-user-to-domainadmin --username benutzer1 --domain adtakeover
     python shared-utils/ucs-winrm.py add-user-to-domainadmin --username benutzer2 --domain adtakeover
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
