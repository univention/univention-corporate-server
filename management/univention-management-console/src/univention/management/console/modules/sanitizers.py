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
	:param object default: if not given and not
	  :attr:`~Sanitizer.required` but :attr:`~Sanitizer.may_change_value`
	  default is returned. Note that this value is not passing the
	  sanitizing procedure, so make sure to be able to handle it.
	  Default: *None*
	:param bool may_change_value: if the process of sanitizing is allowed
	  to alter *request.options*. If not, the sanitizer can still be used
	  for validation. Default: *True*
	'''
	def __init__(self, **kwargs):
		self.further_arguments = kwargs.get('further_arguments', None)
		self.required = kwargs.get('required', False)
		self.default = kwargs.get('default', None)
		self.may_change_value = kwargs.get('may_change_value', True)

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
		format_dict = {'value' : value, 'name' : name}
		format_dict.update(kwargs)
		format_dict.update(self.__dict__)
		msg = '%(name)s (%(value)r): ' + msg
		raise ValidationError(msg % format_dict, name, value)

class DictSanitizer(Sanitizer):
	''' DictSanitizer makes sure that the value is a dict and sanitizes its fields.

	You can give the same parameters as the base class.
	Plus:

	:param sanitizers: will be applied to the content of the sanitized dict
	:param bool allow_other_keys: if other keys than those in
	  :attr:`~DictSanitizer.sanitizers` are allowed.
	:type sanitizers: {string : :class:`~Sanitizer`}
	'''
	def __init__(self, sanitizers, allow_other_keys=True, **kwargs):
		super(DictSanitizer, self).__init__(**kwargs)
		self.sanitizers = sanitizers
		self.allow_other_keys = allow_other_keys

	def _sanitize(self, value, name, further_arguments):
		if not isinstance(value, dict):
			self.raise_formatted_validation_error(_('Not a "dict"'), name, type(value).__name__)

		if not self.allow_other_keys and any(key not in self.sanitizers for key in value):
			self.raise_validation_error(_('Has more than the allowed keys'))

		altered_value = copy.deepcopy(value)

		multi_error = MultiValidationError()
		for attr, sanitizer in self.sanitizers.iteritems():
			try:
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

	:param sanitizer: sanitizes each of the sanitized list's elements
	:param int min_elements: must have at least this number of elements
	:param int max_elements: must have at most this number of elements
	:type sanitizer: :class:`~Sanitizer`
	'''
	def __init__(self, sanitizer, min_elements=None, max_elements=None, **kwargs):
		super(ListSanitizer, self).__init__(**kwargs)
		self.sanitizer = sanitizer
		self.min_elements = min_elements
		self.max_elements = max_elements

	def _sanitize(self, value, name, further_arguments):
		if not isinstance(value, list):
			self.raise_formatted_validation_error(_('Not a "list"'), name, type(value).__name__)

		if self.min_elements is not None and len(value) < self.min_elements:
			self.raise_validation_error(_('Must have at least %(min_elements)d elements'))
		if self.max_elements is not None and len(value) > self.max_elements:
			self.raise_validation_error(_('Must have at most %(max_elements)d elements'))

		multi_error = MultiValidationError()
		altered_value = []
		for i, item in enumerate(value):
			name = 'Element #%d' % i
			try:
				altered_value.append(self.sanitizer.sanitize(name, {name : item}))
			except ValidationError as e:
				multi_error.add_error(e, i)
		if multi_error.has_errors():
			raise multi_error
		return altered_value

class BooleanSanitizer(Sanitizer):
	'''IntegerSanitizer makes sure that the value is a bool.
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

class PatternSanitizer(Sanitizer):
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
	default='.*' -> matches everything
	default='(?!)' -> matches nothing

	Plus:

	:param bool add_asterisks: add asterisks at the beginning and the end
	  of the value if needed. "string" -> "\*string*", "" -> "*"
	:param bool ignore_case: pattern is compiled with re.IGNORECASE flag
	  to search case insensitive.
	:param int max_number_of_asterisks: An error will be raised if
	  the number of * in the pattern exceeds this limit. Useful because
	  searching with too many of these patterns in a regular expression
	  can be very expensive. Note that * from
	  :attr:`~PatternSanitizer.add_asterisks` do count. *None* means an
	  arbitrary number is allowed.
	'''
	def __init__(self, add_asterisks=True, ignore_case=True, max_number_of_asterisks=5, **kwargs):
		default = kwargs.get('default')
		if isinstance(default, basestring):
			default = re.compile(default)
		kwargs['default'] = default
		super(PatternSanitizer, self).__init__(**kwargs)
		self.add_asterisks = add_asterisks
		self.ignore_case = ignore_case
		self.max_number_of_asterisks = max_number_of_asterisks

	def __deepcopy__(self, memo):
		new = PatternSanitizer(
			self.add_asterisks,
			self.ignore_case,
			self.max_number_of_asterisks,
			further_arguments=copy.copy(self.further_arguments),
			required=self.required,
			default=None,
			may_change_value=self.may_change_value,
		)
		try:
			new.default = re.compile(default.pattern, default.flags)
		except:
			# None?
			pass
		return new

	def _sanitize(self, value, name, further_fields):
		if value is None:
			value = ''
		value = str(value)
		value = re.sub(r'\*+', '*', value)
		if self.add_asterisks:
			if not value.startswith('*'):
				value = '*%s' % value
			if not value.endswith('*'):
				value = '%s*' % value
		if self.max_number_of_asterisks is not None:
			if value.count('*') > self.max_number_of_asterisks:
				# show the possibly changed value
				self.raise_formatted_validation_error(_('The maximum number of asterisks (*) in the search string is %(max_number_of_asterisks)d'), name, value)
		value = re.escape(value)
		value = value.replace(r'\*', '.*')
		flags = 0
		if self.ignore_case:
			flags = flags | re.IGNORECASE
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
			regex_pattern = re.compile(regex_pattern, flags = re_flags)
		self.minimum = minimum
		self.maximum = maximum
		self.regex_pattern = regex_pattern

	def __deepcopy__(self, memo):
		new = StringSanitizer(
			None,
			0,
			self.minimum,
			self.maximum,
			further_arguments=copy.copy(self.further_arguments),
			required=self.required,
			default=self.default,
			may_change_value=self.may_change_value,
		)
		try:
			new.regex_pattern = re.compile(regex_pattern.pattern, regex_pattern.flags)
		except:
			# None?
			pass
		return new

	def _sanitize(self, value, name, further_args):
		if not isinstance(value, basestring):
			self.raise_validation_error(_('Value is not a string'))

		if self.minimum and len(value) < self.minimum:
			self.raise_validation_error(_('Value is too short, it has to be at least of length %(minimum)d'))

		if self.maximum and len(value) > self.maximum:
			self.raise_validation_error(_('Value is too long, it has to be at most of length %(maximum)d'))

		if self.regex_pattern and not self.regex_pattern.match(value):
			self.raise_validation_error(_('Value is invalid'))

		return value

class MappingSanitizer(Sanitizer):
	''' MappingSanitizer makes sure that the input is in a key in a
	dictionary and returns the corresponding value.
	
	:param mapping: the dictionary that is used for sanitizing
	:type mapping: {object : object}
	'''
	def __init__(self, mapping, **kwargs):
		super(MappingSanitizer, self).__init__(**kwargs)
		try:
			# sorted works with every base data type, even inter-data type!
			self.sorted_keys = sorted(mapping.keys())
		except:
			# but who knows...
			self.sorted_keys = mapping.keys()
		self.mapping = mapping

	def _sanitize(self, value, name, further_args):
		try:
			return self.mapping[value]
		except KeyError:
			self.raise_validation_error(_('Value has to be in %(sorted_keys)r'))

class ChoicesSanitizer(MappingSanitizer):
	''' MappingSanitizer makes sure that the input is in a given set of
	choices.
	
	:param [object] choices: the allowed choices used.
	'''
	def __init__(self, choices, **kwargs):
		mapping = dict([(choice, choice) for choice in choices])
		super(ChoiceSanitizer, self).__init__(mapping, **kwargs)

