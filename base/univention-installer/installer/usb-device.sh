#!/bin/sh
#
# Univention Installer
#  helper script: scanning for USB mass storage devices
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

count=0
syslogfile=/var/log/syslogd
#Kernel 2.4

#Kernel 2.6
#str=`dmesg | grep -A4 "USB Mass Storage" | grep ": SCSI emulation for USB Mass Storage device" | sed -e 's| .*||'`

if [ "$1" = "2.4" ]; then
	str=`cat $syslogfile | grep -A5 "USB Mass Storage" | sed -e 's|.* kernel: ||' | grep Attached |\
		sed 	-e 's/.*disk //' \
			-e 's/,\ channel.*//' \
			-e 's/at //' \
			-e 's/ /_/'`

	str_sort=`echo $str | sort|uniq`
	i=0
	for dev_scsi in $str_sort; do
		Dev=`echo $dev_scsi |sed -e 's|_.*||'`
		scsi=`echo $dev_scsi | sed -e 's|.*_||'`


		#Kernel 2.4
		file=`grep -l $scsi /proc/scsi/usb-storage-*/*`
		if [ -z "$file" ]; then
			continue
		fi
		a=`grep Attached $file | awk -F ':' '{print $2}'`
		attached=`echo $a | sed -e 's| ||g'`


		if [ "$attached" = "Yes" ] ; then

			vendor=`grep Vendor  $file | awk -F: '{print $2}' | sed -e 's| |_|g'`
			echo "$i $vendor $scsi $Dev"

			i=$((i+1))
		fi
	done

else

	unset mounted remove
	cleanup ( ) {
		[ -z "$mounted" ] || /bin/umount "${sysfsmtpt}"
		[ -z "$remove"  ] || /bin/rmdir "${sysfsmtpt}"
	}
	trap cleanup exit

	# prepare sysfs
	sysfsmtpt=$(/bin/mount | /bin/grep "type sysfs" |
		    /bin/sed 's|.\+ on \(.\+\) type sysfs.*|\1|');
	[[ -n "${sysfsmtpt}" ]] || {
	  sysfsmtpt=/sys
	  [[ -d "${sysfsmtpt}" ]] || { /bin/mkdir "${sysfsmtpt}"; remove=1; }
	  /bin/mount -tsysfs -onodev,noexec,nosuid sysfs "${sysfsmtpt}" >/dev/null 2>&1\
	  || exit 1
	  mounted=1
	}

	# get info
	i=0
	dir="${sysfsmtpt}/bus/usb/drivers/usb-storage"
	for s in `/bin/ls -d ${dir}/*:*/host*/target*:*:*/*:*:*:*/block:* 2>/dev/null`;
	do
	  # Nearly everything we need is encoded in this path, let's grab the pieces:
	  str=$(echo "$s" | /bin/sed -e "s|${dir}/\(.\+\):.\+/host\(.\+\)/target\2:\(.\+\):\(.\+\)/\2:\3:\4:.\+/block:\(.\+\)|\1 scsi\2 \5|")
	  token=`echo $str| awk '{ print $1 }'`
	  bus=`echo $str| awk '{ print $2 }'`
	  device=`echo $str| awk '{ print $3 }'`
	  manufact=$(/bin/cat /sys/bus/usb/devices/"${token}"/manufacturer |
		     /bin/sed -e 's| *$||' -e 's| |_|g')
	  echo $i "${manufact}" "${bus}" "${device}"
	  i=$(($i + 1))
	done

fi
