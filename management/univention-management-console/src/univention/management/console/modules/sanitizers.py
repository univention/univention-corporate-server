#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Sanitizer Classes used in decorator
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

"""
Sanitize classes for the sanitize decorator
===========================================

This module provides the Sanitize base class as well as some important
and often used Sanitizers. They are used in the
:class:`~univention.management.console.modules.decorators.sanitize` function.
If the provided classes do not meet your requirements you can easily
make one yourself.

The main job of sanitizers is to alter values if needed so that they
cannot do something harmful in the exposed UMC-functions. But they are also
very helpful when one needs to just validate input.
"""
import re
import copy

import ldap.filter

from univention.lib.i18n import Translation
_ = Translation('univention.management.console').translate


class UnformattedValidationError(Exception):

	"""
	Unformatted error raised when the sanitizer finds a value he
	cannot use at all (e.g. letters when an int is expected).
	Should be "enhanced" to a ValidationError.
	"""

	def __init__(self, msg, kwargs):
		self.msg = msg
		self.kwargs = kwargs

	def __str__(self):
		return self.msg


class ValidationError(Exception):

	"""
	Error raised when the sanitizer finds a value he cannot use at all
	(e.g. letters when an int is expected).
	"""

	def __init__(self, msg, name, value):
		self.msg = msg
		self.name = name
		self.value = value

	def __str__(self):
		return self.msg

	def number_of_errors(self):
		'''1...'''
		return 1

	def result(self):
		'''Returns the message'''
		# return {'name' : self.name, 'value' : self.value, 'msg' : self.msg}
		return self.msg


class MultiValidationError(ValidationError):

	"""
	Error used for validation of an arbitrary number of sanitizers.
	Used by :class:`~DictSanitizer` and :class:`~ListSanitizer`.
	"""

	def __init__(self):
		self.validation_errors = {}

	def add_error(self, e, name):
		'''Adds a :class:`ValidationError`'''
		self.validation_errors[name] = e

	def number_of_errors(self):
		'''Cumulative number of errors found'''
		num = 0
		for k, v in self.validation_errors.iteritems():
			num += v.number_of_errors()
		return num

	def __str__(self):
		return _('%d error(s) occurred') % self.number_of_errors()

	def has_errors(self):
		'''Found any errors'''
		return bool(self.validation_errors)

	def result(self):
		'''Returns a errors in a similar way like the arguments were passed
		to the sanitizers.'''
		return dict([(name, e.result()) for name, e in self.validation_errors.iteritems()])


class Sanitizer(object):

	'''
	Base class of all sanitizers.

	For reasons of extensibility and for ease of subclassing, the
	parameters are \**kwargs. But only the following are meaningful:

	:param [string] further_arguments: names of arguments that should be
		passed along with the actual argument in order to return something
		reasonable. Default: *None*
	:param bool required: if the argument is required. Default: *False*
	:param object default: if argument is not given and not
		:attr:`~Sanitizer.required`, default is returned - even when not
		:attr:`~Sanitizer.may_change_value`. Note that this value is not
		passing the sanitizing procedure, so make sure to be able to handle
		it. Default: *None*
	:param bool may_change_value: if the process of sanitizing is allowed
		to alter *request.options*. If not, the sanitizer can still be used
		for validation. Default: *True*
	:param bool allow_none: if None is allowed and not further validated.
		Default: *False*
	'''

	def __init__(self, **kwargs):
		self.further_arguments = kwargs.get('further_arguments', None)
		self.required = kwargs.get('required', False)
		self.default = kwargs.get('default', None)
		self.may_change_value = kwargs.get('may_change_value', True)
		self.allow_none = kwargs.get('allow_none', False)

	def sanitize(self, name, options):
		'''Sanitize function. Internally calls _sanitize with the
		correct values and returns the new value (together with a flag
		indicating whether the value was found at all).
		If you write your own Sanitize class, you probably want to
		override :meth:`~Sanitizer._sanitize`.

		.. document private functions
		.. automethod:: _sanitize
		'''
		if name not in options:
			if self.required:
				self.raise_formatted_validation_error(_('Argument required'), name, None)
			else:
				return self.default
		value = options[name]
		if value is None and self.allow_none:
			return value
		if self.further_arguments:
			further_arguments = dict([(field, options.get(field)) for field in self.further_arguments])
		else:
			further_arguments = {}
		try:
			new_value = self._sanitize(value, name, further_arguments)
			if self.may_change_value:
				return new_value
			else:
				return value
		except UnformattedValidationError as e:
			self.raise_formatted_validation_error(str(e), name, value, **e.kwargs)

	def _sanitize(self, value, name, further_arguments):
		'''The method where the actual sanitizing takes place.

		The standard method just returns *value* so be sure to
		override this method in your Sanitize class.

		:param object value: the value as found in *request.options*.
		:param string name: the name of the argument currently
			sanitized.
		:param further_arguments: dictionary
			holding the values of those additional arguments
			in *request.options* that are needed for sanitizing.
			the arguments come straight from the not altered
			options dict (i.e. before potentially changing
			sanitizing happened).
		:type further_arguments: {string : object}
		'''
		return value

	def raise_validation_error(self, msg, **kwargs):
		'''Used to more or less uniformly raise a
		:class:`~ValidationError`. This will actually raise an
		:class:`~UnformattedValidationError` for your convenience.
		If used in :meth:`~Sanitizer._sanitize`, it will be
		automatically enriched with name, value und formatting in
		:meth:`~Sanitizer.sanitize`.

		:param dict \**kwargs: additional arguments for formatting
		'''
		raise UnformattedValidationError(msg, kwargs)

	def raise_formatted_validation_error(self, msg, name, value, **kwargs):
		'''Used to more or less uniformly raise a
		:class:`~ValidationError`. *name* and *value* need to passed
		because the sanitizer should be thread safe.

		:param string msg: error message
		:param string name: name of the argument
		:param object value: the argument which caused the error
		:param dict \**kwargs: additional arguments for formatting
		'''
		format_dict = {'value': value, 'name': name}
		format_dict.update(kwargs)
		format_dict.update(self.__dict__)
		# msg = '%(name)s (%(value)r): ' + msg
		raise ValidationError(msg % format_dict, name, value)


class DictSanitizer(Sanitizer):

	''' DictSanitizer makes sure that the value is a dict and sanitizes its fields.

	You can give the same parameters as the base class.
	Plus:

	:param sanitizers: will be applied to the content of the sanitized dict
	:param bool allow_other_keys: if other keys than those in
		:attr:`~DictSanitizer.sanitizers` are allowed.
	:param default_sanitizer: will be applied to the content if no sanitizer is defined
	:type sanitizers: {string : :class:`~Sanitizer`}
	:type default_sanitizer: :class:`~Sanitizer`
	'''

	def __init__(self, sanitizers, allow_other_keys=True, default_sanitizer=None, **kwargs):
		self._copy_value = kwargs.pop('_copy_value', True)
		super(DictSanitizer, self).__init__(**kwargs)
		self.sanitizers = sanitizers
		self.default_sanitizer = default_sanitizer
		self.allow_other_keys = allow_other_keys

	def _sanitize(self, value, name, further_arguments):
		if not isinstance(value, dict):
			self.raise_formatted_validation_error(_('Not a "dict"'), name, type(value).__name__)

		if not self.allow_other_keys and any(key not in self.sanitizers for key in value):
			self.raise_validation_error(_('Has more than the allowed keys'))

		altered_value = copy.deepcopy(value) if self._copy_value else value

		multi_error = MultiValidationError()
		for attr in set(value.keys() + self.sanitizers.keys()):
			sanitizer = self.sanitizers.get(attr, self.default_sanitizer)
			try:
				if sanitizer:
					altered_value[attr] = sanitizer.sanitize(attr, value)
			except ValidationError as e:
				multi_error.add_error(e, attr)

		if multi_error.has_errors():
			raise multi_error

		return altered_value

	def __add__(self, other):
		new = copy.deepcopy(self)
		new.sanitizers.update(other.sanitizers)
		return new


class ListSanitizer(Sanitizer):

	''' ListSanitizer makes sure that the value is a list and sanitizes its elements.

	You can give the same parameters as the base class.
	Plus:

	:param sanitizer: sanitizes each of the sanitized list's elements.
		If *None*, no sanitizing of elements takes place.
	:param int min_elements: must have at least this number of elements
	:param int max_elements: must have at most this number of elements
	:type sanitizer: :class:`~Sanitizer`
	'''

	def __init__(self, sanitizer=None, min_elements=None, max_elements=None, **kwargs):
		super(ListSanitizer, self).__init__(**kwargs)
		self.sanitizer = sanitizer
		self.min_elements = min_elements
		self.max_elements = max_elements

	def _sanitize(self, value, name, further_arguments):
		if not isinstance(value, list):
			self.raise_formatted_validation_error(_('Not a "list"'), name, type(value).__name__)

		if self.min_elements is not None and len(value) < self.min_elements:
			self.raise_validation_error(_('Must have at least %(min_elements)d element(s)'))
		if self.max_elements is not None and len(value) > self.max_elements:
			self.raise_validation_error(_('May have at most %(max_elements)d element(s)'))

		if self.sanitizer is None:
			# no sanitizer given: we can only
			# check instance and min/max elements
			return value

		multi_error = MultiValidationError()
		altered_value = []
		for i, item in enumerate(value):
			name = 'Element #%d' % i
			try:
				altered_value.append(self.sanitizer.sanitize(name, {name: item}))
			except ValidationError as e:
				multi_error.add_error(e, i)
		if multi_error.has_errors():
			raise multi_error
		return altered_value


class BooleanSanitizer(Sanitizer):

	'''BooleanSanitizer makes sure that the value is a bool.
	It converts other data types if possible.
	'''

	def _sanitize(self, value, name, further_arguments):
		try:
			return bool(value)
		except:
			self.raise_validation_error(_('Cannot be converted to a boolean'))


class IntegerSanitizer(Sanitizer):

	'''IntegerSanitizer makes sure that the value is an int.
	It converts other data types if possible and is able
	to validate boundaries.

	You can give the same parameters as the base class.
	Plus:

	:param int minimum: minimal value allowed
	:param bool minimum_strict: if the value must be > minimum
		(>= otherwise)
	:param int maximum: maximal value allowed
	:param bool maximum_strict: if the value must be < maximum
		(<= otherwise)
	'''

	def __init__(self, minimum=None, maximum=None, minimum_strict=None, maximum_strict=None, **kwargs):
		super(IntegerSanitizer, self).__init__(**kwargs)
		self.minimum = minimum
		self.maximum = maximum
		self.minimum_strict = minimum_strict
		self.maximum_strict = maximum_strict

	def _sanitize(self, value, name, further_arguments):
		try:
			value = int(value)
			if not isinstance(value, int):
				# value is of type 'long'
				raise ValueError
		except (ValueError, TypeError):
			self.raise_validation_error(_('Cannot be converted to a number'))
		else:
			if self.minimum is not None:
				if self.minimum_strict:
					if not value > self.minimum:
						self.raise_validation_error(_('Should stay %s') % '> %(minimum)d')
				else:
					if not value >= self.minimum:
						self.raise_validation_error(_('Should stay %s') % '>= %(minimum)d')
			if self.maximum is not None:
				if self.maximum_strict:
					if not value < self.maximum:
						self.raise_validation_error(_('Should stay %s') % '< %(maximum)d')
				else:
					if not value <= self.maximum:
						self.raise_validation_error(_('Should stay %s') % '<= %(maximum)d')
			return value


class SearchSanitizer(Sanitizer):

	''' Baseclass for other Sanitizers that are used for a simple search.
	That means that everything is escaped except for asterisks that are
	considered as wildcards for any number of characters. (If
	:attr:`~SearchSanitizer.use_asterisks` is True, which is default)

	Handles adding of asterisks and and some simple sanity checks.
	Real logic is done in a to-be-overridden method named
	:meth:`~SearchSanitizer._escape_and_return`.

	Currently used for :class:`~LDAPSearchSanitizer` and
	:class:`~PatternSanitizer`.

	Like the Baseclass of all Sanitizers, it accepts only keyword-arguments
	(derived classes may vary). You may specify the same as in the Baseclass
	plus:

	:param bool add_asterisks: add asterisks at the beginning and the end
		of the value if needed. Examples:

		* "string" -> "\*string*"
		* "" -> "*"
		* "string*" -> "string*"

		Default: True
	:param int max_number_of_asterisks: An error will be raised if
		the number of * in the string exceeds this limit. Useful because
		searching with too many of these patterns in a search query
		can be very expensive. Note that * from
		:attr:`~SearchSanitizer.add_asterisks` do count. *None* means an
		arbitrary number is allowed. Default: 5
	:param bool use_asterisks: treat asterisks special, i.e. as a
		substring of arbitrary length. If *False*, it will be escaped as
		any other character. If *False* the defaults change:

		* :attr:`~SearchSanitizer.add_asterisks` to *False*
		* :attr:`~SearchSanitizer.max_number_of_asterisks` to *None*.

		Default: True
	'''

	def __init__(self, **kwargs):
		self.use_asterisks = kwargs.get('use_asterisks', True)
		if self.use_asterisks:
			self.add_asterisks = kwargs.get('add_asterisks', True)
			self.max_number_of_asterisks = kwargs.get('max_number_of_asterisks', 5)
		else:
			self.add_asterisks = kwargs.get('add_asterisks', False)
			self.max_number_of_asterisks = kwargs.get('max_number_of_asterisks', None)
		super(SearchSanitizer, self).__init__(**kwargs)

	def _escape_and_return(self, value):
		return value

	def _sanitize(self, value, name, further_fields):
		if value is None:
			value = ''
		value = str(value)
		if self.use_asterisks:
			value = re.sub(r'\*+', '*', value)
		if self.add_asterisks and '*' not in value:
			if not value.startswith('*'):
				value = '*%s' % value
			if not value.endswith('*'):
				value = '%s*' % value
		if self.max_number_of_asterisks is not None:
			if value.count('*') > self.max_number_of_asterisks:
				# show the possibly changed value
				self.raise_formatted_validation_error(_('The maximum number of asterisks (*) in the search string is %(max_number_of_asterisks)d'), name, value)
		return self._escape_and_return(value)


class LDAPSearchSanitizer(SearchSanitizer):

	'''Sanitizer for LDAP-Searches. Everything that
	could possibly confuse an LDAP-Search is escaped
	except for \*.
	'''

	ESCAPED_WILDCARD = ldap.filter.escape_filter_chars('*')

	def _escape_and_return(self, value):
		value = ldap.filter.escape_filter_chars(value)
		if self.use_asterisks:
			value = value.replace(self.ESCAPED_WILDCARD, '*')
		return value


class PatternSanitizer(SearchSanitizer):

	'''PatternSanitizer converts the input into a regular expression.
	It can handle anything (through the inputs __str__ method), but
	only strings seem to make sense.

	The input should be a string with asterisks (*) if needed. An
	askterisk stands for anything at any length (regular expression: .*).

	The sanitizer escapes the input, replaces * with .* and applies
	the params.

	You can give the same parameters as the base class.

	If you specify a string as :attr:`~Sanitizer.default`, it will be
	compiled to a regular expression. Hints:
	default='.*' -> matches everything;
	default='(?!)' -> matches nothing

	Plus:

	:param bool ignore_case: pattern is compiled with re.IGNORECASE flag
		to search case insensitive.
	:param bool multiline: pattern is compiled with re.MULTILINE flag
		to search across multiple lines.
	'''

	def __init__(self, ignore_case=True, multiline=True, **kwargs):
		default = kwargs.get('default')
		if isinstance(default, basestring):
			default = re.compile(default)
		kwargs['default'] = default
		super(PatternSanitizer, self).__init__(**kwargs)
		self.ignore_case = ignore_case
		self.multiline = multiline

	def __deepcopy__(self, memo):
		new = PatternSanitizer(
			self.ignore_case,
			self.multiline,
			use_asterisks=self.use_asterisks,
			add_asterisks=self.add_asterisks,
			max_number_of_asterisks=self.max_number_of_asterisks,
			further_arguments=copy.copy(self.further_arguments),  # string...
			required=self.required,
			default=self.default,  # None or non-copyable pattern
			may_change_value=self.may_change_value,
		)
		return new

	def _escape_and_return(self, value):
		value = re.escape(value)
		if self.use_asterisks:
			value = value.replace(r'\*', '.*')
		flags = 0
		if self.ignore_case:
			flags = flags | re.IGNORECASE
		if self.multiline:
			flags = flags | re.MULTILINE
		return re.compile('^%s$' % value, flags)


class StringSanitizer(Sanitizer):

	''' StringSanitizer makes sure that the input is a string.
	The input can be validated by a regular expression and by string length

	:param regex_pattern: a regex pattern or a string which will be
		compiled into a regex pattern
	:param int re_flags: additional regex flags for the regex_pattern
		which will be compiled if :attr:`~StringSanitizer.regex_pattern`
		is a string
	:param int minimum: the minimum length of the string
	:param int maximum: the maximum length of the string
	:type regex_pattern: basestring or re._pattern_type
	'''

	def __init__(self, regex_pattern=None, re_flags=0, minimum=None, maximum=None, **kwargs):
		super(StringSanitizer, self).__init__(**kwargs)
		if isinstance(regex_pattern, basestring):
			regex_pattern = re.compile(regex_pattern, flags=re_flags)
		self.minimum = minimum
		self.maximum = maximum
		self.regex_pattern = regex_pattern

	def __deepcopy__(self, memo):
		new = StringSanitizer(
			self.regex_pattern,  # None or non-copyable pattern
			0,
			self.minimum,
			self.maximum,
			further_arguments=copy.copy(self.further_arguments),  # strings
			required=self.required,
			default=self.default,
			may_change_value=self.may_change_value,
		)
		return new

	def _sanitize(self, value, name, further_args):
		if not isinstance(value, basestring):
			self.raise_validation_error(_('Value is not a string'))

		if self.minimum and len(value) < self.minimum:
			self.raise_validation_error(_('Value is too short, it has to be at least of length %(minimum)d'))

		if self.maximum and len(value) > self.maximum:
			self.raise_validation_error(_('Value is too long, it has to be at most of length %(maximum)d'))

		if self.regex_pattern and not self.regex_pattern.search(value):
			self.raise_validation_error(_('Value is invalid'))

		return value


class DNSanitizer(StringSanitizer):

	''' DNSanitizer is a sanitizer that checks if the value has correct LDAP
	Distinguished Name syntax '''

	def _sanitize(self, value, name, further_args):
		value = super(DNSanitizer, self)._sanitize(value, name, further_args)
		try:
			ldap.dn.str2dn(value)
		except ldap.DECODING_ERROR:
			self.raise_validation_error(_('Value is not a LDAP DN.'))
		return value


class EmailSanitizer(StringSanitizer):

	''' EmailSanitizer is a very simple sanitizer that checks
	the very basics of an email address: At least 3 characters and
	somewhere in the middle has to be an @-sign '''

	def __init__(self, **kwargs):
		super(EmailSanitizer, self).__init__(r'.@.', **kwargs)


class ChoicesSanitizer(Sanitizer):

	''' ChoicesSanitizer makes sure that the input is in a given set of
	choices.

	:param [object] choices: the allowed choices used.
	'''

	def __init__(self, choices, **kwargs):
		super(ChoicesSanitizer, self).__init__(**kwargs)
		# makes sure to have an iterable and unifies errors msg
		# because list has a different representation than tuple
		self.choices = list(choices)

	def _sanitize(self, value, name, further_args):
		for choice in self.choices:
			if choice == value:
				# return element from choices
				# not value itself: 1 == True
				return choice
		else:
			self.raise_validation_error(_('Value has to be one of %(choices)r'))


class MappingSanitizer(ChoicesSanitizer):

	''' MappingSanitizer makes sure that the input is in a key in a
	dictionary and returns the corresponding value.

	:param mapping: the dictionary that is used for sanitizing
	:type mapping: {object : object}
	'''

	def __init__(self, mapping, **kwargs):
		try:
			# sort allowed values to have reproducible error messages
			# sorted works with every base data type, even inter-data type!
			choices = sorted(mapping.keys())
		except:
			# but who knows...
			choices = mapping.keys()
		super(MappingSanitizer, self).__init__(choices, **kwargs)
		self.mapping = mapping

	def _sanitize(self, value, name, further_args):
		value = super(MappingSanitizer, self)._sanitize(value, name, further_args)
		return self.mapping[value]


__all__ = ['UnformattedValidationError', 'ValidationError', 'MultiValidationError', 'Sanitizer', 'DictSanitizer', 'ListSanitizer', 'BooleanSanitizer', 'IntegerSanitizer', 'SearchSanitizer', 'LDAPSearchSanitizer', 'PatternSanitizer', 'StringSanitizer', 'EmailSanitizer', 'ChoicesSanitizer', 'MappingSanitizer']
