#!/bin/bash
#
# Copyright 2022 Univention GmbH
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

set -x

ansible_register_idps_setup () {
	local traeger1_domain="${1:?missing traeger1_domain}"
	local traeger2_domain="${2:?missing traeger2_domain}"
	local repo_user="${3:?missing repo_user}"
	local repo_password_file="${4:?missing repo_password_file}"
	local rv=0
	wget -e robots=off --cut-dirs=3 -np -R "index.html*" --user "$repo_user" \
		--password="$(< "$repo_password_file")" -r -l 10 \
		"https://service.software-univention.de/apt/00342/docs/keycloak/" || rv=$?
	cd service.software-univention.de/keycloak || rv=$?
	printf "[keycloak]\nlocalhost\n" > hosts.ini
	openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -subj "/CN=id-broker" -keyout id-broker.key -out id-broker.cert
	curl -k "https://ucs-sso.$traeger1_domain/simplesamlphp/saml2/idp/metadata.php" > schools_saml_IDP/traeger1_metadata.xml
	curl -k "https://ucs-sso.$traeger2_domain/simplesamlphp/saml2/idp/metadata.php" > schools_saml_IDP/traeger2_metadata.xml
	printf "register_idps:\n  - alias: traeger1\n    ucsschoolSourceUID: IDBROKER-traeger1\n    path: schools_saml_IDP/traeger1_metadata.xml\n  - alias: traeger2\n    ucsschoolSourceUID: IDBROKER-traeger2\n    path: schools_saml_IDP/traeger2_metadata.xml\n" > schools_saml_IDP/idps.yml
	return $rv
}

# register IDBroker as service in ucs IdP
register_idbroker_as_sp_in_ucs () {
	local broker_fqdn="${1:?missing broker_fqdn}"
	local broker_ip="${2:?missing broker_ip}"
	local keycloak_identifier="${3:?missing keycloak_identifier=}"
	local rv=0
	ucr set hosts/static/"$broker_ip"="$broker_fqdn"
	udm saml/idpconfig modify \
		--dn "id=default-saml-idp,cn=univention,$(ucr get ldap/base)" \
		--append LdapGetAttributes=entryUUID
 	curl -k "https://$broker_fqdn/auth/realms/ID-Broker/broker/traeger1/endpoint/descriptor" > metadata.xml
	udm saml/serviceprovider create \
		--position "cn=saml-serviceprovider,cn=univention,$(ucr get ldap/base)" \
		--set serviceProviderMetadata="$(cat metadata.xml)" \
		--set AssertionConsumerService="https://$broker_fqdn/auth/realms/ID-Broker/broker/$keycloak_identifier/endpoint" \
		--set Identifier="https://$broker_fqdn/auth/realms/ID-Broker/broker/$keycloak_identifier/endpoint/descriptor" \
		--set isActivated=TRUE \
		--set simplesamlNameIDAttribute=entryUUID \
		--set simplesamlAttributes=TRUE \
		--set attributesNameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri" \
		--set LDAPattributes=entryUUID || rv=$?
	return $rv

}

# vim:set filetype=sh ts=4:
