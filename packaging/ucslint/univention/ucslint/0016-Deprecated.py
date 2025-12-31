# SPDX-FileCopyrightText: 2008-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Find use of deprecated functions / programs / scripts."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import univention.ucslint.base as uub


if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


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
            | set(uub.FilteredDirWalkGenerator(path / 'debian', suffixes=('.univention-baseconfig',))),
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
