#!/bin/bash
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2021-2022 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.
export TEXTDOMAINDIR=/usr/share/plymouth/themes/ucs/
export TEXTDOMAIN="univention-bootsplash"
i=0
while ! plymouth --has-active-vt && [ $i -le 200 ]; do
	sleep "0.2"
	((i++))
done
[ "$1" = "boot" ] && plymouth update --status="univention-splash:status:$(gettext "Starting Univention Management Console Server")"
[ "$1" = "shutdown" ] && plymouth update --status="univention-splash:status:$(gettext "Stopping Univention Management Console Server")"
