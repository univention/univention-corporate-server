#!/bin/sh
#
# Univention Installer
#  setup repository
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Configuring online repository")" >&9

. /tmp/installation_profile

if [ -n "$system_role" ]; then
	export server_role="$system_role"
fi

if [ -n "$local_repository" ] && [ "$local_repository" = "true" -o "$local_repository" = "yes" ]; then
	# call univention-repository-create in non-interactive mode with the /sourcedevice directory as installation medium (-N mount is not required)
	chroot /instmnt /usr/sbin/univention-repository-create -n -N -m /sourcedevice
fi

# create sources.list
chroot /instmnt univention-config-registry set repository/online=yes repository/mirror?yes

# create an empty sources.list
if [ -e "/instmnt/etc/apt/sources.list" ]; then
	echo "# This file is not maintained via Univention Configuration Registry
# and can be used to add further package repositories manually
" > /instmnt/etc/apt/sources.list
fi

# update package lists
chroot /instmnt apt-get update
