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
                "isLMSGroup"
        ],
        "workgroup": [
                "divis_startdate",
                "divis_enddate",
                "divis_classtype",
                "idi_schoolyear",
                "group_source-id",
                "isIServGroup",
                "isLMSGroup"
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
	univention-install -y ucs-school-ui-users-frontend
	univention-install -y ucs-school-ui-groups-frontend

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
	# workaround for broken ext. attr. purgeDate: sets the default "0" which conflicts with the syntax iso8601Date
	# has to be fixed by prof services in ucsschool-divis-custom-ldap-extension  (50ucsschool-divis-custom-ldap-extension.inst)
	udm settings/extended_attribute modify --dn cn="purgeDate,cn=DiViS,cn=custom attributes,cn=univention,$(ucr get ldap/base)" --set default=""
	systemctl restart univention-directory-manager-rest.service
}
