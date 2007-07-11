#!/bin/sh
#
# Univention Installer
#  create device configuration
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

architecture=`/bin/uname -m`

# Usage: resolve_symlink file
# Find the real file/device that file points at
resolve_symlink () {
	tmp_fname=$1
	# Resolve symlinks
	while test -L $tmp_fname; do
		tmp_new_fname=`ls -al $tmp_fname | sed -n 's%.*-> \(.*\)%\1%p'`
		if test -z "$tmp_new_fname"; then
			echo "Unrecognized ls output" 2>&1
			exit 1
		fi

		# Convert relative symlinks
		case $tmp_new_fname in
			/*) tmp_fname="$tmp_new_fname"
			;;
			*) tmp_fname="`echo $tmp_fname | sed 's%/[^/]*$%%'`/$tmp_new_fname"
			;;
		esac
	done
	echo "$tmp_fname"
}

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

	if [ "`echo $var | awk '{print $1}'`" = "LVM" ] ; then
		device_num=`resolve_symlink $device_num`
	fi

	echo "device_type=$device_type"
	echo "device_format=$device_format"
	echo "device_fs=$device_fs"
	echo "device_start=$device_start"
	echo "device_end=$device_end"
	echo "device_mp=$device_mp"

	if [ "$device_mp" = '/' ]; then
		mount -t $device_fs $device_num /instmnt $LOG
		touch /instmnt/.log
		python2.4 /sbin/univention-config-registry set installer/device/0/name=$device_num
		python2.4 /sbin/univention-config-registry set installer/device/0/fs=$device_fs
		python2.4 /sbin/univention-config-registry set installer/device/0/mp=$device_mp
	else
		python2.4 /sbin/univention-config-registry set installer/device/$count/name=$device_num
		python2.4 /sbin/univention-config-registry set installer/device/$count/fs=$device_fs
		python2.4 /sbin/univention-config-registry set installer/device/$count/mp=$device_mp
		count=$((count+1))
	fi
done
echo "Done"

if [ -n "$bootloader_record" ]; then
	python2.4 /sbin/univention-config-registry set grub/boot=$bootloader_record
else
	python2.4 /sbin/univention-config-registry set grub/boot=$grub_boot_fallback
fi
