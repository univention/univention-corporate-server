install_user_management_from_branch () {
  local user_management_docker_image="$1"
  local app_settings="${*:2}"
  echo -n univention > /tmp/univention
  if [ -n "$user_management_docker_image" ]; then
	  python3 /root/guardian/appcenter-change-compose-image.py -a ucsschool-user-management -i $user_management_docker_image
  fi
  cmd="univention-app install ucsschool-user-management --noninteractive --username Administrator --pwdfile /tmp/univention"
  if [ -n "$app_settings" ]; then
    exec $cmd --set $app_settings
  else
    exec $cmd
  fi
  container_name="appcenter/apps/ucsschool-user-management/container"
  container=$(ucr get "$container_name")
  commit=$(docker inspect --format='{{.Config.Labels.commit}}' "$container")
  echo "Docker image built from commit: $commit"
}
