#!/bin/sh
#
# Univention Installer
#  run preinst hook script
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

. /tmp/installation_profile

for i in $preinst_hook; do
	if [ -e "/instmnt/sourcedevice/script/$i" ]; then
		mkdir -p /instmnt/etc/univention/preinst
		cp "/instmnt/sourcedevice/script/$i" /instmnt/etc/univention/preinst/
		chmod 700 "/instmnt/etc/univention/preinst/$i"
		chroot /instmnt /etc/univention/preinst/$i
	fi
done
