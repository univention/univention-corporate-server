#!/bin/bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2022-2023 Univention GmbH
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

wait_for_server () {
	local server="${1:?missing server param}"
	for ((i=0; i<300; i++))
	do
		ping -c 2 "$server" && return 0
		sleep 1
	done
	return 1
}


install_keycloak () {
    echo "univention" > /tmp/pwdfile
    local app
    if [ -n "$KEYCLOAK_IMAGE" ]; then
        python3 /root/appcenter-change-compose-image.py -a keycloak -i "$KEYCLOAK_IMAGE"
    fi
    if [ -n "$APPVERSION" ]; then
        app="keycloak=$APPVERSION"
    else
        app="keycloak"
    fi
    univention-app install "$app" --username=Administrator --pwdfile=/tmp/pwdfile --skip --noninteractive "$@"
    # for the app specific test
    echo "keycloak" >>/var/cache/appcenter-installed.txt
}

keycloak_saml_idp_setup () {
    if [ "$(ucr get server/role)" = "domaincontroller_master" ]; then
        udm portals/entry modify --dn "cn=login-saml,cn=entry,cn=portals,cn=univention,$(ucr get ldap/base)" --set activated=TRUE
    fi
    ucr set umc/saml/idp-server="https://ucs-sso-ng.$(ucr get domainname)/realms/ucs/protocol/saml/descriptor"
    service slapd restart
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
    service univention-management-console-server restart
    service univention-portal-server restart
}

performance_settings () {
	ucr set umc/http/processes=8
	ucr set umc/server/processes=8
	systemctl restart univention-management-console-server
	systemctl restart univention-management-console-web-server
}

run_performance_tests () {
	univention-install -y libffi-dev python3-pip
	pip3 install locust bs4
	prlimit -n100000:100000 locust -t 20m -u 500 --spawn-rate 10 --host master.ucs.test --html keycloak.html --headless -f keycloaklocust.py || :
}
