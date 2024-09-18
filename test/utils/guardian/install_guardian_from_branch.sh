install_guardian_management_api_from_branch () {
  local management_api_appcenter_version="$1"
  local management_api_docker_image="$2"
  local app_settings="${*:3}"
  echo -n univention > /tmp/univention
  if [ -n "$management_api_docker_image" ]; then
    python3 /root/guardian/appcenter-change-compose-image.py \
      -a guardian-management-api \
      -i "$management_api_docker_image" \
      -v "$management_api_appcenter_version"
  fi
  local app_name="guardian-management-api"
  if [ -n "$management_api_appcenter_version" ]; then
    app_name="guardian-management-api=${management_api_appcenter_version}"
  fi
  cmd="univention-app install ${app_name} --noninteractive --username Administrator --pwdfile /tmp/univention"
  if [ -n "$app_settings" ]; then
    eval "${cmd} --set ${app_settings}"
  else
    eval "$cmd"
  fi
  container_name="appcenter/apps/guardian-management-api/container"
  container=$(ucr get "$container_name")
  commit=$(docker inspect --format='{{.Config.Labels.commit}}' "$container")
  echo "Docker image built from commit: $commit"
}

install_guardian_authorization_api_from_branch () {
  local authorization_api_appcenter_version="$1"
  local authorization_api_docker_image="$2"
  local opa_docker_image="$3"
  local app_settings="${*:4}"
  echo -n univention > /tmp/univention
  if [ -n "$authorization_api_docker_image" -a -n "$opa_docker_image" ]; then
    python3 /root/guardian/appcenter-change-compose-image.py \
      -a guardian-authorization-api \
      -i "$authorization_api_docker_image" \
      -v "$authorization_api_appcenter_version" \
      -o opa "$opa_docker_image"
  elif [ -n "$authorization_api_docker_image" ]; then
    python3 /root/guardian/appcenter-change-compose-image.py \
      -a guardian-authorization-api \
      -i "$authorization_api_docker_image" \
      -v "$authorization_api_appcenter_version"
  fi
  local app_name="guardian-authorization-api"
  if [ -n "$authorization_api_appcenter_version" ]; then
    app_name="guardian-authorization-api=${authorization_api_appcenter_version}"
  fi
  cmd="univention-app install ${app_name} --noninteractive --username Administrator --pwdfile /tmp/univention"
  if [ -n "$app_settings" ]; then
    eval "${cmd} --set ${app_settings}"
  else
    eval "$cmd"
  fi
  container_name="appcenter/apps/guardian-authorization-api/container"
  container=$(ucr get "$container_name")
  commit=$(docker inspect --format='{{.Config.Labels.commit}}' "$container")
  echo "Docker image built from commit: $commit"
}

install_guardian_management_ui_from_branch () {
  local management_ui_appcenter_version="$1"
  local management_ui_docker_image="$2"
  local app_settings="${*:3}"
  echo -n univention > /tmp/univention
  if [ -n "$management_ui_docker_image" ]; then
    python3 /root/guardian/appcenter-change-compose-image.py \
      -a guardian-management-ui \
      -i "$management_ui_docker_image" \
      -v "$management_ui_appcenter_version"
  fi
  local app_name="guardian-management-ui"
  if [ -n "$management_ui_appcenter_version" ]; then
    app_name="guardian-management-ui=${management_ui_appcenter_version}"
  fi
  cmd="univention-app install ${app_name} --noninteractive --username Administrator --pwdfile /tmp/univention"
  if [ -n "$app_settings" ]; then
    eval "${cmd} --set ${app_settings}"
  else
    eval "$cmd"
  fi
  container_name="appcenter/apps/guardian-management-ui/container"
  container=$(ucr get "$container_name")
  commit=$(docker inspect --format='{{.Config.Labels.commit}}' "$container")
  echo "Docker image built from commit: $commit"
}
