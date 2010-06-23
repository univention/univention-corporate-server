#!/bin/sh
#
# Univention Thin Client Sound support
#  postinst script for the debian package
#
# Copyright 2007-2010 Univention GmbH
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

eval $(univention-baseconfig shell univentionSoundEnabled thinclient/sound/daemon)

if [ -z "$univentionSoundEnabled" -o "$univentionSoundEnabled" = "0" ]; then
	exit 0
fi

DEFAULTGROUP="Domain Users"

# get gid of default group and use name of default group as fallback
udev_sound_group="$(getent group "$DEFAULTGROUP" | cut -d: -f3)"
[ -z "$udev_sound_group" ] && udev_sound_group="$DEFAULTGROUP"

# get uid of user that recently logged in and use username as fallback
udev_sound_owner="$(getent passwd "$USER" | cut -d: -f3)"
[ -z "$udev_sound_owner" ] && udev_sound_owner="$USER"

# current user and group should be owner of sound device
univention-baseconfig set udev/sound/owner="${udev_sound_owner}" udev/sound/group?"${udev_sound_group}"

# tell udev to update devices of sound subsystems
udevadm control reload_rules
udevadm trigger --subsystem-match=sound

exit 0
