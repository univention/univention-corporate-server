#!/bin/bash
. "$TESTLIBPATH/base.sh" || exit 137
. "$TESTLIBPATH/random.sh" || exit 137

group_randomname () { #Generates a random string as groupname and echo it. Usage: GROUPNAME=$(group_randomname)
	random_chars
}

group_create () { #Creates a group named like supplied in the first argument of the function
	#usage:
	#GROUPNAME=$(group_randomname)
	#group_create "$GROUPNAME"

	if [ -n "${1:-}" ]
	then
		local GROUPNAME="$1"
	else
		if [ -z "${GROUPNAME:-}" ]
		then
			GROUPNAME=$(random_mailaddress)
		fi
	fi
	shift

	if [ -z "${MAILADDR:-}" ]
	then
		local MAILADDR=$(random_mailaddress)
	fi

	info "create group $GROUPNAME with Mailaddress $MAILADDR"
	udm-test groups/group create \
		--position="cn=groups,$ldap_base" \
		--set name="$GROUPNAME" \
		--set mailAddress="$MAILADDR@$domainname" \
		"$@"
	local rc=$?
	MAILADDR=
	return $rc
}

group_dn (){ #echos the DN of a Group. E.g. group_dn $GROUPNAME
	local GROUPNAME=${1?:missing parameter: groupname}
	udm-test groups/group list --filter cn="$GROUPNAME" | sed -ne 's/^DN: //p'
}

group_remove () { # Remove a Group. E.g. group_remove $GROUPNAME
	local GROUPNAME=${1?:missing parameter: group name}
	info "group remove $GROUPNAME"
	udm-test groups/group remove --dn="cn=$GROUPNAME,cn=groups,$ldap_base"
}

group_adduser () { # Add User to Group. E.g. group_adduser $USERNAME $GROUPNAME
	local USERNAME=${1?:missing parameter: user name}
	local GROUPNAME=${2?:missing parameter: group name}

	info "add user $USERNAME to group $GROUPNAME"
	udm-test groups/group modify \
		--dn="cn=$GROUPNAME,cn=groups,$ldap_base" \
		--append users="uid=$USERNAME,cn=users,$ldap_base"

	group_hasusermember "$GROUPNAME" "$USERNAME" && group_userismemberof "$USERNAME" "$GROUPNAME"
}

group_addcomputer () { # Add Computer to Group. group_addcomputer $COMPUTERNAME $GROUPNAME
	local COMPUTERNAME=${1?:missing parameter: computer name}
	local GROUPNAME=${2?:missing parameter: group name}

	info "add computer $COMPUTERNAME to group $GROUPNAME"

	udm-test groups/group modify \
		--dn="cn=$GROUPNAME,cn=groups,$ldap_base" \
		--append hosts="cn=$COMPUTERNAME,cn=computers,$ldap_base"
}

group_addgroup () { # Add Group to Group. E.g. group_addgroup $GROUPTOADD $GROUPNAME
	local GROUPTOADD=${1?:missing parameter: group to add}
	local GROUPNAME=${2?:missing parameter: group name}

	info "add group $GROUPTOADD to group $GROUPNAME"

	udm-test groups/group modify \
		--dn="cn=$GROUPNAME,cn=groups,$ldap_base" \
		--append nestedGroup="cn=$GROUPTOADD,cn=groups,$ldap_base"

	group_hasgroupmember "$GROUPNAME" "$GROUPTOADD" && group_ismemberof "$GROUPTOADD" "$GROUPNAME"
}

group_removeuser () { # Remove User from Group. E.g. group_removeuser $USERNAME $GROUPNAME
	local USERNAME=${1?:missing parameter: user name}
	local GROUPNAME=${2?:missing parameter: group name}

	info "remove user $USERNAME from group $GROUPNAME"

	udm-test groups/group modify \
		--dn="cn=$GROUPNAME,cn=groups,$ldap_base" \
		--remove users="uid=$USERNAME,cn=users,$ldap_base"
	local rc=$?
	nscd -i group
	return $rc
}

group_removegroup () { # Remove Group from Group. E.g. group_removegroup $GROUPTOREMOVE $GROUPNAME
	local GROUPTOREM=${1?:missing parameter: group to remove}
	local GROUPNAME=${2?:missing parameter: group name}

	info "remove group $GROUPTOREM from group $GROUPNAME"

	udm-test groups/group modify \
		--dn="cn=$GROUPNAME,cn=groups,$ldap_base" \
		--remove nestedGroup="cn=$GROUPTOREM,cn=groups,$ldap_base"
}

group_rename () { # Rename a group. E.g. group_rename $GROUPNAMEOLD $GROUPNAMENEW
	local GROUPNAMEOLD=${1?:missing parameter: old group name}
	local GROUPNAMENEW=${2?:missing parameter: new group name}

	info "rename group $GROUPNAMEOLD to $GROUPNAMENEW"

	udm-test groups/group modify \
		--dn="cn=$GROUPNAMEOLD,cn=groups,$ldap_base" \
		--set name="$GROUPNAMENEW"
}

group_exists () { # Returns 0, if a Group exists, otherwise 1. E.g. group_exists $GROUPNAME
	local GROUPNAME=${1?:missing parameter: group name}
	univention-directory-manager groups/group list --filter "cn=$GROUPNAME" |
		grep -q "^DN: cn=$GROUPNAME"
}

group_hasgroupmember () { # Checks, whether a Group has a specific group as member. Returns 0 if it is and 1 if not. E.g. group_hasgroupmember $GROUPNAME $GROUPMEMBER
	local GROUPNAME=${1?:missing parameter: group name}
	local GROUPMEMBER=${2?:missing parameter: nested group name}
	udm-test groups/group list --filter "cn=$GROUPNAME" |
		grep -q "nestedGroup: cn=$GROUPMEMBER,"
}

group_hasusermember () { # Checks, whether a Group has a specific user as member. Returns 0 if it is and 1 if not. E.g. group_hasusermember $GROUPNAME $USERNAME
	local GROUPNAME=${1?:missing parameter: group name}
	local USERNAME=${2?:missing parameter: user name}
	udm-test groups/group list --filter "cn=$GROUPNAME" |
		grep -q "users: uid=$USERNAME,"
}

group_hascomputermember () { # Checks, whether a Group has a Computer-Member. E.g. group_hascomputermember $GROUPNAME $COMPUTERNAME . Returns 0 it is and 1 if not.
	local GROUPNAME=${1?:missing parameter: group name}
	local COMPUTERRNAME=${2?:missing parameter: computer name}

	# Convert the string from the NAME-Variable to UTF8, because otherwise this part won't work with mutated vowels
	local tmp1=$(mktemp) tmp2=$(mktemp)
	echo -n "$COMPUTERNAME" >"$tmp1"
	iconv --from-code=ISO-8859-1 --to-code=UTF-8 "$tmp1" >"$tmp2"
	COMPUTERNAME=$(cat "$tmp2")
	rm -f "$tmp1" "$tmp2"
	udm-test groups/group list --filter "cn=$GROUPNAME" |
		grep -q "cn=$COMPUTERNAME"
}

group_ismemberof () { # Checks, whether a Group is member of a specific group. Returns 0 if it is and 1 if not. E.g. group_ismemberof $MEMBERGROUP $GROUPNAME
	local GROUPMEMBER=${1?:missing parameter: member group name}
	local GROUPNAME=${2?:missing parameter: group name}
	udm-test groups/group list --filter cn="$GROUPTOADD" |
		grep -q "memberOf: cn=$GROUPNAME,"
}

group_userismemberof () { # Checks, whether a user is member of a specific group. Returns 0 it is an 1 if not. E.g. group_userismemberof $USERNAME $GROUPNAME
	local USERNAME=${1?:missing parameter: user name}
	local GROUPNAME=${2?:missing parameter: group name}
	udm-test users/user list --filter "uid=$USERNAME" |
		grep -q "cn=$GROUPNAME"
}

group_userisindirectmemberof () { # checks by the command id, whether a user is member of a specific group. E.g. group_userisindirectmemberof $USERNAME $GROUPNAME
	local USERNAME=${1?:missing parameter: user name}
	local GROUPNAME=${2?:missing parameter: group name}
	id "$USERNAME" | grep -q "($GROUPNAME" &&
	su "$USERNAME" -c id | grep -q "($GROUPNAME"
}

group_getent () { # checks with getent, whether the group named $GROUPNAME has a member named $MEMBERNAME
	local GROUPNAME=${1?:missing parameter: group name}
	local MEMBERNAME=${2?:missing parameter: member name}
	getent group "$GROUPNAME" | grep -q "$MEMBERNAME"
}

group_gid () { # echos the id of group $GROUPNAME
	local GROUPNAME=${1?:missing parameter: group name}
	getent group "$GROUPNAME" | cut -d : -f 3
}

# vim: set filetype=sh ts=4:
