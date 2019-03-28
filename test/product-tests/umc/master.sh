#!/bin/bash

set -x
set -e

. lib.sh

# make sure we have a large environment
[ "$(udm users/user list | grep ^DN | wc -l)" -gt 5000 ]
[ "$(udm groups/group list | grep ^DN | wc -l)" -gt 1000 ]
[ "$(udm shares/share list | grep ^DN | wc -l)" -gt 2000 ]
[ "$(udm shares/printer list | grep ^DN | wc -l)" -gt 1000 ]

echo "Success"

exit 0
