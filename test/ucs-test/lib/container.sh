#!/bin/bash
. "$TESTLIBPATH/base.sh" || exit 137

container="cn"

container_create () {
	local NAME=${1?:missing parameter: container name}
	info "create new $container named $NAME"
	local DESCRIPTION=${2:-cn named $1}
	local POSITION=${3:-$ldap_base}
	shift
	shift
	shift
	if udm-test "container/$container" create \
		--set name="$NAME" \
		--set description="$DESCRIPTION" \
		--position "$POSITION" \
		"$@" >&2
	then
		echo "$container=$NAME,$POSITION"
		return 0
	else
		return 1
	fi
}

container_exists () {
	local NAME=${1?:missing parameter: container name}
	info "checks whether a $container with the dn $NAME exists"
	if udm-test "container/$container" list | grep -q "^DN: $NAME"
	then
		info "$container exists"
		return 0
	else
		error "$container does not exists"
		return 1
	fi
}

container_remove () {
	local NAME=${1?:missing parameter: container name}
	info "remove $container with the dn $NAME"
	udm-test "container/$container" remove --dn "$NAME"
}

container_move () {
	local NAMEOLD=${1?:missing parameter: old container name}
	local NAMENEW=${2?:missing parameter: new container name}
	info "move $container with the dn $NAMEOLD to the position $NAMENEW"
	udm-test "container/$container" move --dn "$NAMEOLD" --position "$NAMENEW"
}

container_modify () {
	local NAME=${1?:missing parameter: container name}
	local DESCRIPTION=${2?:missing parameter: description}
	info "modify $container with the dn $NAME, set description to $DESCRIPTION"
	udm-test "container/$container" modify \
		--dn "$NAME" \
		--set description="$DESCRIPTION"
}

# vim:set filetype=sh ts=4:
