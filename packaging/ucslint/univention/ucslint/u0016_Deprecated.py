#!/usr/bin/env python3
#
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
"""Find use of deprecated functions / programs / scripts."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable

import univention.ucslint.base as uub


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
    """Find use of deprecated functions / programs / scripts."""

    def getMsgIds(self) -> uub.MsgIds:
        """Return severity and description for message identifiers."""
        return {
            '0016-1': (uub.RESULT_WARN, 'failed to open file'),
            '0016-2': (uub.RESULT_ERROR, 'Deprecated use of "univention-admin"'),
            '0016-3': (uub.RESULT_ERROR, 'Use of deprecated "univention-baseconfig"'),
            '0016-4': (uub.RESULT_ERROR, 'Use of deprecated "univention_baseconfig"'),
            '0016-5': (uub.RESULT_ERROR, 'Use of deprecated "@%@BCWARNING=@%@"'),
            '0016-6': (uub.RESULT_ERROR, 'Use of deprecated "debian/*.univention-baseconfig"'),
        }

    def check(self, path: Path) -> None:
        """the real check"""
        super().check(path)
        IGNORE_SUFFIXES = ('.1', '.2', '.3', '.4', '.5', '.6', '.7', '.8', '.txt')
        IGNORE_FILES = ('changelog', 'README')
        self.check_files(
            set(uub.FilteredDirWalkGenerator(path, ignore_suffixes=IGNORE_SUFFIXES, ignore_files=IGNORE_FILES))
            | set(uub.FilteredDirWalkGenerator(path / 'debian', suffixes=('.univention-baseconfig',)))
        )

    def check_files(self, paths: Iterable[Path]) -> None:
        tester = uub.UPCFileTester()
        tester.addTest(
            re.compile(r'''(?:(?<=['" \t])|^)(?:/usr/sbin/)?univention-admin(?=['" \t]|$)'''),
            '0016-2', 'Use of deprecated "univention-admin"', cntmax=0)
        tester.addTest(
            re.compile(r'''(?:(?<=['" \t])|^)(?:/usr/sbin/)?univention-baseconfig(?=["' \t]|$)'''),
            '0016-3', 'Use of deprecated "univention-baseconfig"', cntmax=0)
        tester.addTest(
            re.compile(r'''\bfrom\b.+\bunivention_baseconfig\b.+\bimport\b|\bimport\b.+\bunivention_baseconfig\b'''),
            '0016-4', 'Use of deprecated "univention_baseconfig"', cntmax=0)
        tester.addTest(
            re.compile(r'''@%@BCWARNING=.+?@%@'''),
            '0016-5', 'Use of deprecated "@%@BCWARNING=@%@"', cntmax=0)

        paths = list(paths)
        for fn in paths:
            tester.open(fn)
            msglist = tester.runTests()
            self.msg.extend(msglist)

        for fn in paths:
            if fn.suffix == '.univention-baseconfig':
                self.addmsg('0016-6', 'Use of deprecated "debian/*.univention-baseconfig"', fn)


def main():
    import univention.ucslint.main as uum
    sys.exit(uum.run(UniventionPackageCheck))


if __name__ == '__main__':
    main()
