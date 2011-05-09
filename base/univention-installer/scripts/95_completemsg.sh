#!/bin/sh
#
# Univention Installer
#  reboot system
#
# Copyright 2004-2011 Univention GmbH
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

. /tmp/installation_profile

if [ -e "/tmp/installation_error.log" ] && [ -d "/instmnt/var/log/univention" ]; then
	cp /tmp/installation_error.log /instmnt/var/log/univention
	gzip /instmnt/var/log/univention/installation_error.log
fi

if [ -n "$auto_reboot" ] && [ "$auto_reboot" = "Yes" -o "$auto_reboot" = "yes" -o "$auto_reboot" = "True" -o "$auto_reboot" = "true" ]; then
	echo "Auto reboot"
else
	clear
	python2.6 /lib/univention-installer/end.py
fi
