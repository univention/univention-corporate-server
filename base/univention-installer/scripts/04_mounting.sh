#!/bin/sh
#
# Univention Installer
#  mount partitions
#
# Copyright (C) 2004-2009 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

. /tmp/installation_profile

echo -n "Mounting Partitions: " >>/instmnt/.log
echo -n "Mounting Partitions: "

ucr="python2.4 /sbin/univention-config-registry"
tmp="/tmp/installer.partitions.tmp"

$ucr search installer > $tmp

while read line; do

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
