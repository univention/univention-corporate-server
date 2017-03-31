#!/bin/bash
#
# Copyright (C) 2010-2017 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

export DEBIAN_FRONTEND=noninteractive

UPDATER_LOG="/var/log/univention/updater.log"
UPDATE_NEXT_VERSION="$1"

install ()
{
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install "$@" >>"$UPDATER_LOG" 2>&1
}
reinstall ()
{
	install --reinstall "$@"
}
check_and_install ()
{
	local state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		install "$1"
	fi
}
check_and_reinstall ()
{
	local state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		reinstall "$1"
	fi
}
is_installed ()
{
	local state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	test "$state" = "install"
	return $?
}
is_deinstalled() {
	local state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	test "$state" = "deinstall"
	return $?
}

echo -n "Running postup.sh script:"
echo >> "$UPDATER_LOG"
date >>"$UPDATER_LOG" 2>&1

eval "$(univention-config-registry shell)" >>"$UPDATER_LOG" 2>&1

# shell-univention-lib is proberly not installed, so use a local function
is_ucr_true () {
    local value
    value="$(/usr/sbin/univention-config-registry get "$1")"
    case "$(echo -n "$value" | tr '[:upper:]' '[:lower:]')" in
        1|yes|on|true|enable|enabled) return 0 ;;
        0|no|off|false|disable|disabled) return 1 ;;
        *) return 2 ;;
    esac
}

if [ -z "$server_role" ] || [ "$server_role" = "basesystem" ] || [ "$server_role" = "basissystem" ]; then
	install univention-basesystem
elif [ "$server_role" = "domaincontroller_master" ]; then
	install univention-server-master
elif [ "$server_role" = "domaincontroller_backup" ]; then
	install univention-server-backup
elif [ "$server_role" = "domaincontroller_slave" ]; then
	install univention-server-slave
elif [ "$server_role" = "memberserver" ]; then
	install univention-server-member
elif [ "$server_role" = "mobileclient" ]; then
	install univention-mobile-client
elif [ "$server_role" = "fatclient" ] || [ "$server_role" = "managedclient" ]; then
	install univention-managed-client
fi

# update to firefox-esr, can be removed after update to 4.2-0
if is_installed firefox-en; then
	install firefox-esr
	dpkg -P firefox-en >>"$UPDATER_LOG" 2>&1
fi
if is_installed firefox-de; then
	install firefox-esr-l10n-de
	dpkg -P firefox-de >>"$UPDATER_LOG" 2>&1
fi

# after update to apache 2.4 (UCS 4.2), old apache 2.2 config files
# can be purged as they conflict with new naming schema (package has
# already been removed)
if is_deinstalled apache2.2-common; then
	dpkg -P apache2.2-common >>"$UPDATER_LOG" 2>&1
fi

# Update to UCS 4.2 autoremove
if ! is_ucr_true update42/skip/autoremove; then
	DEBIAN_FRONTEND=noninteractive apt-get -y --force-yes autoremove >>"$UPDATER_LOG" 2>&1
fi

# This HAS to be done after the UCS 4.2 apt-get autoremove (Bug #43782#c2)
if is_installed kopano-webmeetings; then
	a2enmod proxy_wstunnel >>"$UPDATER_LOG" 2>&1
	service apache2 restart >>"$UPDATER_LOG" 2>&1
fi

# removes temporary sources list (always required)
if [ -e "/etc/apt/sources.list.d/00_ucs_temporary_installation.list" ]; then
	rm -f /etc/apt/sources.list.d/00_ucs_temporary_installation.list
fi

# executes custom postup script (always required)
if [ ! -z "$update_custom_postup" ]; then
	if [ -f "$update_custom_postup" ]; then
		if [ -x "$update_custom_postup" ]; then
			echo -n "Running custom postupdate script $update_custom_postup"
			"$update_custom_postup" "$UPDATE_NEXT_VERSION" >>"$UPDATER_LOG" 2>&1
			echo "Custom postupdate script $update_custom_postup exited with exitcode: $?" >>"$UPDATER_LOG"
		else
			echo "Custom postupdate script $update_custom_postup is not executable" >>"$UPDATER_LOG"
		fi
	else
		echo "Custom postupdate script $update_custom_postup not found" >>"$UPDATER_LOG"
	fi
fi

if [ -x /usr/sbin/univention-check-templates ]; then
	/usr/sbin/univention-check-templates >>"$UPDATER_LOG" 2>&1
	rc=$?
	if [ "$rc" != 0 ]; then
		echo "Warning: UCR templates were not updated. Please check $UPDATER_LOG or execute univention-check-templates as root."
	fi
fi

if [ -f /var/univention-join/joined -a "$server_role" != basesystem ]; then
	udm "computers/$server_role" modify \
		--binddn "$ldap_hostdn" \
		--bindpwdfile "/etc/machine.secret" \
		--dn "$ldap_hostdn" \
		--set operatingSystem="Univention Corporate Server" \
		--set operatingSystemVersion="4.2-0" >>"$UPDATER_LOG" 2>&1
fi

# Move to mirror mode for previous errata component
ucr set \
	version/erratalevel=0 \
	repository/online/component/4.2-0-errata=enabled \
	repository/online/component/4.2-0-errata/description="Errata updates for UCS 4.2-0" \
	repository/online/component/4.2-0-errata/version="4.2" >>"$UPDATER_LOG" 2>&1

# run remaining joinscripts
if [ "$server_role" = "domaincontroller_master" ]; then
	univention-run-join-scripts >>"$UPDATER_LOG" 2>&1
fi

# Bug #43217: Fix DNS configuration in UCR
[ -x /usr/share/univention-server/univention-fix-ucr-dns ] &&
	/usr/share/univention-server/univention-fix-ucr-dns $(is_installed bind9 || --no-self) >>"$UPDATER_LOG" 2>&1 ||
	: # better safe than sorry

# Bug #44006: 
(
	if [ -x /usr/lib/univention-docker/scripts/migrate_container_MountPoints_to_v2_config ]; then
		restart=0
		if pgrep -F /var/run/docker.pid >/dev/null 2>&1; then
			restart=1
		fi
		service docker stop || true

		## start docker daemon (manually w/o systemd)
		## to make it generate config.v2.json
		. /etc/default/docker	## load DOCKER_OPTS
		/usr/bin/dockerd -H unix:///var/run/docker.sock $DOCKER_OPTS &
		i=0; while [ "$((i++))" -lt 1800 ]; do 
			if docker ps >/dev/null 2>&1; then
				break
			fi
			sleep 1;
		done
		pkill -F /var/run/docker.pid

		## Now migrate volumes to config.v2.json
		/usr/lib/univention-docker/scripts/migrate_container_MountPoints_to_v2_config

		if [ "$restart" = 1 ]; then
			service docker start || true
		fi
	fi
) >>"$UPDATER_LOG" 2>&1

# Bug #44188: recreate and reload packetfilter rules to make sure the system is accessible
service univention-firewall restart >>"$UPDATER_LOG" 2>&1

# Bug #43835: update app cache and portal entries
test -x /usr/bin/univention-app && univention-app update >>"$UPDATER_LOG" 2>&1
python -c '
import sys
from univention.appcenter.ucr import ucr_keys, ucr_instance
sys.path.append("/etc/univention/templates/modules")
import create_portal_entries
import re
ids = set()
for key in ucr_keys():
    match = re.match("ucs/web/overview/entries/(admin|service)/([^/]+)/.*", key)
    if match:
        ids.add(key)
changes = dict((id, (None, None)) for id in ids)
create_portal_entries.handler(ucr_instance(), changes)
' >>"$UPDATER_LOG" 2>&1

echo "


****************************************************
*    THE UPDATE HAS BEEN FINISHED SUCCESSFULLY.    *
* Please make a page reload of UMC and login again *
****************************************************


" >>"$UPDATER_LOG" 2>&1

echo "done."
date >>"$UPDATER_LOG"

# make sure that UMC server is restarted (Bug #43520, Bug #33426)
at now >>"$UPDATER_LOG" 2>&1 <<EOF
sleep 30
/usr/share/univention-updater/enable-apache2-umc --no-restart >>"$UPDATER_LOG" 2>&1
service univention-management-console-server restart >>"$UPDATER_LOG" 2>&1
service univention-management-console-web-server restart >>"$UPDATER_LOG" 2>&1
# the file path moved. during update via UMC the apache is not restarted. The new init script therefore checks the wrong pidfile which fails restarting.
cp /var/run/apache2.pid /var/run/apache2/apache2.pid
service apache2 restart >>"$UPDATER_LOG" 2>&1
EOF

exit 0
