#!/bin/sh
#
# Univention Installer
#  helper script: scanning for USB mass storage devices
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
	sysfsmtpt=/sys
	if ! grep -q sysfs /proc/mounts; then
		if [ ! -d "${sysfsmtpt}" ]; then
			/bin/mkdir "${sysfsmtpt}"
		fi
		/bin/mount -tsysfs -onodev,noexec,nosuid sysfs "${sysfsmtpt}" >/dev/null 2>&1 || exit 1
	fi

	# this works for kernel < 2.6.30
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
		for sub in `/bin/ls -d ${dir}/*:*/host*/target*:*:*/*:*:*:*/block:${device}/${device}* 2>/dev/null`; do
			# Nearly everything we need is encoded in this path, let's grab the pieces:
			str=$(echo "$sub" | /bin/sed -e "s|${dir}/\(.\+\):.\+/host\(.\+\)/target\2:\(.\+\):\(.\+\)/\2:\3:\4:.\+/block:\(.\+\)|\1 scsi\2 \5|")
			token_sub=`echo $str| awk '{ print $1 }'`
			bus_sub=`echo $str| awk '{ print $2 }'`
			device_sub=`echo $str| awk '{ print $3 }' | sed -e 's|.*/||'`
			manufact_sub=$(/bin/cat /sys/bus/usb/devices/"${token}"/manufacturer |
				/bin/sed -e 's| *$||' -e 's| |_|g')
			echo $i "${manufact_sub}" "${bus_sub}" "${device_sub}"
			i=$(($i + 1))
		done
		echo $i "${manufact}" "${bus}" "${device}"
		i=$(($i + 1))
	done

	# this is for kernel >= 2.6.30
	i=0
	dir="${sysfsmtpt}/bus/usb/drivers/usb-storage"
	for s in `/bin/ls -d ${dir}/*:*/host*/target*:*:*/*:*:*:*/block/* 2>/dev/null`; do
		device=$(echo $s | awk -F / '{ print $NF }' | /bin/sed -e 's| *$||' -e 's| |_|g')
		vendor=$(cat $s/device/vendor | /bin/sed -e 's| *$||' -e 's| |_|g')
		media=$(cat $s/device/type | /bin/sed -e 's| *$||' -e 's| |_|g')
		for sub in `/bin/ls -d ${dir}/*:*/host*/target*:*:*/*:*:*:*/block/${device}/${device}* 2>/dev/null`; do
			device_sub=$(echo $sub | awk -F / '{ print $NF }' | /bin/sed -e 's| *$||' -e 's| |_|g')
			vendor_sub=$(cat $s/device/vendor | /bin/sed -e 's| *$||' -e 's| |_|g')
			media_sub=$(cat $s/device/type | /bin/sed -e 's| *$||' -e 's| |_|g')
			echo $i "$vendor_sub" "$media_sub" "$device_sub"
			i=$(($i + 1))
		done
		echo $i "$vendor" "$media" "$device"
		i=$(($i + 1))
	done
fi
