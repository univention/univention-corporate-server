# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2019 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub
from itertools import chain
import re
try:
	from typing import Iterator  # noqa F401
except ImportError:
	pass


def levenshtein(word, distance=1, subst='.'):
	# type: (str, int, str) -> Iterator[str]
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

	l = len(word)
	m_sub = ('%s%s%s' % (word[0:i], subst, word[i + 1:]) for i in xrange(l))
	m_ins = ('%s%s%s' % (word[0:i], subst, word[i:]) for i in xrange(l + 1))
	m_del = ('%s%s' % (word[0:i], word[1 + i:]) for i in xrange(l))
	m_swp = ('%s%s%s%s%s' % (word[0:i], word[j], word[i + 1:j], word[i], word[j + 1:]) for j in xrange(l) for i in xrange(j))
	for modified in chain(m_sub, m_ins, m_del, m_swp):
		for result in levenshtein(modified, distance - 1):
			yield result


UNIVENTION = ('univention', 'Univention', 'UNIVENTION')
"""Correct spellings."""
RE_UNIVENTION = re.compile(
	r'\b(?!{})(?:{})\b'.format(
		'|'.join(UNIVENTION),
		'|'.join(chain(*[levenshtein(word, 2) for word in UNIVENTION])).replace('.', r'\w')
	)
)
"""Regular expression to find misspellings."""


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def getMsgIds(self):
		return {
			'0015-1': [uub.RESULT_WARN, 'failed to open file'],
			'0015-2': [uub.RESULT_WARN, 'file contains "univention" incorrectly written'],
		}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """

	RE_WHITEWORD = re.compile('|'.join("""
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

	RE_WHITELINE = re.compile('|'.join(r"""
		\\[tnr]univention
		-.univention
		[SK]?[0-9][0-9]univention
		univention[0-9]
		univentionr\._baseconfig
		/var/lib/univentions-client-boot/
	""".split()))

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		for fn in uub.FilteredDirWalkGenerator(path, ignore_suffixes=['.gz', '.zip', '.jpeg', '.jpg', '.png', '.svg', '.mo']):
			with open(fn, 'r') as fd:
				for lnr, line in enumerate(fd, start=1):
					origline = line
					if UniventionPackageCheck.RE_WHITELINE.match(line):
						continue
					for match in RE_UNIVENTION.finditer(line):
						found = match.group(0)
						if UniventionPackageCheck.RE_WHITEWORD.match(found):
							continue
						self.debug('%s:%d: found="%s"  origline="%s"' % (fn, lnr, found, origline))
						self.addmsg('0015-2', 'univention is incorrectly spelled: %s' % found, filename=fn, line=lnr)
