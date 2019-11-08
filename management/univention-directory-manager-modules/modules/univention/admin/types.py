# -*- coding: utf-8 -*-
"""
|UDM| type definitions.
"""
# Copyright 2019 Univention GmbH
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

from __future__ import absolute_import

import inspect
import time
import datetime

import ldap.dn

import univention.admin.uexceptions
from univention.admin import localization
import univention.debug as ud

translation = localization.translation('univention/admin')
_ = translation.translate


class TypeHint(object):
	"""

	"""
	_python_types = object

	@property
	def _json_type(self):
		# in most cases, the python type is equivalent to the JSON type
		return self._python_types

	_openapi_type = None
	_openapi_format = None
	_openapi_regex = None
	_openapi_example = None
	_openapi_readonly = None
	_openapi_writeonly = None
	_openapi_nullable = True  # everything which can be removed is nullable

	_umc_widget = None
	_umc_widget_size = None
	_umc_widget_search = None

	_html_element = None
	_html_input_type = None

	_encoding = None
	_minimum = float('-inf')
	_maximum = float('inf')

	_required = False
	_default_value = None
	_default_search_value = None

	_only_printable = False
	_allow_empty_value = False
	_encodes_none = False
	"""None is a valid value for the syntax class, otherwise None means remove"""
	_blacklist = ()
	# _error_message

	_dependencies = None

	def __init__(self, property, property_name):
		self.property = property
		self.property_name = property_name
		self.syntax = self._syntax

	@property
	def _syntax(self):
		# ensure we have an instance of the syntax class and not the type
		syntax = self.property.syntax
		return syntax() if isinstance(syntax, type) else syntax

	def decode(self, value):
		"""
		Decode the given value from an UDM object's property into a python type.
		This must be graceful. Invalid values set at UDM object properties should not cause an exception!

		.. note:: Do not overwrite in subclass!

		.. seealso:: overwrite :func:`univention.admin.types.TypeHint.decode_value` instead.
		"""
		if value is None:
			return
		return self.decode_value(value)

	def encode(self, value):
		"""Encode a value of python type into a string / list / None / etc. suitable for setting at the UDM object.

		.. note:: Do not overwrite in subclass!

		.. seealso:: overwrite :func:`univention.admin.types.TypeHint.encode_value` instead.
		"""
		if value is None and not self._encodes_none:
			return

		self.type_check(value)
		self.type_check_subitems(value)
		return self.encode_value(value)

	def decode_json(self, value):
		return self.to_json_type(self.decode(value))

	def encode_json(self, value):
		return self.encode(self.from_json_type(value))

	def to_json_type(self, value):
		"""Transform the value resulting from :func:`self.decode` into something suitable to transmit via JSON.

			For example, a python datetime.date object into the JSON string with a date format "2019-08-30".
		"""
		if value is None:
			return
		value = self._to_json_type(value)
		if isinstance(value, bytes):
			# fallback for wrong implemented types
			# JSON cannot handle non-UTF-8 bytes
			value = value.decode('utf-8', 'strict')
		return value

	def from_json_type(self, value):
		"""Transform a value from a JSON object into the internal python type.

			For example, converts a JSON string "2019-08-30" into a python datetime.date object.

			.. warning:: When overwriting the type must be checked!
		"""
		if value is None:
			return
		self.type_check_json(value)
		value = self._from_json_type(value)
		return value

	def decode_value(self, value):
		"""Decode the value into a python object.

		.. note:: suitable for subclassing.
		"""
		try:
			return self.syntax.parse(value)
		except univention.admin.uexceptions.valueError as exc:
			ud.debug(ud.ADMIN, ud.WARN, 'ignoring invalid property %s value=%r is invalid: %s' % (self.property_name, value, exc))
			return value

	def encode_value(self, value):
		"""Encode the value into a UDM property value.

		.. note:: suitable for subclassing.
		"""
		return self.syntax.parse(value)

	def _from_json_type(self, value):
		return value

	def _to_json_type(self, value):
		return value

	def type_check(self, value, types=None):
		"""Checks if the value has the correct python type"""
		if not isinstance(value, types or self._python_types):
			must = '%s (%s)' % (self._openapi_type, self._openapi_format) if self._openapi_format else '%s' % (self._openapi_type,)
			actual = type(value).__name__
			ud.debug(ud.ADMIN, ud.WARN, '%r: Value=%r %r' % (self.property_name, value, type(self).__name__))
			raise univention.admin.uexceptions.valueInvalidSyntax(_('Value must be of type %s not %s.') % (must, actual))

	def type_check_json(self, value):
		self.type_check(value, self._json_type)

	def type_check_subitems(self, value):
		pass

	def tostring(self, value):
		"""A printable representation for e.g. the CLI or grid columns in UMC"""
		if self.property.multivalue:
			return [self.syntax.tostring(val) for val in value]
		else:
			return self.syntax.tostring(value)

	def parse_command_line(self, value):
		"""Parse a string from the command line"""
		return self.syntax.parse_command_line(value)

	def get_openapi_definition(self):
		return dict((key, value) for key, value in self.openapi_definition().items() if value is not None and value not in (float('inf'), -float('inf')))

	def openapi_definition(self):
		definition = {
			'type': self._openapi_type,
		}
		if self._openapi_type in ('string', 'number', 'integer'):
			definition['format'] = self._openapi_format
		if self._openapi_type == 'string':
			definition['pattern'] = self._openapi_regex
			definition['minLength'] = self._minimum
			definition['maxLength'] = self._maximum
		definition['example'] = self._openapi_example
		definition['readOnly'] = self._openapi_readonly
		definition['writeOnly'] = self._openapi_writeonly
		definition['nullable'] = self._openapi_nullable
		return definition

	def get_choices(self):
		pass

	def has_dynamic_choices(self):
		pass

	def get_dynamic_choices(self):
		pass

	def reload_dynamic_choices(self):
		pass

	@classmethod
	def detect(cls, property, name):
		"""Detect the :class:`univention.admin.types.TypeHint` type of a property automatically.

		We need this to be backwards compatible, with handlers, we don't influence.

		First considered is the `property.type_class` which can be explicit set in the module handler.

		Otherwise, it depends on wheather the field is multivalue or not:
		multivalue: A unordered :class:`Set` of `syntax.type_class` items
		singlevalue: `syntax.type_class` is used.
		"""
		if property.type_class:
			return property.type_class(property, name)

		syntax = property.syntax() if inspect.isclass(property.syntax) else property.syntax
		type_class = syntax.type_class
		if not type_class:
			ud.debug(ud.ADMIN, ud.WARN, 'Unknown type for property %r: %s' % (name, syntax.name))
			type_class = cls

		if not property.multivalue:
			return type_class(property, name)
		else:
			if syntax.type_class_multivalue:
				return syntax.type_class_multivalue(property, name)

		# create a default type inheriting from a set
		# (LDAP attributes do not have a defined order - unless the "ordered" overlay module is activated and the attribute schema defines it)
		class MultivaluePropertyType(SetType):
			item_type = type_class

		return MultivaluePropertyType(property, name)


class NoneType(TypeHint):
	_python_types = type(None)
	_openapi_type = 'void'
	_encodes_none = True


class BooleanType(TypeHint):
	_python_types = bool
	_openapi_type = 'boolean'

	def decode_value(self, value):
		try:
			if self.syntax.parse(True) == value:
				return True
			elif self.syntax.parse(False) == value:
				return False
			elif self.syntax.parse(None) == value:
				return None
		except univention.admin.uexceptions.valueError:
			pass
		ud.debug(ud.ADMIN, ud.WARN, '%s: %s: not a boolean: %r' % (self.property_name, self.syntax.name, value,))
		return value


class TriBooleanType(BooleanType):

	_encodes_none = True
	_python_types = (bool, type(None))


class IntegerType(TypeHint):
	_python_types = (int, long)
	_openapi_type = 'integer'
	# _openapi_format: int32, int64

	def decode_value(self, value):
		try:
			value = int(value)
		except ValueError:
			ud.debug(ud.ADMIN, ud.WARN, '%s: %s: not a integer: %r' % (self.property_name, self.syntax.name, value,))
		return value


class NumberType(TypeHint):
	_python_types = float
	_openapi_type = 'number'
	_openapi_format = 'double'  # or 'float'


class StringType(TypeHint):
	_python_types = unicode
	_encoding = 'UTF-8'
	_openapi_type = 'string'

	def decode_value(self, value):
		if isinstance(value, bytes):
			value = value.decode(self._encoding, 'strict')
		return value


class Base64Type(StringType):
	_openapi_format = 'byte'


class PasswordType(StringType):
	_openapi_format = 'password'
	_openapi_example = 'univention'  # :-D
	_openapi_readonly = True


class DistinguishedNameType(StringType):
	_openapi_format = 'ldap-dn'
	_openapi_example = 'dc=example,dc=net'

	def encode_value(self, value):
		value = super(DistinguishedNameType, self).encode_value(value)
		try:
			return ldap.dn.dn2str(ldap.dn.str2dn(value))
		except ldap.DECODING_ERROR:
			raise univention.admin.uexceptions.valueInvalidSyntax(_('The LDAP DN is invalid.'))


class LDAPFilterType(StringType):
	_openapi_format = 'ldap-filter'


class EMailAddressType(StringType):
	_openapi_format = 'email'
	_minimum = 3


class BinaryType(TypeHint):
	"""
	.. warning:: Using this type bloats up the JSON value with a high factor for non ascii data.
	.. seealso:: use `univention.admin.types.Base64Type` instead
	"""
	_python_types = bytes
	_encoding = 'ISO8859-1'

	# It is not possible to transmit binary data via JSON. in JSON everything needs to be UTF-8!
	_json_type = unicode
	_json_encoding = 'ISO8859-1'

	_openapi_type = 'string'
	_openapi_format = 'binary'

	def _to_json_type(self, value):
		return value.decode(self._json_encoding, 'strict')

	def _from_json_type(self, value):
		try:
			return value.encode(self._json_encoding, 'strict')
		except UnicodeEncodeError:
			raise univention.admin.uexceptions.valueInvalidSyntax(_('Binary data have invalid encoding (expected: %s).') % (self._encoding,))


class DateType(StringType):
	_python_types = datetime.date
	_json_type = unicode
	_openapi_format = 'date'

	def decode_value(self, value):
		if value == '':
			return
		return self.syntax.to_datetime(value)

	def encode_value(self, value):
		return self.syntax.from_datetime(value)

	def _to_json_type(self, value):  # type: (datetime.date) -> unicode
		return unicode(value.isoformat(), 'ascii')

	def _from_json_type(self, value):  # type: (unicode) -> datetime.date
		try:
			return datetime.date(*time.strptime(value, '%Y-%m-%d')[0:3])
		except ValueError:
			ud.debug(ud.ADMIN, ud.INFO, 'Wrong date format: %r' % (value,))
			raise univention.admin.uexceptions.valueInvalidSyntax(_('Date does not match format "%Y-%m-%d".'))


class TimeType(StringType):
	_python_types = datetime.time
	_json_type = unicode
	_openapi_format = 'time'

	def decode_value(self, value):
		if value == '':
			return
		return self.syntax.to_datetime(value)

	def encode_value(self, value):
		return self.syntax.from_datetime(value)

	def _to_json_type(self, value):  # type: (datetime.time) -> unicode
		return unicode(value.replace(microsecond=0).isoformat(), 'ascii')

	def _from_json_type(self, value):  # type: (unicode) -> datetime.time
		try:
			return datetime.time(*time.strptime(value, '%H:%M:%S')[3:6])
		except ValueError:
			ud.debug(ud.ADMIN, ud.INFO, 'Wrong time format: %r' % (value,))
			raise univention.admin.uexceptions.valueInvalidSyntax(_('Time does not match format "%H:%M:%S".'))


class DateTimeType(StringType):
	"""A DateTime
		syntax classes using this type must support the method from_datetime(), which returns something valid for syntax.parse()
	"""
	_python_types = datetime.datetime
	_json_type = unicode
	_openapi_format = 'date-time'

	def decode_value(self, value):
		if value == '':
			return
		return self.syntax.to_datetime(value)

	def encode_value(self, value):
		return self.syntax.from_datetime(value)

	def _to_json_type(self, value):  # type: (datetime.datetime) -> unicode
		return unicode(' '.join((value.date().isoformat(), value.time().replace(microsecond=0).isoformat())), 'ascii')

	def _from_json_type(self, value):  # type: (unicode) -> datetime.datetime
		try:
			return datetime.datetime(*time.strptime(value, '%Y-%m-%dT%H:%M:%S')[:6])  # FIXME: parse Z at the end
		except ValueError:
			ud.debug(ud.ADMIN, ud.INFO, 'Wrong datetime format: %r' % (value,))
			raise univention.admin.uexceptions.valueInvalidSyntax(_('Datetime does not match format "%Y-%m-%dT%H:%M:%S".'))


class ArrayType(TypeHint):
	_python_types = list
	_openapi_type = 'array'
	_openapi_unique = False


class ListType(ArrayType):
	item_type = None  # must be set in subclasses

	def type_check_subitems(self, value):
		item_type = self.item_type(self.property, self.property_name)
		for item in value:
			item_type.type_check(item)

	def openapi_definition(self):
		definition = super(ListType, self).openapi_definition()
		definition['items'] = self.item_type(self.property, self.property_name).get_openapi_definition()
		definition['minItems'] = self._minimum
		definition['maxItems'] = self._maximum
		definition['uniqueItems'] = self._openapi_unique
		return definition

	def encode_value(self, value):
		item_type = self.item_type(self.property, self.property_name)
		value = [item_type.encode(val) for val in value]
		return [val for val in value if val is not None]

	def decode_value(self, value):
		item_type = self.item_type(self.property, self.property_name)
		return [item_type.decode(val) for val in value]


class SetType(ListType):
	_openapi_unique = True

	# FIXME: this must be done after applying the mapping from property to attribute value
	def __encode_value(self, value):
		# disallow duplicates without re-arranging the order
		# This should prevent that we run into "Type or value exists: attributename: value #0 provided more than once" errors
		# we can't do it completely because equality is defined in the LDAP server schema (e.g. DN syntax: 'dc = foo' equals 'dc=foo' equals 'DC=Foo')
		value = super(SetType, self).encode_value(value)
		if len(value) != len(set(value)):
			raise univention.admin.uexceptions.valueInvalidSyntax(_('Duplicated entries.'))
		return value


class ListOfItems(ArrayType):

	item_types = None  # must be set in subclasses

	@property
	def minimum(self):
		return len(self.item_types)

	@property
	def maximum(self):
		return len(self.item_types)

	def type_check_subitems(self, value):
		if not (self._minimum <= len(value) <= self._maximum):
			univention.admin.uexceptions.valueInvalidSyntax(_('Must have at least %d values.') % (self._minimum,))

		for item_type, item in zip(self.item_types, value):
			item_type = item_type(self.property, self.property_name)
			item_type.type_check(item)

	def encode_value(self, value):
		return [
			item_type(self.property, self.property_name).encode(val)
			for item_type, val in zip(self.item_types, value)
		]

	def decode_value(self, value):
		return [
			item_type(self.property, self.property_name).decode(val)
			for item_type, val in zip(self.item_types, value)
		]

	def openapi_definition(self):
		definition = super(ListOfItems, self).openapi_definition()
		definition['minItems'] = self._minimum
		definition['maxItems'] = self._maximum
		definition['uniqueItems'] = self._openapi_unique
		items = [item.get_openapi_definition() for item in self.item_types]
		if len(set(items)) == 1:
			definition['items'] = items[0]
		else:
			definition['items'] = {
				'oneOf': items
			}
		return definition


class DictionaryType(TypeHint):
	_python_types = dict
	_openapi_type = 'object'

	properties = None

	def decode_value(self, value):
		return self.syntax.todict(value)
		#if not self.syntax.subsyntax_key_value and self.property.multivalue and isinstance(value, (list, tuple)):
		#	value = [self.syntax.todict(val) for val in value]
		#else:
		#	value = self.syntax.todict(value)
		#return value

	def encode_value(self, value):
		return self.syntax.fromdict(value)

	def openapi_definition(self):
		definition = super(DictionaryType, self).openapi_definition()
		definition['properties'] = []
		definition['required'] = []
		if not definition['properties']:
			definition['additionalProperties'] = True
			definition['minProperties'] = self._minimum
			definition['maxProperties'] = self._maximum
			definition.pop('properties', None)
			definition.pop('required', None)
		return definition


class KeyValueDictionaryType(DictionaryType):
	key_type = None
	value_type = None


class SambaLogonHours(ListType):

	item_type = StringType
	_weekdays = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')

	def decode_value(self, value):
		return ['{} {}-{}'.format(self._weekdays[v / 24], v % 24, v % 24 + 1) for v in value]

	def encode_value(self, value):
		try:
			values = [v.split() for v in value]
			return [self._weekdays.index(w) * 24 + int(h.split('-', 1)[0]) for w, h in values]
		except (IndexError, ValueError):
			raise univention.admin.uexceptions.valueInvalidSyntax(_('Invalid format for SambaLogonHours.'))


class AppcenterTranslation(KeyValueDictionaryType):

	key_type = StringType
	value_type = StringType

	def decode_value(self, value):
		value = [x.partition(' ')[::2] for x in value]
		return dict((k.lstrip('[').rstrip(']'), v) for k, v in value)

	def encode_value(self, value):
		value = ['[{}] {}'.format(k, v) for k, v in value.items()]
		return super(AppcenterTranslation, self).encode_value(value)


class UnixTimeinterval(IntegerType):

	def decode_value(self, value):
		return self.syntax.to_integer(value)

	def encode_value(self, value):
		return self.syntax.from_integer(value)
