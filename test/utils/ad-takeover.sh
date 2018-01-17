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
