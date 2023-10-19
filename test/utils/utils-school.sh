#!/bin/bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2019-2023 Univention GmbH
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
  # shellcheck disable=SC2009
  ps aux | grep api-bb
}

install_app_from_branch () {
  local app_name="$1"
  local custom_docker_image="$2"
  local app_settings="${*:3}"
  printf '%s' univention > /tmp/univention
  if [ -n "$custom_docker_image" ]; then
    univention-install --yes univention-appcenter-dev
    univention-app dev-set "$app_name" "DockerImage=$custom_docker_image"
  fi
  cmd="univention-app install $app_name --noninteractive --username Administrator --pwdfile /tmp/univention"
  if [ -n "$app_settings" ]; then
    exec $cmd --set $app_settings
  else
    exec $cmd
  fi
  container_name="appcenter/apps/$app_name/container"
  container=$(ucr get "$container_name")
  commit=$(docker inspect --format='{{.Config.Labels.commit}}' "$container")
	echo "Docker image built from commit: $commit"
}

install_kelvin_api () {
  install_app_from_branch ucsschool-kelvin-rest-api "$UCS_ENV_KELVIN_IMAGE" ucsschool/kelvin/processes=0 ucsschool/kelvin/log_level=DEBUG
}

install_ucsschool_id_connector () {
  install_app_from_branch ucsschool-id-connector "$UCS_ENV_ID_CONNECTOR_IMAGE" ucsschool-id-connector/log_level=DEBUG
}

install_ucsschool_apis () {
  install_app_from_branch ucsschool-apis "$UCS_ENV_UCSSCHOOL_APIS_IMAGE" ucsschool/apis/log_level=DEBUG ucsschool/apis/processes=0
}

install_mv_idm_gw_sender_ext_attrs () {
  local lb
  lb="$(ucr get ldap/base)"
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,${lb}" \
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
    --position "cn=custom attributes,cn=univention,${lb}" \
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
    --position "cn=custom attributes,cn=univention,${lb}" \
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
  local lb
  lb="$(ucr get ldap/base)"
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,${lb}" \
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
    --position "cn=custom attributes,cn=univention,${lb}" \
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
    --position "cn=custom attributes,cn=univention,${lb}" \
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
#!/bin/sh
ucr set repository/app_center/server='appcenter-test.software-univention.de' update/secure_apt='false' appcenter/index/verify='no'
univention-app update
exit 0
EOF
	# shellcheck source=/dev/null
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
#!/bin/sh
ucr set repository/online/server='http://updates-test.knut.univention.de'
exit 0
EOF
	# shellcheck source=/dev/null
	. /usr/share/univention-lib/ldap.sh && ucs_registerLDAPExtension \
		--binddn "cn=admin,$(ucr get ldap/base)" \
		--bindpwdfile=/etc/ldap.secret \
		--packagename setrepo \
		--packageversion "1.0" \
		--data /tmp/repo-test.sh \
		--data_type="join/pre-join"
}

create_virtual_schools () {
	local number_of_schools=${1:?missing number of schools to create}
	local formated_school_number
	rm -f ./virtual_schools.txt
	for ((i=1; i <= number_of_schools; i++)); do
		printf -v formated_school_number "%0${#number_of_schools}d" "$i"
		/usr/share/ucs-school-import/scripts/create_ou --verbose "SchoolVirtual$formated_school_number" "r300-sV$formated_school_number" --displayName "SchuleVirtual$formated_school_number"
		printf "SchoolVirtual%0${#number_of_schools}d\n" "$i" >> ./virtual_schools.txt  # Later used for the import script
	done
}


# used in RAM performance job
# * 50 (big) schools (each 1600 user, 53 classes with ~30 members)
# * 325 (normal) schools (each 640 users, 30 classes with ~20 members)
# * + 300 classes (5 members) in each big school
# * + 150 classes (0 members) in each normal school
# * + 10 workgroups (30 members) in each school
# * total for big schools (the rest is just filler)
#   -> 80000 students, 15000 teachers, 1500 staff
#   -> 50 schools
#   -> 2650 classes with ~30 members
#   -> 15000 classes with 5 members
#   -> 500 workgroups with 30 members
# * total
#   -> 375 schools
#   -> 321000 users (288000 students, 30000 teachers, 3000 staff)
#   -> 81750 classes
#   -> 3750 workgroups
create_users_in_template_job () {
	# don't delete users
	cat <<EOF > /var/lib/ucs-school-import/configs/user_import.json
{
  "no_delete": true
}
EOF
	# fix record_uid
	sed -i 's/"record_uid": "<firstname>.<lastname>"/"record_uid": "<firstname>.<lastname>.<username>"/' \
		/usr/share/ucs-school-import/configs/ucs-school-testuser-import.json
	# add import hook
	cat <<EOF > /usr/share/ucs-school-import/pyhooks/testimport.py
from ucsschool.importer.utils.user_pyhook import UserPyHook

class MyHook(UserPyHook):

    priority = {
        "pre_create": 1,
    }

    def pre_create(self, user):
        user.password = "univention"
        mapping = {
            "staff": "generic_user",
        }
        custome_roles = []
        for role in user.ucsschool_roles:
            role, context, school = role.split(":")
            custome_roles.append(f"{mapping.get(role, role)}:bsb:{school}")
        user.ucsschool_roles += custome_roles

EOF
	# create schools
	school_count=375
	schools_big=()
	schools_normal=()
	for i in $(seq 1 "$school_count"); do
		/usr/share/ucs-school-import/scripts/create_ou "--verbose" "school$i" "replica$i" >/tmp/import.log 2>&1 || return 1
		if [ "$i" -le 50 ]; then
			schools_big+=("school$i")
		else
			schools_normal+=("school$i")
		fi
	done
	# 50 big schools with 1600 students and 53 classes (~30 members)
	/usr/share/ucs-school-import/scripts/ucs-school-testuser-import \
		--classes 2650 \
		--students 80000 \
		--teachers 15000 \
		--staff 1500 \
		"${schools_big[@]}" >/tmp/import.log 2>&1 || return 1
	# 325 normal schools with 640 students and 30 classes (~20 members)
	/usr/share/ucs-school-import/scripts/ucs-school-testuser-import \
		--classes 10000 \
		--students 208000 \
		--teachers 15000 \
		--staff 1500 \
		"${schools_normal[@]}" >/tmp/import.log 2>&1 || return 1
	rm -f /tmp/import.log
	# clean up
	rm -f /usr/share/ucs-school-import/pyhooks/testimport.py
	rm -f /var/lib/ucs-school-import/configs/user_import.json
	# add some more
	# * workgroups, 10 work groups per school with 30 members each
	# * 300 classes to each of the 50 big schools (5 members)
	# * 150 class to each of the 325 normal schools (0 members)
	python3 - <<"EOF" || return 1
from ucsschool.lib.models import School, User
from ucsschool.lib.models.group import SchoolClass, WorkGroup
from univention.admin.uldap import getAdminConnection

import random

lo, po = getAdminConnection()
schools = School.get_all(lo)

for school in schools:
    if school.name == "DEMOSCHOOL":
        continue
    users = [user.dn for user in User.get_all(lo, school.name)]
    # add workgroups to every school
    for i in range(1, 11):
        wg_data = {
            "name": f"{school.name}-workgroup{i}",
            "school": school.name,
            "users": random.sample(users, 30),
        }
        wg = WorkGroup(**wg_data)
        wg.create(lo)
    # add some more classes in big schools
    if len(users) > 1000:
        for i in range(1, 301):
            sc_data = {
                "name": f"{school.name}-extra-class{i}",
                "school": school.name,
                "users": random.sample(users, 5),
            }
            sc = SchoolClass(**sc_data)
            sc.create(lo)
    # add empty classes in normal schools
    else:
        for i in range(1, 153):
            sc_data = {
                "name": f"{school.name}-empty-class{i}",
                "school": school.name,
            }
            sc = SchoolClass(**sc_data)
            sc.create(lo)
EOF


}

# get first 50 schools as python diskcache
create_and_copy_test_data_cache () {
	local root_password="${1:?missing root password}"
	univention-install -y python3-pip sshpass
	pip3 install diskcache
	python3 - <<"EOF" || return 1
from ucsschool.lib.models import School, User, Group
from univention.admin.uldap import getAdminConnection
from diskcache import Index

CACHE_PATH = "/var/lib/test-data"

lo, po = getAdminConnection()
db = Index(str(CACHE_PATH))
db["schools"] = [ f"school{i}" for i in range(1, 51) ]

for i in range(1, 51):
    school = School(f"school{i}")
    print(school)
    data = {
        "users": {},
        "groups": {},
        "students": {},
        "teachers": {},
        "staff": {},
        "admins": {},
        "classes": [],
        "workgroups": [],
    }
    for user in User.get_all(lo, school.name):
        data["users"][user.name] = user.to_dict()
        if user.is_student(lo):
            data["students"][user.name] = user.dn
        elif user.is_teacher(lo):
            data["teachers"][user.name] = user.dn
        elif user.is_staff(lo):
            data["staff"][user.name] = user.dn
        elif user.is_administrator(lo):
            data["admins"][user.name] = user.dn
    for group in Group.get_all(lo, school.name):
        data["groups"][group.name] = group.to_dict()
        if group.self_is_workgroup():
            data["workgroups"].append(group.name)
        elif group.self_is_class():
            data["classes"].append(group.name)
    db[school.name] = data
db.cache.close()
EOF

	shift
	for ip in "$@"; do
		sshpass -p "$root_password" scp -r  -o StrictHostKeyChecking=no -o UpdateHostKeys=no /var/lib/test-data root@"$ip":/var/lib/ || return 1
	done
}

set_udm_properties_for_kelvin_api_tests () {
  cat <<EOF > /etc/ucsschool/kelvin/mapped_udm_properties.json
{
    "user": [
        "description",
        "displayName",
        "e-mail",
        "employeeType",
        "gidNumber",
        "organisation",
        "phone",
        "title",
        "uidNumber"
    ],
    "school_class": [
        "gidNumber",
        "mailAddress"
    ],
    "workgroup": [
        "gidNumber",
        "mailAddress"
    ],
    "school": [
        "description"
    ]
}
EOF
}
