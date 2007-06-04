#!/bin/sh -e
#
# Univention Client Basesystem
#  helper script: configure video and sound hardware
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

eval `univention-baseconfig shell`

echo -n "Detecting hardware:"

# select video server
test -d /ramdisk/etc/X11 || mkdir -p /ramdisk/etc/X11
if echo $x_module | grep -q '^XF86_.*'; then
	# we are using XFree86 3.3.x
	ln -fs "/usr/bin/X11/$x_module" /ramdisk/etc/X11/X
else
	# we are using XFree86 4.x
	#ln -fs /usr/bin/X11/XFree86 /ramdisk/etc/X11/X
	# we are using Xorg
	ln -fs /usr/bin/X11/Xorg /ramdisk/etc/X11/X
fi
echo -n " video"

# select sound driver
if [ "$univentionSoundEnabled" = "1" ]; then
	if [ ! -z "$univentionSoundModule" ]; then
		if [ "$univentionSoundModule" == "auto" ]; then
			if [ -e "/usr/sbin/kudzu" ]; then
				sound_module=$(/usr/sbin/kudzu -p --class=AUDIO | grep ^driver | awk '{print $2}')
				if test "$sound_module"; then
					univention-baseconfig set univentionSoundModule=$sound_module
				fi
			else
				sound_module=$univentionSoundModule
			fi
		else
			sound_module=$univentionSoundModule
		fi

		if test "$sound_module"; then
			/sbin/modprobe "$sound_module"
			echo -n " sound"
		fi
	fi

fi

echo "."
