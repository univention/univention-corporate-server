#
# Univention RADIUS
#
# SPDX-FileCopyrightText: 2022-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


def decode_stationId(stationId: str) -> str:
    norm = "".join(c for c in stationId.lower() if c in "0123456789abcdef")
    return ":".join(norm[i:i + 2] for i in range(0, 12, 2))


def parse_username(username: str) -> str:
    """convert username from host/-format to $-format if required"""
    if not username.startswith('host/'):
        return username
    username = username.split('/', 1)[1]  # remove host/
    username = username.split('.', 1)[0]  # remove right of '.'
    return username + '$'
