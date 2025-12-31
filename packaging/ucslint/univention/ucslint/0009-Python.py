# SPDX-FileCopyrightText: 2008-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import univention.ucslint.base as uub
from univention.ucslint.python import RE_LENIENT, Python36 as PythonVer, python_files


if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
    """Python specific checks."""

    def getMsgIds(self) -> uub.MsgIds:
        return {
            '0009-1': (uub.RESULT_WARN, 'failed to open file'),
            '0009-2': (uub.RESULT_ERROR, 'Python file does not specify Python version in hashbang'),
            '0009-3': (uub.RESULT_ERROR, 'Python file specifies wrong Python version in hashbang'),
            '0009-4': (uub.RESULT_WARN, 'Python file contains whitespace and maybe arguments after Python command'),
            '0009-8': (uub.RESULT_STYLE, 'use ucr.is_true() or .is_false()'),
            '0009-9': (uub.RESULT_ERROR, 'hashbang contains more than one option'),
            '0009-10': (uub.RESULT_WARN, 'invalid Python string literal escape sequence'),
            '0009-11': (uub.RESULT_STYLE, 'Use uldap.searchDn() instead of uldap.search(attr=["dn"])'),
        }

    RE_HASHBANG = re.compile(r'''^#!\s*/usr/bin/python(?:([0-9.]+))?(?:(\s+)(?:(\S+)(\s.*)?)?)?$''')
    RE_STRING = PythonVer.matcher()

    def check(self, path: Path) -> None:
        super().check(path)
        self.check_files(python_files(path))

    def check_files(self, paths: Iterable[Path]) -> None:
        tester = uub.UPCFileTester()
        tester.addTest(re.compile(
            r'''(?:baseConfig|configRegistry|ucr)(?:\[.+\]|\.get\(.+\)).*\bin\s*
            [\[\(]
            (?:\s*(['"])(?:yes|no|1|0|true|false|on|off|enabled?|disabled?)\1\s*,?\s*){3,}
            [\]\)]''', re.VERBOSE | re.IGNORECASE),
            '0009-8', 'use ucr.is_true() or .is_false()', cntmax=0)
        tester.addTest(re.compile(
            r'''\.search\s*\(
            .*?\b
            attr
            \s*=\s*
            (?:(?P<list>\[)|(?P<tuple>\())
            \s*
            (?P<str>["'])
            dn
            (?P=str)
            \s*
            (?(list)\])(?(tuple)\))
            ''', re.VERBOSE),
            '0009-11', 'Use uldap.searchDn() instead of uldap.search(attr=["dn"])', cntmax=0)

        for fn in paths:
            tester.open(fn)
            if not tester.raw:
                continue
            msglist = tester.runTests()
            self.msg.extend(msglist)

            match = self.RE_HASHBANG.match(tester.lines[0])
            if match:
                version, space, option, tail = match.groups()
                if not version:
                    self.addmsg('0009-2', 'file does not specify Python version in hashbang', fn, 1)
                elif version not in {'2.7', '3'}:
                    self.addmsg('0009-3', 'file specifies wrong Python version in hashbang', fn, 1)
                if space and not option:
                    self.addmsg('0009-4', 'file contains whitespace after Python command', fn, 1)
                if tail:
                    self.addmsg('0009-9', 'hashbang contains more than one option', fn, 1)

            for row, col, m in uub.line_regexp(tester.raw, RE_LENIENT):
                txt = m["str"]
                if not txt:
                    continue
                if self.RE_STRING.match(txt):
                    continue

                self.addmsg('0009-10', f'invalid Python string literal: {txt}', fn, row, col)
