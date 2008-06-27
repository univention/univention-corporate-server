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

# start sound server (default: esd)
if [ -n "$thinclient/sound/daemon" -a $thinclient_sound_daemon = "arts" ]; then
	if test -e "/usr/bin/artswrapper" -a -e "/dev/dsp"; then
		#be sure the directory exists, otherwise the artsd on the thinclient isn't able to start
		mkdir -p "/tmp/ksocket-${USERNAME}"
		/usr/bin/artswrapper -n -F 5 -S 8192 -u -p 1601 &
	fi
else
	if test -e "/usr/bin/esd" -a -e "/dev/dsp"; then
		/usr/bin/esd -tcp -public -nobeeps &
		echo "setenv ESPEAKER $HOSTNAME.$(dnsdomainname)" >> ~/.univention-thin-client-session
	fi
fi
