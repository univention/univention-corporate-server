#!/usr/bin/python3

# SPDX-FileCopyrightText: 2021-2023 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Example for creating UCS packages."""

from datetime import datetime


if __name__ == "__main__":
    now = datetime.now()
    filename = f"/tmp/testdeb-{now:%y%m%d%H%M}"
    with open(filename, "a") as tmpfile:
        pass
