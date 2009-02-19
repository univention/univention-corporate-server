#!/bin/sh -e
#
# Univention System Setup
#  setup utils helper script
#
# Copyright (C) 2004-2009 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

profile_file="/var/cache/univention-system-setup/profile"
check_ldap_access=0

while [ $# -gt 0 ]
do
	case "$1" in
		"--check_ldap_access")
			check_ldap_access=1
			shift
			;;
 		"--check_ldap_availability")
 			check_ldap_availability=1
 			shift
 			;;
		*)
			;;
	esac
done

is_variable_set()
{
	if [ ! -e $profile_file ]; then
		return 0
	fi

	if [ -z "$1" ]; then
		return 0
	fi
	value=`egrep "^$1=" $profile_file `
	if [ -z "$value" ]; then
		return 0
	else
		return 1
	fi
}
get_profile_var ()
{
	if [ ! -e $profile_file ]; then
		return
	fi

	if [ -z "$1" ]; then
		return
	fi

	value=`egrep "^$1=" $profile_file |sed -e 's|#.*||' | sed -e "s|^$1=||" | sed -e 's|"||g;s| $||g'`
	echo "$value"
}

service_stop ()
{
	for service in $@; do
		if [ -x /etc/init.d/$service ]; then
			/etc/init.d/$service stop
		fi
	done
}
service_start ()
{
	for service in $@; do
		if [ -x /etc/init.d/$service ]; then
			/etc/init.d/$service start
		fi
	done
}

ldap_binddn ()
{
	eval $(univention-config-registry shell server/role ldap/base ldap/master)
	if [ "$server_role" = "domaincontroller_master" ] || [ "$server_role" = "domaincontroller_backup" ]; then
		echo "cn=admin,$ldap_base"
	else
		ldap_username=`get_profile_var ldap_username`
		if [ -n "$ldap_username" ]; then
			dn=`ldapsearch -x -h $ldap_master "(&(objectClass=person)(uid=$ldap_username))" | grep "dn: " | sed -e 's|dn: ||' | head -n 1`
			echo "$dn"
		fi
	fi
}

ldap_bindpwd ()
{
	eval $(univention-config-registry shell server/role ldap/base ldap/master)
	if [ "$server_role" = "domaincontroller_master" ] || [ "$server_role" = "domaincontroller_backup" ]; then
		echo "`cat /etc/ldap.secret`"
	else
		ldap_password=`get_profile_var ldap_password`
		if [ -n "$ldap_password" ]; then
			echo "$ldap_password"
		fi
	fi
}
