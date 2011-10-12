#!/bin/sh
#
# Univention Installer
#  sync Administrator password to Samba 4
#
# Copyright 2004-2011 Univention GmbH
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Configuring Samba4")" >&9

. /tmp/installation_profile

cat >>/instmnt/admin_pwd.sh <<__EOT__

if [ -x /usr/sbin/univention-password_sync_ucs_to_s4 ]; then
 	/usr/sbin/univention-password_sync_ucs_to_s4 Administrator
fi

__EOT__

chmod +x /instmnt/admin_pwd.sh
chroot /instmnt ./admin_pwd.sh

