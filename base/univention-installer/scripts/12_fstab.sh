#!/bin/sh
#
# Univention Installer
#  create fstab
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

getUUID () {

	local device="$1"
	uuid="$(blkid -s UUID -o value "$device")"
	if [ -n "$uuid" ]; then
		echo "UUID=$uuid"
	fi
}

# update progress message
. /tmp/progress.lib
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Configuring basesystem")" >&9

architecture=`/bin/uname -m`

cat >/instmnt/etc/fstab <<__EOT__
# /etc/fstab: static file system information.
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
__EOT__

# root device
root_device=`python2.6 /sbin/univention-config-registry get installer/device/0/name`
root_fs=`python2.6 /sbin/univention-config-registry get installer/device/0/fs`
if [ "$root_fs" = "xfs" ]; then
	options="defaults"
else
	if [ "$root_fs" = "ext3" -o "$root_fs" = "ext4" -o "$root_fs" = "ext2" ]; then
		options="acl,errors=remount-ro"
	else
		options="errors=remount-ro"
	fi
fi

# convert root device to uuid if possible
uuid="$(getUUID "$root_device")"
if [ -n "$uuid" ]; then
	root_device="$uuid"
fi

cat >>/instmnt/etc/fstab <<__EOT__
$root_device	/	$root_fs	$options	0	1
proc		/proc		proc	defaults	0	0
__EOT__

eval `python2.6 /sbin/univention-config-registry shell`

set | egrep -v "installer_device_0_mp=/" | egrep "installer_device_.*name=" | while read line; do
	device_number=`echo $line | awk -F _ '{print $3}'`
	device=`python2.6 /sbin/univention-config-registry get installer/device/$device_number/name`
	mp=`python2.6 /sbin/univention-config-registry get installer/device/$device_number/mp`
	fs=`python2.6 /sbin/univention-config-registry get installer/device/$device_number/fs`

	if [ -z "$device" ] || [ -z "$fs" ]; then
		continue
	fi

	# convert root device to uuid if possible
	uuid="$(getUUID "$device")"
	if [ -n "$uuid" ]; then
		device="$uuid"
	fi

	if [ "$fs" = "linux-swap" ]; then
cat >>/instmnt/etc/fstab <<__EOT__
$device  none 	swap	sw 0	0
__EOT__
	fi
	if [ "$fs" = "ext3" -o "$fs" = "ext4" -o "$fs" = "ext2" ]; then
		acl=",acl"
	else
		acl=""
	fi

	if [ -z "$mp" -o "$mp" = "None" -o "$mp" = "none" -o "$mp" = "/" ]; then
		continue
	fi

	if [ -z "$fs" -o "$fs" = "None" -o "$fs" = "none" ]; then
		continue
	fi

	cat >>/instmnt/etc/fstab <<__EOT__
$device  $mp 	$fs	defaults$acl	0	0
__EOT__
done

for i in /proc/ide/ide*; do
	for j in $i/hd*; do
		if [ -e "$j/media" ]; then
			a=`cat $j/media| grep -i cdrom`
			if ! test -z "$a"; then
				CDROM_DEVICES="$CDROM_DEVICES `echo $j | cut -d/ -f5`"
			fi
		fi
	done
done

j=""
if [ ! -z "$CDROM_DEVICES" ]; then
	for i in $CDROM_DEVICES; do
		cat >>/instmnt/etc/fstab <<__EOT__
/dev/cdrom$j    /cdrom$j     auto    user,noauto,exec             0       0
__EOT__
		mkdir /instmnt/cdrom$j
		if [ -z $j ]; then j=1; else j=$(($j+1)); fi
	done
elif [ "$architecture" = "powerpc" -o "$architecture" = "ppc64" ]; then
	cat >>/instmnt/etc/fstab <<__EOT__
/dev/iseries/vcda  /cdrom     auto    user,noauto,exec            0       0
__EOT__
	mkdir -p /instmnt/cdrom
# xen
elif [ -d "/proc/xen" ]; then
        . /tmp/installation_profile
        cat >>/instmnt/etc/fstab <<__EOT__
$cdrom_device  /cdrom     auto    user,noauto,exec            0       0
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
