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
from itertools import chain
from typing import Any, Iterator

import univention.ucslint.base as uub


def levenshtein(word: str, distance: int = 1, subst: str = '.') -> Iterator[str]:
    """
    Return modified list of words with given Levenshtein distance.

    :param word: The word to modify.
    :param distance: Levenshtein distance.
    :param subst: Character used for substitution.
    :returns: List of regular expressions.

    >>> set(levenshtein("ab")) == {'ab', '.b', 'a.', '.ab', 'a.b', 'ab.', 'a', 'b', 'ba'}
    True
    """
    yield word
    if distance == 0:
        return

    n = len(word)
    m_sub = (f'{word[0:i]}{subst}{word[i + 1:]}' for i in range(n))
    m_ins = (f'{word[0:i]}{subst}{word[i:]}' for i in range(n + 1))
    m_del = (f'{word[0:i]}{word[1 + i:]}' for i in range(n))
    m_swp = (f'{word[0:i]}{word[j]}{word[i + 1:j]}{word[i]}{word[j + 1:]}' for j in range(n) for i in range(j))
    for modified in chain(m_sub, m_ins, m_del, m_swp):
        yield from levenshtein(modified, distance - 1)


class Trie:
    """
    Regex::Trie in Python.

    Creates a Trie out of a list of words. The trie can be exported to a Regex pattern.
    The corresponding Regex should match much faster than a simple Regex union.
    """

    def __init__(self, *args: str) -> None:
        self.data: dict[str, Any] = {}
        for word in args:
            self.add(word)

    def add(self, word: str) -> None:
        """
        Add new word.

        :param word: Word to add.
        """
        ref = self.data
        for char in word:
            ref = ref.setdefault(char, {})

        ref[''] = None

    def _pattern(self, pData: (dict[str, Any])) -> str:
        """
        Recursively convert Trie structuture to regular expression.

        :param pData: Partial Trie tree.
        :returns: regular expression string.
        """
        data = pData
        if '' in data and len(data) == 1:
            return ''

        alt: list[str] = []
        cc: list[str] = []
        q = False
        for char, subtree in sorted(data.items()):
            if char == '':
                q = True
            else:
                recurse = self._pattern(subtree)
                if recurse == '':
                    cc.append(char)
                else:
                    alt.append(char + recurse)

        cconly = not alt

        if cc:
            alt.append(cc[0] if len(cc) == 1 else f'[{"".join(cc)}]')

        return '{}{}'.format(
            f'(?:{"|".join(alt)})' if len(alt) > 1 or q and not cconly else alt[0],
            '?' if q else '',
        )

    def pattern(self) -> str:
        """
        Convert Trie structuture to regular expression.

        :returns: regular expression.
        """
        return self._pattern(self.data)


UNIVENTION = ('univention', 'Univention', 'UNIVENTION')
"""Correct spellings."""
RE_UNIVENTION = re.compile(
    r'\b(?<![%\\])(?!{})(?:{})\b'.format(
        '|'.join(UNIVENTION),
        Trie(*chain(*[levenshtein(word, 2) for word in UNIVENTION])).pattern().replace('.', r'\w'),
    ),
)
"""Regular expression to find misspellings."""


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

    def getMsgIds(self) -> uub.MsgIds:
        return {
            '0015-1': (uub.RESULT_WARN, 'failed to open file'),
            '0015-2': (uub.RESULT_WARN, 'file contains "univention" incorrectly written'),
        }

    RE_WHITEWORD = re.compile(r'|'.join(r"""
        [0-9][0-9]univention
        punivention
        fBunivention
        invention
        [Kk]uhnivention
        onvention
        unintention
        univention
        Univention
        UNIVENTION
        _univention
        univention_
    """.split()))

    RE_WHITELINE = re.compile(r'|'.join(r"""
        \\[tnr]univention
        -.univention
        [SK]?[0-9][0-9]univention
        univention[0-9]
        univentionr\._baseconfig
        /var/lib/univentions-client-boot/
    """.split()))

    def check(self, path: str) -> None:
        super().check(path)

        for fn in uub.FilteredDirWalkGenerator(path, ignore_suffixes=uub.FilteredDirWalkGenerator.BINARY_SUFFIXES):
            try:
                with open(fn) as fd:
                    for row, line in enumerate(fd, start=1):
                        origline = line
                        if self.RE_WHITELINE.match(line):
                            continue
                        for match in RE_UNIVENTION.finditer(line):
                            found = match.group(0)
                            if self.RE_WHITEWORD.match(found):
                                continue
                            self.debug(f'{fn}:{row}: found="{found}"  origline="{origline}"')
                            self.addmsg('0015-2', f'univention is incorrectly spelled: {found}', fn, row)
            except UnicodeDecodeError:
                # Silently skip binary files
                pass
