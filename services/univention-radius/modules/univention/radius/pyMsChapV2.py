#!/usr/bin/python3
#
# Univention RADIUS 802.1X
#  helper functions for RFC 2759
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2012-2023 Univention GmbH
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

import struct

import passlib.crypto.des
import passlib.hash


def DesEncrypt(data, key):
    # type: (bytes, bytes) -> bytes
    return passlib.crypto.des.des_encrypt_block(key, data)


def HashNtPasswordHash(passwordhash):
    # type: (bytes) -> bytes
    md = MD4()
    md.add(passwordhash)
    return md.finish()


def ChallengeResponse(challenge, passwordhash):
    # type: (bytes, bytes) -> bytes
    z_password_hash = passwordhash.ljust(21, b'\0')
    response = DesEncrypt(challenge, z_password_hash[0:7])
    response += DesEncrypt(challenge, z_password_hash[7:14])
    response += DesEncrypt(challenge, z_password_hash[14:21])
    return response


def leftrotate(i, n):
    return ((i << n) & 0xffffffff) | (i >> (32 - n))


def F(x, y, z):
    return (x & y) | (~x & z)


def G(x, y, z):
    return (x & y) | (x & z) | (y & z)


def H(x, y, z):
    return x ^ y ^ z


class MD4:
    def __init__(self, data=b''):
        self.remainder = data
        self.count = 0
        self.h = [
            0x67452301,
            0xefcdab89,
            0x98badcfe,
            0x10325476,
        ]

    def _add_chunk(self, chunk):
        self.count += 1
        X = list(struct.unpack("<16I", chunk) + (None,) * (80 - 16))
        h = list(self.h)
        # Round 1
        s = (3, 7, 11, 19)
        for r in range(16):
            i = (16 - r) % 4
            k = r
            h[i] = leftrotate((h[i] + F(h[(i + 1) % 4], h[(i + 2) % 4], h[(i + 3) % 4]) + X[k]) % 2**32, s[r % 4])
        # Round 2
        s = (3, 5, 9, 13)
        for r in range(16):
            i = (16 - r) % 4
            k = 4 * (r % 4) + r // 4
            h[i] = leftrotate((h[i] + G(h[(i + 1) % 4], h[(i + 2) % 4], h[(i + 3) % 4]) + X[k] + 0x5a827999) % 2**32, s[r % 4])
        # Round 3
        s = (3, 9, 11, 15)
        k = (0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15)  # wish I could function
        for r in range(16):
            i = (16 - r) % 4
            h[i] = leftrotate((h[i] + H(h[(i + 1) % 4], h[(i + 2) % 4], h[(i + 3) % 4]) + X[k[r]] + 0x6ed9eba1) % 2**32, s[r % 4])

        for i, v in enumerate(h):
            self.h[i] = (v + self.h[i]) % 2**32

    def add(self, data):
        message = self.remainder + data
        r = len(message) % 64
        if r != 0:
            self.remainder = message[-r:]
        else:
            self.remainder = b''
        for chunk in range(0, len(message) - r, 64):
            self._add_chunk(message[chunk:chunk + 64])
        return self

    def finish(self):
        ll = len(self.remainder) + 64 * self.count
        self.add(b'\x80' + b'\x00' * ((55 - ll) % 64) + struct.pack("<Q", ll * 8))
        out = struct.pack("<4I", *self.h)
        self.__init__()
        return out
