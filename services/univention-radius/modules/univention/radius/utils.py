# -*- coding: utf-8 -*-
#
# Univention RADIUS
#
# Copyright (C) 2022 Univention GmbH
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


def decode_stationId(stationId):
	# type: (str) -> str
	norm = "".join(c for c in stationId.lower() if c in "0123456789abcdef")
	return ":".join(norm[i:i + 2] for i in range(0, 12, 2))


def parse_username(username):
	# type: (str) -> str
	'''convert username from host/-format to $-format if required'''
	if not username.startswith('host/'):
		return username
	username = username.split('/', 1)[1]  # remove host/
	username = username.split('.', 1)[0]  # remove right of '.'
	return username + '$'
