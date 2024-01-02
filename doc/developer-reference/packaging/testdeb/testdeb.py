#!/usr/bin/python3

# SPDX-FileCopyrightText: 2021-2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Example for creating UCS packages."""

from datetime import datetime


if __name__ == "__main__":
    now = datetime.now()
    filename = "/tmp/testdeb-{:%y%m%d%H%M}".format(now)
    with open(filename, "a") as tmpfile:
        pass
