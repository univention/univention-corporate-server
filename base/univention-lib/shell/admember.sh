# shellcheck shell=sh
# Univention admember Shell Library
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2014-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

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
if univention.lib.admember.add_host_record_in_ad(binddn='$1', bindpw='$2', bindpwdfile='$3', fqdn='$4', ip='$5'):
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
