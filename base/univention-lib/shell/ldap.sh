# Univention Common Shell Library
#
# Copyright 2011 Univention GmbH
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


#
# ucs_getAttrOfDN returns the attribute value of an LDAP object
# ucs_getAttrOfDN <attributename> <DN>
# e.g. ucs_getAttrOfDN "krb5PasswordEnd" "uid=testuser,cn=users,dc=test,dc=system"
# ==> 20110622112559Z
#
ucs_getAttrOfDN() { # <attr> <dn>
	if [ -n "$1" -a -n "$2" ]; then
		ldapsearch -x -s base -b "$2" -LLL "$1" | ldapsearch-wrapper | ldapsearch-decode64 | sed -ne "s/^$1: //p"
	fi
}

#
# ucs_convertUID2DN returns DN of user object for specified UID
# ucs_convertUID2DN <uid>
# e.g. ucs_convertUID2DN "testuser"
#
ucs_convertUID2DN() { # <uid>
	uid=$(echo -n "$1"|base64 -w 0)
	if [ -n "$1" ]; then
		ldapsearch -x -LLL "uid=$(echo -n "$uid"|base64 -d)" dn | ldapsearch-wrapper | ldapsearch-decode64 | sed -ne 's/dn: //p'
	fi
}

#
# ucs_convertUID2DN returns UID of user object for specified DN
# ucs_convertUID2DN <user dn>
# e.g. ucs_convertUID2DN "uid=testuser,cn=users,dc=test,dc=system"
#
ucs_convertDN2UID() { # <userdn>
	ucs_getAttrOfDN "uid" "$1"
}

#
# ucs_getGroupMembersDirect returns all members of specified group
# ucs_getGroupMembersDirect <group dn>
# e.g. ucs_getGroupMembersDirect "cn=Domain Admins,cn=groups,dc=test,dc=system"
#
ucs_getGroupMembersDirect() { # <groupDN>
	ucs_getAttrOfDN "uniqueMember" "$1"
}

#
# ucs_getGroupMembersDirect returns all members of specified group and of all nested groups
# ucs_getGroupMembersDirect <group dn>
# e.g. ucs_getGroupMembersDirect "cn=Domain Admins,cn=groups,dc=test,dc=system"
#
ucs_getGroupMembersRecursive(){ # <groupDN>
	local reply
	while read reply
	do
		if [ -z "$(ldapsearch -x -LLL -b "$reply" '(!(objectClass=univentionGroup))' dn | sed -ne "s/^dn: //p")" ]
		then
			ucs_getGroupMembersRecursive "$reply"
		else
			echo "$reply"
		fi
	done < <(ucs_getGroupMembersDirect "$1") | sort -u
}
