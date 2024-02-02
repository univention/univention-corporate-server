#!/bin/bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2022-2024 Univention GmbH
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
	# Setup passwordless ssh login for ansible
	ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -q -N ""
	cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
	ssh -o "StrictHostKeyChecking=accept-new" localhost true
	# Download ansible scripts
	#wget "http://service.knut.univention.de/apt/00342/deployment/keycloak/ansible_playbook.tar.gz"
	wget --user "$repo_user" --password="$(< "$repo_password_file")" \
		"https://service.software-univention.de/apt/00342/deployment/keycloak/ansible_playbook.tar.gz" || return $?
	tar -xf ansible_playbook.tar.gz
	cd deployment || return $?
	# check the jenkins-data repo for the following files
	cp /root/id-broker-TESTING.cert id-broker.cert
	cp /root/id-broker-TESTING.key id-broker.key
	# shellcheck disable=SC1091
	. /root/id-broker-secrets.sh
	sed -i "s/broker.local/$(hostname -d)/g" inventories/jenkins/hosts
	sed -i "s/CLIENT_SECRET=CLIENT_SECRET/CLIENT_SECRET=$UTA_CLIENT_SECRET/g" /etc/univention-test-app.conf
	sed -i "s/ID_BROKER_KEYCLOAK_FQDN=ID_BROKER_KEYCLOAK_FQDN/ID_BROKER_KEYCLOAK_FQDN=kc.$(hostname -d)/g" /etc/univention-test-app.conf
	sed -i "s/ID_BROKER_SDAPI_FQDN=ID_BROKER_SDAPI_FQDN/ID_BROKER_SDAPI_FQDN=self-disclosure1.$(hostname -d)/g" /etc/univention-test-app.conf
	echo "EXTERNAL_ROOT_URL=https://$(hostname -f)/univention-test-app/" >> /etc/univention-test-app.conf
	curl -k "https://ucs-sso.$traeger1_domain/simplesamlphp/saml2/idp/metadata.php" > files/jenkins/univention_id_broker/idp_metadata/traeger1_metadata.xml
	curl -k "https://ucs-sso.$traeger2_domain/simplesamlphp/saml2/idp/metadata.php" > files/jenkins/univention_id_broker/idp_metadata/traeger2_metadata.xml
}

create_certificate_kc_vhost () {
	univention-certificate new -name kc.broker.test -id 658b0aaf-48dc-4a32-991f-db46648b22a5 -days 365
}

wait_for_certificate_replication () {
	local end=$(($(date +%s)+1500))
	while [ "$(date +%s)" -lt "$end" ]
	do
		[ -d "/etc/univention/ssl/kc.broker.test/" ] &&
			return 0
		sleep 5
	done
	return 1
}

apache_custom_vhosts () {
	local keycloak2_ip="${1:?missing keycloak2_ip}"
	local domain="${2:?missing domain}"
	univention-add-vhost --conffile /var/lib/keycloak/keycloak_ProxyPass.conf kc.broker.test 443
	cd /etc/apache2/sites-available/ || return 1
	cp /root/univention-vhosts.conf.example univention-vhosts.conf
	sed -i "s/KEYCLOAK2_IP/$keycloak2_ip/g" univention-vhosts.conf
	sed -i "s/DOMAIN/$domain/g" univention-vhosts.conf
	cp /root/keycloak_ProxyPass.conf.example /var/lib/keycloak/keycloak_ProxyPass.conf
	sed -i "s/DOMAIN/$domain/g" /var/lib/keycloak/keycloak_ProxyPass.conf
	service apache2 restart
}

ansible_run_keycloak_configuration () {
	cd deployment || return $?
	/usr/local/bin/ansible-galaxy install -r requirements.yml
	ANSIBLE_LOG_PATH=ansible.log /usr/local/bin/ansible-playbook site.yml --vault-password-file /root/idbroker_jenkins_ansible.password -i inventories/jenkins
}

# register IDBroker as service in ucs IdP
register_idbroker_as_sp_in_ucs () {
	local broker_fqdn="${1:?missing broker_fqdn}"
	local broker_ip="${2:?missing broker_ip}"
	local keycloak_identifier="${3:?missing keycloak_identifier=}"
	local lb
	lb="$(ucr get ldap/base)"
	ucr set hosts/static/"$broker_ip"="$broker_fqdn"
	udm saml/idpconfig modify \
		--dn "id=default-saml-idp,cn=univention,${lb}" \
		--append LdapGetAttributes=entryUUID
	curl -k "https://$broker_fqdn/auth/realms/ID-Broker/broker/$keycloak_identifier/endpoint/descriptor" > metadata.xml
	udm saml/serviceprovider create \
		--position "cn=saml-serviceprovider,cn=univention,${lb}" \
		--set serviceProviderMetadata="$(cat metadata.xml)" \
		--set AssertionConsumerService="https://$broker_fqdn/auth/realms/ID-Broker/broker/$keycloak_identifier/endpoint" \
		--set Identifier="https://$broker_fqdn/auth/realms/ID-Broker/broker/$keycloak_identifier/endpoint/descriptor" \
		--set isActivated=TRUE \
		--set simplesamlNameIDAttribute=entryUUID \
		--set simplesamlAttributes=TRUE \
		--set attributesNameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri" \
		--set LDAPattributes='entryUUID entryUUID' || return 1
}

add_bettermarks_app_portal_link () {
	local keycloak_identifier="${1:?missing keycloak_identifier=}"
	local lb
	lb="$(ucr get ldap/base)"
	if udm portals/entry list &> /dev/null; then
		# UCS >= 5.0
		udm portals/entry create \
			--position "cn=entry,cn=portals,cn=univention,${lb}" \
			--set activated=TRUE \
			--set description="en_US \"bettermarks is an adaptive learning system for maths\"" \
			--set displayName="en_US \"bettermarks\"" \
			--set link="en_US \"https://acc.bettermarks.com/auth/univention/DE_univention?kc_idp_hint=$keycloak_identifier\"" \
			--set linkTarget=useportaldefault \
			--set name=bettermarks \
			--set icon="$(base64 bettermarks-logo.svg)"
		udm portals/category modify \
			--dn "cn=domain-service,cn=category,cn=portals,cn=univention,${lb}" \
			--append entries="cn=bettermarks,cn=entry,cn=portals,cn=univention,${lb}"
	else
		# UCS < 5.0
		udm settings/portal_entry create \
			--position "cn=portal,cn=univention,${lb}" \
			--set activated=TRUE \
			--set authRestriction=anonymous \
			--set category=service \
			--set description="en_US \"bettermarks is an adaptive learning system for maths\"" \
			--set displayName="en_US \"bettermarks\"" \
			--set link="https://acc.bettermarks.com/auth/univention/DE_univention?kc_idp_hint=$keycloak_identifier" \
			--set linkTarget=useportaldefault \
			--set name=bettermarks \
			--set portal="cn=ucsschool_demo_portal,cn=portal,cn=univention,${lb}" \
			--set icon="$(base64 bettermarks-logo.svg)"
	fi
}

add_test_app_portal_link () {
	local broker_fqdn="${1:?missing broker_fqdn}"
	local keycloak_identifier="${2:?missing keycloak_identifier=}"
	local lb
	lb="$(ucr get ldap/base)"
	if udm portals/entry list &> /dev/null; then
		# UCS >= 5.0
		udm portals/entry create \
			--position "cn=entry,cn=portals,cn=univention,${lb}" \
			--set activated=TRUE \
			--set description="en_US \"Test app to check oauth login and tokens\"" \
			--set displayName="en_US \"Test oauth\"" \
			--set link="en_US \"https://$broker_fqdn/univention-test-app/?kc_idp_hint=$keycloak_identifier&pkce=y\"" \
			--set linkTarget=useportaldefault \
			--set name=univention-test-app \
			--set icon="$(base64 oidc-logo.svg)"
		udm portals/category modify \
			--dn "cn=domain-service,cn=category,cn=portals,cn=univention,${lb}" \
			--append entries="cn=univention-test-app,cn=entry,cn=portals,cn=univention,${lb}"
	else
		# UCS < 5.0
		udm settings/portal_entry create \
			--position "cn=portal,cn=univention,${lb}" \
			--set activated=TRUE \
			--set authRestriction=anonymous \
			--set category=service \
			--set description="en_US \"Test app to check oauth login and tokens\"" \
			--set displayName="en_US \"Test oauth\"" \
			--set link="https://$broker_fqdn/univention-test-app/?kc_idp_hint=$keycloak_identifier&pkce=y" \
			--set linkTarget=useportaldefault \
			--set name=univention-test-app \
			--set portal="cn=ucsschool_demo_portal,cn=portal,cn=univention,${lb}" \
			--set icon="$(base64 oidc-logo.svg)"
	fi
}

create_id_connector_school_authority_config () {
	local domain_admin_password="${1:?missing domain_admin_password}"
	local provisioning_fqdn="${2:?missing provisioning_fqdn}"
	local config_name="${3:?missing config_name}"
	local username="${4:?missing username}"
	local password="${5:?missing password}"
	local token

	token="$(curl -s -X POST "https://$(hostname -f)/ucsschool-id-connector/api/token" \
		-H 'accept: application/json' \
		-H 'Content-Type:application/x-www-form-urlencoded' \
		-d 'username=Administrator' \
		-d "password=$domain_admin_password" |
		python -c "import json, sys; print(json.loads(sys.stdin.read())['access_token'])")"
	curl -X POST "https://$(hostname -f)/ucsschool-id-connector/api/v1/school_authorities" \
		-H 'accept: application/json' \
		-H "Authorization: Bearer $token" \
		-H 'Content-Type: application/json' \
		-d "{
				\"name\": \"$config_name\",
				\"active\": true,
				\"url\": \"https://$provisioning_fqdn/\",
				\"plugins\": [\"id_broker-users\", \"id_broker-groups\"],
				\"plugin_configs\": {
					\"id_broker\": {
						\"password\": \"$password\",
						\"username\": \"$username\",
						\"schools\": [\"DEMOSCHOOL\", \"ou1\", \"ou2\"],
						\"version\": 1
					}
				}
		}"
}

create_school_users_classes () {
	local ou1="ou1"
	local ou2="ou2"
	local lb
	lb="$(ucr get ldap/base)"

	/usr/share/ucs-school-import/scripts/create_ou "$ou1"
	/usr/share/ucs-school-import/scripts/create_ou "$ou2"
	i=1; python -m ucsschool.lib.models create --name "stud${i}"  --set firstname "Traeger${i}" --set lastname "Student${i}" --set password univention --school DEMOSCHOOL Student
	i=1; python -m ucsschool.lib.models create --name "teach${i}" --set firstname "Traeger${i}" --set lastname "Teacher${i}" --set password univention --school DEMOSCHOOL Teacher
	i=2; python -m ucsschool.lib.models create --name "stud${i}"  --set firstname "Traeger${i}" --set lastname "Student${i}" --set password univention --school DEMOSCHOOL --append schools DEMOSCHOOL --append schools "$ou1" Student
	i=2; python -m ucsschool.lib.models create --name "teach${i}" --set firstname "Traeger${i}" --set lastname "Teacher${i}" --set password univention --school DEMOSCHOOL --append schools DEMOSCHOOL --append schools "$ou1" Teacher
	i=3; python -m ucsschool.lib.models create --name "stud${i}"  --set firstname "Traeger${i}" --set lastname "Student${i}" --set password univention --school "$ou1"     --append schools "$ou1"     --append schools "$ou2" Student
	i=3; python -m ucsschool.lib.models create --name "teach${i}" --set firstname "Traeger${i}" --set lastname "Teacher${i}" --set password univention --school "$ou1"     --append schools "$ou1"     --append schools "$ou2" Teacher
	python -m ucsschool.lib.models modify --dn "cn=DEMOSCHOOL-Democlass,cn=klassen,cn=schueler,cn=groups,ou=DEMOSCHOOL,${lb}" \
		--append users "uid=stud1,cn=schueler,cn=users,ou=DEMOSCHOOL,${lb}" \
		--append users "uid=stud2,cn=schueler,cn=users,ou=DEMOSCHOOL,${lb}" \
		--append users "uid=teach1,cn=lehrer,cn=users,ou=DEMOSCHOOL,${lb}" \
		--append users "uid=teach2,cn=lehrer,cn=users,ou=DEMOSCHOOL,${lb}" SchoolClass
	python -m ucsschool.lib.models create SchoolClass \
		--name "${ou1}-1a" \
		--school "$ou1" \
		--append users "uid=stud2,cn=schueler,cn=users,ou=DEMOSCHOOL,${lb}" \
		--append users "uid=stud3,cn=schueler,cn=users,ou=${ou1},${lb}" \
		--append users "uid=teach2,cn=lehrer,cn=users,ou=DEMOSCHOOL,${lb}" \
		--append users "uid=teach3,cn=lehrer,cn=users,ou=${ou1},${lb}"
	python -m ucsschool.lib.models create SchoolClass \
		--name "${ou2}-1a" \
		--school "$ou2" \
		--append users "uid=stud3,cn=schueler,cn=users,ou=${ou1},${lb}" \
		--append users "uid=teach3,cn=lehrer,cn=users,ou=${ou1},${lb}"
	python -m ucsschool.lib.models create Workgroup \
		--name "${ou1}-wg1" \
		--school "$ou1" \
		--append users "uid=stud2,cn=schueler,cn=users,ou=DEMOSCHOOL,${lb}" \
		--append users "uid=stud3,cn=schueler,cn=users,ou=${ou1},${lb}" \
		--append users "uid=teach2,cn=lehrer,cn=users,ou=DEMOSCHOOL,${lb}" \
		--append users "uid=teach3,cn=lehrer,cn=users,ou=${ou1},${lb}"
	python -m ucsschool.lib.models create Workgroup \
		--name "${ou2}-wg1" \
		--school "$ou2" \
		--append users "uid=stud3,cn=schueler,cn=users,ou=${ou1},${lb}" \
		--append users "uid=teach3,cn=lehrer,cn=users,ou=${ou1},${lb}"

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

	service apache2 restart
}

install_id_connector_broker_plugin () {
	# until we have "ucsschool/extras" install the id connector
	# broker plugin from the 5.0 test repo
	echo "deb http://updates-test.software-univention.de/5.0/maintained/component/ idbroker_DEVEL/all/" > /etc/apt/sources.list.d/broker.list
	echo "deb http://updates-test.software-univention.de/5.0/maintained/component/ idbroker_DEVEL/amd64/" >> /etc/apt/sources.list.d/broker.list
	apt-get -q update || return 1
	apt-get -y install id-broker-id-connector-plugin || return 1
	univention-app configure ucsschool-id-connector --set 'ucsschool-id-connector/log_level'=DEBUG
	univention-app restart ucsschool-id-connector
}

# Setup dns entries for Traeger, to be able to download idp metadata
kvm_setup_dns_entries_in_broker () {
	# only for kvm
	[ "$KVM_BUILD_SERVER" = "EC2" ] && return 0
	local lb
	lb="$(ucr get ldap/base)"
	udm dns/forward_zone create --set zone="${UCS_ENV_TRAEGER1_DOMAIN}" --set nameserver="$(hostname -f)." --position="cn=dns,${lb}" || return 1
	# shellcheck disable=SC2153
	udm dns/host_record create --set a="${TRAEGER1_IP}" --set name=ucs-sso --position zoneName="${UCS_ENV_TRAEGER1_DOMAIN},cn=dns,${lb}" || return 1
	udm dns/host_record create --set a="${TRAEGER1_IP}" --set name=traeger1 --position zoneName="${UCS_ENV_TRAEGER1_DOMAIN},cn=dns,${lb}" || return 1
	udm dns/forward_zone create --set zone="${UCS_ENV_TRAEGER2_DOMAIN}" --set nameserver="$(hostname -f)." --position="cn=dns,${lb}" || return 1
	# shellcheck disable=SC2153
	udm dns/host_record create --set a="${TRAEGER2_IP}" --set name=ucs-sso --position zoneName="${UCS_ENV_TRAEGER2_DOMAIN},cn=dns,${lb}" || return 1
	udm dns/host_record create --set a="${TRAEGER2_IP}" --set name=traeger2 --position zoneName="${UCS_ENV_TRAEGER2_DOMAIN},cn=dns,${lb}" || return 1
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
	apt-get -q update
	hostname jumphost
	ucr set repository/online=true
	DEBIAN_FRONTEND=noninteractive univention-install -y id-broker-performance-tests
	echo 'root soft nofile 10240' >> /etc/security/limits.conf
	echo 'root hard nofile 10240' >> /etc/security/limits.conf
	echo "fs.file-max=1048576" > /etc/sysctl.d/99-file-max.conf
	sysctl -p
}

start_openvpn () {
	apt-get -q update
	apt-get -y install openvpn
	openvpn --config /root/vpn/client.conf --daemon
}

install_ansible () {
	apt-get -q update
	apt-get -y install python3-pip
	pip3 install 'ansible<=2.11.12'
}

# fix traeger host records for id broker kvm templates
fix_traeger_dns_entries_in_broker_domain () {
	local traeger1_ip="${1:?missing ip}"
	local traeger2_ip="${2:?missing ip}"
	local lb
	lb="$(ucr get ldap/base)"
	udm dns/host_record modify --dn "relativeDomainName=traeger1,zoneName=traeger1.test,cn=dns,${lb}" --set a="$traeger1_ip"
	udm dns/host_record modify --dn "relativeDomainName=ucs-sso,zoneName=traeger1.test,cn=dns,${lb}" --set a="$traeger1_ip"
	udm dns/host_record modify --dn "relativeDomainName=traeger2,zoneName=traeger2.test,cn=dns,${lb}" --set a="$traeger2_ip"
	udm dns/host_record modify --dn "relativeDomainName=ucs-sso,zoneName=traeger2.test,cn=dns,${lb}" --set a="$traeger2_ip"
	# ucs sso TODO add other systems
	udm dns/host_record modify --dn "relativeDomainName=ucs-sso,zoneName=$(ucr get domainname),cn=dns,${lb}" --set a="$(ucr get interfaces/eth0/address)"
}

fix_broker_dns_entries_on_traeger () {
	local kc1_ip="${1:?missing ip}"
	local provisioning1_ip="${2:?missing ip}"
	# kc1
	ucr search --value --brief login.kc1.broker.test | cut -d: -f1 | xargs -r ucr unset
	# shellcheck disable=SC2140
	ucr set "hosts/static/$kc1_ip"="login.kc1.broker.test"
	# provisioning1
	udm dns/host_record modify --dn "relativeDomainName=provisioning1,zoneName=broker.test,cn=dns,$(ucr get ldap/base)" --set a="$provisioning1_ip"
	# ucs sso
	udm dns/host_record modify --dn "relativeDomainName=ucs-sso,zoneName=$(ucr get domainname),cn=dns,$(ucr get ldap/base)" --set a="$(ucr get interfaces/eth0/address)"
}

fix_keycloak_container_in_template () {
	local id ip cfg
	id="$(docker inspect keycloak --format '{{ .Id }}')"
	ip="$(ucr get interfaces/eth0/address)"
	cfg="/var/lib/docker/containers/$id/config.v2.json"
	docker stop keycloak
	python3 - <<EOF || return 1
import json
new_env = []
with open("$cfg", "r") as f:
    data = json.load(f)
for env in data["Config"]["Env"]:
    # remove admin settings, otherwise container won't start
    # with User with username 'admin' already added to
    # '/opt/jboss/keycloak/standalone/configuration/keycloak-add-user.json'
    if env.startswith("KEYCLOAK_PASSWORD="):
        continue
    # update ip
    if env.startswith("JGROUPS_DISCOVERY_EXTERNAL_IP="):
        env = "JGROUPS_DISCOVERY_EXTERNAL_IP=$ip"
    new_env.append(env)
data["Config"]["Env"] = new_env
with open("$cfg", "w") as f:
    json.dump(data, f)
EOF
	service docker restart
	docker start keycloak
	sleep 120
}

# make env file available in ssh session
set_env_variables_from_env_file () {
	local env_file="${1:?missing env file}"
	local entry
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
	local IFS=$'\n' entry
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
	ucr set listener/module/portal_groups/deactivate=yes
}

performance_optimizations_traeger () {
	# just for our tests
	ucr set ldap/database/mdb/envflags=nosync
}

setup_kelvin_udm_rest () {
	ucr set directory/manager/rest/processes=0
	univention-app configure ucsschool-kelvin-rest-api --set ucsschool/kelvin/processes=0 --set ucsschool/kelvin/log_level=DEBUG
	systemctl restart univention-directory-manager-rest
	univention-app restart ucsschool-kelvin-rest-api
}

add_broker_ca_to_host_and_idconnector () {
	local primary_ip="${1:?missing primary ip}"
	curl -k "https://$primary_ip/ucs-root-ca.crt" > /usr/local/share/ca-certificates/idbroker.crt
	update-ca-certificates
	docker cp /usr/local/share/ca-certificates/idbroker.crt "$(ucr get appcenter/apps/ucsschool-id-connector/container)":/usr/local/share/ca-certificates/idbroker.crt
	univention-app shell ucsschool-id-connector update-ca-certificates
}

add_dns_for_ID-Broker () {
	local broker_domain="${1:?missing broker domain}"
	local primary_ip="${2:?missing ID-Broker primary ip}"
	local provisioning_ip="${3:?missing provisioning ip}"
	udm dns/forward_zone create \
		--set zone="$broker_domain" \
		--set nameserver="$(hostname -f)." \
		--position="cn=dns,$(ucr get ldap/base)" || return 1
	udm dns/host_record create \
		--set a="$primary_ip" \
		--set name=idbroker-primary \
		--position "zoneName=$broker_domain,cn=dns,$(ucr get ldap/base)" || return 1
	udm dns/host_record create \
		--set a="$provisioning_ip" \
		--set name=provisioning1 \
		--position "zoneName=$broker_domain,cn=dns,$(ucr get ldap/base)" || return 1
	while ! nslookup "provisioning1.$broker_domain" | grep -q "$provisioning_ip"; do
		echo "Waiting for DNS..."
		sleep 1
	done
}

wait_for_sddb_provisioning () {
    if ! univention-app status id-broker-sddb-builder; then
        echo "No id-broker-sddb-builder running"
        return 0
    fi
    while true; do
        echo "Waiting for appcenter listener"
        sleep 10
        new_listener_objects=$(find /var/lib/univention-appcenter/apps/id-broker-sddb-builder/data/listener/ -name "*.json" | wc -l)

        if [[ "$new_listener_objects" -gt 0 ]]; then
            echo "$new_listener_objects new appcenter listener objects"
            univention-app shell id-broker-sddb-builder /tmp/univention-id-broker-sddb-builder.listener_trigger >> sddb_listener.log 2>&1
        else
            break
        fi
    done
    while true; do
        echo "Waiting for converter daemon"
        sleep 10
        queue_length=$(univention-app shell id-broker-sddb-builder sddb-builder queues length regular)
        if [[ "$queue_length" -gt 0 ]]; then
            echo "$queue_length items on converter queue"
        else
            echo "converter daemon queue is empty"
            break
        fi
    done
}

resync_sddb () {
    if ! univention-app status id-broker-sddb-builder; then
        echo "No id-broker-sddb-builder running"
        return 0
    fi
    univention-app shell id-broker-sddb-builder sddb-builder queues bulk-append regular sp_mapping ""
    echo "Append all ucsschool items to queue"
    schools=$(python3 -c 'from ucsschool.lib.models.school import School; from univention.uldap import getMachineConnection; lo = getMachineConnection(); print(" ".join(school.name for school in School.get_all(lo, filter_str="(ucsschoolSourceUID=*)")))')
    for school in $schools; do
        univention-app shell id-broker-sddb-builder sddb-builder queues bulk-append regular school "$school"
    done
    wait_for_sddb_provisioning
}

install_id_broker_sddb_builder () {
  . utils.sh && install_docker_app_from_branch id-broker-sddb-builder "$UCS_ENV_ID_BROKER_SDDB_BUILDER_IMAGE" kelvin_host="$(hostname -f)" db_url="redis://$(hostname -f):6379" kelvin_username=Administrator kelvin_password=univention converter_daemon_num_workers=24
}

load_sddb_jenkins () {
    if [[ "$UCS_CACHED_SDDB" == "true" ]]; then
        wget "http://omar.knut.univention.de/build2/ucs_5.0-0-id-broker-5.0/data/dump.rdb"
        docker stop redis-stack
        mv dump.rdb /var/lib/redis/data/
        docker start redis-stack
        univention-app restart id-broker-sddb-builder
    else
        resync_sddb
    fi
    wait_for_sddb_provisioning
}

configure_self_disclosure () {
    local sddb_host
    local API_CONFIG
    sddb_host="sddb.$(hostname -d)"
    API_CONFIG="/etc/ucsschool/apis/id-broker/self-disclosure-api.json"
    mkdir -p "$(dirname $API_CONFIG)"
      python -c "
import json
try:
  conf = json.load(open('$API_CONFIG'))
except IOError:
  conf = {}
if 'redis_url' not in conf:
  conf = {'redis_url': 'redis://$sddb_host:6379', 'sddb_rest_host': '$sddb_host'}
json.dump(conf, open('$API_CONFIG', 'w'), indent=4, sort_keys=True)
"
}

# vim:set filetype=sh ts=4:
