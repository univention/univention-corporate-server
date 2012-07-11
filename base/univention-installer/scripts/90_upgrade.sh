#!/bin/sh
#
# Univention Installer
#  install packages
#
# Copyright 2004-2012 Univention GmbH
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

# upgrade progress message

. /tmp/installation_profile

export server_role="$system_role"

if [ "$update_system_after_installation" = "true" ] || [ "$update_system_after_installation" = "yes" ]; then
	. /tmp/progress.lib
	echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Updating system")" >&9
	echo "__SUBMSG__:$(LC_ALL=$INSTALLERLOCALE gettext "This might take a while depending on the number of pending updates.")" >&9

	if [ "$server_role" = "domaincontroller_master" ]; then
		# Update to latest patchlevel
		cat >/instmnt/upgrade.sh <<"__EOT__"
#!/bin/sh
eval "$(ucr shell)"
echo "Running upgrade on DC Master: univention-upgrade --noninteractive --updateto $version_version-99"
univention-upgrade --noninteractive --updateto "$version_version-99"
__EOT__
	else
		# Try to update to the same version as DC master
		cat >/instmnt/upgrade.sh <<"__EOT__"
#!/bin/sh
eval "$(ucr shell)"
if [ -e /var/univention-join/joined ]; then
	vv=$(univention-ssh /etc/machine.secret $hostname\$@$hostname /usr/sbin/ucr get version/version 2>/dev/null)
	pl=$(univention-ssh /etc/machine.secret $hostname\$@$hostname /usr/sbin/ucr get version/patchlevel 2>/dev/null)
	echo "Running upgrade to DC Master  version: univention-upgrade --noninteractive --updateto $vv-$pl"
	univention-upgrade --noninteractive --updateto "$vv-$pl"
else
	echo "Running normal upgrade: univention-upgrade --noninteractive --updateto $version_version-0"
	univention-upgrade --noninteractive --updateto "$version_version-0"
fi
__EOT__
	fi
	chmod +x /instmnt/upgrade.sh
	chroot /instmnt ./upgrade.sh </dev/tty1
fi
