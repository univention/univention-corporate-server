#!/bin/bash
# shortcut to test some requests

base="http://Administrator:univention@10.200.27.130:8888/udm"

_curl() {
	curl -s -f "$@" > /dev/null || echo curl "$@"
}

_curl -i "$base/"
_curl -i "$base/users/user/"
_curl -i "$base/users/object-types/"
_curl -i "$base/users/user/options"
_curl -i "$base/users/user/templates"
_curl -i "$base/users/user/containers"
_curl -i "$base/users/user/policies"
_curl -i "$base/users/user/report-types"
#_curl -i "$base/users/user/report/PDF%20Document/?"
_curl -i "$base/users/user/properties/mailPrimaryAddress/default"
_curl -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal/properties/"
_curl -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal/properties/primaryGroup/choices"
_curl -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal/policies/umc/"
_curl -i "$base/users/user/policies/umc/uid%3DAdministrator%2Ccn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal/"
_curl -i "$base/users/user/policies/umc/cn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal/?container=yes"
_curl -i "$base/users/user/policies/umc/uid%3DAdministrator%2Ccn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal/?policy=cn%3Ddefault-umc-users%2Ccn%3DUMC%2Ccn%3Dpolicies%2Cdc%3Dschool%2Cdc%3Dlocal"
_curl -i "$base/users/user/policies/umc/cn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal/?container=yes&policy=cn%3Ddefault-umc-users%2Ccn%3DUMC%2Ccn%3Dpolicies%2Cdc%3Dschool%2Cdc%3Dlocal"
_curl -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal/layout"

# search for users:
_curl -i "$base/users/user/"

# create a user:
#_curl -XPOST -i "$base/users/user/"

# get a specific user:
_curl -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal"

# modify a specific user:
#_curl -X PUT -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal"
#_curl -X PATCH -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal"
#
## remove a specific user:
#_curl -X DELETE -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2Cdc%3Dschool%2Cdc%3Dlocal"
