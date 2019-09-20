#!/bin/bash
#
# Univention KDE
#  create 1M file in home dir. if an error occurs, home is nearly full
#  (quota) and user will be warned.
#
# Copyright (C) 2004-2019 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of the software contained in this package
# as well as the source package itself are made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
# 
# Binary versions of this package provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
# 
# In the case you use the software under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

dd if=/dev/zero of=$HOME/.kde/.spacesaver bs=10k count=25 >/dev/null 2>&1 || {
    case $LANG in
		de*)
			echo -e 'Der ihrem Benutzerkonto zugewiesene Speicherplatz wird knapp.\nSie sollten nicht benÃ¶tigte Dateien lÃ¶schen oder den Systemverwalter\num eine ErhÃ¶hung der Speicherplatzquote bitten.' \
				| xmessage -center -file -
			;;
		*)
			echo -e 'Your account is running out of disk space.\n You should delete some unused files or ask your administrator\nfor quota increasement.' \
				| xmessage -geometry -file -
			;;
    esac
}
