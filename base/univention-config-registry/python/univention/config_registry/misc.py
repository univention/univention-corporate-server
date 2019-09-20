# -*- coding: utf-8 -*-
#
"""Univention Configuration Registry helper functions."""
#  main configuration registry classes
#
# Copyright 2004-2019 Univention GmbH
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
from __future__ import print_function
import sys
import os
import re
import string  # pylint: disable-msg=W0402
try:
	from typing import Dict, IO, List, Text  # noqa F401
except ImportError:
	pass

__all__ = [
	'replace_dict', 'replace_umlaut', 'directory_files',
	'escape_value',
	'key_shell_escape', 'validate_key', 'INVALID_KEY_CHARS',
]


def replace_dict(line, dictionary):
	# type: (Text, Dict[Text, str]) -> Text
	"""
	Map any character from line to its value from dictionary.

	>>> replace_dict('kernel', {'e': 'E', 'k': '', 'n': 'pp'})
	'ErppEl'
	"""
	return ''.join((dictionary.get(_, _) for _ in line))


def replace_umlaut(line):
	# type: (Text) -> Text
	u"""
	Replace german umlauts.

	>>> replace_umlaut(u'überschrieben')
	u'ueberschrieben'
	"""
	return replace_dict(line, UMLAUTS)  # pylint: disable-msg=E1101


try:
	from pipes import quote as escape_value
except ImportError:
	_safechars = frozenset(string.ascii_letters + string.digits + '@%_-+=:,./')

	def escape_value(text):  # type: ignore
		# type: (str) -> str
		"""
		Return a shell-escaped version of the file string.

		:param text: Shell command argument.
		:returns: Escaped argument string.
		"""
		for c in text:
			if c not in _safechars:
				break
		else:
			if not text:
				return "''"
			return text
		# use single quotes, and put single quotes into double quotes
		# the string $'b is then quoted as '$'"'"'b'
		return "'" + text.replace("'", "'\"'\"'") + "'"


UMLAUTS = {  # type: ignore # pylint: disable-msg=W0612
	u'Ä': 'Ae',
	u'ä': 'ae',
	u'Ö': 'Oe',
	u'ö': 'oe',
	u'Ü': 'Ue',
	u'ü': 'ue',
	u'ß': 'ss',
}


def key_shell_escape(line):
	# type: (str) -> str
	"""
	Escape variable name by substituting shell invalid characters by '_'.

	:param line: UCR variable name.
	:returns: substitued variable name
	"""
	if not line:
		raise ValueError('got empty line')
	new_line = []
	if line[0] in string.digits:
		new_line.append('_')
	for letter in line:
		if letter in VALID_CHARS:  # pylint: disable-msg=E1101
			new_line.append(letter)
		else:
			new_line.append('_')

	return ''.join(new_line)


VALID_CHARS = (  # type: ignore # pylint: disable-msg=W0612
	string.ascii_letters + string.digits + '_')


def validate_key(key, out=sys.stderr):
	# type: (Text, IO) -> bool
	"""
	Check if key consists of only shell valid characters.

	:param key: UCR variable name to check.
	:param out: Output stream where error message is printed to.
	:returns: `True` if the name is valid, `False` otherwise.
	"""
	old = key
	key = replace_umlaut(key)

	if old != key:
		print('Please fix invalid umlaut in config variable key "%s" to %s.' % (old, key), file=out)
		return False

	if len(key) > 0:
		if ': ' in key:
			print('Please fix invalid ": " in config variable key "%s".' % (key,), file=out)
			return False
		match = INVALID_KEY_CHARS.search(key)

		if not match:
			return True
		print('Please fix invalid character "%s" in config variable key "%s".' % (match.group(), key), file=out)
	return False


INVALID_KEY_CHARS = re.compile('[][\r\n!"#$%&\'()+,;<=>?\\\\`{}§]')


def directory_files(directory):
	# type: (str) -> List[str]
	"""
	Return a list of all files below the given directory.

	:param directory: Base directory path.
	:returns: List of absolute file names.
	"""
	result = []
	for dirpath, _dirnames, filenames in os.walk(directory):
		for filename in filenames:
			filename = os.path.join(dirpath, filename)
			if os.path.isfile(filename):
				result.append(filename)
	return result


if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim:set sw=4 ts=4 noet:
