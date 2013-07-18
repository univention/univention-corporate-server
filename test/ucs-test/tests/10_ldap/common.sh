#!/bin/sh

hasPwdAccess () { # has user $1 access to reset password of user $2 ?
	local adminuser="uid=$1,cn=users,$ldap_base"
	local adminpwd=univention
	[ "$adminuser" = "$tests_domainadmin_account" ] && adminpwd="$tests_domainadmin_pwd"
	local targetuser="uid=$2,cn=users,$ldap_base"
	local testpwd="$(random_chars 12 "${_lowerletters}")"
	local passwd="${3:-$testpwd}"
	udm-test users/user modify \
		--binddn "$adminuser" \
		--bindpwd "$adminpwd" \
		--dn "$targetuser" \
		--set password="$passwd" \
		--set overridePWHistory=1 \
		--set overridePWLength=1
	return $?
}

hasDescrAccess () { # has user $1 access to set description of user $2 ?
	local adminuser="uid=$1,cn=users,$ldap_base"
	local adminpwd=univention
	[ "$adminuser" = "$tests_domainadmin_account" ] && adminpwd="$tests_domainadmin_pwd"
	local targetuser="uid=$2,cn=users,$ldap_base"
	udm-test users/user modify \
		--binddn "$adminuser" \
		--bindpwd "$adminpwd" \
		--dn "$targetuser" \
		--set description="$(date)"
	return $?
}

resetPwd () { # reset password to univention for user $1
	local targetuser="uid=$1,cn=users,$ldap_base"
	local targetpwd="${2:-univention}"
	[ "$targetuser" = "$tests_domainadmin_account" ] && targetpwd="$tests_domainadmin_pwd"
	udm-test users/user modify \
		--dn "$targetuser" \
		--set password="$targetpwd" \
		--set overridePWHistory=1 \
		--set overridePWLength=1
	return $?
}
