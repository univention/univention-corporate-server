# SPDX-FileCopyrightText: 2008-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re
from itertools import chain
from typing import TYPE_CHECKING, Any

import univention.ucslint.base as uub


if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path


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

    RE_WHITEWORD = re.compile(r'|'.join([  # noqa: FLY002
        r"[0-9][0-9]univention",
        r"Xunivention",
        r"punivention",
        r"fBunivention",
        r"invention",
        r"[Kk]uhnivention",
        r"onvention",
        r"unintention",
        r"univention",
        r"Univention",
        r"UNIVENTION",
        r"_univention",
        r"univention_",
    ]))

    RE_WHITELINE = re.compile(r'|'.join([  # noqa: FLY002
        r"\\[tnr]univention",
        r"-.univention",
        r"[SK]?[0-9][0-9]univention",
        r"univention[0-9]",
        r"univentionr\._baseconfig",
        r"/var/lib/univentions-client-boot/",
    ]))

    def check(self, path: Path) -> None:
        super().check(path)
        self.check_files(uub.FilteredDirWalkGenerator(path, ignore_suffixes=uub.FilteredDirWalkGenerator.BINARY_SUFFIXES))

    def check_files(self, paths: Iterable[Path]) -> None:
        for fn in paths:
            try:
                with fn.open() as fd:
                    for row, line in enumerate(fd, start=1):
                        origline = line
                        if self.RE_WHITELINE.match(line):
                            continue
                        for match in RE_UNIVENTION.finditer(line):
                            found = match[0]
                            if self.RE_WHITEWORD.match(found):
                                continue
                            self.debug('%s:%s: found="%s"  origline="%s"', fn, row, found, origline)
                            self.addmsg('0015-2', f'univention is incorrectly spelled: {found}', fn, row)
            except UnicodeDecodeError:
                # Silently skip binary files
                pass
