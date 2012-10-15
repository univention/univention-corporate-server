#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console module:
#   Testscript for umc sanitizer
#
# Copyright 2012 Univention GmbH
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

from univention.management.console.modules import Base
from univention.management.console.protocol.definitions import *

from univention.management.console.modules.decorators import sanitize, simple_response
import univention.management.console.modules.sanitizers as s

class Instance( Base ):
	@sanitize(value=s.BooleanSanitizer(required=True))
	@simple_response
	def bool(self, value):
		""" bool is just an int with 1 bit, so:
			True: 1 == True, 0 == False, isinstance(True, int)
			False: 2 == True, isinstance(1, bool)
		"""
		assert repr(value) in ('True', 'False'), 'Value is not a bool'
		return '%r' % (value,)

	_choices = ('Ja', 2, True, (2,), [], {})
	@sanitize(value=s.ChoicesSanitizer(choices = _choices, required=True))
	@simple_response
	def choices(self, value):
		assert value in self._choices, 'A value is not in choices'
		assert isinstance(value, type(self._choices[self._choices.index(value)])), 'A choice has the wrong type' # makes sense !;)
		return '%r' % (value,)

	@sanitize(value=s.DictSanitizer({}, required=True))
	@simple_response
	def dict(self, value):
		assert isinstance(value, dict), 'Value is not a dict: %r' % (value)
		return '%r' % (value,)

	@sanitize(value=s.DictSanitizer({'foo': s.Sanitizer(), 'bar': s.Sanitizer()}, required=True, allow_other_keys=False))
	@simple_response
	def dict_2(self, value):
		assert set(value) == set(['foo', 'bar']), 'There are invalid keys: %r' % (list(values))
		return '%r' % (value,)

	@sanitize(value=s.EmailSanitizer(required=True))
	@simple_response
	def email(self, value):
		assert isinstance(value, basestring) and value.count('@') == 1, 'Value is not a string or does not contain @: %r' % (value,)
		return '%r' % (value,)

	@sanitize(value=s.IntegerSanitizer(required=True))
	@simple_response
	def int(self, value):
		assert isinstance(value, int), 'Value is not an int' # could be long
		return '%r' % (value,)

	@sanitize(value=s.LDAPSearchSanitizer(required=True))
	@simple_response
	def ldapsearch(self, value):
		# TODO
		return '%r' % (value,)

	@sanitize(value=s.ListSanitizer(s.Sanitizer(), required=True)),
	@simple_response
	def list(self, value):
		assert isinstance(value, (list, tuple)), 'No List given'
		return '%r' % (value,)

	@sanitize(value=s.ListSanitizer({}, min_elements=3, max_elements=6, required=True))
	@simple_response
	def list2(self, value):
		assert 3 <= len(value) <= 6, 'List length is wrong: %d' % len(value)
		return '%r' % (value,)

	_mapping = {
		u'foo': 'bar',
		b'bar': 1,
		'baz': []
	}
	@sanitize(value=s.MappingSanitizer(_mapping, required=True))
	@simple_response
	def mapping(self, value):
		assert value in _mapping.values(), 'Mapping failed: %r' % (value,) # TODO: more?
		return '%r' % (value,)

	@sanitize(value=s.PatternSanitizer(required=True))
	@simple_response
	def pattern(self, value):
		import re
		assert isinstance(value, re._pattern_type)
		# TODO: check *
		return '%r' % (value,)

	@sanitize(value=s.StringSanitizer(required=True))
	@simple_response
	def string(self, value):
		assert isinstance(value, basestring)
		if not isinstance(value, unicode):
			# Is it possible that we don't have unicode here?
			try:
				value.decode('utf-8')
			except:
				assert False, 'no unicode'
		return '%r' % (value,)
