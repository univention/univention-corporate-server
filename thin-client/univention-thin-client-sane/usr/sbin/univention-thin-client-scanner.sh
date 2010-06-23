#!/bin/sh
#
# Univention Thin Client Scanner Support
#  add/remove desktop link for scanners
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

desktop="$HOME/Desktop/Scanner.desktop"

# add scanner script
if [ $SCANNER_ACTION = "add" ]; then
	if [ ! -f $desktop ]; then
		cat << EOF > $desktop
[Desktop Entry]
Comment=Startet das Scan-Programm Kooka
Comment[de]=Startet das Scan-Programm Kooka
Encoding=UTF-8
Exec=/usr/bin/univention-thin-client-kooka "$SCANNER_HOST"
GenericName=Scannen mit Kooka
GenericName[de]=Scannen mit Kooka
Icon=scanner
MimeType=
Name=Scanner
Name[de]=Scanner
Path=
StartupNotify=true
Terminal=false
TerminalOptions=
Type=Application
X-DCOP-ServiceType=
X-KDE-SubstituteUID=false
X-KDE-Username=
EOF
		chmod a+x $desktop
	fi
# remove scanner script
else
	if [ -f $desktop ]; then
		rm -f $desktop
	fi
fi
