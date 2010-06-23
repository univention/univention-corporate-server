#!/bin/sh
#
# Univention Thin Client VNC support
#  postinst script for the debian package
#
# Copyright 2007-2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

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
