#!/bin/sh
#
# Univention Installer
#  mount partitions
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

# Mount /xxx partitions
set | egrep "^dev_" | while read line; do
	name=`echo $line | sed -e 's|=.*||'`
	var=`echo $line | sed -e 's|.*=.||;s|"||g' | sed -e "s|'||g"`
	if [ "$name" = "devices" ]; then
		continue
	fi
	# dev_%d = "parttype device type format fstype start end mpoint"
	device_name=`echo $var | awk '{print $2}'`
	device_type=`echo $var | awk '{print $3}'`
 	device_format=`echo $var | awk '{print $4}'`
	device_fs=`echo $var | awk '{print $5}'`
	device_start=`echo $var | awk '{print $6}'`
	device_end=`echo $var | awk '{print $7}'`
	device_mp=`echo $var | awk '{print $8}'`

	if [ -n "$device_fs" ]; then
		if [ "$device_fs" = "linux-swap" ]; then
			swapon $device_name
		elif [ -z "$device_mp" ]; then
			continue;
		elif [ "$device_mp" = '/' ]; then
			continue;
		elif [ "$device_mp" = 'unknown' ]; then
			continue;
		elif [ "$device_fs" = 'unknown' ]; then
			continue;
		elif [ "$device_fs" = 'None' -o "$device_fs" = "none" ]; then
			continue;
		elif [ "$device_mp" = 'None' -o "$device_mp" = "none" ]; then
			continue;
		else
			mkdir -p /instmnt/$device_mp
			mount -t $device_fs $device_name /instmnt/$device_mp
			echo -n "  $device_name ($device_mp)" >>/instmnt/.log
			echo -n "  $device_name ($device_mp)"
			if [ "$device_mp" = "/tmp" ]; then
			    chmod 0777 /instmnt/$device_mp
			    chmod +t /instmnt/$device_mp
			fi
		fi
	fi
done
echo "" >>/instmnt/.log
echo ""

mkdir -p /instmnt/tmp
mkdir -p /tmp/logging
