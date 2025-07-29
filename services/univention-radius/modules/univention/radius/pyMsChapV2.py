#!/usr/bin/python3
#
# Univention RADIUS 802.1X
#  helper functions for RFC 2759
#
# SPDX-FileCopyrightText: 2012-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import passlib.crypto.des
from samba.crypto import md4_hash_blob


def md4(data):
    # type: (bytes) -> bytes
    return md4_hash_blob(data)


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
