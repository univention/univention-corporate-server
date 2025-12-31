# shellcheck shell=sh
# Univention admember Shell Library
#
# SPDX-FileCopyrightText: 2014-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# create a ucs-sso A record in AD
# $1 binddn
# $2 bindpw
# $3 bindpwdfile
# $4 fqdn
# $5 ip
add_host_record_in_ad () {
python3 -c "
import univention.lib.admember
import sys
univention.lib.admember.initialize_debug()
if univention.lib.admember.add_host_record_in_ad(binddn='$1', bindpw='$2', bindpwdfile='$3', fqdn='$4', ip='$5', sso='$6'):
	sys.exit(0)
else:
	sys.exit(1)
"
}

is_domain_in_admember_mode () {
python3 -c "
import univention.lib.admember
import sys
univention.lib.admember.initialize_debug()
if univention.lib.admember.is_domain_in_admember_mode():
	sys.exit(0)
else:
	sys.exit(1)
"
}

is_localhost_in_admember_mode () {
python3 -c "
import univention.lib.admember
import sys
univention.lib.admember.initialize_debug()
if univention.lib.admember.is_localhost_in_admember_mode():
        sys.exit(0)
else:
        sys.exit(1)
"
}

configure_backup_as_ad_member() {
python3 -c "
import univention.lib.admember
univention.lib.admember.initialize_debug()
univention.lib.admember.configure_backup_as_ad_member()
"
}

configure_slave_as_ad_member () {
python3 -c "
import univention.lib.admember
univention.lib.admember.initialize_debug()
univention.lib.admember.configure_slave_as_ad_member()
"
}

configure_member_as_ad_member () {
python3 -c "
import univention.lib.admember
univention.lib.admember.initialize_debug()
univention.lib.admember.configure_member_as_ad_member()
"
}

revert_backup_ad_member () {
python3 -c "
import univention.lib.admember
univention.lib.admember.initialize_debug()
univention.lib.admember.revert_backup_ad_member()
"
}

configure_container_as_ad_member () {
python3 -c "
import univention.lib.admember
univention.lib.admember.initialize_debug()
univention.lib.admember.configure_container_as_ad_member()
"
}

revert_slave_ad_member() {
python3 -c "
import univention.lib.admember
univention.lib.admember.initialize_debug()
univention.lib.admember.revert_slave_ad_member()
"
}

revert_member_ad_member() {
python3 -c "
import univention.lib.admember
univention.lib.admember.initialize_debug()
univention.lib.admember.revert_member_ad_member()
"
}

revert_container_ad_member() {
python3 -c "
import univention.lib.admember
univention.lib.admember.initialize_debug()
univention.lib.admember.revert_container_ad_member()
"
}

configure_nonmaster_as_ad_member () {
	local role="${1:-}"
	case "$role" in
	domaincontroller_backup) configure_backup_as_ad_member ;;
	domaincontroller_slave) configure_slave_as_ad_member ;;
	memberserver) configure_member_as_ad_member ;;
	container) configure_container_as_ad_member ;;
	esac
}

revert_nonmaster_ad_member () {
	local role="${1:-}"
	case "$role" in
	domaincontroller_backup) revert_backup_ad_member ;;
	domaincontroller_slave) revert_slave_ad_member ;;
	memberserver) revert_member_ad_member ;;
	container) revert_container_ad_member ;;
	esac
}
