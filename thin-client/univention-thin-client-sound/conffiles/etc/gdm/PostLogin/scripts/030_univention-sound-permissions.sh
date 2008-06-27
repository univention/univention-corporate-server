#!/bin/sh -e
#
# Univention Thin Client Sound support
#  postinst script for the debian package
#
# Copyright (C) 2007 Univention GmbH
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

eval $(univention-baseconfig shell univentionSoundEnabled thinclient/sound/daemon)

if [ -z "$univentionSoundEnabled" -o $univentionSoundEnabled = "0" ]; then
	exit 0
fi

# current user should be owner of sound device
univention-baseconfig set udev/sound/owner=$USER

# tell udev to update devices of sound subsystems
udevcontrol reload_rules
udevtrigger --subsystem-match=sound
