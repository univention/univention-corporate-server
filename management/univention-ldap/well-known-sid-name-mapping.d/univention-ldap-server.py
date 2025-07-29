#!/usr/bin/python3
#
# Univention LDAP
#  restart the slapd server after well-known-sid-name-mapping made UCR changes
#
# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess

import univention.debug as ud


relevant_names = ('Administrator', 'Domain Admins', 'Windows Hosts')


def postrun(modified_default_names=None):
    if not isinstance(modified_default_names, list):
        return

    slapd_restart = False
    for name in modified_default_names:
        if name in relevant_names:
            slapd_restart = True
            break

    if slapd_restart:
        p1 = subprocess.Popen(['invoke-rc.d', 'slapd', 'graceful-restart'], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (stdout, _stderr) = p1.communicate()
        if stdout:
            ud.debug(ud.LISTENER, ud.ERROR, "%s: postrun: %s" % ('well-known-sid-name-mapping.d/univention-ldap-server.py', stdout.decode('UTF-8', 'replace')))
