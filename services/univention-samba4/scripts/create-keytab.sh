#!/bin/bash
#
# Univention Samba4
#  Re-create /etc/krb5.keytab
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

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
