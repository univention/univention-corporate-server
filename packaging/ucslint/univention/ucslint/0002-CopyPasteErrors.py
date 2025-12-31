# SPDX-FileCopyrightText: 2008-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re
from itertools import chain
from typing import TYPE_CHECKING

import univention.ucslint.base as uub


if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


# 1) check if strings like "dc=univention,dc=qa" appear in debian/* and conffiles/*
# 2) check if strings like "univention.qa" appear in debian/* and conffiles/*


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

    def getMsgIds(self) -> uub.MsgIds:
        return {
            '0002-1': (uub.RESULT_WARN, 'cannot open file'),
            '0002-2': (uub.RESULT_ERROR, 'found basedn used in QA'),
            '0002-3': (uub.RESULT_ERROR, 'found domainname used in QA'),
        }

    def check(self, path: Path) -> None:
        super().check(path)
        self.check_files(chain(
            uub.FilteredDirWalkGenerator(path / 'conffiles'),
            uub.FilteredDirWalkGenerator(path / 'debian'),
        ))

    def check_files(self, paths: Iterable[Path]) -> None:
        tester = uub.UPCFileTester()
        tester.addTest(re.compile(r'dc=univention,dc=(?:local|qa|test)'), '0002-2', 'contains invalid basedn', cntmax=0)
        tester.addTest(re.compile(r'univention\.(?:local|qa|test)'), '0002-3', 'contains invalid domainname', cntmax=0)

        for fn in paths:
            try:
                tester.open(fn)
            except OSError:
                self.addmsg('0002-1', 'failed to open and read file', fn)
            else:
                self.msg += tester.runTests()
