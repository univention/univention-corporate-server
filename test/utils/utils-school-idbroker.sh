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
	local keycloak_password="${5:?missing keycloak_password}"
	local kc1_ip="${6:?missing kc1_ip}"
	local kc2_ip="${7:?missing kc2_ip}"
	local db_extern="${8:?missing domain}"
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

	# TODO place files on service.software-univention
	cp /root/main.yml main.yml
	cp /root/vars.yml vars.yml
	cp /root/keycloak.yml keycloak.yml
	cp /root/JDBC_PING.cli JDBC_PING.cli
	cp /root/web_interface.yml web_interface.yml
	cp /root/database.yml database.yml

	cp /root/id-broker-TESTING.cert id-broker.cert
	cp /root/id-broker-TESTING.key id-broker.key
	# shellcheck disable=SC1091
	source /root/id-broker-secrets.sh
	sed -i "s/KEYCLOAK_IP/$kc1_ip/g" hosts.ini
	sed -i "s/KEYCLOAK2_IP/$kc2_ip/g" hosts.ini
	sed -i "s/DOMAIN/$db_extern/g" hosts.ini
	sed -i "s/hostssl keycloak keycloak KEYCLOAK2_IP/hostssl keycloak keycloak $kc2_ip/g" database.yml
	sed -i "s/BETTERMARKS_CLIENT_SECRET/$BETTERMARKS_CLIENT_SECRET/g" clients.yml
	sed -i "s/UTA_CLIENT_SECRET/$UTA_CLIENT_SECRET/g" clients.yml
	sed -i "s/UTA_REDIRECT/https:\/\/$(hostname -f)\/univention-test-app\/authorize/g" clients.yml
	sed -i "s/keycloak_password: admin/keycloak_password: $keycloak_password/g" vars.yml
	sed -i "s/CLIENT_SECRET=CLIENT_SECRET/CLIENT_SECRET=$UTA_CLIENT_SECRET/g" /etc/univention-test-app.conf
	sed -i "s/ID_BROKER_KEYCLOAK_FQDN=ID_BROKER_KEYCLOAK_FQDN/ID_BROKER_KEYCLOAK_FQDN=kc.$(hostname -d)/g" /etc/univention-test-app.conf
	sed -i "s/ID_BROKER_SDAPI_FQDN=ID_BROKER_SDAPI_FQDN/ID_BROKER_SDAPI_FQDN=self-disclosure1.$(hostname -d)/g" /etc/univention-test-app.conf
	echo "EXTERNAL_ROOT_URL=https://$(hostname -f)/univention-test-app/" >> /etc/univention-test-app.conf
	curl -k "https://ucs-sso.$traeger1_domain/simplesamlphp/saml2/idp/metadata.php" > schools_saml_IDP/traeger1_metadata.xml
	curl -k "https://ucs-sso.$traeger2_domain/simplesamlphp/saml2/idp/metadata.php" > schools_saml_IDP/traeger2_metadata.xml
	return $rv
}

create_certificate_kc_vhost () {
	univention-certificate new -name kc.broker.local -id 658b0aaf-48dc-4a32-991f-db46648b22a5 -days 365 || return 1
	return 0
}

apache_custom_vhosts () {
	local keycloak2_ip="${1:?missing keycloak2_ip}"
	local domain="${2:?missing domain}"
	univention-add-vhost --conffile /var/lib/keycloak/keycloak_ProxyPass.conf kc.broker.local 443
	cd /etc/apache2/sites-available/
	cp /root/univention-vhosts.conf.example univention-vhosts.conf
	sed -i "s/KEYCLOAK2_IP/$keycloak2_ip/g" univention-vhosts.conf
	sed -i "s/DOMAIN/$domain/g" univention-vhosts.conf
	cp /root/keycloak_ProxyPass.conf.example /var/lib/keycloak/keycloak_ProxyPass.conf
	sed -i "s/DOMAIN/$domain/g" /var/lib/keycloak/keycloak_ProxyPass.conf
	service apache2 restart || return 1
	return 0
}

ansible_run_keycloak_configuration () {
	local rv=0
	cd service.software-univention.de/keycloak || rv=$?
	/usr/local/bin/ansible-playbook -i hosts.ini main.yml || rv=$?
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
	curl -k "https://$broker_fqdn/auth/realms/ID-Broker/broker/$keycloak_identifier/endpoint/descriptor" > metadata.xml
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
		--set link="https://acc.bettermarks.com/auth/univention/DE_univention?kc_idp_hint=$keycloak_identifier" \
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
		--set link="https://$broker_fqdn/univention-test-app/?kc_idp_hint=$keycloak_identifier&pkce=y" \
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

	# wait for id connector "replication"
	# TODO find a better way
	local i=0
	local queue_entries=0
	local out_queues="/var/lib/univention-appcenter/apps/ucsschool-id-connector/data/out_queues"
	for i in $(seq 60); do
		sleep 10
		# shellcheck disable=SC2012
		queue_entries=$(ls ${out_queues}/*/*_ready.json 2>/dev/null | wc -l)
		[ 0 -eq "$queue_entries" ] && break
	done
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
	# TODO if certificates for kc2 are created
	# elif [ "$(hostname)" = "kc2" ]; then
	# 	ucr set --forced \
	# 		apache2/vhosts/login.kc2.broker0.dev.univention-id-broker.com/443/ssl/certificate="/etc/univention/letsencrypt/signed_chain.crt" \
	# 		apache2/vhosts/login.kc2.broker0.dev.univention-id-broker.com/443/ssl/key="/etc/univention/letsencrypt/domain.key"
	fi

	service apache2 restart || return 1

	return 0
}

install_id_connector_broker_plugin () {
	# until we have "ucsschool/extras" install the id connector
	# broker plugin from the 5.0 test repo
	echo "deb http://updates-test.software-univention.de/5.0/maintained/component/ idbroker_DEVEL/all/" > /etc/apt/sources.list.d/broker.list
	echo "deb http://updates-test.software-univention.de/5.0/maintained/component/ idbroker_DEVEL/amd64/" >> /etc/apt/sources.list.d/broker.list
	apt-get -y update || return 1
	apt-get -y install id-broker-id-connector-plugin || return 1
	univention-app configure ucsschool-id-connector --set 'ucsschool-id-connector/log_level'=DEBUG
	univention-app restart ucsschool-id-connector
}

# Setup dns entries for Traeger, to be able to download idp metadata
kvm_setup_dns_entries_in_broker () {
	# only for kvm
	[ "$KVM_BUILD_SERVER" = "EC2" ] && return 0
	udm dns/forward_zone create --set zone="${UCS_ENV_TRAEGER1_DOMAIN}" --set nameserver="$(hostname -f)." --position="cn=dns,$(ucr get ldap/base)" || return 1
	# shellcheck disable=SC2153
	udm dns/host_record create --set a="${TRAEGER1_IP}" --set name=ucs-sso --position zoneName="${UCS_ENV_TRAEGER1_DOMAIN},cn=dns,$(ucr get ldap/base)" || return 1
	udm dns/host_record create --set a="${TRAEGER1_IP}" --set name=traeger1 --position zoneName="${UCS_ENV_TRAEGER1_DOMAIN},cn=dns,$(ucr get ldap/base)" || return 1
	udm dns/forward_zone create --set zone="${UCS_ENV_TRAEGER2_DOMAIN}" --set nameserver="$(hostname -f)." --position="cn=dns,$(ucr get ldap/base)" || return 1
	# shellcheck disable=SC2153
	udm dns/host_record create --set a="${TRAEGER2_IP}" --set name=ucs-sso --position zoneName="${UCS_ENV_TRAEGER2_DOMAIN},cn=dns,$(ucr get ldap/base)" || return 1
	udm dns/host_record create --set a="${TRAEGER2_IP}" --set name=traeger2 --position zoneName="${UCS_ENV_TRAEGER2_DOMAIN},cn=dns,$(ucr get ldap/base)" || return 1
}

# add entry to ssh environment to pass variables via env
add_to_ssh_environment () {
	local entry="${1:?missing entry}"
	# add newline if missing
	[ -n "$(tail -c1 /root/.ssh/environment)" ] && printf '\n' >>/root/.ssh/environment
	echo "$entry" >> /root/.ssh/environment
}

# create hosts entry
add_to_hosts () {
	local ip="${1:?missing ip}"
	local fqdn="${2:?missing fqdn}"
	ucr set "hosts/static/$ip=$fqdn"
}

# setup the jump host for the id broker performance tests
prepare_jump_host () {
    apt-get -y update
    hostname jumphost
    DEBIAN_FRONTEND=noninteractive apt-get -y install id-broker-performance-tests
    echo 'root soft nofile 10240' >> /etc/security/limits.conf
    echo 'root hard nofile 10240' >> /etc/security/limits.conf
    echo "fs.file-max=1048576" > /etc/sysctl.d/99-file-max.conf
    sysctl -p
}

start_openvpn () {
    apt-get -y update
	apt-get -y install openvpn
	openvpn --config /root/vpn/client.conf --daemon
}

install_ansible () {
	apt-get -y update
	apt-get -y install python3-pip
	pip3 install ansible
}

# fix traeger host records for id broker kvm templates
fix_traeger_dns_entries_in_broker_domain () {
	local traeger1_ip="${1:?missing ip}"
	local traeger2_ip="${2:?missing ip}"
	udm dns/host_record modify --dn "relativeDomainName=traeger1,zoneName=traeger1.local,cn=dns,dc=idbroker,dc=local" --set a="$traeger1_ip"
	udm dns/host_record modify --dn "relativeDomainName=ucs-sso,zoneName=traeger1.local,cn=dns,dc=idbroker,dc=local" --set a="$traeger1_ip"
	udm dns/host_record modify --dn "relativeDomainName=traeger2,zoneName=traeger2.local,cn=dns,dc=idbroker,dc=local" --set a="$traeger2_ip"
	udm dns/host_record modify --dn "relativeDomainName=ucs-sso,zoneName=traeger2.local,cn=dns,dc=idbroker,dc=local" --set a="$traeger2_ip"
	# ucs sso TODO add other systems
	udm dns/host_record modify --dn "relativeDomainName=ucs-sso,zoneName=$(ucr get domainname),cn=dns,$(ucr get ldap/base)" --set a="$(ucr get interfaces/eth0/address)"
}

fix_broker_dns_entries_on_traeger () {
	local kc1_ip="${1:?missing ip}"
	local provisioning1_ip="${2:?missing ip}"
	# kc1
	ucr search --value --brief login.kc1.broker.local | awk -F : '{print $1}' | xargs  ucr unset
	# shellcheck disable=SC2140
	ucr set "hosts/static/$kc1_ip"="login.kc1.broker.local"
	# provisioning1
	udm dns/host_record modify --dn "relativeDomainName=provisioning1,zoneName=broker.local,cn=dns,$(ucr get ldap/base)" --set a="$provisioning1_ip"
	# ucs sso
	udm dns/host_record modify --dn "relativeDomainName=ucs-sso,zoneName=$(ucr get domainname),cn=dns,$(ucr get ldap/base)" --set a="$(ucr get interfaces/eth0/address)"
}

# make env file available in ssh session
set_env_variables_from_env_file () {
	local env_file="${1:?missing env file}"
	while read -r entry; do
		add_to_ssh_environment "$entry"
	done < "$env_file"
	return 0
}

# we pass locust env vars like this from jenkins to the instance
# (docker can't handle newlines in env files :-( )
#    UCS_ENV_LOCUST_VARS=var1=val1:DELIM:var2=val 2:DELIM...
# this function makes proper env var from this
set_locust_env_vars () {
	local locust_vars="${1:-"LOCUST_LOGLEVEL=info:DELIM:LOCUST_RUN_TIME=5m:DELIM:LOCUST_SPAWN_RATE=0.03333:DELIM:LOCUST_STOP_TIMEOUT=60:DELIM:LOCUST_USERS=8"}"
	local IFS=$'\n'
	for entry in ${locust_vars//:DELIM:/$'\n'}; do
		add_to_ssh_environment "$entry"
	done
}

performance_optimizations_broker () {
	# just for our tests
	ucr set ldap/database/mdb/envflags=nosync
	# official
	# Deactivate expensive updates of the NSS and the portal group cache and add regular portal group updates at night
	ucr set \
		nss/group/cachefile/invalidate_on_changes=no \
		cron/portal_groups/command='/usr/sbin/univention-portal update --reason ldap:group' \
		cron/portal_groups/time='30 4 * * *' \
		cron/portal_groups/description='Update UCS portal group cache.'
	# TODO activate once Bug 54696 is fixed
	#ucr set listener/module/portal_groups/deactivate=yes
}

performance_optimizations_traeger () {
	# just for our tests
	ucr set ldap/database/mdb/envflags=nosync
}

# vim:set filetype=sh ts=4:
