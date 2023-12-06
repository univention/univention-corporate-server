
install_guardian_management_api_from_branch () {
  local management_api_docker_image="$1"
  local app_settings="${*:2}"
  echo -n univention > /tmp/univention
  if [ -n "$management_api_docker_image" ]; then
	  python3 /root/guardian/appcenter-change-compose-image.py -a guardian-management-api -i $management_api_docker_image
  fi
  cmd="univention-app install guardian-management-api --noninteractive --username Administrator --pwdfile /tmp/univention"
  if [ -n "$app_settings" ]; then
    exec $cmd --set $app_settings
  else
    exec $cmd
  fi
  container_name="appcenter/apps/guardian-management-api/container"
  container=$(ucr get "$container_name")
  commit=$(docker inspect --format='{{.Config.Labels.commit}}' "$container")
  echo "Docker image built from commit: $commit"
}

install_guardian_authorization_api_from_branch () {
  local authorization_api_docker_image="$1"
  local opa_docker_image="$2"
  local app_settings="${*:3}"
  echo -n univention > /tmp/univention
  if [ -n "$authorization_api_docker_image" -a -n "$opa_docker_image" ]; then
	  python3 /root/guardian/appcenter-change-compose-image.py -a guardian-authorization-api -i $authorization_api_docker_image -o opa $opa_docker_image
  elif [ -n "$authorization_api_docker_image" ]; then
	  python3 /root/guardian/appcenter-change-compose-image.py -a guardian-authorization-api -i $authorization_api_docker_image
  fi
  cmd="univention-app install guardian-authorization-api --noninteractive --username Administrator --pwdfile /tmp/univention"
  if [ -n "$app_settings" ]; then
    exec $cmd --set $app_settings
  else
    exec $cmd
  fi
  container_name="appcenter/apps/guardian-authorization-api/container"
  container=$(ucr get "$container_name")
  commit=$(docker inspect --format='{{.Config.Labels.commit}}' "$container")
  echo "Docker image built from commit: $commit"
}
