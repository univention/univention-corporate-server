#!/bin/bash -e
#
# Univention Client Devices
#  imports local devices of a thin client
#
# Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

DEVICES="cdrom:/dev/hda:iso9660:ro:L floppy:/dev/fd0:vfat:rw:K"
MNT_ROOT="/var/lib/univention-client-devices"
ACTION=$1
USER=$2
CLIENT=${3/.*/}
export USER PASSWD
HOME=`getent passwd $USER | awk 'BEGIN { FS=":" }{ print $6 }'`;

cleanup() {
	true
}

setup() {
	true
}

cleanup_device() {
	local name=$1
	local device=$2
	local filesystem=$3
	local mode=$4
	local options=$5
	local drive=$6

	if [ -L "$HOME/$name" ]; then
		rm -f "$HOME/$name"
	fi
	umount -l "$MNT_ROOT/$CLIENT/$name"
	rmdir "$MNT_ROOT/$CLIENT/$name"
}

setup_device() {
	local name=$1
	local device=$2
	local filesystem=$3
	local mode=$4
	local options=$5
	local drive=$6

	mkdir -p "$MNT_ROOT/$CLIENT/$name" 2>/dev/null || true
	mount -t smbfs -o username=$USER,uid=`id -u $USER`,gid=`id -g $USER`,dmask=0700,fmask=0600,rw \
		//$CLIENT/$name "$MNT_ROOT/$CLIENT/$name"

	if [ -L "$HOME/$name" ]; then
		rm -f "$HOME/$name"
	fi
	if ! [ -e "$HOME/$name" ]; then
		ln -s "$MNT_ROOT/$CLIENT/$name" "$HOME/$name"
	fi

}

if [ "$ACTION" = "start" ]; then
	cleanup
	setup
elif [ "$ACTION" = "stop" ]; then
	cleanup
fi

options="uid=`id -u $SUDO_USER`,gid=`id -g $SUDO_USER`"
for DEVICE in $DEVICES; do
	IFS=":"
	set $DEVICE
	name=$1
	device=$2
	filesystem=$3
	mode=$4
	drive=$5

	if [ "$ACTION" = "start" ]; then
		setup_device $name $device $filesystem $mode $options $drive || true
	elif [ "$ACTION" = "stop" ]; then
		cleanup_device $name $device $filesystem $mode $options $drive || true
	fi
done
