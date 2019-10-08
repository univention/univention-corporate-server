#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console module:
#   Testscript for umc sanitizer
#
# Copyright 2012-2019 Univention GmbH
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

from univention.management.console.modules import Base

from univention.lib.i18n import Translation

from univention.management.console.modules.decorators import simple_response, log, file_upload, multi_response, sanitize
import univention.management.console.modules.sanitizers as s

_ = Translation('univention.management.console').translate


class Instance(Base):

	@sanitize(value=s.BooleanSanitizer(required=True))
	@simple_response
	@log
	def bool(self, value):
		""" bool is just an int with 1 bit, so:
			True: 1 == True, 0 == False, isinstance(True, int)
			False: 2 == True, isinstance(1, bool)
		"""
		assert repr(value) in ('True', 'False'), 'Value is not a bool'
		return '%r' % (value,)

	_choices = ('Ja', 2, True, (2,), [], {})

	@sanitize(value=s.ChoicesSanitizer(choices=_choices, required=True))
	@simple_response
	@log
	def choices(self, value):
		assert value in self._choices, 'A value is not in choices'
		assert isinstance(value, type(self._choices[self._choices.index(value)])), 'A choice has the wrong type'  # makes sense !;)
		return '%r' % (value,)

	@sanitize(value=s.DictSanitizer({}, required=True))
	@simple_response
	@log
	def dict(self, value):
		assert isinstance(value, dict), 'Value is not a dict: %r' % (value)
		return '%r' % (value,)

	@sanitize(value=s.DictSanitizer({'foo': s.Sanitizer(), 'bar': s.Sanitizer()}, required=True, allow_other_keys=False))
	@simple_response
	@log
	def dict_a(self, value):
		assert set(value) == set(['foo', 'bar']), 'There are invalid keys: %r' % (list(value))
		return '%r' % (value,)

	@sanitize(value=s.EmailSanitizer(required=True))
	@simple_response
	@log
	def email(self, value):
		assert isinstance(value, basestring) and value.count('@') == 1, 'Value is not a string or does not contain @: %r' % (value,)
		return '%r' % (value,)

	@sanitize(value=s.IntegerSanitizer(required=True))
	@simple_response
	@log
	def int(self, value):
		assert isinstance(value, int), 'Value is not an int'  # could be long
		return '%r' % (value,)

	@sanitize(value=s.LDAPSearchSanitizer(required=True))
	@simple_response
	@log
	def ldapsearch(self, value):
		# TODO
		return '%r' % (value,)

	@sanitize(value=s.ListSanitizer(s.Sanitizer(), required=True))
	@simple_response
	@log
	def list(self, value):
		assert isinstance(value, (list, tuple)), 'No List given'
		return '%r' % (value,)

	@sanitize(value=s.ListSanitizer(min_elements=3, max_elements=6, required=True))
	@simple_response
	@log
	def list_a(self, value):
		assert 3 <= len(value) <= 6, 'wrong list length: %d' % len(value)
		return '%r' % (value,)

	_mapping = {
		u'foo': 'bar',
		b'bar': 1,
		'baz': []
	}

	@sanitize(value=s.MappingSanitizer(_mapping, required=True))
	@simple_response
	@log
	def mapping(self, value):
		assert value in self._mapping.values(), 'Mapping failed: %r' % (value,)  # TODO: more?
		return '%r' % (value,)

	@sanitize(value=s.PatternSanitizer(required=True))
	@simple_response
	@log
	def pattern(self, value):
		import re
		assert isinstance(value, re._pattern_type)
		assert value.pattern.count('.*') < 6, 'pattern contains more than 5 stars'
		return '%r' % (value,)

	@sanitize(value=s.StringSanitizer(required=True))
	@simple_response
	@log
	def string(self, value):
		assert isinstance(value, basestring)
		if not isinstance(value, unicode):
			# Is it possible that we don't have unicode here?
			try:
				value.decode('utf-8')
			except:
				assert False, 'no unicode'
		return '%r' % (value,)

	@simple_response
	@log
	def simple(self, value, foo='default'):
		return '%r %r' % (value, foo)

	@multi_response
	@log
	def multi(self, iterator, *values):
		assert all(map(lambda v: isinstance(v, dict), iterator))
		yield '%r %s' % (list(iterator), values)

	@file_upload
	def upload(self, request):
		assert request.command == 'UPLOAD'
		self.finished(request.id, True)

	@multi_response(single_values=True)
	def single(self, iterator, *values):
		return '%r' % (values)
