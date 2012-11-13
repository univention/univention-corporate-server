#!/bin/sh
#
# Univention Installer
#  install Univention Configuration Registry
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

# update progress message
. /tmp/progress.lib
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Installing Univention base packages")" >&9

# Bug 28473: disable reconfiguration of interfaces temporary - will be reenabled before reboot
ucr set --force interfaces/restart/auto=no

# copy UCR settings from installer ramdisk to new system
for fn in base.conf base-ldap.conf base-forced.conf ; do
	cp "/etc/univention/$fn" "/instmnt/etc/univention/$fn"
done

PIPE="yes yes '' |"
cat >/instmnt/install_config_registry.sh <<__EOT__
#!/bin/sh
echo "PROGRESS: $0: Calculating number of packages"
PKGCNT="\$(apt-get -y -o APT::Get::AllowUnauthenticated=1 install -s -y --ignore-missing python-univention-lib univention-config-registry bind9-host | grep "^Inst " | wc -l)"
echo "__STEPS__:\$((\$PKGCNT * 3))" >&9

export DEBIAN_FRONTEND=noninteractive
apt-get -y -o APT::Status-FD=9 -o APT::Get::AllowUnauthenticated=1 install python-univention-lib
$PIPE dpkg --configure -a
apt-get -y -o APT::Status-FD=9 -o APT::Get::AllowUnauthenticated=1 install univention-config-registry
$PIPE dpkg --configure -a
apt-get -y -o APT::Status-FD=9 -o APT::Get::AllowUnauthenticated=1 install bind9-host
$PIPE dpkg --configure -a
__EOT__
chmod +x /instmnt/install_config_registry.sh
chroot /instmnt ./install_config_registry.sh
