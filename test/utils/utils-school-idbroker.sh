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

ansible_preperation () {
	local traeger1_domain="${1:?missing traeger1_domain}"
	local traeger2_domain="${2:?missing traeger2_domain}"
	local repo_user="${3:?missing repo_user}"
	local repo_password_file="${4:?missing repo_password_file}"
	local rv=0
	# Setup passwordless ssh login for ansible
	ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -q -N ""
	cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
	ssh -o "StrictHostKeyChecking=accept-new" localhost true
	# Download ansible scripts
	wget -e robots=off --cut-dirs=3 -np -R "index.html*" --user "$repo_user" \
		--password="$(< "$repo_password_file")" -r -l 10 \
		"https://service.software-univention.de/apt/00342/docs/keycloak/" || rv=$?
	cd service.software-univention.de/keycloak || rv=$?
	# check the jenkins-data repo for the following files
	cp /root/hosts.ini hosts.ini
	cp /root/idps.yml schools_saml_IDP/idps.yml
	cp /root/clients.yml clients.yml
	cp /root/id-broker-TESTING.cert id-broker.cert
	cp /root/id-broker-TESTING.key id-broker.key
	source /root/id-broker-secrets.sh
	sed -i "s/BETTERMARKS_CLIENT_SECRET/$BETTERMARKS_CLIENT_SECRET/g" clients.yml
	sed -i "s/UTA_CLIENT_SECRET/$UTA_CLIENT_SECRET/g" clients.yml
	sed -i "s/UTA_REDIRECT/https:\/\/$(hostname -f)\/univention-test-app\/authorize/g" clients.yml
	sed -i "s/keycloak_user: admin/keycloak_user: $KC_ADMIN_USER/g" keycloak.yml
	sed -i "s/keycloak_password: admin/keycloak_password: $KC_ADMIN_PASS/g" keycloak.yml
	sed -i "s/CLIENT_SECRET=CLIENT_SECRET/CLIENT_SECRET=$UTA_CLIENT_SECRET/g" /etc/univention-test-app.conf
	sed -i "s/ID_BROKER_KEYCLOAK_FQDN=ID_BROKER_KEYCLOAK_FQDN/ID_BROKER_KEYCLOAK_FQDN=$(hostname -f)/g" /etc/univention-test-app.conf
	curl -k "https://ucs-sso.$traeger1_domain/simplesamlphp/saml2/idp/metadata.php" > schools_saml_IDP/traeger1_metadata.xml
	curl -k "https://ucs-sso.$traeger2_domain/simplesamlphp/saml2/idp/metadata.php" > schools_saml_IDP/traeger2_metadata.xml
	return $rv
}

ansible_run_keycloak_configuration () {
	local rv=0
	cd service.software-univention.de/keycloak || rv=$?
	/usr/local/bin/ansible-playbook -i hosts.ini keycloak.yml || rv=$?
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

add_bettermarks_app_portal_link () {
	local keycloak_identifier="${1:?missing keycloak_identifier=}"
	local rv=0
	udm settings/portal_entry create \
		--position "cn=portal,cn=univention,$(ucr get ldap/base)" \
		--set activated=TRUE \
		--set authRestriction=anonymous \
		--set category=service \
		--set description="en_US \"bettermarks is an adaptive learning system for maths\"" \
		--set displayName="en_US \"bettermarks\"" \
		--set link="https://acc.bettermarks.com/auth/univention/DE_univention/?kc_idp_hint=$keycloak_identifier" \
		--set linkTarget=useportaldefault \
		--set name=bettermarks \
		--set portal="cn=ucsschool_demo_portal,cn=portal,cn=univention,$(ucr get ldap/base)" \
		--set icon="$(base64 bettermarks-logo.svg)" || rv=$?
}

add_test_app_portal_link () {
	local broker_fqdn="${1:?missing broker_fqdn}"
	local keycloak_identifier="${2:?missing keycloak_identifier=}"
	local rv=0
	udm settings/portal_entry create \
		--position "cn=portal,cn=univention,$(ucr get ldap/base)" \
		--set activated=TRUE \
		--set authRestriction=anonymous \
		--set category=service \
		--set description="en_US \"Test app to check oauth login and tokens\"" \
		--set displayName="en_US \"Test oauth\"" \
		--set link="https://$broker_fqdn/univention-test-app/?kc_idp_hint=$keycloak_identifier" \
		--set linkTarget=useportaldefault \
		--set name=univention-test-app \
		--set portal="cn=ucsschool_demo_portal,cn=portal,cn=univention,$(ucr get ldap/base)" \
		--set icon="$(base64 oidc-logo.svg)" || rv=$?
	return $rv
}

create_id_connector_school_authority_config () {
  local domain_admin_password="${1:?missing domain_admin_password}"
  local provisioning_fqdn="${2:?missing provisioning_fqdn}"
  local config_name="${3:?missing config_name}"
  local username="${4:?missing username}"
  local password="${5:?missing password}"

  token="$(curl -s -X POST "https://$(hostname -f)/ucsschool-id-connector/api/token" \
    -H "accept: application/json" \
    -H "Content-Type:application/x-www-form-urlencoded" \
    -d "username=Administrator" \
    -d "password=$domain_admin_password" \
    | python -c "import json, sys; print(json.loads(sys.stdin.read())['access_token'])" \
    )"
  curl -X POST "https://$(hostname -f)/ucsschool-id-connector/api/v1/school_authorities" \
    -H "accept: application/json" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"$config_name\",
      \"active\": true,
      \"url\": \"https://$provisioning_fqdn/\",
      \"plugins\": [\"id_broker-users\", \"id_broker-groups\"],
      \"plugin_configs\": {
          \"id_broker\": {
              \"password\": \"$password\",
              \"username\": \"$username\",
              \"version\": 1
          }
      }
  }"
}

create_school_users_classes () {
  local ou1="ou1"
  local ou2="ou2"

  /usr/share/ucs-school-import/scripts/create_ou "$ou1"
  /usr/share/ucs-school-import/scripts/create_ou "$ou2"
  i=1; python -m ucsschool.lib.models create --name "stud${i}"  --set firstname "Traeger${i}" --set lastname "Student${i}" --set password univention --school DEMOSCHOOL Student
  i=1; python -m ucsschool.lib.models create --name "teach${i}" --set firstname "Traeger${i}" --set lastname "Teacher${i}" --set password univention --school DEMOSCHOOL Teacher
  i=2; python -m ucsschool.lib.models create --name "stud${i}"  --set firstname "Traeger${i}" --set lastname "Student${i}" --set password univention --school DEMOSCHOOL --append schools DEMOSCHOOL --append schools "$ou1" Student
  i=2; python -m ucsschool.lib.models create --name "teach${i}" --set firstname "Traeger${i}" --set lastname "Teacher${i}" --set password univention --school DEMOSCHOOL --append schools DEMOSCHOOL --append schools "$ou1" Teacher
  i=3; python -m ucsschool.lib.models create --name "stud${i}"  --set firstname "Traeger${i}" --set lastname "Student${i}" --set password univention --school "$ou1"     --append schools "$ou1"     --append schools "$ou2" Student
  i=3; python -m ucsschool.lib.models create --name "teach${i}" --set firstname "Traeger${i}" --set lastname "Teacher${i}" --set password univention --school "$ou1"     --append schools "$ou1"     --append schools "$ou2" Teacher
  python -m ucsschool.lib.models modify --dn "cn=DEMOSCHOOL-Democlass,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=stud1,cn=schueler,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=stud2,cn=schueler,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=teach1,cn=lehrer,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=teach2,cn=lehrer,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" SchoolClass
  python -m ucsschool.lib.models create SchoolClass \
    --name "${ou1}-1a" \
    --school "$ou1" \
    --append users "uid=stud2,cn=schueler,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=stud3,cn=schueler,cn=users,ou=${ou1},$(ucr get ldap/base)" \
    --append users "uid=teach2,cn=lehrer,cn=users,ou=DEMOSCHOOL,$(ucr get ldap/base)" \
    --append users "uid=teach3,cn=lehrer,cn=users,ou=${ou1},$(ucr get ldap/base)"
  python -m ucsschool.lib.models create SchoolClass \
    --name "${ou2}-1a" \
    --school "$ou2" \
    --append users "uid=stud3,cn=schueler,cn=users,ou=${ou1},$(ucr get ldap/base)" \
    --append users "uid=teach3,cn=lehrer,cn=users,ou=${ou1},$(ucr get ldap/base)"
}

# install letsencrypt and copy certificate files from local
setup_letsencrypt () {

	# only for EC2
	test "$KVM_BUILD_SERVER" = "EC2" ||  return 0

	local admin_password="${1:?missing admin_password}"
	local domains="${2:?missing domains}"
	local password_file

	password_file="$(mktemp)"
	echo "$admin_password" > "$password_file"

	univention-app install "letsencrypt" --noninteractive --username="Administrator" --pwdfile="$password_file" || return 1
	cp /root/letsencrypt/domain.key /root/letsencrypt/account.key /root/letsencrypt/signed_chain.crt /root/letsencrypt/domain.csr /etc/univention/letsencrypt/ || return 1
	ucr set \
		letsencrypt/domains="$domains" \
		apache2/ssl/certificate="/etc/univention/letsencrypt/signed_chain.crt" \
		apache2/ssl/key="/etc/univention/letsencrypt/domain.key"

	# special setup for keycloak and ucs-sso vhosts
	if [ "$(hostname)" = "traeger1" ] || [ "$(hostname)" = "traeger2" ]; then
		ucr set \
			saml/apache2/ssl/certificate="/etc/univention/letsencrypt/signed_chain.crt" \
			saml/apache2/ssl/key="/etc/univention/letsencrypt/domain.key"
	elif [ "$(hostname)" = "kc1" ]; then
		ucr set --forced \
			apache2/vhosts/login.kc1.broker0.dev.univention-id-broker.com/443/ssl/certificate="/etc/univention/letsencrypt/signed_chain.crt" \
			apache2/vhosts/login.kc1.broker0.dev.univention-id-broker.com/443/ssl/key="/etc/univention/letsencrypt/domain.key"
	fi


	service apache2 restart || return 1

	return 0
}


# vim:set filetype=sh ts=4:
