#!/bin/sh
#
# Univention Installer
#  setup udev rules for network interface
#
# Copyright 2008-2012 Univention GmbH
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Updating udev rules")" >&9

. /tmp/installation_profile

UDEVDIR="/instmnt/etc/udev/rules.d"
mkdir -p "$UDEVDIR"
export UDEVRULEFN="${UDEVDIR}/70-persistent-net.rules"

# if dummy network interface is in use, delete mapping from existing rules file
if [ -f "/tmp/dummy-network-interface.txt" -a -f "$UDEVRULEFN" ] ; then
	MACADDR=$(/bin/ifconfig eth0 | grep " HWaddr " | awk "{ print $NF }")
	TMPFN=$(mktemp /tmp/temp.XXXXXXX)
	cat $UDEVRULEFN | grep -v "eth0" | grep -v "$MACADDR" > $TMPFN
	cat $TMPFN > $UDEVRULEFN
fi

if [ -e /instmnt/dev/.udev.disabled ]; then
	# enable udev, also see 10_debootstrap.sh
	mv /instmnt/dev/.udev.disabled /instmnt/dev/.udev
fi
