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
                "ucsschoolPurgeTimestamp"
        ]
}

EOT
    univention-app shell ucsschool-kelvin-rest-api /var/lib/univention-appcenter/apps/ucsschool-kelvin-rest-api/data/update_openapi_client
    univention-app shell ucsschool-kelvin-rest-api /etc/init.d/ucsschool-kelvin-rest-api restart
}

install_frontend_apps () {
	echo -n univention > /tmp/univention

	# use brach image if given
	if [ -n "$UCS_ENV_RANKINE_USERS_IMAGE" ]; then
		univention-app dev-set ucsschool-bff-users "DockerImage=$UCS_ENV_RANKINE_USERS_IMAGE"
	fi
	univention-app install --noninteractive --username Administrator --pwdfile /tmp/univention ucsschool-bff-users

	docker images
	docker ps -a
}

install_frontend_packages () {
	univention-install -y ucs-school-ui-users-frontend

	# create dev clients for easier testing
	/usr/share/ucs-school-ui-common/scripts/univention-create-keycloak-clients --admin-password univention --client-id school-ui-users-dev --direct-access
}

install_all_attributes_primary () {
    # get APT customer repo $username and @password from the RAM secrets
    export $(grep -v '^#' /etc/ram.secrets| xargs)
	echo -n univention > /tmp/univention

    /usr/sbin/univention-config-registry set \
      repository/online/component/fhh-bsb-iam=yes \
      repository/online/component/fhh-bsb-iam/server='service.knut.univention.de' \
      repository/online/component/fhh-bsb-iam/prefix="apt/$username" \
      repository/online/component/fhh-bsb-iam/parts='maintained' \
      repository/online/component/fhh-bsb-iam/username="$username" \
      repository/online/component/fhh-bsb-iam/password="$password"

    univention-install -y ucsschool-divis-custom-ldap-extension ucsschool-iserv-custom-ldap-extension ucsschool-moodle-custom-ldap-extension univention-saml
    systemctl restart univention-directory-manager-rest.service
}
