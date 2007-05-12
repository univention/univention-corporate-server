#!/bin/sh
#
# Univention Installer
#  copies installer scripts
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

if [ -n "$cdrom_device" ]; then
	nfs=`echo $cdrom_device | grep "nfs:"`
	smbfs=`echo $cdrom_device | grep "smbfs:"`
	if [ -n "$nfs" ]; then
		mount -t nfs `echo $cdrom_device | sed -e 's|nfs:||'` /mnt
	elif [ -n "$smbfs" ]; then
		mount -t smbfs `echo $cdrom_device | sed -e 's|smbfs:||'` /mnt
	else
		mount $cdrom_device /mnt
	fi
fi

if [ -d /mnt/script/installer ]; then
	cp /mnt/script/installer/* /lib/univention-installer-scripts.d/
	chmod +x /lib/univention-installer-scripts.d/*
fi

umount /mnt
