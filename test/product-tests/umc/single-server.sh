#!/bin/bash

# export UCS=10.200.7.160
# export ADMIN_PASSWORD=univention
# export WINRM_DOMAIN="four.three"
# export WINRM_CLIENT=10.200.7.65
# export WINRM_USER=Administrator
# export WINRM_PASSWORD=univention

set -x
set -e

# make sure we have a large environment
[ "$(udm users/user list | grep ^DN | wc -l)" -gt 5000 ]
[ "$(udm groups/group list | grep ^DN | wc -l)" -gt 1000 ]
[ "$(udm shares/share list | grep ^DN | wc -l)" -gt 2000 ]
[ "$(udm shares/printer list | grep ^DN | wc -l)" -gt 1000 ]

echo "Success"

exit 0
