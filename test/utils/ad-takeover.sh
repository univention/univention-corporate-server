#!/bin/bash

function create_user {
    for value in {1..10}
    do
        python shared-utils/ucs-winrm.py create-user --user-name user$value --user-password Univention@$value
    done
}

create_user
