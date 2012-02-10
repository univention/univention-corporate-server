#!/bin/sh
# -*- coding: utf-8 -*-
#
# Univention Lib
#  shell function for creating UMC operation and acl objects
#
# Copyright 2011-2012 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

eval "$(ucr shell ldap/base)"

BIND_ARGS="$@"

umc_frontend_new_hash () {
	# create new timestamps for index.html and debug.html in order to
	# avoid caching problems in browsers
	timestamp=$(date +'%Y%d%m%H%M%S')
	for ifile in index.html debug.html js/umc/login.html; do
		f="/usr/share/univention-management-console-frontend/$ifile"
		[ -w "$f" ] && sed -i 's/\$\(.*\)\$/$'$timestamp'$/' "$f"
	done

	# update the symlinks to the js/css directories
	for idir in css js; do
		rm -f "/usr/share/univention-management-console-frontend/${idir}_\$"*\$ || true
		ln -s "$idir" "/usr/share/univention-management-console-frontend/${idir}_\$${timestamp}\$" || true
	done

	return 0
}

umc_init () {
	# containers
	udm container/cn create $BIND_ARGS --ignore_exists --position cn=univention,$ldap_base --set name=UMC
	udm container/cn create $BIND_ARGS --ignore_exists --position cn=policies,$ldap_base --set name=UMC --set policyPath=1
	udm container/cn create $BIND_ARGS --ignore_exists --position cn=UMC,cn=univention,$ldap_base --set name=operations

	# default policies
	udm policies/umc create $BIND_ARGS --ignore_exists --set name=default-umc-all \
		--position cn=UMC,cn=policies,$ldap_base

	# link default admin policy to the domain admins
	udm groups/group modify $BIND_ARGS --ignore_exists --dn "cn=Domain Admins,cn=groups,$ldap_base" \
		--policy-reference="cn=default-umc-all,cn=UMC,cn=policies,$ldap_base"
}

_umc_remove_old () {
	# removes an object and ignores all errors
	name=$1; shift
	module=$1; shift
	container=$1

	udm $module remove $BIND_ARGS --dn "cn=$name,$container,$ldap_base" 2>/dev/null || true
}

umc_operation_create () {
	# example: umc_operation_create "udm" "UDM" "users/user" "udm/*:objectType=users/*"
	name=$1; shift
	description=$1; shift
	flavor=$1; shift
	operations=""
	for oper in "$@"; do
		operations="$operations --append operation=$oper "
	done
	udm settings/umc_operationset create $BIND_ARGS --ignore_exists \
		--position cn=operations,cn=UMC,cn=univention,$ldap_base \
		--set name="$name" \
		--set description="$description" \
		--set flavor="$flavor" $operations
}

umc_policy_append () {
	# example: umc_policy_append "default-umc-all" "udm-all" "udm-users"
	policy="$1"; shift

	ops=""
	for op in "$@"; do
		ops="$ops --append allow=cn=$op,cn=operations,cn=UMC,cn=univention,$ldap_base "
	done

	udm policies/umc modify $BIND_ARGS --ignore_exists \
		--dn "cn=$policy,cn=UMC,cn=policies,$ldap_base" $ops
}
