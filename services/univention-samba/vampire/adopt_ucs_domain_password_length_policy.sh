#!/bin/bash
#
# Univention Samba
#  helper script: adjust min password length in samba policy
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


### this script may be removed after update to ucs3.1 (Bug #21262)
###
### This script checks if the old default for min password length is
### still active in the Samba domain policy.
### If this is the case, it checks if there is a single UCS password
### policy referenced at the ldap/base and if it differs from the
### value in the Samba domain policy.
### If these strict criteria are met, the Samba min password length
### is set to the value of the UCS password policy.

eval "$(univention-config-registry shell)"

sambaMinPwdLength=$(univention-ldapsearch -xLLL \
	"(&(objectclass=sambadomain)(sambaDomainName=$windows_domain))" \
	sambaMinPwdLength | sed -n 's/^sambaMinPwdLength: \(.*\)$/\1/p')

if [ "$sambaMinPwdLength" = "5" ]; then
	## the samba domain policy still has the pre ucs3.1 default

	## check UDM password policies for the domain
	univentionPolicyPWHistory=$(univention-ldapsearch -xLLL \
					univentionPWLength=* dn \
					| sed -n 's/^dn: \(.*\)/\1/p')
	## count referenced UDM password policies
	referenced_policies=0
	unset univentionPWLength
	while read policy_dn; do
		referencing_objects=$(univention-ldapsearch -xLLL \
						univentionPolicyReference="$policy_dn" dn \
						| sed -n 's/^dn: \(.*\)/\1/p')
		referenced_policies=$(($referenced_policies+1))
		if [ "$referenced_policies" -gt 1 ]; then
			## more than one referenced policy, stop
			break
		fi

		while read referencing_dn; do
			if [ "$referencing_dn" = "$ldap_base" ]; then
				univentionPWLength=$(univention-ldapsearch -xLLL \
						-b "$policy_dn" -s base univentionPWLength \
						| sed -n 's/^univentionPWLength: \(.*\)/\1/p')
			fi
		done <<<"$referencing_objects"
		
	done <<<"$univentionPolicyPWHistory"

	if [ "$referenced_policies" = 1 ] && [ -n "$univentionPWLength" ]; then
		## OK, there is a single active UDM policy, it's connected to the ldap/base
		if [ "$univentionPWLength" != "$sambaMinPwdLength" ]; then
			## and the old samba default policy does not match, adjust it:
			pdbedit -P "min password length" -C "$univentionPWLength"
		fi
	fi
fi
