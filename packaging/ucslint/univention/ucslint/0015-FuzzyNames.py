# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2022 Univention GmbH
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

import re
from itertools import chain
from typing import Any, Dict, Iterator, List  # noqa F401

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
	m_sub = ('%s%s%s' % (word[0:i], subst, word[i + 1:]) for i in range(n))
	m_ins = ('%s%s%s' % (word[0:i], subst, word[i:]) for i in range(n + 1))
	m_del = ('%s%s' % (word[0:i], word[1 + i:]) for i in range(n))
	m_swp = ('%s%s%s%s%s' % (word[0:i], word[j], word[i + 1:j], word[i], word[j + 1:]) for j in range(n) for i in range(j))
	for modified in chain(m_sub, m_ins, m_del, m_swp):
		for result in levenshtein(modified, distance - 1):
			yield result


class Trie():
	"""
	Regex::Trie in Python. Creates a Trie out of a list of words. The trie can be exported to a Regex pattern.
	The corresponding Regex should match much faster than a simple Regex union.
	"""

	def __init__(self, *args: str) -> None:
		self.data = {}  # type: Dict[str, Any]
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

	def _pattern(self, pData: (Dict[str, Any])) -> str:
		"""
		Recursively convert Trie structuture to regular expression.

		:params pData: Partial Trie tree.
		:returns: regular expression string.
		"""
		data = pData
		if '' in data and len(data) == 1:
			return ''

		alt = []  # type: List[str]
		cc = []  # type: List[str]
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
			alt.append(cc[0] if len(cc) == 1 else '[%s]' % ''.join(cc))

		return '%s%s' % (
			'(?:%s)' % '|'.join(alt) if len(alt) > 1 or q and not cconly else alt[0],
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
		Trie(*chain(*[levenshtein(word, 2) for word in UNIVENTION])).pattern().replace('.', r'\w')
	)
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
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		for fn in uub.FilteredDirWalkGenerator(path, ignore_suffixes=uub.FilteredDirWalkGenerator.BINARY_SUFFIXES):
			try:
				with open(fn, 'r') as fd:
					for row, line in enumerate(fd, start=1):
						origline = line
						if self.RE_WHITELINE.match(line):
							continue
						for match in RE_UNIVENTION.finditer(line):
							found = match.group(0)
							if self.RE_WHITEWORD.match(found):
								continue
							self.debug('%s:%d: found="%s"  origline="%s"' % (fn, row, found, origline))
							self.addmsg('0015-2', 'univention is incorrectly spelled: %s' % found, fn, row)
			except UnicodeDecodeError:
				# Silently skip binary files
				pass
