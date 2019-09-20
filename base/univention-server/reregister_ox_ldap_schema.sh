#!/bin/bash
#
# Copyright (C) 2018-2019 Univention GmbH <https://www.univention.de/>
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

. /usr/share/univention-lib/all.sh || exit 1

eval "$(ucr shell)"


update_ucr_template () {
	if [ -f "/etc/univention/templates/files/etc/ldap/slapd.conf.d/29univention-open-xchange_schema" ] ; then
		if [ ! "$(sha1sum /etc/univention/templates/files/etc/ldap/slapd.conf.d/29univention-open-xchange_schema | cut -d' ' -f1)" = "6c0adfc18b5be8c827588feb27bb15d7973e6dee" ] ; then
			# UCR template exists and is still outdated
			cat >/etc/univention/templates/files/etc/ldap/slapd.conf.d/29univention-open-xchange_schema <<EOF
@!@
import os.path
if (configRegistry.get('ldap/server/type') == "master") and configRegistry.is_false('ox/master/42/registered_ldap_acls', True):
	if not os.path.isfile("/usr/share/univention-ldap/schema/legacy/kolab2.schema"):
		print 'include        /usr/share/univention-ldap/schema/oxforucs-extra.schema'
	print 'include         /usr/share/univention-ldap/schema/oxforucs.schema'
@!@
EOF
			echo "OX schema subtemplate has been updated"
		fi
	fi
}

fix_backup () {
	if ! is_ucr_true "ox/master/42/registered_ldap_acls" ; then
		# variable is <unset> or "true/yes/1/..." ==> problem is still unfixed

		# install new version of UCR template
		update_ucr_template
		# disable schema inclusion / will be fixed on DC master
		ucr set ox/master/42/registered_ldap_acls=yes
		# commit changes
		ucr commit /etc/ldap/slapd.conf
	fi
}

fix_master () {
	if is_ucr_true "ox/master/42/registered_ldap_acls" ; then
		echo "OX LDAP schema has already been reregistered."
	else
		# variable is <unset> or "true/yes/1/..." ==> problem is still unfixed

		# install new version of UCR template
		update_ucr_template

		echo "Trying to switch from static LDAP OX schema to registered LDAP schema..."
		ucr set ox/master/42/registered_ldap_acls=yes
		# be sure that the config file is recreated
		ucr commit /etc/ldap/slapd.conf

		DIR=/usr/share/univention-ldap/schema
		SCHEMA=()
		if [ ! -f "/usr/share/univention-ldap/schema/legacy/kolab2.schema" ] ; then
			SCHEMA+=("--schema" "$DIR/oxforucs-extra.schema")
		fi
		SCHEMA+=("--schema" "$DIR/oxforucs.schema")

		export UNIVENTION_APP_IDENTIFIER='oxseforucs_7.8.4-ucs11'
		PKG_VERSION="9.0.8-1A~4.2.0.20180503"
		PKG_NAME="univention-ox"

		if ! ucs_registerLDAPExtension \
			"${SCHEMA[@]}" \
			--packagename "$PKG_NAME" \
			--packageversion "$PKG_VERSION" ;
		then
			echo "ERROR: registration of LDAP schema failed - reverting changes"
			echo "ERROR: please call '$0' to retry again"
			ucr unset ox/master/42/registered_ldap_acls
			ucr commit /etc/ldap/slapd.conf
			systemctl restart slapd.service
			exit 1
		else
			echo "OK: switch from static to registered OX LDAP schema was successful"
		fi
	fi
}


if LANG=C dpkg-query -W -f '${Status}' univention-ox-directory-integration | egrep -i ' (installed|Triggers-awaiting|Triggers-pending|Half-configured|Unpacked|Half-installed)$' ; then
	# OX schema package is installed
	case "$server_role" in
		domaincontroller_master)
			fix_master
			;;
		domaincontroller_backup)
			fix_backup
			;;
		*)
			echo "$0: nothing to do on this server role!"
			;;
	esac
fi

exit 0
