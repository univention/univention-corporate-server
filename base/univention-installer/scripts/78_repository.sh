#!/bin/sh
#
# Univention Installer
#  setup repository
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

if [ -n "$system_role" ]; then
	export server_role="$system_role"
fi

if [ -n "$local_repository" ] && [ "$local_repository" = "true" -o "$local_repository" = "yes" ]; then
	# call univention-repository-create in non-interactive mode with the /sourcedevice directory as installation medium (-N mount is not required)
	chroot /instmnt /usr/sbin/univention-repository-create -n -N -m /sourcedevice
fi

# create sources.list
chroot /instmnt univention-config-registry set repository/online=yes repository/mirror?yes

# create an empty sources.list
if [ -e "/instmnt/etc/apt/sources.list" ]; then
	echo "# This file is not maintained via Univention Configuration Registry
# and can be used to add further package repositories manually
" > /instmnt/etc/apt/sources.list
fi

# update package lists
chroot /instmnt apt-get update
