#!/usr/bin/python3
# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import socket
import subprocess

import ldap

import univention.uldap


def is_service_active(service: str, hostname: str = socket.gethostname()) -> bool:
    lo = univention.uldap.getMachineConnection()
    raw_filter = '(&(univentionService=%s)(cn=%s))'
    filter_expr = ldap.filter.filter_format(raw_filter, (service, hostname))
    return any(dn is not None for dn, _attr in lo.search(filter_expr, attr=['cn']))


def active_services(lo: univention.uldap.access | None = None) -> list[bytes] | None:
    if not lo:
        lo = univention.uldap.getMachineConnection()
    res = lo.search(base=lo.binddn, scope='base', attr=['univentionService'])
    if res:
        _dn, attr = res[0]
        return attr.get('univentionService', [])
    return None


def run_with_output(cmd) -> tuple[bool, str]:
    output = []
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (stdout, stderr) = process.communicate()
    if stdout:
        output.append('\nSTDOUT:\n{}'.format(stdout.decode('UTF-8', 'replace')))
    if stderr:
        output.append('\nSTDERR:\n{}'.format(stderr.decode('UTF-8', 'replace')))
    return (process.returncode == 0, '\n'.join(output))
