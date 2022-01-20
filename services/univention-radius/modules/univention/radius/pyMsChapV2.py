#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention RADIUS 802.1X
#  helper functions for RFC 2759
#
# Copyright (C) 2012-2021 Univention GmbH
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

import hashlib
import passlib.crypto.des


def md4(data):
	# type: (bytes) -> bytes
	md = hashlib.new('md4')
	md.update(data)
	return md.digest()


def DesEncrypt(data, key):
	# type: (bytes, bytes) -> bytes
	return passlib.crypto.des.des_encrypt_block(key, data)


def HashNtPasswordHash(passwordhash):
	# type: (bytes) -> bytes
	return md4(passwordhash)


def ChallengeResponse(challenge, passwordhash):
	# type: (bytes, bytes) -> bytes
	z_password_hash = passwordhash.ljust(21, b'\0')
	response = DesEncrypt(challenge, z_password_hash[0:7])
	response += DesEncrypt(challenge, z_password_hash[7:14])
	response += DesEncrypt(challenge, z_password_hash[14:21])
	return response
