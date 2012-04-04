#!/bin/bash
. "$TESTLIBPATH/base.sh" || exit 137

SHARE_HOST="$hostname.$domainname"
SHARE_POSITION="cn=$hostname.$domainname,cn=shares,$ldap_base"
SHARE_WRITEABLE=1
SHARE_OWNER=0 #must be number
SHARE_GROUP=0 #must be numer
SHARE_DIRECTORYMODE=0755

share_create () {
	local name=${1?:missing parameter: share name}
	local path=${2?:missing parameter: share path}
	univention-directory-manager shares/share create \
		--set name="$name" \
		--set path="$path" \
		--position "$SHARE_POSITION" \
		--set writeable="$SHARE_WRITEABLE" \
		--set owner="$SHARE_OWNER" \
		--set group="$SHARE_GROUP" \
		--set directorymode="$SHARE_DIRECTORYMODE" \
		--set host="$SHARE_HOST"
}

share_exists () {
	local name=${1?:missing parameter: share name}
	univention-directory-manager shares/share list --filter "cn=$name" | \
		grep -q "^DN: cn=$1,$SHARE_POSITION"
}

share_remove () {
	local name=${1?:missing parameter: share name}
	univention-directory-manager shares/share remove --dn "cn=$name,$SHARE_POSITION"
}

share_mountlocal_nfs () {
	local name=${1?:missing parameter: share name}
	local path=${2?:missing parameter: mount point}
	mount localhost:"$name" "$path"
}

share_mountlocal_samba () {
	local name=${1?:missing parameter: share name}
	local path=${2?:missing parameter: mount point}
	local USERNAME=${3:-$NAME}
	local PASSWORD=${4:-univention}
	log_and_execute mount //localhost/"$1" "$2" -o username="$USERNAME",password="$PASSWORD"
}

# vim:set filetype=sh ts=4:
