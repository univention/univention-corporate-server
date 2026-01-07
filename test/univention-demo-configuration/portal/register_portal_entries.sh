#!/bin/bash
# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

eval "$(ucr shell ldap/base ldap/hostdn)"
: "${ldap_base:?missing}" "${ldap_hostdn:?missing}"
DIR="$(dirname "$0")"

univention-directory-manager portals/entry modify \
	--dn "cn=login-ucs,cn=entry,cn=portals,cn=univention,$ldap_base" \
	--set backgroundColor="var(--bgc-content-body)"

univention-directory-manager portals/category remove --ignore_not_exists \
	--dn "cn=demo-service,cn=category,cn=portals,cn=univention,$ldap_base"
univention-directory-manager portals/category create \
	--position "cn=category,cn=portals,cn=univention,$ldap_base" \
	--set name=demo-service \
	--append entries="cn=login-ucs,cn=entry,cn=portals,cn=univention,$ldap_base" \
	--append displayName='"en_US" "Applications"' \
	--append displayName='"de_DE" "Applikationen"' \
	--append displayName='"fr_FR" "Applications"'

univention-directory-manager portals/category remove --ignore_not_exists \
	--dn "cn=demo-admin,cn=category,cn=portals,cn=univention,$ldap_base"
univention-directory-manager portals/category create \
	--position "cn=category,cn=portals,cn=univention,$ldap_base" \
	--set name=demo-admin \
	--append displayName='"en_US" "Administration"' \
	--append displayName='"de_DE" "Verwaltung"' \
	--append displayName='"fr_FR" "Administration"'

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

univention-directory-manager portals/entry remove --ignore_not_exists \
    	--dn "cn=summit_2026,cn=entry,cn=portals,cn=univention,$ldap_base"
univention-directory-manager portals/entry create \
	--position "cn=entry,cn=portals,cn=univention,$ldap_base" \
	--set name=summit_2026 \
	--append displayName='"en_US" "Univention Summit 2026"' \
	--append displayName='"de_DE" "Univention Summit 2026"' \
	--append displayName='"fr_FR" "Univention Summit 2026"' \
	--append description='"en_US" "Univention Summit 2026 - Let&apos;s Connect - January 28 &amp; 29 in Bremen"' \
	--append description='"de_DE" "Univention Summit 2026 - Let&apos;s Connect - 28. &amp; 29. Januar in Bremen"' \
	--append description='"fr_FR" "Univention Summit 2026 - Let&apos;s Connecter - 28 &amp; 29 Janvier à Brême"' \
	--append link='"en_US" "https://univention-summit.com/"' \
        --append link='"de_DE" "https://univention-summit.de/"' \
        --append link='"fr_FR" "https://univention-summit.com/"' \
	--set linkTarget=newwindow \
	--set anonymous=true \
	--set icon="$(base64 "$DIR/summit_icon.svg")"

univention-directory-manager portals/category remove --ignore_not_exists \
	--dn "cn=announcements,cn=category,cn=portals,cn=univention,$ldap_base"
univention-directory-manager portals/category create \
	--position "cn=category,cn=portals,cn=univention,$ldap_base" \
	--set name=announcements \
	--append displayName='"en_US" "Announcements"' \
	--append displayName='"de_DE" "Ankündigungen"' \
	--append displayName='"fr_FR" "Annonces"' \
	--append entries="cn=summit_2026,cn=entry,cn=portals,cn=univention,$ldap_base"

create_app_entry () {
	local cn=demo-$1 catalogID="$2" label="$3" description_en="$4" description_de="$5" description_fr="$6" backgroundColor="$7"
	local link="/apps/?cn=$cn&catalogID=$catalogID&label=$label"
	local icon="$DIR/app-logo-$1.svg"
	local position="cn=entry,cn=portals,cn=univention,$ldap_base"
	local dn="cn=$cn,$position"

	udm portals/entry remove --ignore_not_exists --dn "$dn"
	udm portals/entry create \
		--position="$position" \
		--set name="$cn" \
		--set backgroundColor="$backgroundColor" \
		--append displayName='"en_US" "'"$label"'"' \
		--append description='"en_US" "'"$description_en"'"' \
		--append displayName='"de_DE" "'"$label"'"' \
		--append displayName='"fr_FR" "'"$label"'"' \
		--append description='"de_DE" "'"$description_de"'"' \
		--append description='"fr_FR" "'"$description_fr"'"' \
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
	"Solution en nuage pour la synchronisation et le partage de données et de fichiers" \
	"#041E42"

create_app_entry \
	nextcloud nextcloud \
	Nextcloud \
	"Secure storing, syncing &amp; sharing data in and outside your organization" \
	"Daten sicher speichern, synchronisieren &amp; teilen in und außerhalb Ihrer Organisation" \
	"Stockage, synchronisation et partage sécurisés des données à l'intérieur et à l'extérieur de votre organisation." \
	"#0082c9"

create_app_entry \
	kopano kopano-core \
	Kopano \
	"Kopano Sharing &amp; Communication Software for Professionals" \
	"Kopano Sharing &amp; Communication Software für Profis" \
	"Kopano Sharing &amp; Logiciel de communication pour les professionnels" \
	"#424242"

create_app_entry \
	ox oxseforucs \
	"OX App Suite" \
	"Groupware, email and communication platform" \
	"Groupware, E-Mail- und Kommunikationsplattform" \
	"Plateforme de groupware, de mail et de communication" \
	"#284b73"

create_app_entry \
	collabora collabora-online \
	"Collabora Online" \
	"Powerful LibreOffice-based online office suite" \
	"Leistungsstarke LibreOffice-basierte Online-Office-Suite" \
	"Suite bureautique en ligne puissante basée sur LibreOffice" \
	"#504999"

create_app_entry \
	onlyoffice onlyoffice-ds-integration \
	"ONLYOFFICE Docs Enterprise Edition" \
	"Feature-rich office suite on your own server" \
	"Leistungsstarke Büro- und Produktivitäts-Suite auf Ihrem eigenen Server" \
	"Une suite bureautique riche en fonctionnalités sur votre propre serveur" \
	"#14416F"

create_app_entry \
	openproject openproject \
	OpenProject \
	"Open Source Project Management. Powerful. Easy-to-use. Enterprise class." \
	"Open Source Projekt-Management Software und Team Kollaboration" \
	"Management de projet Open Source. Puissant. Facile à utiliser" \
	"#1a67a3"

create_admin_entry () {
	local cn="demo-$1" label="$2" description_en="$3" description_de="$4" description_fr="$5" link="$6"
	local icon="$DIR/admin-entry-logo-$1.svg"
	local position="cn=entry,cn=portals,cn=univention,$ldap_base"
	local dn="cn=$cn,$position"

	udm portals/entry remove --ignore_not_exists --dn "$dn"
	udm portals/entry create --ignore_exists \
		--position="$position" \
		--set name="$cn" \
		--set backgroundColor="transparent" \
		--append displayName='"en_US" "'"$label"'"' \
		--append description='"en_US" "'"$description_en"'"' \
		--append displayName='"de_DE" "'"$label"'"' \
		--append displayName='"fr_FR" "'"$label"'"' \
		--append description='"de_DE" "'"$description_de"'"' \
		--append description='"fr_FR" "'"$description_fr"'"' \
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
# 	"La base de données de support d'Univention" \
# 	"http://sdb.univention.de"

univention-config-registry filter <"$DIR/domain-portal.ldif" | ldapmodify -D "$ldap_hostdn" -y /etc/machine.secret
cp "$DIR/portal.css" /usr/share/univention-portal/css/custom.css

ucr set portal/default-dn="cn=demo,cn=portal,cn=portals,cn=univention,$ldap_base"
