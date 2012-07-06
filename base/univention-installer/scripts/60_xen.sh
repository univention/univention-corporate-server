#!/bin/sh
#
# Univention Installer
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

# Add Xen console
if test -c /dev/hvc0 ; then
	# update progress message
	. /tmp/progress.lib
    echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Configuring XEN")" >&9

    cat <<EOF >>/instmnt/etc/inittab
hvc0:2345:respawn:/sbin/getty 38400 hvc0
EOF

echo hvc0 >>/instmnt/etc/securetty
fi
