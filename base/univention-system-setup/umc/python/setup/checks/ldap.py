#!/usr/bin/python3
#
# Univention Management Console
#  module: system setup
#
# SPDX-FileCopyrightText: 2018-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


from shlex import quote
from subprocess import PIPE, Popen

from ldap.filter import filter_format

from univention.management.console.log import MODULE
from univention.management.console.modules.setup.util import _temporary_password_file


def check_if_uid_is_available(uid: str, role: str, address: str, username: str, password: str) -> bool:
    """
    check if either the UID it not yet taken at all
    or it is already taken (by our previous self) and still matches the server role
    """
    filter_s = filter_format("(&(objectClass=person)(uid=%s)(!(univentionServerRole=%s)))", [uid, role])
    rcmd = 'univention-ldapsearch -LLL %s 1.1' % (quote(filter_s),)
    with _temporary_password_file(password) as password_file:
        cmd = [
            "univention-ssh", "--no-split",
            password_file,
            '%s@%s' % (username, address),
            rcmd,
        ]
        MODULE.info("Running %s", " ".join(quote(arg) for arg in cmd))
        process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        if process.wait() or stderr:
            MODULE.error("Failed checking uid=%s role=%s: %r", uid, role, stderr)
    return not stdout.strip()
