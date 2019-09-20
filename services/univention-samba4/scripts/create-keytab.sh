#!/bin/bash
#
# Univention Samba4
#  Re-create /etc/krb5.keytab
#
# Copyright 2004-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

eval "$(univention-config-registry shell)"

if [ -e /var/lib/samba/private/secrets.ldb ]; then
	tmpfile=$(mktemp)

	ldbmodify -H /var/lib/samba/private/secrets.ldb <<-%EOF
	dn: flatname=$windows_domain,cn=Primary Domains
	changetype: modify
	replace: krb5Keytab
	krb5Keytab: $tmpfile
	-
	%EOF

	sleep 2
	rm /etc/krb5.keytab

	ldbmodify -H /var/lib/samba/private/secrets.ldb <<-%EOF
	dn: flatname=$windows_domain,cn=Primary Domains
	changetype: modify
	replace: krb5Keytab
	krb5Keytab: /etc/krb5.keytab
	-
	%EOF

	rm $tmpfile
else
	echo "The file /var/lib/samba/private/secrets.ldb does not exist. Skip the modification."
fi

exit 0
