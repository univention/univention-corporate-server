#!/bin/sh
#
# Univention Installer
#  create sources.list
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

mkdir -p /instmnt/etc/apt/
mkdir -p /instmnt/sourcedevice
## check for repository structure
# old repository (DVD)
if [ -d /mnt/packages ]; then
	cat >/instmnt/etc/apt/sources.list <<__EOT__
#UCS Installation

deb file:/sourcedevice/packages ./

__EOT__
else
    version=`cat /mnt/.univention_install | grep VERSION | sed -e 's|VERSION=||'`

    repo_dir="file:/sourcedevice/mirror/${version}/maintained/ ${version}-0"
	cat >/instmnt/etc/apt/sources.list <<__EOT__
#UCS Installation

deb $repo_dir/all/
__EOT__
	for arch in i386 amd64 extern; do
		if [ -d "/mnt/mirror/${version}/maintained/${version}-0/$arch" ]; then
			echo "deb $repo_dir/$arch/" >> /instmnt/etc/apt/sources.list
		fi
	done
fi

chmod 644 /instmnt/etc/apt/sources.list
rm -Rf /instmnt/etc/apt/sources.list.d

# umount the source device (mounted in 10_debootstrap.sh)
umount /mnt
