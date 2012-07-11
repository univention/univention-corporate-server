#!/bin/sh
#
# Univention Installer
#  create sources.list
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Configuring basesystem")" >&9

mkdir -p /instmnt/etc/apt/
mkdir -p /instmnt/sourcedevice
## check for repository structure
# old repository (DVD)
if [ -d /mnt/packages ]; then
	cat >/instmnt/etc/apt/sources.list <<__EOT__
#UCS Installation

deb file:/sourcedevice/packages ./
__EOT__
else
    version=`cat /mnt/.univention_install | grep VERSION | sed -e 's|VERSION=||'`

    repo_dir="file:/sourcedevice/mirror/${version}/maintained/ ${version}-0"
	cat >/instmnt/etc/apt/sources.list <<__EOT__
#UCS Installation

deb $repo_dir/all/
__EOT__
	for arch in i386 amd64 extern; do
		if [ -d "/mnt/mirror/${version}/maintained/${version}-0/$arch" ]; then
			echo "deb $repo_dir/$arch/" >> /instmnt/etc/apt/sources.list
		fi
	done
fi

chmod 644 /instmnt/etc/apt/sources.list
rm -Rf /instmnt/etc/apt/sources.list.d

# umount the source device (mounted in 10_debootstrap.sh)
umount /mnt
