# Helper lib for writing join-scripts for the Univention App Center
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

. /usr/share/univention-join/joinscripthelper.lib
. /usr/share/univention-lib/ldap.sh

JS_SCRIPT_FULLNAME="$(readlink -f "$JS_RUNNING_FILENAME")"
APP="$(echo "$JS_SCRIPT_FULLNAME" | sed 's/.*\/[0-9]\+\(\(.*\)-uninstall\.uinst\|\(.*\)\.u\?inst\)/\2\3/')"
SERVICE="$(univention-app get "$APP" Application:Name --values-only)"
ucr_container_key="$(univention-app get $APP ucr_container_key --values-only)"
APP_VERSION="$(univention-app get $APP version --values-only)"
CONTAINER=$(ucr get "$ucr_container_key")

joinscript_add_simple_app_system_user () {
	local password
	local pwdfile

	password="$(makepasswd)"
	pwdfile="/etc/$APP.secret"
	joinscript_run_in_container touch "$pwdfile"
	joinscript_run_in_container chmod 600 "$pwdfile"
	echo "$password" > $(joinscript_container_file "$pwdfile")

	eval "$(ucr shell ldap/base)"

	udm users/ldap create "$@" --ignore_exists \
		--position "cn=users,$ldap_base" \
		--set username="$APP-systemuser" \
		--set password="$password" \
		--set firstname="$SERVICE Service" \
		--set lastname="LDAP Account" \
		--set description="Account used by $SERVICE to authenticate against LDAP directory" \
		--set objectFlag="hidden" || die

	udm users/ldap modify "$@" \
		--dn "uid=$APP-systemuser,cn=users,$ldap_base" \
		--set password="$password"
}

joinscript_container_is_running () {
	univention-app status "$APP"
	return $?
}

joinscript_run_in_container () {
	joinscript_container_is_running 1>/dev/null || die
	univention-app shell "$APP" "$@"
}

joinscript_container_file_touch () {
	local filename
	filename="$(joinscript_container_file $1)"
	mkdir -p "$(dirname $filename)"
	touch "$filename"
	echo "$filename"
}

joinscript_container_file () {
	joinscript_container_is_running 1>/dev/null || die
	docker_dir="$(docker inspect --format={{.GraphDriver.Data.MergedDir}} $CONTAINER)"
	echo "${docker_dir}/${1}"
}

joinscript_register_schema () {
	ucs_registerLDAPExtension \
		--schema "/usr/share/univention-appcenter/apps/$APP/$APP.schema" \
		--packagename "appcenter-app-$APP" \
		--packageversion "$APP_VERSION" \
		"$@"
}
