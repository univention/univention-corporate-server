#!/bin/sh
#
# Univention Installer
#  create fstab
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

architecture=`/bin/uname -m`

cat >/instmnt/etc/fstab <<__EOT__
# /etc/fstab: static file system information.
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
__EOT__

#ROOT Device
root_device=`python2.4 /sbin/univention-config-registry get installer/device/0/name`
root_fs=`python2.4 /sbin/univention-config-registry get installer/device/0/fs`
if [ "$root_fs" = "xfs" ]; then
	options="defaults"
else
	if [ "$root_fs" = "ext3" ]; then
		options="acl,errors=remount-ro"
	else
		options="errors=remount-ro"
	fi
fi

cat >>/instmnt/etc/fstab <<__EOT__
$root_device	/	$root_fs	$options	0	1
proc		/proc		proc	defaults	0	0
__EOT__


eval `python2.4 /sbin/univention-config-registry shell`

set | egrep -v "installer_device_0_mp=/" | egrep "installer_device_.*name=" | while read line; do
	device_number=`echo $line | awk -F _ '{print $3}'`
	device=`python2.4 /sbin/univention-config-registry get installer/device/$device_number/name`
	mp=`python2.4 /sbin/univention-config-registry get installer/device/$device_number/mp`
	fs=`python2.4 /sbin/univention-config-registry get installer/device/$device_number/fs`

	if [ -z "$device" ] || [ -z "$fs" ]; then
		continue
	fi

	if [ "$fs" = "linux-swap" ]; then
cat >>/instmnt/etc/fstab <<__EOT__
$device  none 	swap	sw 0	0
__EOT__
	fi
	if [ "$fs" = "ext3" ]; then
		acl=",acl"
	else
		acl=""
	fi

	if [ -z "$mp" ]; then
		continue
	fi

	if [ "$mp" = "None" ] || [ "$mp" = "/" ]; then
		continue
	fi

cat >>/instmnt/etc/fstab <<__EOT__
$device  $mp 	$fs	defaults$acl	0	0
__EOT__

done


for i in /proc/ide/ide*; do
	for j in $i/hd*; do
		a=`cat $j/media| grep -i cdrom`
		if ! test -z "$a"; then
			CDROM_DEVICES="$CDROM_DEVICES `echo $j | cut -d/ -f5`"
		fi
	done
done

j=""
if [ ! -z "$CDROM_DEVICES" ]; then
	for i in $CDROM_DEVICES; do
		cat >>/instmnt/etc/fstab <<__EOT__
/dev/$i  /cdrom$j     auto    user,noauto,exec             0       0
__EOT__
		mkdir /instmnt/cdrom$j
		if [ -z $j ]; then j=1; else j=$(($j+1)); fi
	done
elif [ "$architecture" = "powerpc" -o "$architecture" = "ppc64" ]; then
	cat >>/instmnt/etc/fstab <<__EOT__
/dev/iseries/vcda  /cdrom     auto    user,noauto,exec            0       0
__EOT__
	mkdir -p /instmnt/cdrom
else
	cat >>/instmnt/etc/fstab <<__EOT__
/dev/sr0  /cdrom     auto    user,noauto,exec            0       0
__EOT__
	mkdir -p /instmnt/cdrom
fi

cat >>/instmnt/etc/fstab <<__EOT__
/dev/fd0  /floppy     vfat    user,noauto,exec            0       0
__EOT__
mkdir /instmnt/floppy
