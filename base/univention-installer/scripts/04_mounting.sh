#!/bin/sh
#
# Univention Installer
#  mount partitions
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Mounting target devices")" >&9

. /tmp/installation_profile

echo -n "Mounting Partitions: " >>/instmnt/.log
echo -n "Mounting Partitions: "

ucr="python2.6 /sbin/univention-config-registry"
tmp="/tmp/installer.partitions.tmp"

$ucr search --brief installer > $tmp

while read line
do
	device=$(echo $line | awk -F / {'print $2'})

	if [ "device" = "$device" ]; then
		value=$(echo $line | awk -F : {'print $2'})
		key=$(echo $line | awk -F : {'print $1'})
		count=$(echo $key | awk -F / {'print $3'})
		typ=$(echo $key | awk -F / {'print $4'})

		value=$(echo $value | sed 's/\s//g')
		if [ -z "$value" ]; then
			value="None"
		fi

		if [ "name" = "$typ" ]; then
			name=$value
		fi
		if [ "fs" = "$typ" ]; then
			fs=$value
		fi
		if [ "mp" = "$typ" ]; then
			mp=$value
		fi

		if [ -n "$name" ] && [ -n "$fs" ] && [ -n "$mp" ]; then
			if [ "$fs" = "linux-swap" ]; then
				swapon $name
			elif [ "$fs" = 'None' -o "$fs" = "none" -o "$fs" = 'unknown' ]; then
				true
			elif [ "$mp" = 'None' -o "$mp" = "none" -o "$mp" = 'unknown' -o "$mp" = '/' ]; then
				true
			else
				mkdir -p /instmnt/$mp
				/bin/mount -t $fs $name /instmnt/$mp
				echo -n "  $name ($mp)" >>/instmnt/.log
				echo -n "  $name ($mp)"
				if [ "$mp" = "/tmp" ]; then
				    chmod 0777 /instmnt/$mp
				    chmod +t /instmnt/$mp
				fi
			fi

			unset name
			unset fs
			unset mp
		fi
	fi
done < $tmp

rm -f $tmp

mkdir -p /instmnt/tmp
mkdir -p /tmp/logging
