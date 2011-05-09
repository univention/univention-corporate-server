#!/bin/sh
set -e
udm settings/extended_options create \
	--position "cn=custom attributes,cn=univention,$(ucr get ldap/base)" \
	--set name=Inventory \
	--set module=computers/windows \
	--set shortDescription="Inventory" \
	--set longDescription="Inventory extension" \
	--set translationShortDescription='"de_DE" "Inventarisierung"' \
	--set translationShortDescription='"fr_FR" "Inventaire"' \
	--set translationLongDescription='"de_DE" "Inventarisierungserweiterung"' \
	--set default=1 \
	--set editable=1
udm settings/extended_options modify \
	--dn "cn=Inventory,cn=custom attributes,cn=univention,$(ucr get ldap/base)" \
	--append module=users/user \
	--append module=groups/group \
	--set shortDescription="Inventory2" \
	--set longDescription="Inventory extension2" \
	--remove translationShortDescription='"fr_FR" "Inventaire"' \
	--append translationShortDescription='"es_ES" "inventarización"' \
	--set default= \
	--set editable=0
udm settings/extended_options remove \
	--dn "cn=Inventory,cn=custom attributes,cn=univention,$(ucr get ldap/base)"
