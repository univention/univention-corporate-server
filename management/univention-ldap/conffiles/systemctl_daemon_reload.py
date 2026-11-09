#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from subprocess import call


def postinst(ucr, changes):
    call(['systemctl', 'daemon-reload'])
