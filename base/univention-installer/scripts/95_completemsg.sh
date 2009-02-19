#!/bin/sh
#
# Univention Installer
#  reboot system
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

if [ -e "/tmp/installation_error.log" ] && [ -d "/instmnt/var/log/univention" ]; then
	cp /tmp/installation_error.log /instmnt/var/log/univention
fi

if [ -n "$auto_reboot" ] && [ "$auto_reboot" = "Yes" -o "$auto_reboot" = "yes" -o "$auto_reboot" = "True" -o "$auto_reboot" = "true" ]; then
	echo "Auto reboot"
else
	clear
	python /lib/univention-installer/end.py
fi
