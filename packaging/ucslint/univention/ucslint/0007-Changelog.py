# SPDX-FileCopyrightText: 2008-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re
from email.utils import mktime_tz, parsedate_tz
from typing import TYPE_CHECKING

from debian.changelog import Changelog, ChangelogParseError

import univention.ucslint.base as uub


if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


REticket = re.compile(
    r'''
    (Bug:?[ ]\#[0-9]{1,6} # Bugzilla
    |Issue:?[ ]\#[0-9]{1,6} # Redmine
    |Ticket(\#:[ ]|:?[ ]\#)2[0-9]{3}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])(?:1[0-9]{7}|21[0-9]{6})) # OTRS
    (?![0-9]) # not followed by additional digits
    ''', re.VERBOSE)
RECENT_ENTRIES = 2


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

    def getMsgIds(self) -> uub.MsgIds:
        return {
            '0007-1': (uub.RESULT_WARN, 'failed to open file'),
            '0007-2': (uub.RESULT_WARN, 'changelog does not contain ticket/bug/issue number'),
            '0007-3': (uub.RESULT_ERROR, 'debian/changelog entries are not strict-monotonically increasing by time'),
            '0007-4': (uub.RESULT_ERROR, 'debian/changelog entries are not strict-monotonically increasing by version'),
            '0007-5': (uub.RESULT_WARN, 'old debian/changelog entries are not strict-monotonically increasing by time'),
            '0007-6': (uub.RESULT_WARN, 'old debian/changelog entries are not strict-monotonically increasing by version'),
        }

    def check(self, path: Path) -> None:
        super().check(path)
        self._main(path / 'debian' / 'changelog')

    def check_files(self, paths: Iterable[Path]) -> None:
        for fn in paths:
            if fn.name == 'changelog':
                self._main(fn)

    def _main(self, fn: str) -> None:
        try:
            with fn.open() as stream:
                changelog = Changelog(stream, strict=True)
        except OSError as ex:
            self.addmsg('0007-1', f'failed to open and read file: {ex}', fn)
            return
        except ChangelogParseError as ex:
            self.addmsg('0007-1', str(ex), fn)
            return

        for change in changelog[0].changes():
            if REticket.search(change):
                break
        else:
            self.addmsg('0007-2', 'latest changelog entry does not contain bug/ticket/issue number', fn)

        last = None
        for nr, block in enumerate(changelog):
            if last:
                if mktime_tz(parsedate_tz(last.date)) <= mktime_tz(parsedate_tz(block.date)):
                    if nr < RECENT_ENTRIES:
                        self.addmsg('0007-3', f'not strict-monotonically increasing by time: {last.date} <= {block.date}', fn)
                    else:
                        self.addmsg('0007-5', f'old not strict-monotonically increasing by time: {last.date} <= {block.date}', fn)

                if last.version <= block.version:
                    if nr < RECENT_ENTRIES:
                        self.addmsg('0007-4', f'not strict-monotonically increasing by version: {last.version} <= {block.version}', fn)
                    else:
                        self.addmsg('0007-6', f'old not strict-monotonically increasing by version: {last.version} <= {block.version}', fn)

            last = block
