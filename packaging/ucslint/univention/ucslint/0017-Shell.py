# SPDX-FileCopyrightText: 2008-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Find unquoted usage of eval "$(ucr shell)"."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import univention.ucslint.base as uub
from univention.ucslint.common import RE_HASHBANG_SHELL


if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

    def __init__(self) -> None:
        super().__init__()
        self.tester = uub.UPCFileTester()
        self.tester.addTest(
            re.compile(r'eval\s+(`|[$][(])\s*(/usr/sbin/)?(ucr|univention-config-registry)\s+shell\s*[^`)]*[`)]\s*'),
            '0017-1', 'unquoted call of eval "$(ucr shell)"', cntmax=0)
        self.tester.addTest(re.compile(
            r'\b tr \s+ (-[a-zA-Z]+\s+)* \[', re.VERBOSE),
            '0017-2', 'unquoted argument for tr (e.g. "tr -d [a-z]")', cntmax=0)
        self.tester.addTest(re.compile(
            r'''\b tr \s+ (-[a-zA-Z]+\s+)* ["']\[+[^\]]+\]+["']\s+\[''', re.VERBOSE),
            '0017-2', 'unquoted argument for tr (e.g. "tr -d [a-z]")', cntmax=0)
        self.tester.addTest(re.compile(
            r'\b univention-ldapsearch \b .* \s-[a-wyzA-Z]*x[a-wyzA-Z]* \b', re.VERBOSE),
            '0017-3', 'use of univention-ldapsearch -x', cntmax=0)
        self.tester.addTest(
            re.compile(r'\b (?:/sbin/)? ip6?tables \b \s+ (?!--wait \b)', re.VERBOSE),
            '0017-4', 'iptables without --wait', cntmax=0)
        self.tester.addTest(
            re.compile(r'\b sed \s+ .* s (.) .* \\\(\.\*\\\) \$? \1 \\1 \1', re.VERBOSE),
            '0017-5', 'Use `sed -n "s/^prefix: //p"`', cntmax=0)
        self.tester.addTest(
            re.compile(r'\b sed (?: \s+ -[bnsuz]*[Er][bnsuze]* \b )+ .* s (.) .* \(\.\*\) \$? \1 \\1 \1', re.VERBOSE),
            '0017-5', 'Use `sed -n "s/^prefix: //p"`', cntmax=0)
        self.tester.addTest(
            re.compile(r'\b ldapsearch \b .+ \b ldapsearch-wrapper \b', re.VERBOSE),
            '0017-6', 'Use `ldapsearch -o ldif-wrap=no`', cntmax=0)
        self.tester.addTest(
            re.compile(r'\b (\w+) \[ \${\#\1\[[@*]\]} \]=', re.VERBOSE),
            '0017-7', 'Use `array+=(val)`', cntmax=0)
        self.tester.addTest(
            re.compile(r'''\b (?:cat|more) \s+ (?:'[^']*'|"[^"]*"|[^"'*? |])+ \s* \|(?!\|)''', re.VERBOSE),
            '0017-8', "Useless use of `cat`; redirect STDIN instead", cntmax=0)
        self.tester.addTest(
            re.compile(r'\b grep \b .* \|(?!\|) .* \b (?:awk|perl|sed) \b', re.VERBOSE),
            '0017-9', "Useless use of `grep`; use /PATTERN/s instead", cntmax=0)
        self.tester.addTest(
            re.compile(r'\b echo \s+ (?:-[ne]+ \s+)* (")? \$\( [^<][^)]* \) \1 \s* (?:$|[|&]|\d*[<>])', re.VERBOSE),
            '0017-10', "Useless use of `echo $(...)` for single argument", cntmax=0)

    def getMsgIds(self) -> uub.MsgIds:
        return {
            '0017-1': (uub.RESULT_WARN, 'script contains unquoted calls of eval "$(ucr shell)"'),
            '0017-2': (uub.RESULT_ERROR, 'script contains unquoted arguments of tr'),
            '0017-3': (uub.RESULT_WARN, 'LDAP simple bind is an internal detail of "univention-ldapsearch"'),
            '0017-4': (uub.RESULT_ERROR, 'ip[6]tables --wait must be used since UCS-4.2'),
            '0017-5': (uub.RESULT_STYLE, 'Use `sed -n "s/^prefix: //p"`'),
            '0017-6': (uub.RESULT_STYLE, 'Use `ldapsearch -LLLo ldif-wrap=no`'),
            '0017-7': (uub.RESULT_STYLE, 'Use `array+=(val)`'),
            '0017-8': (uub.RESULT_STYLE, "Useless use of `cat`; redirect STDIN instead"),
            '0017-9': (uub.RESULT_STYLE, "Useless use of `grep`; use /PATTERN/s instead"),
            '0017-10': (uub.RESULT_STYLE, "Useless use of `echo $(...)` for single argument"),
        }

    def check(self, path: Path) -> None:
        super().check(path)

        #
        # search shell scripts and execute test
        #
        self.check_files(uub.FilteredDirWalkGenerator(path, suffixes=['.sh'], reHashBang=RE_HASHBANG_SHELL))

    def check_files(self, paths: Iterable[Path]) -> None:
        for fn in paths:
            try:
                self.tester.open(fn)
            except OSError:
                continue
            else:
                msglist = self.tester.runTests()
                self.msg.extend(msglist)
