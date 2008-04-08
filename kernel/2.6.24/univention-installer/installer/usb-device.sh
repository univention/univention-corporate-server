#!/bin/sh
#
# Univention Installer
#  helper script: scanning for USB mass storage devices
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

count=0
#Kernel 2.4

#Kernel 2.6
#str=`dmesg | grep -A4 "USB Mass Storage" | grep ": SCSI emulation for USB Mass Storage device" | sed -e 's| .*||'`

if [ "$1" = "2.4" ]; then
	str=`cat /var/log/syslogd | grep -A5 "USB Mass Storage" | sed -e 's|.* kernel: ||' | grep Attached |\
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
	str=`cat /var/log/syslogd | grep -A5 "USB Mass Storage" | sed -e 's|.* kernel: ||' | grep [": SCSI emulation for USB Mass Storage device","SCSI device "]| sed -e 's|SCSI device ||' | sed -e 's| .*||' | grep [a-z] | grep -v "usb-storage" | grep -v ": new " | grep -v Initializing | grep -v usbcore | sed -e 's|:||g'`
	i=0

	for d in $str; do
		if [ -z "$scsi" ]; then
			scsi=$d
			continue
		fi

		file=`grep -l "$scsi" /proc/scsi/usb-storage/* `
		if [ -n "$file" ]; then
			vendor=`grep "Vendor:" $file | awk -F ':' '{print $2}'|  sed -e 's|^ *||g;s| |_|g' `
			echo "$i $vendor $scsi $d"
			i=$((i+1))
		fi
		scsi=''
	done


fi
