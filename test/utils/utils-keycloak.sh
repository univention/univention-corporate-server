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
set -e

install_upgrade_keycloak () {
	echo "univention" > /tmp/pwdfile
	local app location image_name
	local project=600
	local repo_id=68
	local gitlab="git.knut.univention.de"
	# TODO add versio parameter to ./update-appcenter-test.sh and appcenter-change-compose-image.py
	#      (currently only "latest" is supported)
	if [ -n "$KEYCLOAK_BRANCH" ]; then
		univention-app update
		univention-install -y git slugify jq
		git clone "https://$gitlab/univention/components/keycloak-app.git" /opt/keycloak-app
		cd /opt/keycloak-app
		git checkout "$KEYCLOAK_BRANCH"
		# update local cache files for app
		./update-appcenter-test.sh -l
		# gitlab doesn't like underscore and dots
		image_name="${KEYCLOAK_BRANCH//_/}"
		image_name="${image_name//./}"
		# change image in local cache
		image_name="branch-$(slugify "$image_name")"
		location="$(curl "https://$gitlab/api/v4/projects/$project/registry/repositories/$repo_id/tags/$image_name" | jq -r '.location')"
		if [ -n "$location" ] && [ ! "$location" = "null" ]; then
			python3 /root/appcenter-change-compose-image.py -a keycloak -i "$location"
		fi
		# never update appcenter cache in UMC
		ucr set appcenter/umc/update/always=false
		ucr set update/check/cron/enabled='no'
		ucr set update/check/boot/enabled='no'
	fi
	if [ -n "$APPVERSION" ]; then
		app="keycloak=$APPVERSION"
	else
		app="keycloak"
	fi
	if [ -z "$(ucr get "appcenter/apps/keycloak/status")" ]; then
		# installation
		univention-app install "$app" --username=Administrator --pwdfile=/tmp/pwdfile --skip --noninteractive "$@" || return 1
	else
		# upgrade
		univention-app upgrade "$app" --username=Administrator --pwdfile=/tmp/pwdfile --skip --noninteractive "$@" || return 1
	fi
	# for the app specific test
	echo "keycloak" >>/var/cache/appcenter-installed.txt
}

keycloak_saml_idp_setup () {
    domainname="$(ucr get domainname)"
    local idp="${1:-ucs-sso-ng.${domainname,,}}"
    if [ "$(ucr get server/role)" = "domaincontroller_master" ]; then
        udm portals/entry modify --dn "cn=login-saml,cn=entry,cn=portals,cn=univention,$(ucr get ldap/base)" --set activated=TRUE
    fi
    ucr set umc/saml/idp-server="https://$idp/realms/ucs/protocol/saml/descriptor"
    systemctl restart slapd || true
}

keycloak_umc_oidc_idp_setup() {
	local idp="${1:-ucs-sso-ng.$(ucr get domainname)}"
	local fqdn="$(ucr get hostname).$(ucr get domainname)"

	# FIXME
	local join_user join_pwdfile
	join_pwdfile="/tmp/pwdfile"
	join_user="Administrator"
	echo -n "univention" > "$join_pwdfile"

	ucr set umc/web/oidc/enabled=true
	ucr set umc/oidc/issuer="https://$idp/realms/ucs"

	ucr set umc/oidc/rp/server="${fqdn,,}"
	univention-run-join-scripts -dcaccount "$join_user" -dcpwd "$join_pwdfile" --force --run-scripts 92univention-management-console-web-server

	if [ "$(ucr get server/role)" = "domaincontroller_master" ]; then
		udm portals/entry create --ignore_exists \
			--position "cn=entry,cn=portals,cn=univention,$(ucr get ldap/base)" \
			--set name=login-oidc \
			--append displayName="\"en_US\" \"OIDC Login\"" \
			--append displayName="\"de_DE\" \"OIDC Login\"" \
			--append description="\"en_US\" \"Log in to the portal\"" \
			--append description="\"de_DE\" \"Am Portal anmelden\"" \
			--append link='"en_US" "/univention/oidc/?location=/univention/portal/"' \
			--set anonymous=TRUE \
			--set activated=TRUE \
			--set linkTarget=samewindow \
			--set icon="$(base64 /usr/share/univention-portal/login.svg)"
		udm  portals/category modify --ignore_exists \
			--dn "cn=domain-service,cn=category,cn=portals,cn=univention,$(ucr get ldap/base)" \
			--append entries="cn=login-oidc,cn=entry,cn=portals,cn=univention,$(ucr get ldap/base)"
	fi
}

install_self_service () {
    if [ "$(ucr get server/role)" = "domaincontroller_master" ]; then
        apt-get -y install univention-self-service-master univention-self-service
        ucr set \
            umc/self-service/account-registration/frontend/enabled=true \
            umc/self-service/account-registration/backend/enabled=true \
            umc/self-service/account-verification/backend/enabled=true
        # this is for simplesamlphp
        #  only verified account in simplesamlphp login
        #  error message for account verification
        ucr set \
            saml/idp/selfservice/check_email_verification=true \
            saml/idp/selfservice/account-verification/error-descr='<span>You must <a href="https://master.ucs.test/univention/selfservice/#/selfservice/verifyaccount">verify your account</a> before you can login.</span>'
    else
        apt-get -s -y install univention-self-service
    fi
    deb-systemd-invoke restart univention-management-console-server univention-portal-server
}

umc_multiproc_settings () {
	local procs="${1:-8}"
	ucr set umc/http/processes="$procs"
	service apache2 restart
	service univention-management-console-server restart
}

run_performance_tests () {
	univention-install -y libffi-dev python3-pip
	pip3 install locust bs4 diskcache
	if [ "false" = "$UCS_TEST_RUN" ]; then
		echo "Test disabled by UCS_TEST_RUN"
	else
		prlimit -n100000:100000 locust -t 10m -u 200 --spawn-rate 4 --headless --host https://primary.ucs.test \
			--csv loginPrimaryAndBackup --html loginPrimaryAndBackup.html -f keycloaklocust.py PrimaryAndBackup || :
		prlimit -n100000:100000 locust -t 10m -u 200 --spawn-rate 4 --headless --host https://primary.ucs.test \
			--csv loginPrimaryOnly --html loginPrimaryOnly.html -f keycloaklocust.py PrimaryOnly || :
		prlimit -n100000:100000 locust -t 10m -u 40  --spawn-rate 2 --headless --host https://primary.ucs.test \
			--csv PrimaryOnlyWithUMCLogin --html PrimaryOnlyWithUMCLogin.html -f keycloaklocust.py PrimaryOnlyWithUMCLogin || :
	fi
}

add_fqdn_to_dns () {
	local fqdn="${1:?missing fqdn}"; shift
	local ip="${1:?missing ip}"; shift
	local name="${fqdn%%.*}"
	local domain="${fqdn#*.}"
	/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists \
		"$domain" add zone "root@$domain." 1 28800 7200 604800 10800 "$(ucr get hostname).$(ucr get domainname)."
	/usr/share/univention-directory-manager-tools/univention-dnsedit "$@" --ignore-exists \
		"$domain" add a "$name" "$ip"
}

# create a dummy certificate in /opt/$fqdn
create_dummy_certficate () {
	local fqdn="${1:?missing fqdn}"; shift
	univention-certificate new -name "$fqdn"
	mv /etc/univention/ssl/"$fqdn" /opt/
}

copy_dummy_certficate () {
	local ip="${1:?missing ip}"; shift
	local root_password="${1:?missing root_password}"; shift
	local fqdn="${1:?missing fqdn}"; shift
	univention-install -y sshpass
	sshpass -p "$root_password" scp -r  -o StrictHostKeyChecking=no -o UpdateHostKeys=no root@"$ip":/opt/"$fqdn" /opt
}

set_dns_forwarder () {
	# set dns forwarder to an ip that can resolv $fqdn
	local forwarder="${1:?missing forwarder}"; shift
	# external fqdn setup
	ucr set dns/forwarder1="$forwarder"
	ucr unset dns/forwarder2 dns/forwarder3
	systemctl restart bind9
}

external_keycloak_fqdn_config () {
	# requiremnts:
	# * certifcate must be in /opt/$fqdn
	# * external name is resolvable via DNS
	local fqdn="${1:?missing fqdn}"; shift
	local certificate="${1:?missing certificate}"; shift
	local keyfile="${1:?missing keyfile}"; shift
	# keycloak config
	ucr set \
		keycloak/apache2/ssl/certificate="$certificate" \
		keycloak/apache2/ssl/key="$keyfile" \
		keycloak/server/sso/autoregistration=false \
		keycloak/server/sso/fqdn="${fqdn}"
	# to not create a certificate for external name in univention-saml/91univention-saml.inst
	#ucr set keycloak/server/sso/certificate/generation=false
}

external_portal_config_saml () {
	# requiremnts:
	# * certificate/apache config for external portal
	local fqdn="${1:?missing fqdn}"; shift
	local certificate="${1:?missing certificate}"; shift
	local keyfile="${1:?missing keyfile}"; shift

	# FIXME
	local join_user join_pwdfile
	join_pwdfile="/tmp/pwdfile"
	join_user="Administrator"
	echo -n "univention" > "$join_pwdfile"

	ucr set umc/saml/sp-server="$fqdn"
	# workaround for https://forge.univention.org/bugzilla/show_bug.cgi?id=55982
	# copy certificate to /etc/univention/ssl
	mkdir -p "/etc/univention/ssl/$fqdn"
	cp -rf "$certificate" "/etc/univention/ssl/$fqdn/cert.pem"
	cp -rf "$keyfile" "/etc/univention/ssl/$fqdn/private.key"

	# re run join
	univention-run-join-scripts -dcaccount "$join_user" -dcpwd "$join_pwdfile" --force --run-scripts 92univention-management-console-web-server
}

external_portal_config_oidc () {
	local fqdn="${1:?missing fqdn}"; shift

	# oidc
	ucr set umc/oidc/rp/server="${fqdn,,}"

	# we have to set a password, so that the password is the same for every client
	# in case we have multiple UCS servers act as one portal (load balancing setup)
	echo "univention" > /etc/umc-oidc.secret
	chmod 600 /etc/umc-oidc.secret

	# FIXME
	local join_user join_pwdfile
	join_pwdfile="/tmp/pwdfile"
	join_user="Administrator"
	echo -n "univention" > "$join_pwdfile"
	# re run join
	univention-run-join-scripts -dcaccount "$join_user" -dcpwd "$join_pwdfile" --force --run-scripts 92univention-management-console-web-server

	# WHY?
	service slapd restart || true
}


external_portal_config_oidc_manually () {
	local fqdn="${1:?missing fqdn}"; shift
	local idp="${1:?missing idp}"; shift

	# oidc configuration
	ucr set \
		umc/oidc/autoconfiguration=false \
		umc/web/oidc/enabled=true \
		umc/oidc/rp/server="$fqdn" \
		umc/oidc/issuer="https://${idp}/realms/ucs" \
		umc/oidc/default-op="$fqdn"

	# create oidc client
	echo "univention" > /etc/umc-oidc.secret
	chmod 600 /etc/umc-oidc.secret

	# create a client for the host, just to please the test
	# 04_misc.py::test_every_umc_server_has_a_oidc_client
	univention-keycloak --binduser Administrator --bindpwd univention oidc/rp create \
		--app-url "https://$(ucr get hostname).$(ucr get domainname)/univention/oidc/" \
		"https://$(ucr get hostname).$(ucr get domainname)/univention/oidc/"

	# umc oidc configuration
	ucr set \
		"umc/oidc/$fqdn/client-id"="https://$fqdn/univention/oidc/" \
		"umc/oidc/$fqdn/client-secret-file"="/etc/umc-oidc.secret" \
		"umc/oidc/$fqdn/extra-parameter"="kc_idp_hint" \
		"umc/oidc/$fqdn/issuer"="https://$idp/realms/ucs" \
		"umc/oidc/$fqdn/openid-certs"="/usr/share/univention-management-console/oidc/https%3A%2F%2F${idp}%2Frealms%2Fucs.jwks" \
		"umc/oidc/$fqdn/openid-configuration"="/usr/share/univention-management-console/oidc/https%3A%2F%2F${idp}%2Frealms%2Fucs.json"

	# ldap
	local hostname domainname
	hostname="$(ucr get hostname)"
	domainname="$(ucr get domainname)"
	ucr set \
		"ldap/server/sasl/oauthbearer/trusted-audience/$domainname?ldaps://$domainname/" \
		"ldap/server/sasl/oauthbearer/trusted-audience/$hostname.$domainname?ldaps://$hostname.$domainname/" \
		"ldap/server/sasl/oauthbearer/trusted-issuer/$hostname.$domainname=https://$idp/realms/ucs" \
		"ldap/server/sasl/oauthbearer/trusted-jwks/$hostname.$domainname"="/usr/share/univention-management-console/oidc/https%3A%2F%2F${idp}%2Frealms%2Fucs.jwks" \
		"ldap/server/sasl/oauthbearer/trusted-authorized-party/$fqdn"="https://$fqdn/univention/oidc/"

	# not necessary for the setup,
	# just a test the we don't break the manual configuration
	ucr set umc/oidc/issuer="https://${idp}/realms/ucs"
	local join_user join_pwdfile
	join_pwdfile="/tmp/pwdfile"
	join_user="Administrator"
	echo -n "univention" > "$join_pwdfile"
	# re run join
	univention-run-join-scripts -dcaccount "$join_user" -dcpwd "$join_pwdfile" --force --run-scripts 92univention-management-console-web-server

	service univention-management-console-server restart
	service slapd restart || true
}

# FIXME
haproxy_config_external_fqdn () {

	local primary_ip="${1:?missing ip for primary}"; shift
	local backup_ip="${1:?missing ip for backup}"; shift
	local replica_ip="${1:?missing ip for replica}"; shift
	local member_ip="${1:?missing ip for member}"; shift
	service apache2 stop
	univention-install -y haproxy
	# cert for ha proxy, we need the key in the cert file, and every cert in one directory
	mkdir -p /opt/certs
	cat /opt/portal.extern.test/cert.pem /opt/portal.extern.test/private.key >> /opt/certs/portal.pem
	cat /opt/auth.extern.test/cert.pem /opt/auth.extern.test/private.key >> /opt/certs/auth.pem
	cat <<EOF >> "/etc/haproxy/haproxy.cfg"

frontend portal_httpd
	bind :443 ssl crt /opt/certs
	use_backend portals if { req.hdr(host) -i portal.extern.test }
	use_backend keycloaks if { req.hdr(host) -i auth.extern.test }

backend portals
	balance roundrobin
	timeout server 10000
	# sticky sessions
	cookie SERVER insert indirect nocache
	server master  $primary_ip:443 ssl ca-file /etc/ssl/certs/ca-certificates.crt check cookie master
	server backup  $backup_ip:443 ssl ca-file /etc/ssl/certs/ca-certificates.crt check cookie backup
	server replica $replica_ip:443 ssl ca-file /etc/ssl/certs/ca-certificates.crt check cookie replica
	server member  $member_ip:443 ssl ca-file /etc/ssl/certs/ca-certificates.crt check cookie member


backend keycloaks
	balance roundrobin
	timeout server 10000
	# sticky sessions
	cookie KEYCLOAK insert indirect nocache
	server master $primary_ip:443 ssl ca-file /etc/ssl/certs/ca-certificates.crt check cookie master

EOF
	service haproxy restart
}

# FIXME
haproxy_config_external_fqdn_add_second_keycloak () {
	local backup_ip="${1:?missing ip for backup}"; shift
	cat <<EOF >> "/etc/haproxy/haproxy.cfg"
	server backup $backup_ip:443 ssl ca-file /etc/ssl/certs/ca-certificates.crt check cookie backup
EOF
	service haproxy restart
}
