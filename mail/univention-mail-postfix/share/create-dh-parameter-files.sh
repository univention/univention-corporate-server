#!/bin/sh
#
# Univention mail Postfix
#
# Copyright 2014-2019 Univention GmbH
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

# (re)create DH keys
umask 022
openssl dhparam -out /etc/postfix/dh_512.pem.tmp -2 512 && mv /etc/postfix/dh_512.pem.tmp /etc/postfix/dh_512.pem
#openssl dhparam -out /etc/postfix/dh_1024.pem.tmp -2 1024 && mv /etc/postfix/dh_1024.pem.tmp /etc/postfix/dh_1024.pem
openssl dhparam -out /etc/postfix/dh_2048.pem.tmp -2 2048 && mv /etc/postfix/dh_2048.pem.tmp /etc/postfix/dh_2048.pem
chmod 644 /etc/postfix/dh_2048.pem /etc/postfix/dh_512.pem

invoke-rc.d postfix reload || true

exit 0
