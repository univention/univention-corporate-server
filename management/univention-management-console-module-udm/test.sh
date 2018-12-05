#!/bin/bash
# shortcut to test some requests

# ucr set security/packetfilter/package/univention-udm/tcp/8888/all=ACCEPT
# Folgende Apache Regel ist notwendig in univention.conf:
# <LocationMatch "^/univention/(udm/.*)">
#        ProxyPassMatch http://127.0.0.1:8888/$1 retry=0 timeout=311
#</LocationMatch>


host="10.200.27.130"
host="192.168.188.129"
base="http://Administrator:univention@$host:8888/udm"
ldap_base="dc%3Dschool%2Cdc%3Dlocal"
ldap_base="dc%3Dfbest%2Cdc%3Ddev"

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
_curl -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2C$ldap_base/properties/"
_curl -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2C$ldap_base/properties/primaryGroup/choices"
_curl -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2C$ldap_base/policies/umc/"
_curl -i "$base/users/user/policies/umc/uid%3DAdministrator%2Ccn%3Dusers%2C$ldap_base/"
_curl -i "$base/users/user/policies/umc/cn%3Dusers%2C$ldap_base/?container=yes"
_curl -i "$base/users/user/policies/umc/uid%3DAdministrator%2Ccn%3Dusers%2C$ldap_base/?policy=cn%3Ddefault-umc-users%2Ccn%3DUMC%2Ccn%3Dpolicies%2C$ldap_base"
_curl -i "$base/users/user/policies/umc/cn%3Dusers%2C$ldap_base/?container=yes&policy=cn%3Ddefault-umc-users%2Ccn%3DUMC%2Ccn%3Dpolicies%2C$ldap_base"
_curl -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2C$ldap_base/layout"

# search for users:
_curl -i "$base/users/user/"

# create a user:
#_curl -XPOST -i "$base/users/user/"

# get a specific user:
_curl -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2C$ldap_base"

# modify a specific user:
#_curl -X PUT -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2C$ldap_base"
#_curl -X PATCH -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2C$ldap_base"
#
## remove a specific user:
#_curl -X DELETE -i "$base/users/user/uid%3DAdministrator%2Ccn%3Dusers%2C$ldap_base"
