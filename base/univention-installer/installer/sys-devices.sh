#!/bin/bash
#
# Univention Installer
#  helper script: scanning /sys for devices
#  usage: $0 BUS TYPE
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

if [ -z "$1" -o -z "$2" ]; then
	exit 0
fi

bus=$1
type=$2
kversion=$(uname -r | awk -F '-' {'print $1'})
kmajor=$(echo $kversion | awk -F '.' {'print $2'})
kminor=$(echo $kversion | awk -F '.' {'print $3'})
devscount=0
devs=()
syslogfile=/var/log/syslogd

# return 0 if we found what we wanted
check_device () {
	local wanted=$1
	local found=$2

	if [ "$wanted" = "all" -o "$wanted" = "$found" ]; then
		return 0
	else
		return 1
	fi
}

# check sysfs for kernel 2630 and later
sysfs2630 () {
	local bus=$1
	local type=$2

	# seem that type 5 is a cdrom and type 0 is a harddisc, but further investigations
 	# are necessary
	if [ "$type" = "cdrom" ]; then
		wanted_type=5
	elif [ "$type" = "disc" ]; then
		wanted_type=0
	else
		wanted_type=all
	fi

	# usb
	if [ "$bus" = "usb" -o "$bus" = "all" ]; then
		dir="${sysfsmtpt}/bus/usb/drivers/usb-storage"
		for s in `/bin/ls -d ${dir}/*:*/host*/target*:*:*/*:*:*:*/block/* 2>/dev/null`; do
			device=$(echo $s | awk -F / {'print $NF'})
			vendor=$(cat $s/device/vendor)
			media=$(cat $s/device/type)
			if check_device "$wanted_type" "$media"; then
				devs[$devscount]="$device/$vendor/$media"
				devscount=$(($devscount + 1))
			fi
		done
	fi

	# scsi

	# ide
}

# check sysfs for kernel 2619 and later
sysfs2619 () {
	local bus=$1
	local type=$2

	# seem that type 5 is a cdrom and type 0 is a harddisc, but further investigations
 	# are necessary
	if [ "$type" = "cdrom" ]; then
		wanted_type=5
	elif [ "$type" = "disc" ]; then
		wanted_type=0
	else
		wanted_type=all
	fi

	# usb
	if [ "$bus" = "usb" -o "$bus" = "all" ]; then
		dir="${sysfsmtpt}/bus/usb/drivers/usb-storage"
		for s in `/bin/ls -d ${dir}/*:*/host*/target*:*:*/*:*:*:*/block:* 2>/dev/null`; do
			# Nearly everything we need is encoded in this path, let's grab the pieces:
			str=$(echo "$s" | /bin/sed -e "s|${dir}/\(.\+\):.\+/host\(.\+\)/target\2:\(.\+\):\(.\+\)/\2:\3:\4:.\+/block:\(.\+\)|\1 scsi\2 \5|")
			token=`echo $str| awk '{ print $1 }'`
			bus=`echo $str| awk '{ print $2 }'`
			device=`echo $str| awk '{ print $3 }'`
			manufact=$(/bin/cat /sys/bus/usb/devices/"${token}"/manufacturer | /bin/sed -e 's| *$||' -e 's| |_|g')
			dev=${device:0:2}
			media=$(cat $s/device/type)
			if check_device "$wanted_type" "$media"; then
				devs[$devscount]="$device/$manufact/$bus"
				devscount=$(($devscount + 1))
			fi
		done
	fi

	# scsi

	# ide
}


# unset mounted remove
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

# check devices

# >= 2.6.30
if [ "$kmajor" -ge 6 -a "$kminor" -ge 30 ]; then
	sysfs2630 $bus $type
# >= 2.6.19
elif [ "$kmajor" -ge 6 -a "$kminor" -ge 19 ]; then
	sysfs2619 $bus $type
fi

# print devices
i=0
for dev in "${devs[@]}"; do
	echo "${i}/${dev}"
	i=$(($i + 1))
done

exit 0
