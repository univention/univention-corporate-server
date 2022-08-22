set_udm_properties_for_kelvin () {
  echo '{ "user": ["displayName", "e-mail", "accountActivationDate", "pwdChangeNextLogin", "serviceprovider", "ucsschoolPurgeTimestamp"]}' > /etc/ucsschool/kelvin/mapped_udm_properties.json
  univention-app restart ucsschool-kelvin-rest-api
}

install_ucschool_bff_users () {
  # do not rename function: used as install_[ENV:TEST_API]_api in autotest-241-ucsschool-HTTP-API.cfg
  . utils.sh && switch_to_test_app_center || true
  echo -n univention > /tmp/univention
  # use brach image if given
  if [ -n "$UCS_ENV_BFF_USERS_IMAGE" ]; then
    if [[ $UCS_ENV_BFF_USERS_IMAGE =~ ^gitregistry.knut.univention.de.* ]]; then
        docker login -u "$GITLAB_REGISTRY_TOKEN" -p "$GITLAB_REGISTRY_TOKEN_SECRET" gitregistry.knut.univention.de
    fi
    univention-app dev-set ucsschool-bff-users "DockerImage=$UCS_ENV_BFF_USERS_IMAGE"
  fi
  univention-app install --noninteractive --username Administrator --pwdfile /tmp/univention ucsschool-bff-users
  docker images
  docker ps -a
  univention-app shell ucsschool-bff-users ps aux
}