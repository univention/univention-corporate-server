#!/bin/sh
#
# Univention Installer
#  setup repository
#
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009 Univention GmbH
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
chroot /instmnt univention-config-registry commit \
					/etc/apt/sources.list.d/15_ucs-online-version.list \
					/etc/apt/sources.list.d/18_ucs-online-security.list \
					/etc/apt/sources.list.d/20_ucs-online-component.list \
					/etc/apt/mirror.list

#create an empty sources.list
if [ -e "/etc/apt/sources.list" ]; then
	mv /etc/apt/sources.list /etc/apt/sources.list.unused
	touch /etc/apt/sources.list
fi
