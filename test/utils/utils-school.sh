#!/bin/bash
# SPDX-FileCopyrightText: 2019-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -x

. utils.sh

install_kelvin_api () {
  install_docker_app_from_branch ucsschool-kelvin-rest-api "$UCS_ENV_KELVIN_IMAGE" ucsschool/kelvin/processes=0 ucsschool/kelvin/log_level=DEBUG || return $?
}

install_kelvin_in_version() {
  # Install kelvin in a specified version
  local -i rv=0
  printf '%s' univention > /tmp/univention
  if [ -n "$(ucr get "appcenter/apps/ucsschool-kelvin-rest-api/version")" ]; then
    univention-app remove ucsschool-kelvin-rest-api
  fi
  if [ -n "$KELVIN_VERSION" ]; then
      univention-app install ucsschool-kelvin-rest-api="$KELVIN_VERSION" --noninteractive --set ucsschool/kelvin/processes=0 ucsschool/kelvin/log_level=DEBUG --username Administrator --pwdfile /tmp/univention || rv=$?
      echo "Installed kelvin in Version $(ucr get "appcenter/apps/ucsschool-kelvin-rest-api/version")"
      return $rv
  else
    install_kelvin_api
  fi
}

install_kelvin_prod_version_from_test() {
  # UPGRADE_FROM_PROD: install a *released* (prod) kelvin version to upgrade from.
  # KELVIN_VERSION pins that version, otherwise the latest released one is used.
  # When the scenario runs with the test appcenter, the install is done from
  # there: the test appcenter is a superset of prod, so released versions are
  # available there too, and installing from test (instead of switching the whole
  # appcenter to prod) keeps already-installed test versions of dependencies
  # (e.g. ucsschool) known, so dependency resolution does not pull them into the
  # transaction and abort ("Automatically added App ...").
  local -i rv=0
  local version="$KELVIN_VERSION"
  printf '%s' univention > /tmp/univention
  if [ -n "$(ucr get "appcenter/apps/ucsschool-kelvin-rest-api/version")" ]; then
    univention-app remove ucsschool-kelvin-rest-api
    systemctl stop docker-app-ucsschool-kelvin-rest-api.service
    systemctl daemon-reload
  fi
  if [ -z "$version" ]; then
    # peek at prod only to read the latest installable version (reading does not touch installed apps)
    UCS_TEST_APPCENTER=false switch_app_center
    version="$(univention-app get ucsschool-kelvin-rest-api version | sed -n 's/^Version: //p')"
    # back to the appcenter the scenario runs with
    switch_app_center
  fi
  echo "Installing released kelvin version $version"
  univention-app install "ucsschool-kelvin-rest-api=$version" --noninteractive --set ucsschool/kelvin/processes=0 ucsschool/kelvin/log_level=DEBUG --username Administrator --pwdfile /tmp/univention || rv=$?
  return $rv
}

install_kelvin_version_join_script() {
  # The synthetic "1000-<version>" only lives in the appcenter cache
  # (/var/cache/univention-appcenter/...). That cache is authoritative and gets
  # rebuilt from the server on every "univention-app update"; a ucsschool
  # pre-join hook triggers such a reset via "univention-app upgrade", which
  # drops the 1000-<version> entry and orphans the installed kelvin app, so its
  # own join script (/usr/lib/univention-install/50ucsschool-kelvin-rest-api.inst)
  # then fails. Install a join script numbered below 50 so it re-applies the
  # dev-set and restores the entry *before* kelvin's join script runs.
  [ -n "$KELVIN_UPGRADE_VERSION" ] || return 0
  cat >/usr/lib/univention-install/49reset_kelvin_dev_version.inst <<EOF
#!/bin/bash
VERSION=1
. /usr/share/univention-join/joinscripthelper.lib
joinscript_init
univention-app dev-set ucsschool-kelvin-rest-api="$KELVIN_UPGRADE_VERSION" Version="1000-$KELVIN_UPGRADE_VERSION"
joinscript_save_current_version
exit 0
EOF
  chmod +x /usr/lib/univention-install/49reset_kelvin_dev_version.inst
}

upgrade_kelvin_to_version() {
  # Upgrade Kelvin to a specified version
  local -i rv=0
  printf '%s' univention > /tmp/univention
  if [ -n "$KELVIN_UPGRADE_VERSION" ]; then
    # restore the cache entry before kelvin's own join script runs (see helper)
    install_kelvin_version_join_script
    univention-app dev-set ucsschool-kelvin-rest-api="$KELVIN_UPGRADE_VERSION" Version="1000-$KELVIN_UPGRADE_VERSION"
    univention-app upgrade ucsschool-kelvin-rest-api="1000-$KELVIN_UPGRADE_VERSION" --noninteractive --username Administrator --pwdfile /tmp/univention || rv=$?
    univention-app dev-set ucsschool-kelvin-rest-api="$KELVIN_UPGRADE_VERSION" Version="1000-$KELVIN_UPGRADE_VERSION"
    return $rv
  else
    upgrade_kelvin
  fi
}

install_ucsschool_in_version() {
  # Install UCS@School in a specified version
  local -i rv=0
  printf '%s' univention > /tmp/univention
  if [ -n "$UCSSCHOOL_VERSION" ]; then
    univention-app install ucsschool="$UCSSCHOOL_VERSION" --noninteractive --username Administrator --pwdfile /tmp/univention || rv=$?
    return $rv
  else
    install_ucsschool
  fi
}

upgrade_ucsschool_to_version() {
  # Upgrade UCS@School to a specified version
  local -i rv=0
  printf '%s' univention > /tmp/univention
  if [ -n "$UCSSCHOOL_UPGRADE_VERSION" ]; then
    univention-app dev-set ucsschool="$UCSSCHOOL_UPGRADE_VERSION" Version="1000-$UCSSCHOOL_UPGRADE_VERSION"
    univention-app upgrade ucsschool="1000-$UCSSCHOOL_UPGRADE_VERSION" --noninteractive --username Administrator --pwdfile /tmp/univention || rv=$?
    return $rv
  fi
}

upgrade_kelvin () {
  local -i rv=0
  printf '%s' univention > /tmp/univention
  univention-app upgrade ucsschool-kelvin-rest-api --noninteractive --username Administrator --pwdfile /tmp/univention || rv=$?
  univention-app info
  return $rv
}

install_ucsschool_id_connector () {
  install_docker_app_from_branch ucsschool-id-connector "$UCS_ENV_ID_CONNECTOR_IMAGE" ucsschool-id-connector/log_level=DEBUG || return $?
}

install_ucsschool_id_connector_in_version() {
  local -i rv=0
  printf '%s' univention > /tmp/univention
  if [ -n "$ID_CONNECTOR_VERSION" ]; then
    univention-app install ucsschool-id-connector="$ID_CONNECTOR_VERSION" --set ucsschool-id-connector/log_level=DEBUG --username Administrator --pwdfile /tmp/univention || rv=$?
    return $rv
  else
    install_ucsschool_id_connector
  fi
}

upgrade_ucsschool_id_connector_to_version() {
  # Upgrade ID Connector to a specified version
  local -i rv=0
  printf '%s' univention > /tmp/univention
  if [ -n "$ID_CONNECTOR_UPGRADE_VERSION" ]; then
    univention-app dev-set ucsschool-id-connector="$ID_CONNECTOR_UPGRADE_VERSION" Version="1000-$ID_CONNECTOR_UPGRADE_VERSION"
    univention-app upgrade ucsschool-id-connector="1000-$ID_CONNECTOR_UPGRADE_VERSION" --noninteractive --username Administrator --pwdfile /tmp/univention || rv=$?
    return $rv
  else
    upgrade_id_connector
  fi
}

upgrade_id_connector () {
  local latest_version
  local -i rv=0
  printf '%s' univention > /tmp/univention
  if [ -n "$UCS_ENV_ID_CONNECTOR_IMAGE" ]; then
    latest_version=$(univention-app list ucsschool-id-connector | tail -n 1 | tr -d '[:space:]')
    univention-app dev-set ucsschool-id-connector="$latest_version" "DockerImage=$UCS_ENV_ID_CONNECTOR_IMAGE"
  fi
  univention-app upgrade ucsschool-id-connector --noninteractive --username Administrator --pwdfile /tmp/univention || rv=$?
  univention-app info
  return $rv
}

add_ca_to_host () {
    local host_fqdn="${1:?missing fqdn}"
    curl -k "https://$host_fqdn/ucs-root-ca.crt" > /usr/local/share/ca-certificates/"$host_fqdn".crt
    update-ca-certificates
}

add_dns_entry () {
        local hostname="${1:?missing hostname}"
    local domain="${2:?missing domain}"
    local ip="${3:?missing ip}"
    udm dns/forward_zone create \
        --set zone="$domain" \
        --set nameserver="$(hostname -f)." \
        --position="cn=dns,$(ucr get ldap/base)" \
                --ignore_exists || return 1
    udm dns/host_record create \
        --set a="$ip" \
        --set name="$hostname" \
        --position "zoneName=$domain,cn=dns,$(ucr get ldap/base)" || return 1
    while ! nslookup "$hostname.$domain" | grep -q "$ip"; do
        echo "Waiting for DNS..."
        sleep 1
    done
}

install_ucsschool_apis () {
  install_docker_app_from_branch ucsschool-apis "$UCS_ENV_UCSSCHOOL_APIS_IMAGE" ucsschool/apis/log_level=DEBUG ucsschool/apis/processes=0 || return $?
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
    case "${1:?public}" in
    public) return 0 ;;
    esac

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
        "description",
        "userPath"
    ]
}
EOF
}

# UCS@school performance test helpers

udm_rest_setup () {
	ucr set directory/manager/rest/processes=0
	systemctl restart univention-directory-manager-rest
}

kelvin_setup () {
	univention-app configure ucsschool-kelvin-rest-api --set ucsschool/kelvin/processes=0 --set ucsschool/kelvin/log_level=DEBUG && univention-app restart ucsschool-kelvin-rest-api
}

register_cpu_count () {
    # Register the CPU-Count so the system that does the performance test can check
    # that the right amount of CPUs is set.
    ucr set test/kelvin-performance/cpu-count="$(lscpu --online --parse | grep -v ^# | wc -l)"
}

performance_test_settings () {
	ucr set \
		nss/group/cachefile/invalidate_on_changes=no \
		listener/module/portal_groups/deactivate=yes
	service univention-directory-listener restart
}

performance_test_setup () {
	ucr set security/limits/user/root/soft/nofile=10240
	ucr set security/limits/user/root/hard/nofile=10240
	echo "fs.file-max=1048576" > /etc/sysctl.d/99-file-max.conf
	sysctl -p
}

performance_test_checkout_build_install () {
	local branch="$1"
	local gitlab="git.knut.univention.de"
	[ -z "$branch" ] && echo "ERROR: performance_test_checkout_build_install: specified branch name is empty string" && exit 1
	univention-install -y git
	git clone -b "$branch" "https://$gitlab/univention/dev/education/ucsschool-kelvin-rest-api.git" /var/tmp/kelvin
	cd /var/tmp/kelvin/ucs-test-ucsschool-kelvin
	DEBIAN_FRONTEND=noninteractive apt-get build-dep --yes . && \
		dpkg-buildpackage -b && \
		DEBIAN_FRONTEND=noninteractive apt-get install --yes -f ../ucs-test-ucsschool-kelvin-performance_*.deb || \
			{ echo "ERROR: BUILD OF ucs-test-ucsschool-kelvin-performance FAILED" ; return 1; }
	echo "INFO: ucs-test-ucsschool-kelvin-performance built and installed"
	dpkg -l ucs-test-ucsschool-kelvin-performance
}

SAR_ARGS=( -b -n DEV,IP,TCP,UDP -P ALL -q -r ALL -S -u ALL )
DATA_DIR=/var/log/perfstats

start_system_stats_collection () {
 local host="${1:?missing hostname}"

 apt-get install -y scour sysstat
 mkdir -pv "$DATA_DIR"
 touch "$DATA_DIR/empty-$host"
 # Starting the next two commands in the background has proven to be unreliable. Retrying in a loop.
 count=0; while ! pgrep -f 'ram.sar' > /dev/null && test $count -lt 100; do (nohup sar "${SAR_ARGS[@]}" -o "$DATA_DIR/ram.sar" 1 >/dev/null &); count=$(( count + 1 )); sleep 1; done
 # When not looked at every day anymore, reduce size with: ... | bzip2 -9c > $DATA_DIR/stats-$host.top.txt.bz2 &
 count=0; while ! pgrep -f 'top -bci' > /dev/null && test $count -lt 100; do (nohup top -bci -w512 -d 1 > "$DATA_DIR/stats-$host.top.txt" &); count=$(( count + 1 )); sleep 1; done
 pgrep -af 'top|sar'
}

end_system_stats_collection () {
 local host="${1:?missing hostname}"

 pgrep -af 'top|sar'
 pkill -f ram.sar -SIGINT || true
 pkill -f 'top -bci' || true
 ls -la "$DATA_DIR"
 [ -e "$DATA_DIR/ram.sar" ] && sadf -g "$DATA_DIR/ram.sar" -- "${SAR_ARGS[@]}" | scour -o "$DATA_DIR/stats-$host.sar.svg" || echo "Not found: $DATA_DIR/ram.sar"
 # stats.sar.txt (decompressed) can be uploaded to https://sarchart.dotsuresh.com/ for interactive graphs
 [ -e "$DATA_DIR/ram.sar" ] && sar "${SAR_ARGS[@]}" -f "$DATA_DIR/ram.sar" | bzip2 -9c > "$DATA_DIR/stats-$host.sar.txt.bz2" || echo "Not found: $DATA_DIR/ram.sar"
}
