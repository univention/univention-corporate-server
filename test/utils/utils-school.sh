#!/bin/bash
#
# Copyright 2019-2022 Univention GmbH
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

install_bb_api () {
  # do not rename function: used as install_[ENV:TEST_API]_api in autotest-241-ucsschool-HTTP-API.cfg
  ucr set bb/http_api/users/django_debug=yes bb/http_api/users/wsgi_server_capture_output=yes bb/http_api/users/wsgi_server_loglevel=debug bb/http_api/users/enable_session_authentication=yes tests/ucsschool/http-api/bb=yes
  cp -v /usr/share/ucs-school-import/configs/ucs-school-testuser-http-import.json /var/lib/ucs-school-import/configs/user_import.json
  python -c 'import json; fp = open("/var/lib/ucs-school-import/configs/user_import.json", "r+w"); config = json.load(fp); config["configuration_checks"] = ["defaults", "mapped_udm_properties"]; config["mapped_udm_properties"] = ["phone", "e-mail", "organisation"]; fp.seek(0); json.dump(config, fp, indent=4, sort_keys=True); fp.close()'
  echo -e "deb [trusted=yes] http://192.168.0.10/build2/ ucs_4.4-0-min-brandenburg/all/\ndeb [trusted=yes] http://192.168.0.10/build2/ ucs_4.4-0-min-brandenburg/amd64/" > /etc/apt/sources.list.d/30_BB.list
  univention-install -y ucs-school-http-api-bb
  ps aux | grep api-bb
}

install_kelvin_api () {
  # do not rename function: used as install_[ENV:TEST_API]_api in autotest-241-ucsschool-HTTP-API.cfg
  . utils.sh && switch_to_test_app_center || true
  echo -n univention > /tmp/univention
  # use brach image if given
  if [ -n "$UCS_ENV_KELVIN_IMAGE" ]; then
    if [[ $UCS_ENV_KELVIN_IMAGE =~ ^gitregistry.knut.univention.de.* ]]; then
        docker login -u "$GITLAB_REGISTRY_TOKEN" -p "$GITLAB_REGISTRY_TOKEN_SECRET" gitregistry.knut.univention.de
    fi
    univention-app dev-set ucsschool-kelvin-rest-api "DockerImage=$UCS_ENV_KELVIN_IMAGE"
  fi
  univention-app install --noninteractive --username Administrator --pwdfile /tmp/univention ucsschool-kelvin-rest-api
  docker images
  docker ps -a
  univention-app shell ucsschool-kelvin-rest-api ps aux
}

install_mv_idm_gw_sender_ext_attrs () {
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,$(ucr get ldap/base)" \
    --set name="mvDst" \
    --set CLIName="mvDst" \
    --set shortDescription="mvDst" \
    --set module="users/user" \
    --set syntax=string \
    --set default="" \
    --set multivalue=1 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute13 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=1
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,$(ucr get ldap/base)" \
    --set name="UUID" \
    --set CLIName="UUID" \
    --set shortDescription="UUID" \
    --set module="users/user" \
    --set syntax=string \
    --set default="" \
    --set multivalue=0 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute14 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=0
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,$(ucr get ldap/base)" \
    --set name="mvStaffType" \
    --set CLIName="mvStaffType" \
    --set shortDescription="mvStaffType" \
    --set module="users/user" \
    --set syntax=string \
    --set default="" \
    --set multivalue=1 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute15 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=0
}

install_mv_idm_gw_receiver_ext_attrs () {
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,$(ucr get ldap/base)" \
    --set name="stamm_dienststelle" \
    --set CLIName="stamm_dienststelle" \
    --set shortDescription="Stammdienststelle" \
    --set module="users/user" \
    --append options="ucsschoolStudent" \
    --append options="ucsschoolTeacher" \
    --append options="ucsschoolStaff" \
    --append options="ucsschoolAdministrator" \
    --set tabName="UCS@school" \
    --set tabPosition=9 \
    --set groupName="IDM Gateway" \
    --set groupPosition="1" \
    --append translationGroupName='"de_DE" "IDM Gateway"' \
    --append translationGroupName='"fr_FR" "Passerelle IDM"' \
    --set syntax=string \
    --set default="" \
    --set multivalue=0 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute13 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=0
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,$(ucr get ldap/base)" \
    --set name="idm_gw_last_update" \
    --set CLIName="idm_gw_last_update" \
    --set shortDescription="Date of last update by the IDM GW" \
    --set module="users/user" \
    --append options="ucsschoolStudent" \
    --append options="ucsschoolTeacher" \
    --append options="ucsschoolStaff" \
    --append options="ucsschoolAdministrator" \
    --set tabName="UCS@school" \
    --set tabPosition=9 \
    --set groupName="IDM Gateway" \
    --set groupPosition="2" \
    --append translationGroupName='"de_DE" "IDM Gateway"' \
    --append translationGroupName='"fr_FR" "Passerelle IDM"' \
    --set syntax=string \
    --set default="" \
    --set multivalue=0 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute14 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=0
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,$(ucr get ldap/base)" \
    --set name="idm_gw_pw_sync" \
    --set CLIName="idm_gw_pw_sync" \
    --set shortDescription="IDM Gateway password sync" \
    --set module="users/user" \
    --append options="ucsschoolStudent" \
    --append options="ucsschoolTeacher" \
    --append options="ucsschoolStaff" \
    --append options="ucsschoolAdministrator" \
    --set syntax=string \
    --set default="" \
    --set multivalue=0 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute15 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=1
}

add_pre_join_hook_to_install_from_test_appcenter () {
	# do not use univention-appcenter-dev, if we have a pending appcenter errata update
	# this new version is used on the dvd, but at this point we can't install errata-test
	# packages and so installing univention-appcenter-dev might fail due to compatibility
	# reasons (dvd: errata-test univention-appcenter vs univention-appcenter-dev from release
	# errata packages)
	cat <<-'EOF' >"/tmp/appcenter-test.sh"
#!/bin/bash
ucr set repository/app_center/server='appcenter-test.software-univention.de' update/secure_apt='false' appcenter/index/verify='no'
univention-app update
exit 0
EOF
	. /usr/share/univention-lib/ldap.sh && ucs_registerLDAPExtension \
		--binddn "cn=admin,$(ucr get ldap/base)" \
		--bindpwdfile=/etc/ldap.secret \
		--packagename dummy \
		--packageversion "1.0" \
		--data /tmp/appcenter-test.sh \
		--data_type="join/pre-join"
}

add_pre_join_hook_to_install_from_test_repository () {
	# activate test repository for school-replica join
	cat <<-'EOF' >"/tmp/repo-test.sh"
#!/bin/bash
ucr set repository/online/server='updates-test.knut.univention.de'
exit 0
EOF
	. /usr/share/univention-lib/ldap.sh && ucs_registerLDAPExtension \
		--binddn "cn=admin,$(ucr get ldap/base)" \
		--bindpwdfile=/etc/ldap.secret \
		--packagename setrepo \
		--packageversion "1.0" \
		--data /tmp/repo-test.sh \
		--data_type="join/pre-join"
}
