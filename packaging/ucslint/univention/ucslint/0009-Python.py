# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2008-2023 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from __future__ import annotations

import re
from pathlib import Path

import univention.ucslint.base as uub
from univention.ucslint.python import RE_LENIENT, Python36 as PythonVer, python_files


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

        for fn in python_files(path):
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
