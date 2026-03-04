#!/usr/bin/python3
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""license check"""

from __future__ import annotations

import datetime
import getopt
from typing import TYPE_CHECKING

import univention.admin.license
import univention.admin.uldap
import univention.config_registry
from univention.admin import uexceptions


# import univention.license
# from ldap.filter import filter_format


if TYPE_CHECKING:
    from collections.abc import Callable


License = univention.admin.license.License
_license = univention.admin.license._license


class UsageError(Exception):
    pass


def usage(msg: str | None = None) -> list[str]:
    out = []
    script_name = 'univention-license-check'
    if msg:
        out.append('E: %s' % msg)
    out.append('usage: %s [options]' % script_name)
    out.append('options:')
    out.append('  --%-30s %s' % ('binddn', 'bind DN'))
    out.append('  --%-30s %s' % ('bindpw', 'bind password'))
    out.append('  --%-30s %s' % ('list-dns', 'list DNs of found objects'))
    out.append('OPERATION FAILED')
    return out


def parse_options(argv: list[str]) -> dict[str, str]:
    options = {}
    long_opts = ['binddn=', 'bindpw=', 'list-dns']
    try:
        opts, args = getopt.getopt(argv, '', long_opts)
    except getopt.error as msg:
        raise UsageError(str(msg))
    if args:
        raise UsageError('options "%s" not recognized' % ' '.join(args))
    for opt, val in opts:
        options[opt[2:]] = val
    return options


def default_pw() -> str:
    with open('/etc/ldap.secret') as secret:
        return secret.readline().strip()


def format(label: str, num: int, max: str, expired: bool, cmp: Callable, ignored: bool = False) -> str:
    args = [(label + ':').ljust(20), str(num).rjust(9), str(max).rjust(9), 'OK']
    if expired:
        args[-1] = 'EXPIRED'
    elif cmp(num, max) > 0:
        args[-1] = 'FAILED'
    if ignored and args[-1] in ['FAILED', 'EXPIRED']:
        args[-1] = 'IGNORED'
    return '%s %s of %s... %s' % tuple(args)


def check_license(lo: univention.admin.uldap.access, dn: str | None, list_dns: bool, expired: int) -> list[str]:
    if expired == -1:
        return ['No valid license object found', 'OPERATION FAILED']
    out: list[str] = []

    def check_code(code: int) -> None:
        for label, value in [('basedn', 4), ('enddate', 2), ('signature', 1)]:
            if code & value == value:
                code ^= value
                ok = 'FAILED'
            else:
                ok = 'OK'
            out.append('Checking %s... %s' % ((label.ljust(10)), ok))

    def check_type() -> None:
        assert _license is not None
        v = _license.version
        types = _license.licenses[v]
        maximum = [_license.licenses[v][type] for type in types]
        num = [_license.real[v][type] for type in types]
        for i, m, n in zip(range(len(types)), maximum, num):
            if i == License.USERS:
                n -= _license.sysAccountsFound
                if n < 0:
                    n = 0
            ln = _license.names[v][i]
            if m:
                ignored = v == '2' and i == License.SERVERS  # Ignore the server count
                out.append(format(ln, n, m, False, _license.compare, ignored))
                if list_dns and i == License.USERS:
                    out.append("  %s Systemaccounts are ignored." % _license.sysAccountsFound)

    def check_time() -> None:
        now = datetime.date.today()
        then = _license.endDate
        if then != 'unlimited':
            (day, month, year) = then.split('.')
            then_ = datetime.date(int(year), int(month), int(day))
            if now > then_:
                out.append('Has expired on: %s                  -- EXPIRED' % then_)
            else:
                out.append('Will expire on: %s' % then)

    if dn is not None and list_dns:
        out.append('License found at: %s' % dn)
    check_code(_license.error)
    check_type()
    check_time()
    return out


def main(argv: list[str]) -> list[str]:
    options = parse_options(argv)
    configRegistry = univention.config_registry.ConfigRegistry()
    configRegistry.load()
    baseDN = configRegistry['ldap/base']
    master = configRegistry['ldap/master']
    port = int(configRegistry.get('ldap/master/port', '7389'))
    binddn = options.get('binddn', 'cn=admin,%s' % baseDN)
    bindpw = options.get('bindpw', None)
    if bindpw is None:
        try:
            bindpw = default_pw()
        except OSError:
            raise UsageError("Permission denied, try `--binddn' and `--bindpw'")
    try:
        lo = univention.admin.uldap.access(host=master, port=port, base=baseDN, binddn=binddn, bindpw=bindpw)
    except uexceptions.authFail:
        raise UsageError("Authentication failed, try `--bindpw'")

    out = ['Base DN: %s' % baseDN]
    try:
        _license.init_select(lo, 'admin')
    except uexceptions.base:  # ignore license... Exceptions
        pass
    out.extend(check_license(lo, None, 'list-dns' in options, 0))
    return out


def doit(argv: list[str]) -> list[str]:
    try:
        return main(argv[1:])
    except UsageError as msg:
        return usage(str(msg))


if __name__ == '__main__':
    import sys
    print('\n'.join(doit(sys.argv)))
