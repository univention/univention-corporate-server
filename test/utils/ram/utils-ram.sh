set_udm_properties_for_kelvin () {
	echo '{ "user": ["displayName", "e-mail", "accountActivationDate", "pwdChangeNextLogin", "serviceprovider", "ucsschoolPurgeTimestamp"]}' > /etc/ucsschool/kelvin/mapped_udm_properties.json
	univention-app restart ucsschool-kelvin-rest-api
}

install_frontend_apps () {
	local kelvin_host=${1:?missing kelvin_host}

	echo -n univention > /tmp/univention

	# use brach image if given
	if [ -n "$UCS_ENV_RANKINE_USERS_IMAGE" ]; then
		univention-app dev-set ucsschool-bff-users "DockerImage=$UCS_ENV_RANKINE_USERS_IMAGE"
	fi
	univention-app install --noninteractive --username Administrator --pwdfile /tmp/univention ucsschool-bff-users
	univention-app configure ucsschool-bff-users --set \
		ucsschool/ui_users/kelvin/username=Administrator \
		ucsschool/ui_users/kelvin/password=univention \
		ucsschool/ui_users/kelvin/host="$kelvin_host" \
		ucsschool/ui_users/kelvin/ssl_verify=0
	univention-app restart ucsschool-bff-users # TODO, shouldn't this be part of the App's configure_host?

	docker images
	docker ps -a
}

install_frontend_packages () {
	univention-install -y ucs-school-ui-users-frontend

	# create dev clients for easier testing
	/usr/share/ucs-school-ui-common/scripts/univention-create-keycloak-clients --admin-password univention --client-id school-ui-users-dev --direct-access
}
