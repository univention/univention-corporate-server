#!/bin/sh
#
# Univention Installer
#  reboot system
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

. /tmp/installation_profile

/bin/umount /instmnt/proc/fs/nfsd > /dev/null 2>&1
/bin/umount /instmnt/proc > /dev/null 2>&1
/bin/umount /instmnt/sys > /dev/null 2>&1
/bin/umount /instmnt/dev > /dev/null 2>&1

IFS='
'
for i in $(ucr search --brief installer/.*/mp | awk -F ': ' '{print $2}'); do 
	if [ "$i" = "/" -o "$i" = "None" -o "$i" = "none" -o "$i" = "unknown" ]; then
		continue
	fi
	if [ ! -d "/instmnst/$i" ]; then
		continue
	fi
	/bin/umount "/instmnst/$i" > /dev/null 2>&1
done
unset IFS

# root
/bin/umount /instmnt > /dev/null 2>&1

# fsck on ext file systems
if [ $? -eq 0 ]; then
	root=$(ucr get installer/device/0/name)
	fs=$(ucr get installer/device/0/fs)
	if [ -n "$root" -a -b "$root" -a -n "$fs" ]; then
		if [ "$fs" = "ext2" -o "$fs" = "ext3" -o "$fs" = "ext4" ]; then
			e2fsck -y "$root" > /dev/null 2>&1
		fi
	fi
fi

/bin/umount -l /instmnt > /dev/null 2>&1

sync

reboot
