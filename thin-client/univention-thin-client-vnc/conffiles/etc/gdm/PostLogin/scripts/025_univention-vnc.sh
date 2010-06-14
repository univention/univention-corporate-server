#!/bin/sh
#
# Univention Thin Client VNC support
#  postinst script for the debian package
#
# Copyright (C) 2007-2010 Univention GmbH
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

eval $(univention-baseconfig shell xorg/vnc/exporttype xorg/vnc/viewonly)

if [ -n "$xorg_vnc_exporttype" -a "$xorg_vnc_exporttype" = "1" ]; then

	# view only
	if [ -n "$xorg_vnc_viewonly" -a "$xorg_vnc_viewonly" = "1" ]; then
		viewonly="-viewonly"
	else
		viewonly=""
	fi

	# create vnc password
	passwdfile="$HOME/.ucs-tc-vnc-password.txt"
	passwd=$$
	POS=2 
	LEN=8
	passwd=$(echo "$passwd" | md5sum | md5sum)
	randpw="${passwd:$POS:$LEN}"
	echo $randpw > "$passwdfile"

	# start x11vnc
	killall -9 x11vnc
	x11vnc -desktop :0 -shared -auth "/var/lib/gdm/:0.Xauth" \
		-o /tmp/x11vnc.log -noxdamage -bg $viewonly \
		-accept "yes:0,no:*,view:3 univention-vnc-session-confirm $passwdfile" \
		-forever -passwdfile "$passwdfile" -afteraccept "killall xmessage"
fi

exit 0
