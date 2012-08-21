#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Sanitizer Classes used in decorator
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

from univention.lib.i18n import Translation
_ = Translation( 'univention.management.console' ).translate

class UnformattedValidationError(Exception):
	"""
	Unformatted error raised when the sanitizer finds a value he
	cannot use at all (e.g. letters when an int is expected).
	Should be "enhanced" to a ValidationError.
	"""
	def __init__(self, message, kwargs):
		self.message = message
		self.kwargs = kwargs

	def __str__(self):
		return self.message

class ValidationError(Exception):
	"""
	Error raised when the sanitizer finds a value he cannot use at all
	(e.g. letters when an int is expected).
	"""
	def __init__(self, message, name, value):
		self.message = message
		self.name = name
		self.value = value

	def __str__(self):
		return self.message

class Sanitizer(object):
	'''
	Base class of all sanitizers.

	:param [string] further_arguments: names of arguments that should be
	  passed along with the actual argument in order to return something
	  reasonable.
	:param bool required: if the argument is required.
	:param object default: if not given and not
	  :attr:`~Sanitizer.required` but :attr:`~Sanitizer.may_change_value`
	  default is returned. Note that this value is not passing the
	  sanitizing procedure, so make sure to be able to handle it.
	:param bool may_change_value: if the process of sanitizing is allowed
	  to alter *request.options*. If not, the sanitizer can still be used
	  for validation.
	'''
	def __init__(self, further_arguments=None, required=False, default=None, may_change_value=False):
		self.further_arguments = further_arguments
		self.required = required
		self.default = default
		self.may_change_value = may_change_value

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
				if self.may_change_value:
					return self.default
				else:
					return None
		value = options[name]
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

		:param dict **kwargs: additional arguments for formatting
		'''
		raise UnformattedValidationError(msg, kwargs)

	def raise_formatted_validation_error(self, msg, name, value, **kwargs):
		'''Used to more or less uniformly raise a
		:class:`~ValidationError`. *name* and *value* need to passed
		because the sanitizer should be thread safe.

		:param string msg: error message
		:param string name: name of the argument
		:param object value: the argument which caused the error
		:param dict **kwargs: additional arguments for formatting
		'''
		format_dict = {'value' : value, 'name' : name}
		format_dict.update(kwargs)
		format_dict.update(self.__dict__)
		msg = '%(name)s (%(value)r): ' + msg
		raise ValidationError(msg % format_dict, name, value)

class DictSanitizer(Sanitizer):
	''' DictSanitizer makes sure that the value is a dict and sanitizes its fields.

	You can give the same parameters as the base class.
	Plus:

	:param sanitizers: contains a sanitizer for every key of the dict
	:param bool allow_other_keys: if other keys than those in
	:attr:`~DictSanitizer.sanitizers` are allowed.
	:type sanitizers: {string : `~Sanitizer`}.
	'''
	def __init__(self, sanitizers, allow_other_keys=True, further_arguments=None, required=False, default=None, may_change_value=True):
		super(DictSanitizer, self).__init__(further_arguments, required, default, may_change_value)
		self.sanitizers = sanitizers
		self.allow_other_keys = allow_other_keys

	def _sanitize(self, value, name, further_arguments):
		if not isinstance(value, dict):
			self.raise_formatted_validation_error(_('Not a "dict"'), name, type(value).__name__)

		if not self.allow_other_keys and any(key not in self.sanitizers for key in value):
			self.raise_validation_error(_('Has more than the allowed keys'))

		altered_value = copy.deepcopy(value)

		for attr, sanitizer in self.sanitizers.iteritems():
			altered_value[attr] = sanitizer.sanitize(attr, value)

		return altered_value

class ListSanitizer(Sanitizer):
	''' ListSanitizer makes sure that the value is a list and sanitizes its elements.

	You can give the same parameters as the base class.
	Plus:

	:param sanitizer: a Sanitize class for every list element
	:param bool may_change_value: only validate input or change the list input
	:type sanitizer: `~Sanitizer`.
	'''
	def __init__(self, sanitizer, further_arguments=None, required=False, default=None, may_change_value=True):
		super(ListSanitizer, self).__init__(further_arguments, required, default, may_change_value)
		self.sanitizer = sanitizer

	def _sanitize(self, value, name, further_arguments):
		if not isinstance(value, list):
			self.raise_formatted_validation_error(_('Not a "list"'), name, type(value).__name__)

		altered_value = []
		for i, item in enumerate(value):
			name = 'Element #%d' % i
			result = self.sanitizer.sanitize(name, {name : item})
			altered_value.append(result)
		return altered_value

class IntegerSanitizer(Sanitizer):
	'''IntegerSanitizer makes sure that the value is an int.
	It converts other data types if possible and is able
	to validate boundaries.

	You can give the same parameters as the base class without
	:attr:`~Sanitizer.may_change_value`, as it always may.
	Plus:

	:param int minimum: minimal value allowed
	:param bool minimum_strict: if the value must be > minimum
	  (>= otherwise)
	:param int maximum: maximal value allowed
	:param bool maximum_strict: if the value must be < maximum
	  (<= otherwise)
	'''
	def __init__(self, further_arguments=None, required=False, default=None,
			minimum=None, maximum=None, minimum_strict=None, maximum_strict=None):
		super(IntegerSanitizer, self).__init__(further_arguments, required, default, may_change_value=True)
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

class PatternSanitizer(Sanitizer):
	'''PatternSanitizer converts the input into a regular expression.
	It can handle anything (through the inputs __str__ method), but
	only strings seem to make sense.

	The input should be a string with asterisks (*) if needed. An
	askterisk stands for anything at any length (regular expression: .*).

	The sanitizer escapes the input, replaces * with .* and applies
	the params.

	You can give the same parameters as the base class without
	:attr:`~Sanitizer.may_change_value`, as it always may.

	If you specify a string as :attr:`~Sanitizer.default`, it will be
	compiled to a regular expression. Hints:
	default='.*' -> matches everything
	default='(?!)' -> matches nothing

	Plus:

	:param bool add_asterisks: add asterisks at the beginning and the end
	  of the value if needed. "string" -> "\*string*", "" -> "*"
	:param bool ignore_case: pattern is compiled with re.IGNORECASE flag
	  to search case insensitive.
	'''
	def __init__(self, add_asterisks=True, ignore_case=True, further_arguments=None, required=False, default=None):
		if isinstance(default, basestring):
			default = re.compile(default)
		super(PatternSanitizer, self).__init__(further_arguments, required, default, may_change_value=True)
		self.add_asterisks = add_asterisks
		self.ignore_case = ignore_case

	def _sanitize(self, value, name, further_fields):
		if value is None:
			value = ''
		try:
			value = str(value)
			value = re.sub(r'\*+', '*', value)
			if self.add_asterisks:
				if not value.startswith('*'):
					value = '*%s' % value
				if not value.endswith('*'):
					value = '%s*' % value
			value = re.escape(value)
			value = value.replace(r'\*', '.*')
			flags = 0
			if self.ignore_case:
				flags = flags | re.IGNORECASE
			return re.compile(value, flags)
		except:
			# although i cant think of a case were this should fail
			self.raise_validation_error(_('Not a valid search pattern'))

class StringSanitizer(Sanitizer):
	''' StringSanitizer makges sure that the input is a string.
		The input can be validated by a regular expression and by string length

		:param basestring|SRE_Pattern regex_pattern: a regex pattern or a string which will be compiled into a regex pattern
		:param int re_flags: additional regex flags for the regex_pattern which will be compiled if regex_pattern is a string
		:param int minimum: the minimum length of the string
		:param int maximum: the maximum length of the string
	'''
	def __init__(self, regex_pattern=None, re_flags=0, minimum=None, maximum=None, further_arguments=None, required=False, default=''):
		super(StringSanitizer, self).__init__(further_arguments, required, default, may_change_value=True)
		if isinstance(regex_pattern, basestring):
			regex_pattern = re.compile(regex_pattern, flags = re_flags)
		self.minimum = minimum
		self.maximum = maximum
		self.regex_pattern = regex_pattern

	def _sanitize(self, value, name, further_args):
		if not isinstance(value, basestring):
			self.raise_validation_error(_('Value is not a string'))

		if self.minimum and len(value) < self.minimum:
			self.raise_validation_error(_('Value is too short, it have to be of length %(minimum)d'))

		if self.maximum and len(value) > self.maximum:
			self.raise_validation_error(_('Value is too long, it have to be of length %(maximum)d'))

		if self.regex_pattern and not self.regex_pattern.match(value):
			self.raise_validation_error(_('Value is invalid'))
