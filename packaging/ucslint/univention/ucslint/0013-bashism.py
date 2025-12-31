# SPDX-FileCopyrightText: 2008-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

import univention.ucslint.base as uub
from univention.ucslint.common import RE_HASHBANG_SHELL


if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


RE_BASHISM = re.compile(r'^.*?\s+line\s+(\d+)\s+[(](.*?)[)][:]\n([^\n]+)$')
RE_LOCAL = re.compile(
    r'''
    \blocal\b
    \s+
    \w+
    =
    (?:\$(?![?$!#\s'"]
        |\{[?$!#]\}
        |$)
    |`
    )
    ''',
    re.VERBOSE,
)


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

    def getMsgIds(self) -> uub.MsgIds:
        return {
            '0013-1': (uub.RESULT_WARN, 'failed to open file'),
            '0013-2': (uub.RESULT_ERROR, 'possible bashism found'),
            '0013-3': (uub.RESULT_WARN, 'cannot parse output of "checkbashism"'),
            '0013-4': (uub.RESULT_WARN, 'unquoted local variable'),
        }

    def check(self, path: Path) -> None:
        super().check(path)

        self.check_files(uub.FilteredDirWalkGenerator(
            path,
            ignore_suffixes=['.po'],
            reHashBang=RE_HASHBANG_SHELL,
        ))

    def check_files(self, paths: Iterable[Path]) -> None:
        for fn in paths:
            self.debug("Testing file %s", fn)
            try:
                self.check_bashism(fn)
                self.check_unquoted_local(fn)
            except (OSError, UnicodeDecodeError):
                self.addmsg('0013-1', 'failed to open file', fn)

    def check_bashism(self, fn: Path) -> None:
        p = subprocess.Popen(['checkbashisms', fn], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _stdout, stderr = p.communicate()
        # 2 = file is no shell script or file is already bash script
        # 1 = bashism found
        # 0 = everything is posix compliant
        if p.returncode == 1:
            for item in stderr.decode('utf-8', 'replace').split('possible bashism in '):
                item = item.strip()
                if not item:
                    continue

                match = RE_BASHISM.search(item)
                if not match:
                    escaped = item.replace('\n', '\\n').replace('\r', '\\r')
                    self.addmsg('0013-3', f'cannot parse checkbashism output:\n"{escaped}"', fn)
                    continue

                row = int(match[1])
                msg = match[2]
                code = match[3]

                self.addmsg('0013-2', f'possible bashism ({msg}):\n{code}', fn, row)

    def check_unquoted_local(self, fn: Path) -> None:
        with fn.open() as fd:
            for row, line in enumerate(fd, start=1):
                line = line.strip()
                match = RE_LOCAL.search(line)
                if not match:
                    continue

                self.addmsg('0013-4', f'unquoted local variable: {line}', fn, row)
