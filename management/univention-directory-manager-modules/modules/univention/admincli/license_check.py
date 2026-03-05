#!/usr/bin/python3
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""license check"""

from __future__ import annotations

import datetime
import getopt
import traceback
from typing import TYPE_CHECKING

from ldap.filter import filter_format

import univention.admin.license
import univention.admin.uldap
import univention.config_registry
import univention.license
from univention.admin import uexceptions


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


def find_licenses(lo: univention.admin.uldap.access, baseDN: str, module: str = '*') -> list[str]:
    def find_wrap(dir: str) -> list[str]:
        try:
            return lo.searchDn(base=dir, filter='(univentionLicenseObject=*)')
        except uexceptions.noObject:
            return []
    filter = filter_format('univentionLicenseModule=%s', [module])
    dirs = ['cn=default containers,cn=univention,%s' % baseDN]
    objects = [o for d in dirs for o in find_wrap(d)]
    containers = [c.decode('UTF-8') for o in objects for c in lo.get(o)['univentionLicenseObject']]
    licenses = [license for c in containers for license in lo.searchDn(base=c, filter=filter)]
    return licenses


def choose_license(lo: univention.admin.uldap.access, dns: list[str]) -> tuple[str | None, int]:
    for dn in dns:
        retval = univention.license.check(dn)
        if retval == -1:
            continue
        return dn, retval
    return None, -1


def check_license(lo: univention.admin.uldap.access, dn: str, list_dns: list[str], expired: int) -> list[str]:
    if expired == -1:
        return ['No valid license object found', 'OPERATION FAILED']
    out: list[str] = []

    def check_code(code: int) -> None:
        for label, value in [('searchpath', 8), ('basedn', 4), ('enddate', 2), ('signature', 1)]:
            if code >= value:
                code -= value
                ok = 'FAILED'
            else:
                ok = 'OK'
            out.append('Checking %s... %s' % ((label.ljust(10)), ok))

    def check_type() -> None:
        assert _license is not None
        v = _license.version
        types = _license.licenses[v]
        if dn is None:
            maximum = [_license.licenses[v][type] for type in types]
        else:
            maximum = [lo.get(dn)[_license.keys[v][type]][0].decode('utf-8') for type in types]
        objs = [lo.searchDn(filter=_license.filters[v][type]) for type in types]
        num = [len(obj or '') for obj in objs]
        _license.checkObjectCounts(maximum, num)
        for i, m, n, odn in zip(range(len(types)), maximum, num, objs):
            if i in (License.USERS, License.ACCOUNT):
                n -= _license.sysAccountsFound
                if n < 0:
                    n = 0
            ln = _license.names[v][i]
            if m:
                if list_dns:
                    out.append("")

                ignored = False
                if v == '2' and i == License.SERVERS:
                    # Ignore the server count
                    ignored = True
                out.append(format(ln, n, m, False, _license.compare, ignored))
                if list_dns and maximum != 'unlimited':
                    out.extend("  %s" % dnout for dnout in odn)
                if list_dns and (i in (License.USERS, License.ACCOUNT)):
                    out.append("  %s Systemaccounts are ignored." % _license.sysAccountsFound)

    def check_time() -> None:
        now = datetime.date.today()
        then = lo.get(dn)['univentionLicenseEndDate'][0].decode('UTF-8')
        if then != 'unlimited':
            (day, month, year) = then.split('.')
            then_ = datetime.date(int(year), int(month), int(day))
            if now > then_:
                out.append('Has expired on: %s                  -- EXPIRED' % then_)
            else:
                out.append('Will expire on: %s' % then)

    if dn is not None and list_dns:
        out.append('License found at: %s' % dn)
    check_code(expired)
    check_type()
    if dn is not None:
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
        out.extend(check_license(lo, None, 'list-dns' in options, 0))
    except uexceptions.base:
        dns = find_licenses(lo, baseDN, 'admin')
        dn, expired = choose_license(lo, dns)
        out.extend(check_license(lo, dn, 'list-dns' in options, expired))
    except Exception:
        # output any other tracebacks
        trace_out = traceback.format_exc().splitlines()
        out.extend(trace_out)
    finally:
        return out  # noqa: B012


def doit(argv: list[str]) -> list[str]:
    try:
        out = main(argv[1:])
        return out
    except UsageError as msg:
        return usage(str(msg))


if __name__ == '__main__':
    import sys
    print('\n'.join(doit(sys.argv)))
