#!/bin/sh
#
# Univention Installer
#  create device configuration
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
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Preparing target device")" >&9

. /tmp/installation_profile

architecture=`/bin/uname -m`

get_device_disk ()
{
	partition_name=$( echo $1 | sed -e 's|dev_||' | sed -e 's|_|/|g')

	echo "$partition_name" | egrep ".*hd[a-z]([0-9]*)$" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*hd[a-z]*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*sd[a-z]([0-9]*)$" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*sd[a-z]*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*md([0-9]*)$" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*md*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*xd[a-z]([0-9]*)$" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*xd[a-z]*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*ad[a-z]([0-9]*)$" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*ad[a-z]*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*ed[a-z]([0-9]*)$" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*ed[a-z]*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*pd[a-z]([0-9]*)$" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*pd[a-z]*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*pf[a-z]([0-9]*)$" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*pf[a-z]*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*vd[a-z]([0-9]*)$" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*vd[a-z]*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*dasd[a-z]([0-9]*)$" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*dasd[a-z]*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*dpti[a-z]([0-9]*)" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*dpti[0-9]*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*c[0-9]d[0-9]*" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*c[0-9]*d[0-9]*\)\(.*\)/\1/p'
	fi

	echo "$partition_name" | egrep ".*ar[0-9]*" >/dev/null 2>&1
	if [ $? = 0 ]; then
		echo "$partition_name" | sed -ne 's/\(.*ar[0-9]*\)\(.*\)/\1/p'
	fi
}

if [ "$architecture" = "powerpc" -o "$architecture" = "ppc64" ]; then
	mkdir -p /dev/iseries
	mknod /dev/iseries/vcda b 113 0
	mknod /dev/iseries/vda b 112 0
	mknod /dev/iseries/vdb b 112 8
	mknod /dev/iseries/vdc b 112 16

	for i in 1 2 3 4 5 6 7; do
		mknod /dev/iseries/vda$i b 112 $i
	done

	for i in 9 10 11 12 13 14 15; do
		mknod /dev/iseries/vdb$((i-8)) b 112 $i
	done

	for i in 17 18 19 20 21 22 23; do
		mknod /dev/iseries/vdc$((i-16)) b 112 $i
	done
fi

# reactivate all volume groups
vgchange -ay

count=1
echo "Creating disks"
set | egrep "^dev_" | while read line; do
	name=`echo $line | sed -e 's|=.*||'`
	var=`echo $line | sed -e 's|.*=.||;s|"||g' | sed -e "s|'||g"`
	if [ "$name" = "devices" ]; then
		continue
	fi

	# dev_%d = "parttype device type format fstype start end mpoint"
	device_num=`echo $var | awk '{print $2}'`
	device_type=`echo $var | awk '{print $3}'`
 	device_format=`echo $var | awk '{print $4}'`
	device_fs=`echo $var | awk '{print $5}'`
	device_start=`echo $var | awk '{print $6}'`
	device_end=`echo $var | awk '{print $7}'`
	device_mp=`echo $var | awk '{print $8}'`

	echo "device_type=$device_type"
	echo "device_format=$device_format"
	echo "device_fs=$device_fs"
	echo "device_start=$device_start"
	echo "device_end=$device_end"
	echo "device_mp=$device_mp"

	if [ "$device_fs" = "EFI" ] ; then
		device_fs="vfat"
	fi

	if [ "$device_mp" = '/' ]; then
		python2.6 /sbin/univention-config-registry set installer/device/0/name?$device_num
		python2.6 /sbin/univention-config-registry set installer/device/0/fs?$device_fs
		python2.6 /sbin/univention-config-registry set installer/device/0/mp?$device_mp
	else
		python2.6 /sbin/univention-config-registry set installer/device/$count/name?$device_num
		python2.6 /sbin/univention-config-registry set installer/device/$count/fs?$device_fs
		python2.6 /sbin/univention-config-registry set installer/device/$count/mp?$device_mp
		count=$((count+1))
	fi
done
echo "Done"

# mount root filesystem
fs=$(python2.6 /sbin/univention-config-registry get installer/device/0/fs)
dev=$(python2.6 /sbin/univention-config-registry get installer/device/0/name)
msg=$(/bin/mount -t "$fs" "$dev" /instmnt 2>&1)

# error message if root could not be mounted
if [ 0 -ne "$?" ]; then
	echo "could not mount root in $0" >> /tmp/installation_error.log
	echo $msg >> /tmp/installation_error.log
fi

touch /instmnt/.log

# get bootloader_record via /proc/cmdline and overwrite value of profile/installer
kernel_bootloader_record="$(sed -rne 's/.*\bbootloaderrecord=([^ ]+)\s*.*/\1/p' /proc/cmdline)"
if [ -n "$kernel_bootloader_record" ] ; then
	bootloader_record="$kernel_bootloader_record"
fi

# get bootloader_record via /proc/partitions
if [ -z "$bootloader_record" ] ; then
	partitions_device="$(egrep -r '^\s*[0-9]+\s+' /proc/partitions | head -n1 | awk '{ print $NF }')"
	[ -n "$partitions_device" ] && bootloader_record="/dev/$partitions_device"
fi

if [ -n "$bootloader_record" ]; then
	python2.6 /sbin/univention-config-registry set "grub/boot?$bootloader_record"
else
	echo
	echo "ERROR: bootloader_record has not been set!"
	echo
	echo
	sleep 15s
fi
