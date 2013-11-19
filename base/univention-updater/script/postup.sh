#!/bin/bash
#
# Copyright (C) 2010-2013 Univention GmbH
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
	state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		install "$1"
	fi
}
check_and_reinstall ()
{
	state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		reinstall "$1"
	fi
}

echo -n "Running postup.sh script:"
echo >> "$UPDATER_LOG"
date >>"$UPDATER_LOG" 2>&1

eval "$(univention-config-registry shell)" >>"$UPDATER_LOG" 2>&1

# Remove VNC module; Bug #30158
univention-remove -y --purge univention-management-console-module-vnc >>"$UPDATER_LOG" 2>&1

# Remove Flash plugin installer, Bug #31852
univention-remove -y --purge univention-flashplugin >>"$UPDATER_LOG" 2>&1

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
		if [ "$rc" = 1 ]; then
			echo "Warning: $rc UCR template was not updated. Please check $UPDATER_LOG or execute univention-check-templates as root."
		else
			echo "Warning: $rc UCR templates were not updated. Please check $UPDATER_LOG or execute univention-check-templates as root."
		fi
	fi
fi

# For UCS 3.2-0 a reinstallation of GRUB2 is required - otherwise the system is unbootable (Bug #32634)
eval "$(ucr shell update/grub/boot)"
if [ -n "$update_grub_boot" ] ; then
	echo "Installing new grub version into device \"$update_grub_boot\" ..." >> "$UPDATER_LOG"
	grub-install "$update_grub_boot" && \
       ucr unset update/grub/boot || \
       echo -e "Warning: Installation of GRUB on device \"$update_grub_boot\" failed!\nPlease run 'grub-install <DEVICE>' manually, to update GRUB on your boot device." | tee -a "$UPDATER_LOG" >&2
fi
. /usr/share/univention-lib/ucr.sh
if is_ucr_true grub/efi ; then
	echo "Installing new grub version ..." >> "$UPDATER_LOG"
	grub-install || echo -e "Warning: Installation of GRUB failed!\nPlease run 'grub-install' manually, to update GRUB on your boot device." | tee -a "$UPDATER_LOG" >&2
fi

# For UCS 3.2 update scenario, should be removed after the UCS 3.2 release
#  https://forge.univention.org/bugzilla/show_bug.cgi?id=33121
ucr set connector/s4/mapping/group/grouptype?false >>"$UPDATER_LOG" 2>&1

# For UCS 3.2-0 a reboot is required
univention-config-registry set update/reboot/required=true >>"$UPDATER_LOG" 2>&1

# Move to mirror mode for previous errata component
ucr set \
	repository/online/component/3.1-1-errata=false \
	repository/online/component/3.1-1-errata/localmirror=true >>"$UPDATER_LOG" 2>&1	

# Set errata component for UCS 3.2-0
ucr set \
	repository/online/component/3.2-0-errata=enabled \
	repository/online/component/3.2-0-errata/description="Errata updates for UCS 3.2-0" \
	repository/online/component/3.2-0-errata/version="3.2" >>"$UPDATER_LOG" 2>&1

# Reset errata level
univention-config-registry set version/erratalevel=0 >>"$UPDATER_LOG" 2>&1

# make sure that UMC server is restarted (Bug #33426)
echo "


****************************************************
*    THE UPDATE HAS BEEN FINISHED SUCCESSFULLY.    *
* Please make a page reload of UMC and login again *
****************************************************


" >>"$UPDATER_LOG" 2>&1

echo -n "Restart UMC server components to finish update... " >>"$UPDATER_LOG" 2>&1
sleep 10s
/usr/share/univention-updater/disable-apache2-umc --exclude-apache >>"$UPDATER_LOG" 2>&1
/usr/share/univention-updater/enable-apache2-umc >>"$UPDATER_LOG" 2>&1
echo "restart done" >>"$UPDATER_LOG" 2>&1

echo "done."
date >>"$UPDATER_LOG"

exit 0
