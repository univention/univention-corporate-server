# shellcheck shell=sh
set -e
set -x

set_udm_properties_for_kelvin () {
    cat <<EOT > /etc/ucsschool/kelvin/mapped_udm_properties.json
{
        "user": [
                "accountActivationDate",
                "displayName",
                "divisNameAffix",
                "divisNickname",
                "e-mail",
                "networkAccess",
                "PasswordRecoveryEmail",
                "PasswordRecoveryEmailVerified",
                "pwdChangeNextLogin",
                "serviceprovider",
                "ucsschoolPurgeTimestamp",
                "uidNumber"
        ],
        "school_class": [
                "divis_startdate",
                "divis_enddate",
                "divis_classtype",
                "idi_schoolyear",
                "group_source-id",
                "isIServGroup",
                "isLMSGroup",
                "disabled",
                "divis_coursetype",
                "recordUID",
                "idi_schoolyear",
                "purgeDate",
                "serviceprovidergroup"
        ],
        "workgroup": [
                "divis_startdate",
                "divis_enddate",
                "divis_classtype",
                "idi_schoolyear",
                "group_source-id",
                "isIServGroup",
                "isLMSGroup",
                "disabled",
                "divis_coursetype",
                "recordUID",
                "idi_schoolyear",
                "purgeDate",
                "serviceprovidergroup"
        ]
}

EOT
    univention-app shell ucsschool-kelvin-rest-api /var/lib/univention-appcenter/apps/ucsschool-kelvin-rest-api/data/update_openapi_client
    univention-app shell ucsschool-kelvin-rest-api /etc/init.d/ucsschool-kelvin-rest-api restart
}

install_frontend_app () {
	local app="$1"
	local main_image="$2"
	local branch_image="$3"
	univention-install --yes univention-appcenter-dev
	if [ -n "$branch_image" ]; then
		univention-app dev-set "$app" "DockerImage=$branch_image"
	else
		if [ "$UCSSCHOOL_RELEASE" = "scope" ]; then
			univention-app dev-set "$app" "DockerImage=$main_image"
		fi
	fi
	univention-app install --noninteractive --username Administrator --pwdfile /tmp/univention "$app"
}

install_frontend_apps () {
	echo -n univention > /tmp/univention

	install_frontend_app "ucsschool-bff-users" "gitregistry.knut.univention.de/univention/ucsschool-components/ui-users:latest" "$UCS_ENV_RANKINE_USERS_IMAGE"
	install_frontend_app "ucsschool-bff-groups" "gitregistry.knut.univention.de/univention/ucsschool-components/ui-groups:latest" "$UCS_ENV_RANKINE_GROUPS_IMAGE"

	docker images
	docker ps -a
}

install_frontend_packages () {
	# also add internal school repo for up-to-date frontend packages
	local version
	if [ "$UCSSCHOOL_RELEASE" != "public" ]; then
		version="${UCS_VERSION%%-*}"
		cat <<EOF > "/etc/apt/sources.list.d/99_internal_school.list"
deb [trusted=yes] http://192.168.0.10/build2/ ucs_$version-0-ucs-school-$version/all/
deb [trusted=yes] http://192.168.0.10/build2/ ucs_$version-0-ucs-school-$version/\$(ARCH)/
EOF
	fi

	univention-install -y ucs-school-ui-users-frontend
	univention-install -y ucs-school-ui-groups-frontend

	rm -f /etc/apt/sources.list.d/99_internal_school.list

	# create dev clients for easier testing
	/usr/share/ucs-school-ui-common/scripts/univention-create-keycloak-clients --admin-password univention --client-id school-ui-users-dev --direct-access
	/usr/share/ucs-school-ui-common/scripts/univention-create-keycloak-clients --admin-password univention --client-id school-ui-groups-dev --direct-access
}

install_all_attributes_primary () {
	# get APT customer repo $username and @password from the RAM secrets
	# shellcheck disable=SC2046
	export $(grep -v '^#' /etc/ram.secrets| xargs)
	echo -n univention > /tmp/univention

	# shellcheck disable=SC2154
	/usr/sbin/univention-config-registry set \
		repository/online/component/fhh-bsb-iam=yes \
		repository/online/component/fhh-bsb-iam/server='service.knut.univention.de' \
		repository/online/component/fhh-bsb-iam/prefix="apt/$username" \
		repository/online/component/fhh-bsb-iam/parts='maintained' \
		repository/online/component/fhh-bsb-iam/username="$username" \
		repository/online/component/fhh-bsb-iam/password="$password"

	# also add internal repo
	cat <<"EOF" > "/etc/apt/sources.list.d/99_bsb.list"
deb [trusted=yes] http://192.168.0.10/build2/ ucs_5.0-0-fhh-bsb-iam-dev/all/
deb [trusted=yes] http://192.168.0.10/build2/ ucs_5.0-0-fhh-bsb-iam-dev/$(ARCH)/
EOF

	univention-install -y ucsschool-divis-custom-ldap-extension ucsschool-iserv-custom-ldap-extension ucsschool-moodle-custom-ldap-extension univention-saml
	systemctl restart univention-directory-manager-rest.service
}

create_test_admin_account () {
	local username password fqdn token
	test -z "$(which jq)" && univention-install -y jq
	test -z "$(which curl)" && univention-install -y curl
	username="Administrator"
	password="univention"
	fqdn="$(hostname -f)"
	token="$(curl -s -k -X POST "https://$fqdn/ucsschool/kelvin/token" \
		-H "Content-Type:application/x-www-form-urlencoded" \
		-d "username=$username" \
		-d "password=$password" | jq -r '.access_token')"
	curl -X POST "https://$fqdn/ucsschool/kelvin/v1/users/" \
		-H "Authorization: Bearer $token" \
		-H "accept: application/json" \
		-H "Content-Type: application/json" \
		-d '{
			"name": "admin",
			"firstname": "test",
			"lastname": "admin",
			"password": "univentionunivention",
			"school": "https://'"$fqdn"'/ucsschool/kelvin/v1/schools/school1",
			"roles": ["https://'"$fqdn"'/ucsschool/kelvin/v1/roles/teacher"],
			"record_uid": "admin",
			"ucsschool_roles": ["technical_admin:bsb:*", "teacher:school:school1"]
		}'
	udm users/user modify \
		--dn "uid=admin,cn=lehrer,cn=users,ou=school1,$(ucr get ldap/base)" \
		--set password=univention  \
		--append groups="cn=Domain Users,cn=groups,$(ucr get ldap/base)"
}
