#!/bin/bash
#
# Copyright 2017-2019 Univention GmbH
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

eval "$(ucr shell)"
DIR="$(dirname $0)"

create_app_entry () {
	cn=demo-$1
	catalogID="$2"
	label="$3"
	description_en="$4"
	description_de="$5"
	link="/apps/?cn=$cn&catalogID=$catalogID&label=$label"
	icon="$DIR/app-logo-$1.svg"
	position="cn=portal,cn=univention,$ldap_base"
	dn="cn=$cn,$position"

	# remove previous entry
	search_result="$(univention-ldapsearch -LLL -b "$position" "cn=$cn" dn)"
	if [ -n "$search_result" ]; then
		udm settings/portal_entry remove --dn "$dn"
	fi

	# add new entry
	udm settings/portal_entry create --ignore_exists \
		--position="$position" \
		--set name="$cn" \
		--append displayName="\"en_US\" \"$label\"" \
		--append description="\"en_US\" \"$description_en\"" \
		--append displayName="\"de_DE\" \"$label\"" \
		--append description="\"de_DE\" \"$description_de\"" \
		--append link="$link" \
		--set category=service \
		--set icon="$(base64 "$icon")" \
		--set portal="cn=domain,cn=portal,cn=univention,$ldap_base"
}

create_app_entry \
	kopano kopano-core \
	Kopano \
	"Kopano Sharing &amp; Communication Software for Professionals" \
	"Kopano Sharing &amp; Communication Software für Profis"

create_app_entry \
	nextcloud nextcloud \
	Nextcloud \
	"Secure storing, syncing &amp; sharing data in and outside your organization" \
	"Daten sicher speichern, synchronisieren &amp; teilen in und außerhalb Ihrer Organisation"

create_app_entry \
	openproject openproject \
	OpenProject \
	"Leading open source project management software" \
	"Führende Open Source Projekt Management Software"

create_app_entry \
	owncloud owncloud82 \
	ownCloud \
	"Cloud solution for data and file sync and share" \
	"Cloud Lösung für Filesync und -share"

create_app_entry \
	suitecrm digitec-suitecrm \
	SuiteCRM \
	"Open Source customer relationship management for the world" \
	"Open Source Customer Relationship Management für die Welt"

create_admin_entry () {
	cn=demo-$1
	label="$2"
	description_en="$3"
	description_de="$4"
	link="$5"
	icon="$DIR/admin-entry-logo-$1.svg"
	position="cn=portal,cn=univention,$ldap_base"
	dn="cn=$cn,$position"

	# remove previous entry
	search_result="$(univention-ldapsearch -LLL -b "$position" "cn=$cn" dn)"
	if [ -n "$search_result" ]; then
		udm settings/portal_entry remove --dn "$dn"
	fi

	# add new entry
	udm settings/portal_entry create --ignore_exists \
		--position="$position" \
		--set name="$cn" \
		--append displayName="\"en_US\" \"$label\"" \
		--append description="\"en_US\" \"$description_en\"" \
		--append displayName="\"de_DE\" \"$label\"" \
		--append description="\"de_DE\" \"$description_de\"" \
		--append link="$link" \
		--set category=admin \
		--set icon="$(base64 "$icon")" \
		--set portal="cn=domain,cn=portal,cn=univention,$ldap_base"
}

create_admin_entry \
	help \
	"Univention Help" \
	"The Univention community for discussion and help" \
	"Die Univention-Community für Diskussion und Hilfe" \
	"https://help.univention.com"

create_admin_entry \
	sdb \
	"Univention SDB" \
	"The Univention support database" \
	"Die Univention-Support-Datenbank" \
	"http://sdb.univention.de"

function has_portal_background {
	univention-ldapsearch -LLL -b "cn=portal,cn=univention,$ldap_base" cn=domain | grep -q univentionPortalBackground:
}

if ! has_portal_background; then
	cat "$DIR/domain-portal.ldif" | univention-config-registry filter | ldapmodify -D "$ldap_hostdn" -y /etc/machine.secret 
fi

