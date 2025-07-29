# SPDX-FileCopyrightText: 2008-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import univention.ucslint.base as uub
from univention.ucslint.python import MATCHED_LENIENT as MATCHED_STRING, _or, python_files


if TYPE_CHECKING:
    from collections.abc import Iterable


# 1) check if translation strings are correct; detect something like  _('foo %s bar' % var)  ==> _('foo %s bar') % var
# 2) check if all translation strings are translated in de.po file


RE_FUZZY = re.compile(r'^\#,[ ] .*? \b fuzzy \b', re.MULTILINE | re.VERBOSE)
RE_EMPTY = re.compile(r'msgstr ""\n\n', re.DOTALL)
RE_CHARSET = re.compile(r'"Content-Type: text/plain; charset=(.*?)\\n"', re.DOTALL)

NON_STRING = r"""[^'"#\n]"""
CONTEXT = _or(NON_STRING, MATCHED_STRING)
SEPARATOR = r"[([{\s,:]"
TRANSLATION = r"(_\(\s*" + MATCHED_STRING + r"\s*%\s*(?:[^\n]+\))?)"
RE_TRANSLATION = re.compile(CONTEXT + SEPARATOR + TRANSLATION, re.DOTALL | re.MULTILINE | re.VERBOSE)


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

    def getMsgIds(self) -> uub.MsgIds:
        return {
            '0008-1': (uub.RESULT_ERROR, 'substitutes before translation'),
            '0008-2': (uub.RESULT_WARN, 'failed to open file'),
            '0008-3': (uub.RESULT_ERROR, 'po-file contains "fuzzy" string'),
            '0008-4': (uub.RESULT_WARN, 'po-file contains empty msg string'),
            '0008-5': (uub.RESULT_ERROR, 'po-file contains no character set definition'),
            '0008-6': (uub.RESULT_ERROR, 'po-file contains invalid character set definition'),
            '0008-7': (uub.RESULT_WARN, 'found well-known LDAP object but no custom_*name()'),
        }

    def check(self, path: Path) -> None:
        super().check(path)

        self.check_py(python_files(path))
        self.check_po(uub.FilteredDirWalkGenerator(path, suffixes=('.po',)))
        self.check_names(uub.FilteredDirWalkGenerator(
            path,
            ignore_suffixes=uub.FilteredDirWalkGenerator.BINARY_SUFFIXES | uub.FilteredDirWalkGenerator.DOCUMENTATION_SUFFIXES,
        ))

    def check_files(self, paths: Iterable[Path]) -> None:
        # TODO: split into 3 modules
        if self.path != Path('/'):
            self.check_py(python_files(self.path))
        self.check_po([po_file for po_file in paths if po_file.suffix == '.po'])
        if self.path != Path('/'):
            self.check_names(uub.FilteredDirWalkGenerator(
                self.path,
                ignore_suffixes=uub.FilteredDirWalkGenerator.BINARY_SUFFIXES | uub.FilteredDirWalkGenerator.DOCUMENTATION_SUFFIXES,
            ))

    def check_py(self, py_files: Iterable[Path]) -> None:
        """Check Python files."""
        for fn in py_files:
            try:
                content = fn.read_text()
            except OSError:
                self.addmsg('0008-2', 'failed to open and read file', fn)
                continue

            self.debug(f'testing {fn}')
            for row, col, match in uub.line_regexp(content, RE_TRANSLATION):
                self.addmsg('0008-1', f'substitutes before translation: {match[1]}', fn, row, col)

    def check_po(self, po_files: Iterable[Path]) -> None:
        """Check Portable Object files."""
        for fn in po_files:
            try:
                content = fn.read_text()
            except OSError:
                self.addmsg('0008-2', 'failed to open and read file', fn)
                continue

            match = RE_CHARSET.search(content)
            if not match:
                self.addmsg('0008-5', 'cannot find charset definition', fn)
            elif match[1].lower() not in 'utf-8':
                self.addmsg('0008-6', f'invalid charset ({(match[1])}) defined', fn)

            self.debug(f'testing {fn}')
            for regex, errid, errtxt in [
                    (RE_FUZZY, '0008-3', 'contains "fuzzy"'),
                    (RE_EMPTY, '0008-4', 'contains empty msgstr'),
            ]:
                for row, col, _match in uub.line_regexp(content, regex):
                    self.addmsg(errid, errtxt, fn, row, col)

    def check_names(self, files: Iterable[Path]) -> None:
        tester = uub.UPCFileTester()
        tester.addTest(
            re.compile(
                r'''
                (?<!custom_groupname[( ])
                (?<!custom_username[( ])
                (['"]) \b
                (?:Domain\ Users|Domain\ Admins|Administrator|Windows\ Hosts)
                \b \1
                ''', re.VERBOSE),
            '0008-7', 'found well-known LDAP object but no custom_*name()', cntmax=0)

        for fn in files:
            try:
                tester.open(fn)
            except OSError:
                self.addmsg('0002-1', 'failed to open and read file', fn)
                continue
            else:
                self.msg += tester.runTests()
