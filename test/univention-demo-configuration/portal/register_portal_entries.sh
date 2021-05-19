#!/bin/bash
#
# Copyright 2017-2021 Univention GmbH
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

univention-directory-manager portals/entry modify \
	--dn "cn=login-ucs,cn=entry,cn=portals,cn=univention,$ldap_base" \
	--set backgroundColor="var(--color-grey0)"

univention-directory-manager portals/category remove --ignore_not_exists \
	--dn "cn=demo-service,cn=category,cn=portals,cn=univention,$ldap_base"
univention-directory-manager portals/category create \
	--position "cn=category,cn=portals,cn=univention,$ldap_base" \
	--set name=demo-service \
	--append entries="cn=login-ucs,cn=entry,cn=portals,cn=univention,$ldap_base" \
	--append displayName='"en_US" "Applications"' \
	--append displayName='"de_DE" "Applikationen"'

univention-directory-manager portals/category remove --ignore_not_exists \
	--dn "cn=demo-admin,cn=category,cn=portals,cn=univention,$ldap_base"
univention-directory-manager portals/category create \
	--position "cn=category,cn=portals,cn=univention,$ldap_base" \
	--set name=demo-admin \
	--append displayName='"en_US" "Administration"' \
	--append displayName='"de_DE" "Verwaltung"'

univention-directory-manager portals/portal remove --ignore_not_exists \
	--dn "cn=demo,cn=portal,cn=portals,cn=univention,$ldap_base"
univention-directory-manager portals/portal create \
	--position "cn=portal,cn=portals,cn=univention,$ldap_base" \
	--set name=demo \
	--set logo="$(base64 "$DIR/ucs.svg")" \
	--append menuLinks="cn=certificates,cn=folder,cn=portals,cn=univention,$ldap_base" \
	--append menuLinks="cn=help,cn=folder,cn=portals,cn=univention,$ldap_base" \
	--append categories="cn=demo-service,cn=category,cn=portals,cn=univention,$ldap_base" \
	--append categories="cn=demo-admin,cn=category,cn=portals,cn=univention,$ldap_base" \
	--append displayName='"en_US" "UCS"' \
	--set showUmc=TRUE

create_app_entry () {
	cn=demo-$1
	catalogID="$2"
	label="$3"
	description_en="$4"
	description_de="$5"
	backgroundColor="${6:-var(--color-grey0)}"
	link="/apps/?cn=$cn&catalogID=$catalogID&label=$label"
	icon="$DIR/app-logo-$1.svg"
	position="cn=entry,cn=portals,cn=univention,$ldap_base"
	dn="cn=$cn,$position"

	# remove previous entry
	search_result="$(univention-ldapsearch -LLL -b "$position" "cn=$cn" dn)"
	if [ -n "$search_result" ]; then
		udm portals/entry remove --dn "$dn"
	fi

	# add new entry
	udm portals/entry create --ignore_exists \
		--position="$position" \
		--set name="$cn" \
		--set backgroundColor="$backgroundColor" \
		--append displayName='"en_US" "'"$label"'"' \
		--append description='"en_US" "'"$description_en"'"' \
		--append displayName='"de_DE" "'"$label"'"' \
		--append description='"de_DE" "'"$description_de"'"' \
		--append link='"en_US" "'"$link"'"' \
		--set icon="$(base64 "$icon")"

	udm portals/category modify \
		--dn "cn=demo-service,cn=category,cn=portals,cn=univention,$ldap_base" \
		--append entries="$dn"
}

create_app_entry \
	owncloud owncloud \
	ownCloud \
	"Cloud solution for data and file sync and share" \
	"Cloud Lösung für Filesync und -share" \
	"#041E42"

create_app_entry \
	nextcloud nextcloud \
	Nextcloud \
	"Secure storing, syncing &amp; sharing data in and outside your organization" \
	"Daten sicher speichern, synchronisieren &amp; teilen in und außerhalb Ihrer Organisation" \
	"#0082c9"

create_app_entry \
	kopano kopano-core \
	Kopano \
	"Kopano Sharing &amp; Communication Software for Professionals" \
	"Kopano Sharing &amp; Communication Software für Profis" \
	"#424242"

create_app_entry \
	ox oxseforucs \
	"OX App Suite" \
	"Groupware, email and communication platform" \
	"Groupware, E-Mail- und Kommunikationsplattform" \
	"#284b73"

create_app_entry \
	collabora collabora-online \
	"Collabora Online" \
	"Powerful LibreOffice-based online office suite" \
	"Leistungsstarke LibreOffice-basierte Online-Office-Suite" \
	"#504999"

create_app_entry \
	onlyoffice onlyoffice-ds-integration \
	"ONLYOFFICE Docs Enterprise Edition" \
	"Feature-rich office suite on your own server" \
	"Leistungsstarke Büro- und Produktivitäts-Suite auf Ihrem eigenen Server" \
	"#14416F"

create_app_entry \
	openproject openproject \
	OpenProject \
	"Open Source Project Management. Powerful. Easy-to-use. Enterprise class." \
	"Open Source Projekt-Management Software und Team Kollaboration" \
	"#1a67a3"

create_admin_entry () {
	cn=demo-$1
	label="$2"
	description_en="$3"
	description_de="$4"
	link="$5"
	icon="$DIR/admin-entry-logo-$1.svg"
	position="cn=entry,cn=portals,cn=univention,$ldap_base"
	dn="cn=$cn,$position"

	# remove previous entry
	search_result="$(univention-ldapsearch -LLL -b "$position" "cn=$cn" dn)"
	if [ -n "$search_result" ]; then
		udm portals/entry remove --dn "$dn"
	fi

	# add new entry
	udm portals/entry create --ignore_exists \
		--position="$position" \
		--set name="$cn" \
		--set backgroundColor="transparent" \
		--append displayName='"en_US" "'"$label"'"' \
		--append description='"en_US" "'"$description_en"'"' \
		--append displayName='"de_DE" "'"$label"'"' \
		--append description='"de_DE" "'"$description_de"'"' \
		--append link='"en_US" "'"$link"'"' \
		--set linkTarget="newwindow" \
		--set icon="$(base64 "$icon")"

	udm portals/category modify \
		--dn "cn=demo-admin,cn=category,cn=portals,cn=univention,$ldap_base" \
		--append entries="$dn"
}

# create_admin_entry \
# 	sdb \
# 	"Univention SDB" \
# 	"The Univention support database" \
# 	"Die Univention-Support-Datenbank" \
# 	"http://sdb.univention.de"

cat "$DIR/domain-portal.ldif" | univention-config-registry filter | ldapmodify -D "$ldap_hostdn" -y /etc/machine.secret
cp "$DIR/portal.css" /usr/share/univention-portal/css/custom.css

ucr set portal/default-dn="cn=demo,cn=portal,cn=portals,cn=univention,$ldap_base"
