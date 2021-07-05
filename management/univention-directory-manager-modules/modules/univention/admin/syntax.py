# -*- coding: utf-8 -*-
#
# Copyright 2004-2021 Univention GmbH
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
|UDM| syntax definitions.
"""

from __future__ import absolute_import

import re
import ldap
import operator
import ipaddress
import inspect
import time
import datetime
import dateutil
import base64
import zlib
import bz2
import copy
import json
import sys
import os
import shlex
import imghdr
import PIL
import traceback
import io
from io import BytesIO
from operator import itemgetter
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Pattern, Sequence, Tuple, Type, Union  # noqa F401

import six

import univention.debug as ud
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.types
from univention.admin import localization
from univention.lib.ucs import UCS_Version
from univention.lib.umc_module import get_mime_type, get_mime_description, image_mime_type_of_buffer

from ldap.filter import filter_format, escape_filter_chars

if TYPE_CHECKING:
	from univention.admin.uldap import access  # noqa F401

translation = localization.translation('univention/admin')
_ = translation.translate


def import_syntax_files():
	# type: () -> None
	"""
	Load all additional syntax files from :file:`*/univention/admin/syntax.d/*.py`.
	"""
	global _  # don't allow syntax to overwrite our global _ function.
	gettext = _
	for dir_ in sys.path:
		syntax_d = os.path.join(dir_, 'univention/admin/syntax.d/')

		if os.path.isdir(syntax_d):
			syntax_files = (os.path.join(syntax_d, f) for f in os.listdir(syntax_d) if f.endswith('.py'))

			for fn in syntax_files:
				try:
					with io.open(fn, 'rb') as fd:
						exec(fd.read(), sys.modules[__name__].__dict__)
					ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.import_syntax_files: importing %r' % (fn,))
				except Exception:
					ud.debug(ud.ADMIN, ud.ERROR, 'admin.syntax.import_syntax_files: loading %r failed' % (fn,))
					ud.debug(ud.ADMIN, ud.ERROR, 'admin.syntax.import_syntax_files: TRACEBACK:\n%s' % traceback.format_exc())
				finally:
					_ = gettext


choice_update_functions = []  # type: List[Callable]


def __register_choice_update_function(func):
	# type: (Callable[[], None]) -> None
	"""
	Register a function to be called when the syntax classes are to be re-loaded.
	"""
	choice_update_functions.append(func)


def update_choices():
	# type: () -> None
	"""
	Update choices which are defined in LDAP
	>>> import univention.admin.modules
	>>> univention.admin.modules.update()
	>>> update_choices()
	>>> ('settings/portal', 'Portal: Portal') in univentionAdminModules.choices
	True
	"""
	for func in choice_update_functions:
		func()


def is_syntax(syntax_obj, syntax_type):
	# type: (Any, Type) -> bool
	"""
	Returns True if the syntax object/class matches the given type.

	:param syntax_obj: The instance to check.
	:param syntax_type: A syntax class type.
	"""
	return isinstance(syntax_obj, type) and issubclass(syntax_obj, syntax_type) or isinstance(syntax_obj, syntax_type)


class ClassProperty(object):
	"""
	A decorator that can be used to define read-only class properties.
	"""

	def __init__(self, getter):
		self.getter = getter

	def __get__(self, instance, owner):
		return self.getter(owner)


SIZES = ('OneThird', 'Half', 'TwoThirds', 'One', 'FourThirds', 'OneAndAHalf', 'FiveThirds')
"""Widget sizes. UDM uses a two-column layout and by default any widget uses one column. Widgets can also be configured to span (partly) both columns."""


class ISyntax(object):
	"""
	Base class for all syntax classes.
	>>> ISyntax.name
	'ISyntax'
	>>> ISyntax.type
	'ISyntax'
	>>> ISyntax.tostring('Hallo')
	'Hallo'
	"""
	size = 'One'
	"""Widget size. See :py:data:`SIZES`."""

	type_class = None  # type: Optional[Type[univention.admin.types.TypeHint]]
	type_class_multivalue = None

	@ClassProperty
	def name(cls):
		return cls.__name__

	@ClassProperty
	def type(cls):
		return cls.__name__

	@classmethod
	def tostring(self, text):
		# type: (Any) -> str
		"""
		Convert from internal representation to textual representation.

		:param text: internal representation.
		:returns: textual representation.
		"""
		return text

	def parse_command_line(self, value):
		return self.parse(value)


class simple(ISyntax):
	"""
	Base class for single value entries.
	>>> simple.parse('A string')
	'A string'
	>>> simple().parse_command_line('A string')
	'A string'
	>>> simple.new()
	''
	>>> simple.any()
	'*'
	"""
	regex = None  # type: Optional[Pattern]
	"""Regular expression to validate the value."""
	error_message = _('Invalid value')
	"""Error message when an invalid item is selected."""

	type_class = univention.admin.types.StringType

	@classmethod
	def parse(self, text):
		# type: (Any) -> str
		"""
		Validate the value by parsing it.

		:return: the parsed textual value.
		:raises univention.admin.uexceptions.valueError: if the value is invalid.
		"""
		if text is None or self.regex is None or self.regex.match(text) is not None:
			return text
		else:
			raise univention.admin.uexceptions.valueError(self.error_message)

	@classmethod
	def new(self):
		"""
		Return the initial value.
		"""
		return ''

	@classmethod
	def any(self):
		"""
		Return the default search filter.
		"""
		return '*'

	@classmethod
	def checkLdap(self, lo, value):
		# type: (access, Any) -> Any
		"""
		Check the given value against the current LDAP state by
		reading directly from LDAP directory. The function returns nothing
		or raises an exception, if the value does not match with predefined
		constrains.

		:param lo: LDAP connection.
		:param value: The value to check.
		:returns: None on errors.
		:raises Exception: on errors.
		"""


class select(ISyntax):
	"""
	Select item from list of choices::

		self.choices = [(id, _("Display text"), ...]
	"""
	empty_value = False
	"""Allow the empty value."""

	type_class = univention.admin.types.StringType

	@classmethod
	def parse(self, text):
		# type: (Any) -> Optional[str]
		# for the UDM CLI
		if not hasattr(self, 'choices'):
			return text

		if text in map(lambda x: x[0], self.choices) or (not text and select.empty_value):
			return text

		return None  # FIXME

	@classmethod
	def new(self):
		return ''

	@classmethod
	def any(self):
		return '*'


class combobox(select):
	"""
	Select item from list of choices but accept all kind of values::

		self.choices = [(id, _("Display text"), ...]
	"""

	@classmethod
	def parse(cls, text):
		return super(combobox, cls).parse(text) or text


class MultiSelect(ISyntax):
	"""
	Select multiple items from a list of choices.
	"""
	choices = ()  # type: Sequence[Tuple[str, Any]]
	"""The list of choices."""
	empty_value = True
	"""Allow the empty value."""
	error_message = _('Invalid value')
	"""Error message when an invalid item is selected."""

	# FIXME: type_class

	@classmethod
	def parse(self, value):
		# type: (Any) -> List[str]
		# required for UDM CLI
		if isinstance(value, six.string_types):
			value = list(map(lambda x: x, shlex.split(value)))

		if not self.empty_value and not value:
			raise univention.admin.uexceptions.valueError(_('An empty value is not allowed'))
		key_list = list(map(lambda x: x[0], self.choices))
		for item in value:
			if item not in key_list:
				raise univention.admin.uexceptions.valueError(self.error_message)

		return value


class complex(ISyntax):
	"""
	Base class for complex syntax classes consisting of multiple sub-items.
	"""

	delimiter = ' '  # type: Union[str, Sequence[str]]
	"""
	Delimiter to separate the sub-items. Two possibilities:

	1.  Either a single string like `=`, which is used to concatenate all subitems.
	2.  A sequence of `n+1` strings like `['', ': ', '=', '']` to concatenate `n` sub-items. The first and last value is used as a prefix/suffix.
	"""
	min_elements = None  # type: Optional[int]
	"""Minimum number of required values."""
	all_required = True
	"""All sub-values must contain a value."""

	subsyntaxes = []  # type: List[Tuple[str, Type[ISyntax]]]
	subsyntax_names = ()  # type: Tuple[str, ...]
	subsyntax_key_value = False

	@classmethod
	def parse(self, texts, minn=None):
		# type: (Sequence[Any], int) -> List[str]
		if minn is None:
			minn = self.min_elements
		if minn is None:
			minn = len(self.subsyntaxes)

		if len(texts) < minn:
			raise univention.admin.uexceptions.valueInvalidSyntax(_("not enough arguments"))
		elif len(texts) > len(self.subsyntaxes):
			raise univention.admin.uexceptions.valueInvalidSyntax(_("too many arguments"))

		parsed = []
		for i, (text, (desc, syn)) in enumerate(zip(texts, self.subsyntaxes)):
			ud.debug(ud.ADMIN, ud.INFO, 'syntax.py: subsyntax[%s]=%s, texts=%s' % (i, syn, text))
			if text is None and i + 1 < minn:
				raise univention.admin.uexceptions.valueInvalidSyntax(_("Missing argument"))
			s = syn() if inspect.isclass(syn) else syn
			p = s.parse(text)
			parsed.append(p)
		return parsed

	@classmethod
	def fromdict(self, value):
		if self.subsyntax_key_value:
			return [self.parse(item) for item in value.items()]
		elif self.subsyntax_names:
			try:
				return [value[key] for key in self.subsyntax_names]
			except KeyError as exc:
				raise univention.admin.uexceptions.valueInvalidSyntax(_('missing argument %s') % (exc,))
		else:
			raise TypeError('Syntax class is not a dict.')

	@classmethod
	def todict(self, value):
		if self.subsyntax_key_value:
			return dict(value)
		if not self.subsyntax_names:
			raise TypeError('Syntax class is not a dict.')
		values = dict(zip(self.subsyntax_names, [None] * len(self.subsyntax_names)))
		values.update(dict(zip(self.subsyntax_names, value)))
		return values

	@property
	def type_class(cls):
		def _type_class(syn):
			syn = syn() if inspect.isclass(syn) else syn
			return syn.type_class
		if cls.subsyntax_key_value:
			class ComplexMultiValueKeyValueDictType(univention.admin.types.KeyValueDictionaryType):
				key_type = _type_class(cls.subsyntaxes[0][1])
				value_type = _type_class(cls.subsyntaxes[1][1])
			return ComplexMultiValueKeyValueDictType
		elif cls.subsyntax_names:
			class ComplexMultiValueDictType(univention.admin.types.DictionaryType):
				properties = {
					key: _type_class(syn)
					for key, (desc, syn) in zip(cls.subsyntax_names, cls.subsyntaxes)
				}
			return ComplexMultiValueDictType
		else:
			class ComplexListType(univention.admin.types.ListOfItems):
				item_types = [_type_class(sub[1]) for sub in cls.subsyntaxes]
			return ComplexListType

	@property
	def type_class_multivalue(cls):
		if cls.subsyntax_key_value:
			return cls.type_class

	@classmethod
	def tostring(self, texts):
		# type: (Any) -> str
		if self.all_required:
			if len(self.subsyntaxes) != len(texts) or not all(texts):
				return ''

		if isinstance(self.delimiter, six.string_types):
			return self.delimiter.join(texts)

		# FIXME: s/(delimiter)s/\1/
		return ''.join([s for sub in zip(self.delimiters, texts) for s in sub] + [self.delimiter[-1]])

	@classmethod
	def new(self):
		# type: () -> List[str]
		s = []
		for desc, syntax in self.subsyntaxes:
			if not inspect.isclass(syntax):
				s.append(syntax.new())
			else:
				s.append(syntax().new())
		return s

	def any(self):
		# type: () -> List[str]
		s = []
		for desc, syntax in self.subsyntaxes:
			if not inspect.isclass(syntax):
				s.append(syntax.any())
			else:
				s.append(syntax().any())
		return s


class UDM_Objects(ISyntax):
	"""
	Base class to lookup selectable items from |LDAP| entries using their |DN|.

	See :py:class:`UDM_Attribute` for an alternative to use values from one |LDAP| entry..
	>>> UDM_Objects().type_class
	<class 'univention.admin.types.DistinguishedNameType'>
	>>> UDM_Objects.parse("uid=Administrator,cn=users,dc=intranet,dc=example,dc=com")
	'uid=Administrator,cn=users,dc=intranet,dc=example,dc=com'
	>>> UDM_Objects.parse("") #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> UDM_Objects.parse("no dn") #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""
	udm_modules = ()  # type: Sequence[str]
	"""Sequence of |UDM| module names to search for."""
	udm_filter = ''
	"""A |LDAP| filter string to further restrict the matching |LDAP| objects."""
	key = 'dn'
	"""Either 'dn' or the |UDM| property name enclosed in %()s to use as the value for this syntax class."""
	label = None
	"""The |UDM| property name, which is used as the displayed value."""
	regex = re.compile('^([^=,]+=[^=,]+,)*[^=,]+=[^=,]+$')
	"""Regular expression for validating the values."""
	static_values = None  # type: Optional[Sequence[Tuple[str, str]]]
	"""Sequence of additional static items."""
	empty_value = False
	"""Allow to select no entry."""
	depends = None  # type: Optional[str]
	"""The name of another |UDM| property this syntax depends on."""
	error_message = _("Not a valid LDAP DN")
	"""Error message when an invalid item is selected."""
	simple = False  # by default a MultiObjectSelect widget is used; if simple == True a ComboBox is used
	"""With `True`, only a single object can be selected using a ComboBox. With `False` multiple entries can be selected using a MultiObjectSelect widget."""
	use_objects = True
	"""By default with `True` create Python UDM instance for each LDAP entry. With `False` only work with the LDAP attribute data."""

	@property
	def type_class(self):
		if self.key == 'dn':
			return univention.admin.types.DistinguishedNameType
		return univention.admin.types.StringType

	@classmethod
	def parse(self, text):
		if not self.empty_value and not text:
			raise univention.admin.uexceptions.valueError(_('An empty value is not allowed'))
		if isinstance(text, bytes):
			text = text.decode('UTF-8')
		if not text or not self.regex or self.regex.match(text) is not None:
			return text
		raise univention.admin.uexceptions.valueError(self.error_message)


class UDM_Attribute(ISyntax):
	"""
	Base class to lookup selectable items from |LDAP| entries using attribute values.

	See :py:class:`UDM_Objects` for an alternative to use multiple |LDAP| entries.
	"""
	udm_module = None  # type: Optional[str]
	"""|UDM| module name to search for."""
	udm_filter = ''
	"""A |LDAP| filter string to further restrict the matching |LDAP| objects."""
	attribute = None  # type: Optional[str]
	"""The |UDM| property name to use as the value for this syntax class."""
	is_complex = False
	"""True for a complex item consisting of multiple sub-items."""
	key_index = 0
	"""When the UDM property is complex: The number of the sub-item, which is used as the value for this syntax class."""
	label_index = 0
	"""When the UDM property is complex: The number of the sub-item, which is used as the display value."""
	label_format = None
	"""Python format string used to convert the |UDM| properties to the displayed value."""
	regex = None  # type: Optional[Pattern]
	"""Regular expression for validating the values."""
	static_values = None  # type: Optional[Sequence]
	"""Sequence of additional static items."""
	empty_value = False
	"""Allow to select no entry."""
	depends = None  # type: Optional[str]
	"""The name of another |UDM| property this syntax depends on."""
	error_message = _('Invalid value')
	"""Error message when an invalid item is selected."""

	@classmethod
	def parse(self, text):
		if not self.empty_value and not text:
			raise univention.admin.uexceptions.valueError(_('An empty value is not allowed'))
		if not text or not self.regex or self.regex.match(text) is not None:
			return text
		raise univention.admin.uexceptions.valueError(self.error_message)


class none(simple):
	pass


class string(simple):
	"""
	Syntax for a string with unlimited length.
	"""
	min_length = 0
	max_length = 0

	type_class = univention.admin.types.StringType

	@classmethod
	def parse(self, text):
		return text


class string64(simple):
	"""
	Syntax for a string with up to 64 characters.
	>>> string64.parse('a' * 64) == 'a' * 64
	True
	>>> string64.parse('a' * 65)  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	@classmethod
	def parse(self, text):
		self.min_length = 0
		self.max_length = 64

		if len(text) > self.max_length:
			raise univention.admin.uexceptions.valueError(_('The value must not be longer than %d characters.') % self.max_length)
		return text


class OneThirdString(string):
	"""
	Syntax for a string with an input field spanning 1/3 of the width.
	"""
	size = 'OneThird'


class string6(OneThirdString):
	"""
	Syntax for a string with up to 6 characters.
	>>> string6.parse('123456')
	'123456'
	>>> string6.parse('1234567')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	@classmethod
	def parse(self, text):
		self.min_length = 0
		self.max_length = 6

		if len(text) > self.max_length:
			raise univention.admin.uexceptions.valueError(_('The value must not be longer than %d characters.') % self.max_length)
		return text


class HalfString(string):
	"""
	Syntax for a string with an input field spanning 1/2 of the width.
	"""
	size = 'Half'


class TwoThirdsString(string):
	"""
	Syntax for a string with an input field spanning 2/3 of the width.
	"""
	size = 'TwoThirds'


class FourThirdsString(string):
	"""
	Syntax for a string with an input field spanning 4/3 of the width.
	"""
	size = 'FourThirds'


class OneAndAHalfString(string):
	"""
	Syntax for a string with an input field spanning 3/2 of the width.
	"""
	size = 'OneAndAHalf'


class FiveThirdsString(string):
	"""
	Syntax for a string with an input field spanning 5/3 of the width.
	"""
	size = 'FiveThirds'


class TwoString(string):
	"""
	Syntax for a string with an input field spanning 2/1 of the width.
	"""
	size = 'Two'


class TextArea(string):
	"""
	Syntax for a string with an input allowing multi-line input.
	"""
	pass


class Editor(string):
	pass


class TwoEditor(Editor):
	size = 'Two'


class UCSVersion(string):
	"""
	Syntax for an UCS release version `major.minor-patchlevel`.
	>>> UCSVersion.parse('4.3-2')
	'4.3-2'
	>>> UCSVersion.parse('4.3-2 errata200')  # doctest: +IGNORE_EXCEPTION_DETAIL +SKIP
	Traceback (most recent call last):
	...
	valueError:
	>>> UCSVersion.parse('4.3-2.errata200')  # doctest: +IGNORE_EXCEPTION_DETAIL +SKIP
	Traceback (most recent call last):
	...
	valueError:
	>>> UCSVersion.parse('4')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	@classmethod
	def parse(self, value):
		try:
			UCS_Version(value)
		except ValueError:
			raise univention.admin.uexceptions.valueError(_('Invalid UCS version: %s') % (value, ))

		return value


class DebianPackageVersion(string):
	"""
	Syntax for a Debian package version.
	>>> DebianPackageVersion.parse('9.1.1-2A~4.4.0.202005121353')
	'9.1.1-2A~4.4.0.202005121353'
	>>> DebianPackageVersion.parse('7.52.1-5+deb9u10')
	'7.52.1-5+deb9u10'
	>>> DebianPackageVersion.parse('2:7.52.1-5+deb9u10')
	'2:7.52.1-5+deb9u10'
	>>> DebianPackageVersion.parse('wheezy:7.52.1-5+deb9u10')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	>>> DebianPackageVersion.parse('1.0 with spaces...')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	invalid_chars_regex = re.compile('[^-+:.0-9a-zA-Z~]')

	@classmethod
	def parse(self, value):
		m = self.invalid_chars_regex.search(value)
		if m is not None:
			raise univention.admin.uexceptions.valueError(_('Invalid character in debian package version: %s') % m.group())
		p = value.find(':')
		if p != -1 and not value[:p].isdigit():
			raise univention.admin.uexceptions.valueError(_('Non-integer epoch in debian package version: %s') % str(value[:p]))

		return value


class BaseFilename(string):
	"""
	Syntax for a file name. Sub- and parent directories are not allowed.
	>>> BaseFilename.parse('example.txt')
	'example.txt'
	>>> BaseFilename.parse('my-folder/example.txt')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""

	@classmethod
	def parse(self, value):
		if '/' in value:
			raise univention.admin.uexceptions.valueError(_('Filename must not contain slashes: %s') % str(value))
		else:
			return value

# upload classes


class Upload(ISyntax):
	"""
	Syntax to allow uploading a binary file.
	>>> Upload.parse("hallo")
	'hallo'
	"""

	type_class = univention.admin.types.BinaryType

	@classmethod
	def parse(self, value):
		return value


class Base64GzipText(TextArea):
	"""
	Syntax for some `gzip`-compressed and `base64`-encoded data.
	>>> import base64
	>>> import zlib
	>>> content = b'txt'
	>>> bz2string = zlib.compress(content)
	>>> b64string = base64.b64encode(bz2string)
	>>> Base64GzipText.parse(b64string) == b64string
	True
	>>> Base64GzipText.parse(content)  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Value must be bzip2 compressed and Base64 encoded:
	>>> b64string = base64.b64encode(content)
	>>> Base64GzipText.parse('hallo')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not a valid Base64 string: hallo
	"""

	type_class = univention.admin.types.Base64Type

	@classmethod
	def parse(self, text):
		try:
			gziped_data = base64.b64decode(text)
		except Exception:
			raise univention.admin.uexceptions.valueError(_('Not a valid Base64 string: %s') % str(text))
		try:
			zlib.decompress(gziped_data)
		except Exception:
			raise univention.admin.uexceptions.valueError(_('Value must be gzip compressed and Base64 encoded: %s') % str(text))
		return text


class Base64Bzip2Text(TextArea):
	"""
	Syntax for some `bzip2`-compressed and `base64`-encoded data.
	>>> import base64
	>>> import bz2
	>>> content = b'txt'
	>>> bz2string = bz2.compress(content)
	>>> b64string = base64.b64encode(bz2string)
	>>> Base64Bzip2Text.parse(b64string) == b64string
	True
	>>> Base64Bzip2Text.parse(content)  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Value must be bzip2 compressed and Base64 encoded:
	>>> b64string = base64.b64encode(content)
	>>> Base64Bzip2Text.parse('hallo')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not a valid Base64 string: hallo
	"""

	type_class = univention.admin.types.Base64Type

	@classmethod
	def parse(self, text):
		try:
			compressed_data = base64.b64decode(text)
		except Exception:
			raise univention.admin.uexceptions.valueError(_('Not a valid Base64 string: %s') % str(text))
		try:
			bz2.decompress(compressed_data)
		except Exception:
			raise univention.admin.uexceptions.valueError(_('Value must be bzip2 compressed and Base64 encoded: %s') % str(text))
		return text


class Base64Upload(Upload):
	"""
	Syntax to allow uploading a `base64` encoded file.
	>>> import base64
	>>> content = b'...'
	>>> b64string = base64.b64encode(content)
	>>> Base64Upload.parse(b64string) == b64string
	True
	>>> Base64Upload.parse('hallo')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not a valid Base64 string: ...
	"""

	type_class = univention.admin.types.Base64Type

	@classmethod
	def parse(self, text):
		try:
			base64.b64decode(text)
		except Exception:
			raise univention.admin.uexceptions.valueError(_('Not a valid Base64 string: %s') % str(text))
		else:
			return text


class Base64BaseUpload(Base64Upload):
	"""
	Syntax to allow uploading a `base64` encoded file.
	>>> import base64
	>>> content = b'...'
	>>> b64string = base64.b64encode(content)
	>>> Base64BaseUpload.parse(b64string) == b64string
	True
	>>> Base64BaseUpload.parse('hallo')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not a valid Base64 string: ...
	"""
	@classmethod
	def parse(self, text):
		try:
			base64.b64decode(text)
		except Exception:
			raise univention.admin.uexceptions.valueError(_('Not a valid Base64 string: %s') % str(text))
		else:
			return text


class jpegPhoto(Upload):
	"""
	Syntax to allow uploading a `JPEG` or `PNG` photo.

	>>> jpegPhoto.tostring(None)
	''
	>>> import base64
	>>> b64string = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII='
	>>> jpegPhoto.parse(b64string) != b64string  # lets believe the conversion worked
	True
	>>> jpegPhoto.tostring(b64string) == b64string
	True
	>>> import bz2
	>>> content = b'...'
	>>> bz2string = bz2.compress(content)
	>>> b64string = base64.b64encode(bz2string)
	>>> jpegPhoto.parse(b64string)  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Value must be Base64 encoded jpeg.
	"""

	type_class = univention.admin.types.Base64Type

	@classmethod
	def tostring(self, value):
		# type: (Any) -> str
		if value:
			return value
		else:
			return ''

	@classmethod
	def parse(self, text):
		try:
			raw = base64.b64decode(text)
			if imghdr.what(None, raw) == 'png':
				# convert from PNG to JPEG
				try:
					fp = BytesIO(raw)
					text = BytesIO()
					image = PIL.Image.open(fp)
					image = image.convert('RGB')

					def _fileno(*a, **k):
						raise AttributeError()  # workaround for an old PIL lib which can't handle BytesIO
					text.fileno = _fileno
					image.save(text, format='jpeg')
					raw = text.getvalue()
					text = base64.b64encode(raw)
				except (KeyError, IOError, IndexError):
					ud.debug(ud.ADMIN, ud.WARN, 'Failed to convert PNG file into JPEG: %s' % (traceback.format_exc(),))
					raise
					raise univention.admin.uexceptions.valueError(_('Failed to convert PNG file into JPEG format.'))
			# imghdr.what(None, base64.b64dcode(text)) == 'jpeg'  # See Bug #36304
			# this is what imghdr.py probably does in  the future:
			if raw[0:2] != b'\xff\xd8':
				raise ValueError
			return text
		except (base64.binascii.Error, ValueError, TypeError):
			raise univention.admin.uexceptions.valueError(_('Value must be Base64 encoded jpeg.'))


class Base64Bzip2XML(TextArea):
	"""
	Syntax for some `bzip2`-compressed |XML| data.
	>>> import base64
	>>> import bz2
	>>> content = b'<?xml?><xml/>'
	>>> bz2string = bz2.compress(content)
	>>> b64string = base64.b64encode(bz2string)
	>>> Base64Bzip2XML.parse(b64string) == b64string
	True
	>>> Base64Bzip2XML.parse('hallo')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not a valid Base64 string: hallo
	>>> b64string = base64.b64encode(content)
	>>> Base64Bzip2XML.parse(b64string)  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Value must be bzip2 compressed and Base64 encoded: ...
	>>> content = b'...'
	>>> bz2string = bz2.compress(content)
	>>> b64string = base64.b64encode(bz2string)
	>>> Base64Bzip2XML.parse(b64string)  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not Base64 encoded XML data: ...
	"""

	type_class = univention.admin.types.Base64Type

	@classmethod
	def parse(self, text):
		try:
			compressed_data = base64.b64decode(text)
		except Exception:
			raise univention.admin.uexceptions.valueError(_('Not a valid Base64 string: %s') % (text,))
		try:
			data = bz2.decompress(compressed_data)
		except Exception:
			raise univention.admin.uexceptions.valueError(_('Value must be bzip2 compressed and Base64 encoded: %s') % (text,))
		if get_mime_type(data) not in ('application/xml', 'text/xml'):
			raise univention.admin.uexceptions.valueError(_('Not Base64 encoded XML data: %s') % (text,))
		return text


class Base64UMCIcon(TextArea):
	"""
	Syntax for a `base64` encoded icon (|SVG|, |PNG|, |JPEG|).
	>>> b64string = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII='
	>>> Base64UMCIcon.parse(b64string) == b64string
	True
	>>> Base64UMCIcon.parse('hallo')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not a valid Base64 string: hallo
	"""

	type_class = univention.admin.types.Base64Type

	@classmethod
	def parse(self, text):
		try:
			data = base64.b64decode(text)
		except Exception:
			raise univention.admin.uexceptions.valueError(_('Not a valid Base64 string: %s') % str(text))
		image_mime_type_of_buffer(data)  # exact return value irrelevant, only exceptions matter at this point
		return text


class GNUMessageCatalog(TextArea):
	"""
	Syntax for a `base64` encoded binary message catalog `.mo`.
	>>> b64string = b'3hIElQAAAAABAAAAHAAAACQAAAADAAAALAAAAAEAAAA4AAAAAQAAADoAAAAAAAAAAAAAAAEAAABfAF8A'
	>>> GNUMessageCatalog.parse(b64string) == b64string
	True
	>>> GNUMessageCatalog.parse('hallo')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not a valid Base64 string: hallo
	>>> GNUMessageCatalog.parse('aGFsbG8K')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not Base64 encoded GNU message catalog (.mo) data: aGFsbG8K
	"""

	type_class = univention.admin.types.Base64Type

	@classmethod
	def parse(self, text):
		try:
			data = base64.b64decode(text)
		except Exception:
			raise univention.admin.uexceptions.valueError(_('Not a valid Base64 string: %s') % str(text))
		if not get_mime_description(data).startswith('GNU message catalog'):
			raise univention.admin.uexceptions.valueError(_('Not Base64 encoded GNU message catalog (.mo) data: %s') % str(text))
		return text


class Localesubdirname(string):
	"""
	Syntax for a locale, e.g. `language[_COUNTRY][.encoding][@variant]`.

	Must match a directory in :file:`/usr/share/locale/`.
	>>> Localesubdirname.parse('de')
	'de'
	>>> Localesubdirname.parse('fantasy')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""

	@classmethod
	def parse(self, text):
		if text not in os.listdir('/usr/share/locale'):
			raise univention.admin.uexceptions.valueError(_('Not a valid locale subdir name: %s') % str(text))
		return text


class UMCMessageCatalogFilename(string):
	"""
	Syntax for a message catalog filename for UMC module translations`.

	Must have a filename like <language code>-<umcmoduleid>`.
	"""

	@classmethod
	def parse(self, text):
		if '-' not in text:
			raise univention.admin.uexceptions.valueError(_('Not a valid filename for umcmessagecatalog. Must be the language code and UMCModuleID sperated by - %s') % str(text))
		if not len(text.split('-')[0]) == 2:
			raise univention.admin.uexceptions.valueError(_('Not a valid filename for umcmessagecatalog. Must be the language code and UMCModuleID sperated by - %s') % str(text))
		return text


class Localesubdirname_and_GNUMessageCatalog(complex):
	"""
	Syntax for a message catalog and its language.

	See :py:class:`GNUMessageCatalog` and :py:class:`Localesubdirname`.

	>>> Localesubdirname_and_GNUMessageCatalog.parse(('de', '3hIElQ==')) # first bytes of vim.mo
	['de', '3hIElQ==']
	>>> Localesubdirname_and_GNUMessageCatalog.parse(('de', 'qwerty')) #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	univention.admin.uexceptions.valueError:
	>>> Localesubdirname_and_GNUMessageCatalog().new()
	['', '']
	>>> Localesubdirname_and_GNUMessageCatalog().any()
	['*', '*']
	>>> Localesubdirname_and_GNUMessageCatalog().type_class_multivalue.__name__
	'ComplexMultiValueKeyValueDictType'
	"""
	delimiter = ': '
	subsyntaxes = [(_('Locale subdir name'), Localesubdirname), (_('GNU message catalog'), GNUMessageCatalog)]
	subsyntax_key_value = True
	all_required = True


class UMCMessageCatalogFilename_and_GNUMessageCatalog(complex):
	"""
	Syntax for a message catalog and the corresponding UMCMessageCatalogFilename.

	See :py:class:`GNUMessageCatalog` and :py:class:`UMCMessageCatalogFilename`.
	"""
	delimiter = ': '
	subsyntaxes = [(_('UMCMessageCatalogFilename'), UMCMessageCatalogFilename), (_('GNU message catalog'), GNUMessageCatalog)]
	subsyntax_key_value = True
	all_required = True
	multivalue = True


class integer(simple):
	"""
	Syntax for positive numeric values.

	* :py:class:`integerOrEmpty`

	>>> integer.parse('1')
	'1'
	>>> integer.parse('0')
	'0'
	>>> integer.parse(2)
	'2'
	>>> integer.parse('-1') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> integer.parse('1.1') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> integer.parse('text') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> integer.parse('') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""
	min_length = 1
	max_length = 0
	_re = re.compile('^[0-9]+$')
	size = 'Half'

	type_class = univention.admin.types.IntegerType

	@classmethod
	def parse(self, text):
		if isinstance(text, int):
			text = str(text)
		if self._re.match(text) is not None:
			return text
		else:
			raise univention.admin.uexceptions.valueError(_("Value must be a number!"))


class integerOrEmpty(integer):
	"""
	Syntax for positive numeric values or the empty value.
	>>> integerOrEmpty.parse(None)
	>>> integerOrEmpty.parse("")
	>>> integerOrEmpty.parse(0)
	'0'
	>>> integer.parse("0")
	'0'
	"""

	@classmethod
	def parse(self, text):
		if not text and text != 0:
			return
		return super(integerOrEmpty, self).parse(text)


class boolean(simple):
	"""
	Syntax for a boolean checkbox, which internally stores the state as `0` and `1`.

	>>> boolean.parse('')
	''
	>>> boolean.parse('0')
	'0'
	>>> boolean.parse('1')
	'1'
	>>> boolean.parse(True)
	'1'
	>>> boolean.parse(False)
	'0'
	>>> boolean.sanitize_property_search_value(True)
	'1'
	>>> boolean.sanitize_property_search_value(False)
	'0'
	>>> boolean.get_object_property_filter('myAttr', '1')
	'myAttr=1'
	>>> boolean.get_object_property_filter('myAttr', '0')
	'(|(myAttr=0)(!(myAttr=*)))'
	>>> boolean.get_object_property_filter('myAttr', '')
	''
	>>> boolean.parse('2') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> boolean.parse('0.1') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> boolean.parse('text') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""
	min_length = 1
	max_length = 1
	regex = re.compile('^[01]?$')
	error_message = _("Value must be 0 or 1")

	type_class = univention.admin.types.BooleanType

	@classmethod
	def parse(self, text):
		if isinstance(text, bool):
			return '1' if text else '0'
		return super(boolean, self).parse(text)

	@classmethod
	def get_object_property_filter(cls, object_property, object_property_value):
		not_set_filter = '(!(%s=*))' % object_property
		compare_filter = '%s=%s' % (object_property, object_property_value)
		if object_property_value == '0':
			return '(|(%s)%s)' % (compare_filter, not_set_filter)
		elif object_property_value == '1':
			return compare_filter
		else:
			return ''

	@classmethod
	def sanitize_property_search_value(cls, search_value):
		return '1' if search_value is True else '0'


class AppActivatedBoolean(boolean):
	pass


class filesize(simple):
	"""
	Syntax class for a file size supporting SI suffixes like `KB`.

	>>> filesize.parse('0')
	'0'
	>>> filesize.parse('1b')
	'1b'
	>>> filesize.parse('2kB')
	'2kB'
	>>> filesize.parse('3Mb')
	'3Mb'
	>>> filesize.parse('4GB')
	'4GB'
	>>> filesize.parse('5pb') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> filesize.parse('-6') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> filesize.parse('-7.8') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> filesize.parse('text') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""
	min_length = 1
	max_length = 0
	regex = re.compile('^[0-9]+(|[gGmMkK])(|[bB])$')
	error_message = _("Value must be an integer followed by one of GB,MB,KB,B or nothing (equals B)!")


class mail_folder_name(simple):
	"""
	Syntax for |IMAP| mail folder names.

	>>> mail_folder_name.parse('folder_name')
	'folder_name'
	>>> mail_folder_name.parse('folder name') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> mail_folder_name.parse('folder\tname') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> mail_folder_name.parse('folder!name') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""
	@classmethod
	def parse(self, text):
		if "!" in text or " " in text or "\t" in text:
			raise univention.admin.uexceptions.valueError(_("Value may not contain whitespace or exclamation mark !"))
		else:
			return text


class mail_folder_type(select):
	"""
	Syntax for |IMAP| mail folder types.

	>>> mail_folder_type().new()
	''
	>>> mail_folder_type().any()
	'*'
	>>> mail_folder_type.parse('')
	''
	>>> mail_folder_type.parse('mail')
	'mail'
	>>> mail_folder_type.parse('event')
	'event'
	>>> mail_folder_type.parse('contact')
	'contact'
	>>> mail_folder_type.parse('task')
	'task'
	>>> mail_folder_type.parse('note')
	'note'
	>>> mail_folder_type.parse('journal')
	'journal'
	>>> mail_folder_type.parse('invalid')
	"""
	name = 'mail_folder_type'
	choices = [
		('', _('undefined')),
		('mail', _('mails')),
		('event', _('events')),
		('contact', _('contacts')),
		('task', _('tasks')),
		('note', _('notes')),
		('journal', _('journals')),
	]


class string_numbers_letters_dots(simple):
	"""
	Syntax for string consisting of only digits, letters and dots.

	>>> string_numbers_letters_dots.parse('a') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots.parse('A') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots.parse('0') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots.parse('aA')
	'aA'
	>>> string_numbers_letters_dots.parse('a.A')
	'a.A'
	>>> string_numbers_letters_dots.parse('a_A')
	'a_A'
	>>> string_numbers_letters_dots.parse('a-A')
	'a-A'
	>>> string_numbers_letters_dots.parse('.') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots.parse('_') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots.parse('-') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots.parse('/') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""

	regex = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9._-]*([a-zA-Z0-9]$)')
	error_message = _('Value must not contain anything other than digits, letters or dots, must be at least 2 characters long, and start and end with a digit or letter!')


class string_numbers_letters_dots_spaces(simple):
	"""
	Syntax for string consisting of only digits, letters, dots and spaces.
	The later two are not allowed at the beginning and at the end.

	>>> string_numbers_letters_dots_spaces.parse('a') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces.parse('A') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces.parse('0') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces.parse('aA')
	'aA'
	>>> string_numbers_letters_dots_spaces.parse('a.A')
	'a.A'
	>>> string_numbers_letters_dots_spaces.parse('a_A')
	'a_A'
	>>> string_numbers_letters_dots_spaces.parse('a-A')
	'a-A'
	>>> string_numbers_letters_dots_spaces.parse('a A')
	'a A'
	>>> string_numbers_letters_dots_spaces.parse('.') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces.parse('_') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces.parse('-') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces.parse(' ') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> string_numbers_letters_dots_spaces.parse('/') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""

	regex = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9._ -]*([a-zA-Z0-9]$)')
	error_message = _("Value must not contain anything other than digits, letters, dots or spaces, must be at least 2 characters long, and start and end with a digit or letter!")


class phone(simple):
	r"""
	Syntax for (international) telephone numbers.

	>>> phone.parse('+49 421 22232-0')
	'+49 421 22232-0'
	>>> phone.parse('++49 (0)700 Vanity')
	'++49 (0)700 Vanity'
	>>> phone.parse(r'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._ ()\/+-')
	'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._ ()\\/+-'
	>>> phone.parse('^°!$§%&[]{}<>|*~#",.;:') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""
	min_length = 1
	max_length = 16
	regex = re.compile('(?u)[a-zA-Z0-9._ ()\\\\/+-]*$')
	error_message = _("Value must not contain anything other than digits, letters, dots, brackets, slash, plus, or minus!")


class IA5string(string):
	"""
	Syntax for string from International Alphabet 5 (printable |ASCII|)

	>>> IA5string.parse(r''' !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~''')
	' !\"#$%&\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'
	>>> IA5string.parse(b'abc')
	'abc'
	>>> IA5string.parse('öäüÖÄÜß€') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	"""

	@classmethod
	def parse(self, text):
		# type: (Any) -> str
		try:
			if isinstance(text, bytes):
				text = text.decode('UTF-8')
			text.encode('ASCII')
		except UnicodeEncodeError:
			raise univention.admin.uexceptions.valueError(_("Field must only contain ASCII characters!"))
		return text


class uid(simple):
	"""
	Syntax for user account names.

	>>> uid.parse('a') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid.parse('A') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid.parse('0') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid.parse('aA')
	'aA'
	>>> uid.parse('a.A')
	'a.A'
	>>> uid.parse('a_A')
	'a_A'
	>>> uid.parse('a-A')
	'a-A'
	>>> uid.parse('.') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid.parse('_') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid.parse('-') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid.parse('/') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
		...
	valueError:
	>>> uid.parse('admin') #doctest: +IGNORE_EXCEPTION_DETAIL +SKIP
	Traceback (most recent call last):
		...
	valueError:
	>>> uid.parse('Admin')
	'Admin'
	"""
	min_length = 1   # TODO: not enforced here
	max_length = 16  # TODO: not enforced here
	regex = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9._-]*([a-zA-Z0-9]$)')
	# FIXME: (?!admin)
	error_message = _("Value must not contain anything other than digits, letters, dots, dash or underscore, must be at least 2 characters long, must start and end with a digit or letter, and must not be admin!")


class uid_umlauts(simple):
	"""
	Syntax for user account names supporting umlauts.

	>>> uid_umlauts.parse(u'üser') == u'üser'
	True
	>>> uid_umlauts.parse('user') == 'user'
	True
	>>> uid_umlauts.parse(b'admin')
	'admin'
	>>> uid_umlauts.parse('üs er') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	univention.admin.uexceptions.valueError:
	>>> uid_umlauts.parse('ädmin no.2') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	>>> uid_umlauts.parse('admin@2') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	name = 'uid'
	min_length = 1   # TODO: not enforced here
	max_length = 16  # TODO: not enforced here
	_re = re.compile(r'(?u)(^\w[\w -.]*\w$)|\w*$')  # TODO: uid() above must be at least 2 chars long
	# FIXME: The " -." in "[\w -.]" matches the ASCII character range(ord(' '),  ord('.')+1) == range(32, 47)

	@classmethod
	def parse(self, text):
		if isinstance(text, bytes):
			text = text.decode('UTF-8')
		if u" " in text:
			raise univention.admin.uexceptions.valueError(_("Spaces are not allowed in the username!"))
		if self._re.match(text) is not None:
			return text
		else:
			# TODO: Dashes are allowed too
			raise univention.admin.uexceptions.valueError(_("Username must only contain numbers, letters and dots!"))


class uid_umlauts_lower_except_first_letter(simple):
	"""
	Syntax for user account names supporting umlauts expecpt for the first character.
	>>> uid_umlauts_lower_except_first_letter.parse('admin')
	'admin'
	>>> uid_umlauts_lower_except_first_letter.parse(b'admin')
	'admin'
	>>> uid_umlauts_lower_except_first_letter.parse(u'ädmin') == u'ädmin'  # depends on current locale # doctest: +SKIP
	True
	>>> uid_umlauts_lower_except_first_letter.parse('admin@2') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	>>> uid_umlauts_lower_except_first_letter.parse('ADMIN') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	min_length = 1   # TODO: not enforced here
	max_length = 16  # TODO: not enforced here
	_re = re.compile(r'(?u)(^\w[\w -.]*\w$)|\w*$')  # TODO: uid() above must be at least 2 chars long
	# FIXME: The " -." in "[\w -.]" matches the ASCII character range(ord(' '),  ord('.')+1) == range(32, 47)

	@classmethod
	def parse(self, text):
		if isinstance(text, bytes):
			text = text.decode('UTF-8')
		if any(c.isupper() for c in text[1:]):
			raise univention.admin.uexceptions.valueError(_("Only the first letter of the username may be uppercase!"))

		if self._re.match(text) is not None:
			return text
		else:
			raise univention.admin.uexceptions.valueError(_("Username must only contain numbers, letters and dots!"))


class gid(simple):
	"""
	Syntax for group account names.

	>>> gid.parse(u'group')
	u'group'
	>>> gid.parse(u'Groupe d’accès d’autorisation Windows')  # depends on current locale # doctest: +SKIP
	u'Groupe d\u2019acc\u00e8s d\u2019autorisation Windows'
	"""
	min_length = 1   # TODO: not enforced here
	max_length = 32  # TODO: not enforced here
	regex = re.compile(u"(?u)^\\w([\\w -.’]*\\w)?$")
	# FIXME: The " -." in "[\w -.]" matches the ASCII character range(ord(' '),  ord('.')+1) == range(32, 47)
	error_message = _(
		"A group name must start and end with a letter, number or underscore. In between additionally spaces, dashes "
		"and dots are allowed."
	)


class sharePath(simple):
	"""
	Syntax for file share paths.
	The path must be absolute and the following paths are not allowed:

	* :file:`/dev/`
	* :file:`/proc/`
	* :file:`/root/`
	* :file:`/sys/`
	* :file:`/tmp/`
	>>> sharePath.parse('/home/Administator')
	'/home/Administator'
	>>> sharePath.parse('./my-folder') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	>>> sharePath.parse('/root/') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	regex = re.compile('^([^"])+$')
	error_message = _('Value may not contain double quotes (")!')

	@classmethod
	def parse(self, text):
		if not text[0] == '/':
			raise univention.admin.uexceptions.valueInvalidSyntax(_('A path must begin with "/"!'))
		for path in ["tmp", "root", "proc", "dev", "sys"]:
			if re.match("(^/%s$)|(^/%s/)" % (path, path), os.path.realpath(text)):
				raise univention.admin.uexceptions.valueError(_('Path may not start with "%s" !') % path)

		return super(sharePath, self).parse(text)


class passwd(simple):
	"""
	Syntax for passwords.
	>>> passwd.parse('now this is a clever password')
	'now this is a clever password'
	>>> passwd.parse('secret') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	min_length = 8
	max_length = 0
	_re1 = re.compile(r"[A-Z]")
	_re2 = re.compile(r"[a-z]")
	_re3 = re.compile(r"[0-9]")

	type_class = univention.admin.types.PasswordType

	@classmethod
	def parse(self, text):
		if len(text) >= self.min_length:
			return text
		else:
			raise univention.admin.uexceptions.valueError(_('The password is too short, at least %d characters needed.') % self.min_length)


class userPasswd(simple):
	"""
	Syntax for user account passwords.
	>>> userPasswd.parse('now this is a clever password')
	'now this is a clever password'
	>>> userPasswd.parse('') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""

	type_class = univention.admin.types.PasswordType

	@classmethod
	def parse(self, text):
		if text and len(text) > 0:
			return text
		else:
			raise univention.admin.uexceptions.valueError(_('Empty password not allowed!'))


class hostName(simple):
	"""
	hostname based upon :rfc:`1123`::

		<let-or-digit>[*[<let-or-digit-or-hyphen>]<let-or-digit>]

	also allow `_` for Microsoft.

	>>> hostName.parse('a')
	'a'
	>>> hostName.parse('0')
	'0'
	>>> hostName.parse('') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: This is not a valid hostname.
	>>> hostName.parse('a' * 64) # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: This is not a valid hostname.
	>>> hostName.parse('!') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: This is not a valid hostname.
	>>> hostName.parse('-') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: This is not a valid hostname.
	"""

	min_length = 1
	max_length = 63
	regex = re.compile(r"^(?![_-])[a-zA-Z0-9_-]{1,63}(?<![_-])$")
	error_message = _("This is not a valid hostname.")


# UNUSED:
windowsHostName = hostName


class ipv4Address(simple):
	"""
	Syntax class for an IPv4 address.
	`0.0.0.0` is allowed.

	>>> ipv4Address.parse('0.0.0.0')
	'0.0.0.0'
	>>> ipv4Address.parse('hi!') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""

	@classmethod
	def parse(self, text):
		try:
			return str(ipaddress.IPv4Address(u'%s' % (text,)))
		except ValueError:
			raise univention.admin.uexceptions.valueError(_("Not a valid IP address!"))


class ipAddress(simple):
	"""
	Syntax class for an IPv4 or IPv6 address.
	`0.0.0.0` and IPv4-mapped IPv6 addresses are allowed.

	>>> ipAddress.parse('0.0.0.0')
	'0.0.0.0'
	>>> ipAddress.parse('::1')
	'::1'
	>>> ipAddress.parse('hi!') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""

	@classmethod
	def parse(self, text):
		try:
			return str(ipaddress.ip_address(u'%s' % (text,)))
		except ValueError:
			raise univention.admin.uexceptions.valueError(_("Not a valid IP address!"))


class hostOrIP(simple):
	"""
	Syntax class for an IPv4 or IPv6 address or a host name.
	`0.0.0.0` and IPv4-mapped IPv6 addresses are allowed.

	>>> hostOrIP.parse('1.2.3.4')
	'1.2.3.4'
	>>> hostOrIP.parse('1:2:3:4:5:6:7:8')
	'1:2:3:4:5:6:7:8'
	>>> hostOrIP.parse('0x7f000001')
	'0x7f000001'
	>>> hostOrIP.parse('example')
	'example'
	>>> hostOrIP.parse('hi!') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""

	min_length = 0
	max_length = 0

	@classmethod
	def ipAddress(self, text):
		try:
			ipaddress.ip_address(u'%s' % (text,))
			return True
		except ValueError:
			return False

	@classmethod
	def hostName(self, text):
		if text and hostName.regex.match(text) is not None:
			return True
		else:
			return False

	@classmethod
	def parse(self, text):
		if self.hostName(text) or self.ipAddress(text):
			return text
		else:
			raise univention.admin.uexceptions.valueError(_('Not a valid hostname or IP address!'))


class v4netmask(simple):
	"""
	Syntax for a IPv4 network mask.
	May be entered as a *bit mask* or the number of bits.

	>>> v4netmask.parse('255.255.255.0')
	'24'
	>>> v4netmask.parse('24')
	'24'
	>>> v4netmask.parse('0.0.0.0')
	'0'
	>>> v4netmask.parse('255.255.255.255')
	'32'
	>>> v4netmask.parse('33')  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not a valid netmask!
	"""
	min_length = 1
	max_length = 15

	@classmethod
	def netmaskBits(self, dotted):
		return ipaddress.IPv4Network(u'0.0.0.0/%s' % (dotted,), strict=False).prefixlen

	@classmethod
	def parse(self, text):
		try:
			return "%d" % self.netmaskBits(text)
		except ValueError:
			raise univention.admin.uexceptions.valueError(_("Not a valid netmask!"))


class netmask(simple):
	"""
	Syntax for a IPv4 network mask.
	May be entered as a *bit mask* or the number of bits.

	>>> netmask.parse('255.255.255.0')
	'24'
	>>> netmask.parse('1')
	'1'
	>>> netmask.parse('127')
	'127'
	>>> netmask.parse('0') #doctest: +IGNORE_EXCEPTION_DETAIL +SKIP
	Traceback (most recent call last):
	...
	valueError: Not a valid netmask!
	>>> netmask.parse('128') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not a valid netmask!
	"""

	@classmethod
	def parse(self, text):
		if text.isdigit() and int(text) > 0 and int(text) < max(ipaddress.IPV4LENGTH, ipaddress.IPV6LENGTH):
			return str(int(text))
		try:
			return str(ipaddress.IPv4Network(u'0.0.0.0/%s' % (text, ), strict=False).prefixlen)
		except ValueError:
			pass
		raise univention.admin.uexceptions.valueError(_("Not a valid netmask!"))


class ipnetwork(simple):
	"""
	Syntax for a IPv4 or IPv6 network address block.

	>>> ipnetwork.parse('1.2.3.4/255.255.255.0') #doctest: +SKIP
	'1.2.3.0/24'
	>>> ipnetwork.parse('1.2.3.4/24') #doctest: +SKIP
	'1.2.3.0/24'
	>>> ipnetwork.parse('1:2:3:4:5:6:7:8/64') #doctest: +SKIP
	'1:2:3:4/64'
	"""
	@classmethod
	def parse(self, text):
		try:
			# FIXME: missing return
			ipaddress.ip_network(u'%s' % (text,), strict=False)
		except ValueError:
			raise univention.admin.uexceptions.valueError(_("Not a valid network!"))


class IP_AddressRange(complex):
	"""
	Syntax for an IPv4 or IPv6 address range.

	>>> IP_AddressRange.parse(('1.2.3.4', '')) #doctest: +SKIP
	['1.2.3.4']
	>>> IP_AddressRange.parse(('1.2.3.4', '5.6.7.8'))
	['1.2.3.4', '5.6.7.8']
	>>> IP_AddressRange.parse(('::1', '::2'))
	['::1', '::2']
	>>> IP_AddressRange.parse(('5.6.7.8', '1.2.3.4')) #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax: Illegal range
	>>> IP_AddressRange.parse(('::2', '::1'))  #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax: Illegal range
	>>> IP_AddressRange.parse(('1.2.3.4', '::1')) #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Not a valid IP address!
	>>> IP_AddressRange().type_class.__name__
	'ComplexMultiValueDictType'
	"""
	subsyntaxes = (
		(_('First address'), ipAddress),
		(_('Last address'), ipAddress),
	)
	subsyntax_names = ('first', 'last')

	@classmethod
	def parse(self, texts):
		p = super(IP_AddressRange, self).parse(texts)
		try:
			first, last = p
		except ValueError:
			# FIXME: this will never happen as complex.parse() expects exactly two arguments
			return p
		try:
			if ipaddress.ip_address(u'%s' % (first,)) > ipaddress.ip_address(u'%s' % (last,)):
				raise univention.admin.uexceptions.valueInvalidSyntax(_("Illegal range"))
		except TypeError:
			raise univention.admin.uexceptions.valueError(_("Not a valid IP address!"))
		except ValueError:
			# FIXME: which case is this supposed to catch?
			raise univention.admin.uexceptions.valueInvalidSyntax(_("Illegal range"))
		return p


class IPv4_AddressRange(IP_AddressRange):
	"""
	Syntax for an IPv4 address range.

	>>> IPv4_AddressRange.todict(('1.2.3.4',)) == {'first': '1.2.3.4', 'last': None}
	True
	>>> IPv4_AddressRange.todict(('1.2.3.4', '5.6.7.8')) == {'first': '1.2.3.4', 'last': '5.6.7.8'}
	True
	>>> IPv4_AddressRange.fromdict({'first': '1.2.3.4', 'last': '5.6.7.8'})
	['1.2.3.4', '5.6.7.8']
	>>> IPv4_AddressRange.fromdict({'first': '1.2.3.4'})  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax: missing argument 'last'
	>>> IPv4_AddressRange.tostring(['1.2.3.4'])
	'1.2.3.4'
	>>> IPv4_AddressRange.tostring(['1.2.3.4', '5.6.7.8'])
	'1.2.3.4 5.6.7.8'
	>>> IPv4_AddressRange.parse(('1.2.3.4',))
	['1.2.3.4']
	>>> IPv4_AddressRange.parse(('1.2.3.4', '5.6.7.8'))
	['1.2.3.4', '5.6.7.8']
	>>> IPv4_AddressRange.parse(('5.6.7.8', '1.2.3.4'))  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax: Illegal range
	"""
	min_elements = 1
	all_required = False
	subsyntaxes = (
		(_('First address'), ipv4Address),
		(_('Last address'), ipv4Address),
	)
	subsyntax_names = ('first', 'last')


class ipProtocol(select):
	"""
	Syntax class to choose between |TCP| und |UDP|.
	"""
	choices = [('tcp', 'TCP'), ('udp', 'UDP')]


class ipProtocolSRV(select):
	"""
	Syntax for |DNS| service record.
	"""
	choices = [('tcp', 'TCP'), ('udp', 'UDP'), ('msdcs', 'MSDCS'), ('sites', 'SITES'), ('DomainDnsZones', 'DOMAINDNSZONES'), ('ForestDnsZones', 'FORESTDNSZONES')]
	size = 'OneThird'


class absolutePath(simple):
	"""
	Syntax for an absolute file system path.
	>>> absolutePath.parse('/etc/')
	'/etc/'
	>>> absolutePath.parse('../etc/') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	min_length = 1
	max_length = 0
	_re = re.compile('^/.*')

	@classmethod
	def parse(self, text):
		if self._re.match(text) is not None:
			return text
		else:
			raise univention.admin.uexceptions.valueError(_("Not an absolute path!"))


class emailForwardSetting(select):
	"""
	Syntax for selecting the e-mail forwarding setting.
	"""
	choices = [
		('0', _('Redirect all e-mails to forward addresses')),
		('1', _('Keep e-mails and forward a copy')),
	]


class emailAddress(simple):
	"""
	Syntax class for an e-mail address.
	>>> emailAddress.parse('quite@an.email.address')
	'quite@an.email.address'
	>>> emailAddress.parse('not quite an email address') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	min_length = 3
	max_length = 0

	type_class = univention.admin.types.EMailAddressType

	@classmethod
	def parse(self, text):
		if not text.startswith('@') and \
			'@' in text and \
			not text.endswith('@') and \
			' ' not in text:
			return text
		raise univention.admin.uexceptions.valueError(_("Not a valid email address!"))


class emailAddressTemplate(emailAddress):
	"""
	Syntax class for an e-mail address in the |UDM| :py:class:`univention.admin.handlers.settings.usertemplate` module.
	"""
	pass


class emailAddressValidDomain(emailAddress):
	"""
	Syntax class for an e-mail address in one of the registered e-mail domains.

	>>> from univention.admin.uldap import getMachineConnection
	>>> if os.path.exists('/etc/machine.secret'):
	...     lo, pos = getMachineConnection()
	...     emailAddressValidDomain.checkLdap(lo, 'user@example.com') # doctest: +IGNORE_EXCEPTION_DETAIL
	... else:
	...     raise univention.admin.uexceptions.valueError()
	Traceback (most recent call last):
	...
	valueError:
	"""
	name = 'emailAddressValidDomain'
	errMsgDomain = _("The domain part of the following mail addresses is not in list of configured mail domains: %s")

	@classmethod
	def checkLdap(self, lo, mailaddresses):
		# convert mailaddresses to array if necessary
		mailaddresses = copy.deepcopy(mailaddresses)
		if isinstance(mailaddresses, str):
			mailaddresses = [mailaddresses]
		if not isinstance(mailaddresses, list):
			return

		faillist = []
		domainCache = {}
		# iterate over mail addresses
		for mailaddress in mailaddresses:
			if mailaddress:
				domain = mailaddress.rsplit('@', 1)[-1]
				if domain not in domainCache:
					ldapfilter = ldap.filter.filter_format('(&(objectClass=univentionMailDomainname)(cn=%s))', [domain])
					result = lo.searchDn(filter=ldapfilter)
					domainCache[domain] = bool(result)
					ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.%s: address=%r   domain=%r   result=%r' % (self.name, mailaddress, domain, result))
				if not domainCache[domain]:
					faillist.append(mailaddress)
					ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.%s: address=%r   domain=%r' % (self.name, mailaddress, domain))

		if faillist:
			raise univention.admin.uexceptions.valueError(self.errMsgDomain % (', '.join(faillist),))


class primaryEmailAddressValidDomain(emailAddressValidDomain):
	"""
	Syntax class for the primary e-mail address in one of the registered e-mail domains.
	"""
	name = 'primaryEmailAddressValidDomain'
	errMsgDomain = _("The domain part of the primary mail address is not in list of configured mail domains: %s")


class iso8601Date(simple):
	"""
	A date of the format:

	* yyyy-ddd   (2009-213)
	* yyyy-mm    (2009-05)
	* yyyy-mm-dd (2009-05-13)
	* yyyy-Www   (2009-W21)
	* yyyy-Www-D (2009-W21-4)

	with the dashes being optional
	>>> iso8601Date.to_datetime('2020-05')  # doctest: +SKIP
	datetime.date(2020, 5, 1)
	>>> iso8601Date.to_datetime('2020-05-13')
	datetime.date(2020, 5, 13)
	>>> iso8601Date.to_datetime('2020-W42')  # doctest: +SKIP
	datetime.date(2020, 5, 1)
	>>> iso8601Date.to_datetime('2020-W42-0')  # doctest: +SKIP
	datetime.date(2020, 10, 22)
	>>> from datetime import date
	>>> iso8601Date.from_datetime(date(2020, 5, 13))
	'2020-05-13'
	>>> iso8601Date.parse('2020-05-13')
	'2020-05-13'
	>>> iso8601Date.parse('00.00.01') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	# regexp-source: http://regexlib.com/REDetails.aspx?regexp_id=2092
	regex = re.compile(r'^(\d{4}(?:(?:(?:\-)?(?:00[1-9]|0[1-9][0-9]|[1-2][0-9][0-9]|3[0-5][0-9]|36[0-6]))?|(?:(?:\-)?(?:1[0-2]|0[1-9]))?|(?:(?:\-)?(?:1[0-2]|0[1-9])(?:\-)?(?:0[1-9]|[12][0-9]|3[01]))?|(?:(?:\-)?W(?:0[1-9]|[1-4][0-9]|5[0-3]))?|(?:(?:\-)?W(?:0[1-9]|[1-4][0-9]|5[0-3])(?:\-)?[1-7])?)?)$')
	error_message = _('The given date does not conform to iso8601, example: "2009-01-01".')

	type_class = univention.admin.types.DateType

	@classmethod
	def to_datetime(cls, value):
		value = cls.parse(value)
		if value:
			try:
				return dateutil.parser.parse(value).date()  # FIXME: this gives AttributeError: module 'dateutil' has no attribute 'parser'
			except Exception:
				pass
			if re.match(r"\d+-\d+$", value):
				# FIXME: broken: the regex does not allow this format
				return datetime.datetime.strptime(value, "%Y-%j").date()
			elif re.match(r"\d+-W\d+-\d+$", value):
				# FIXME: broken: the regex allows 1-7 while the function expects 0-6. 7 gives a traceback
				return datetime.datetime.strptime(value, "%Y-W%U-%w").date()
			elif re.match(r"\d+-W\d+$", value):
				# FIXME: broken: When used with the strptime() method, %U and %W are only used in calculations when the day of the week and the year are specified.
				return datetime.datetime.strptime(value, "%Y-W%U").date()
			return datetime.date(*time.strptime(value, '%Y-%m-%d')[0:3])

	@classmethod
	def from_datetime(cls, value):
		return value.isoformat()


class date(simple):
	"""
	Syntax for a German date (DD.MM.YY).
	Also accepts the ISO format (YYYY-MM-DD).

	.. warning::
		Centuries are *always* stripped!
		See :py:class:`date2`.

	>>> date.parse(None)
	''
	>>> date.parse('21.12.03')
	'21.12.03'
	>>> date.parse('1961-01-01')
	'01.01.61'
	>>> date.parse('2061-01-01')
	'01.01.61'
	>>> date.parse('01.02.00')
	'01.02.00'
	>>> date.parse('01.02.99')
	'01.02.99'
	>>> date.parse('00.00.01') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	>>> date.parse('01x02y03') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	>>> from datetime import datetime
	>>> date.from_datetime(datetime(2020, 1, 1))
	'2020-01-01T00:00:00'
	>>> date.to_datetime('31.12.19')
	datetime.date(2019, 12, 31)

	Bug #20230:
	>>> date.parse('31.2.1') #doctest: +IGNORE_EXCEPTION_DETAIL +SKIP
	Traceback (most recent call last):
	...
	valueError:
	"""
	name = 'date'
	min_length = 5
	max_length = 0
	_re_iso = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
	_re_de = re.compile(r'^[0-9]{1,2}\.[0-9]{1,2}\.[0-9]+$')

	type_class = univention.admin.types.DateType

	@classmethod
	def parse(self, text):
		if text and self._re_iso.match(text):
			year, month, day = map(int, text.split('-', 2))
			if 1960 < year < 2100 and 1 <= month <= 12 and 1 <= day <= 31:
				return '%02d.%02d.%02d' % (day, month, year % 100)
		if text and self._re_de.match(text):
			day, month, year = map(int, text.split('.', 2))
			if 0 <= year <= 99 and 1 <= month <= 12 and 1 <= day <= 31:
				return text
		if text is not None:
			raise univention.admin.uexceptions.valueError(_("Not a valid Date"))
		return ''

	@classmethod
	def to_datetime(cls, value):
		value = cls.parse(value)
		if value:
			return datetime.date(*time.strptime(value, '%d.%m.%y')[0:3])

	@classmethod
	def from_datetime(cls, value):
		return value.isoformat()


class date2(date):  # fixes the century
	"""
	Syntax for an ISO date (YYYY-MM-DD).
	Also accepts the German format (DD.MM.YY).
	If no century is specified, the date is mapped to 1970..2069.

	>>> date2.parse('21.12.75')
	'1975-12-21'
	>>> date2.parse('21.12.03')
	'2003-12-21'
	>>> date2.parse('1961-01-01')
	'1961-01-01'
	>>> date2.to_datetime('1961-01-01')
	datetime.date(1961, 1, 1)
	>>> date2.parse('2001-02-31')  #doctest: +SKIP
	'2001-02-31'
	>>> date2.parse('just a string') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Full domain name must be between 1 and 253 characters long!
	"""

	@classmethod
	def parse(self, text):
		if text is None:
			return ''
		if self._re_iso.match(text):
			year, month, day = map(int, text.split('-', 2))
			if 1960 < year < 2100 and 1 <= month <= 12 and 1 <= day <= 31:
				return text
		if text and self._re_de.match(text):
			day, month, year = map(int, text.split('.', 2))
			if 0 <= year <= 99 and 1 <= month <= 12 and 1 <= day <= 31:
				# Workaround: Don't wrap 2.1.1970 to 2.1.2070:
				if year >= 70:  # Epoch 0
					return '19%02d-%02d-%02d' % (year, month, day)
				return '20%02d-%02d-%02d' % (year, month, day)
		raise univention.admin.uexceptions.valueError(_("Not a valid Date"))

	@classmethod
	def to_datetime(cls, value):
		value = cls.parse(value)
		if value:
			return datetime.date(*time.strptime(value, '%Y-%m-%d')[0:3])


class reverseLookupSubnet(simple):
	"""
	Syntax for IPv4 or IPv6 sub-network.

	>>> reverseLookupSubnet.parse('1.2.3')
	'1.2.3'
	>>> reverseLookupSubnet.parse('1')
	'1'
	>>> reverseLookupSubnet.parse('1000:2000:3000:4000:5000:6000:7000:800')
	'1000:2000:3000:4000:5000:6000:7000:800'
	"""
	#               <-                      0-255                     ->  *dot  <-                      0-255                     ->
	regex_IPv4 = r'((([1-9]?[0-9])|(1[0-9]{0,2})|(2([0-4][0-9]|5[0-5])))\.){1,2}(([1-9]?[0-9])|(1[0-9]{0,2})|(2([0-4][0-9]|5[0-5])))'
	# normal IPv6 address without "::" substitution, leading zeroes must be preserved, at most 31 nibbles
	regex_IPv6 = r'(([0-9a-f]{4}:){0,7}[0-9a-f]{1,3})|(([0-9a-f]{4}:){0,6}[0-9a-f]{1,4})'
	regex = re.compile(r'^((%s)|(%s))$' % (regex_IPv4, regex_IPv6, ))
	error_message = _('A subnet for reverse lookup consists of the first 1-3 octets of an IPv4 address (example: "192.168.0") or of the first 1 to 31 nibbles of an expanded (with leading zeroes and without ::-substitution) IPv6 address (example: "2001:0db8:010" for "2001:db8:100::/24")')


class reverseLookupZoneName(simple):
	"""
	Syntax for a |DNS| reverse zone name.

	>>> reverseLookupZoneName.parse('3.2.1.in-addr.arpa')
	'3.2.1.in-addr.arpa'
	>>> reverseLookupZoneName.parse('8.7.6.5.4.3.2.1.ip6.arpa')
	'8.7.6.5.4.3.2.1.ip6.arpa'
	"""
	#                       <-    IPv6 reverse zone   -> <-                           IPv4 reverse zone                           ->
	#                       nibble dot-separated ...arpa   <-                      0-255                     -> dot-separated .arpa
	regex = re.compile(r'^((([0-9a-f]\.){1,31}ip6\.arpa)|(((([1-9]?[0-9])|(1[0-9]{0,2})|(2([0-4][0-9]|5[0-5])))\.){1,3}in-addr.arpa))$')
	error_message = _("The name of a reverse zone for IPv4 consists of the reversed subnet address followed by .in-addr.arpa (example: \"0.168.192.in-addr.arpa\") or for IPv6 in nibble format followed by .ip6.arpa (example: \"0.0.0.0.0.0.1.0.8.b.d.0.1.0.0.2.ip6.arpa\")")


class dnsName(simple):
	"""
	:rfc:`1123`: a '.' separated FQDN

	>>> dnsName.parse('') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Missing value!

	A host name (label) can be up to 63 characters

	>>> dnsName.parse('0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Labels must be between 1 and 63 characters long!
	>>> dnsName.parse('a..') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Labels must be between 1 and 63 characters long!

	A full domain name is limited to 253 octets (including the separators).

	>>> dnsName.parse('a.' * 128) # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Full domain name must be between 1 and 253 characters long!
	"""
	min_length = 1
	max_length = 253

	@classmethod
	def parse(self, text):
		if not text:
			raise univention.admin.uexceptions.valueError(_("Missing value!"))
		assert isinstance(text, six.string_types)
		if not 1 <= len(text) <= 253:
			raise univention.admin.uexceptions.valueError(_("Full domain name must be between 1 and 253 characters long!"))
		labels = (text[:-1] if text.endswith('.') else text).split('.')
		if not all(1 <= len(label) <= 63 for label in labels):
			raise univention.admin.uexceptions.valueError(_("Labels must be between 1 and 63 characters long!"))
		return text


# UNUSED:
DNS_Name = dnsName
dnsZone = dnsName


class dnsHostname(dnsName):
	"""
	:rfc:`1123`: a '.' separated FQHN

	A host name (label) can start or end with a letter or a number

	>>> dnsHostname.parse('a')
	'a'
	>>> dnsHostname.parse('A.')
	'A.'
	>>> dnsName.parse('0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
	'0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
	>>> dnsName.parse('0.example.com')
	'0.example.com'

	A host name (label) MUST NOT consist of all numeric values

	>>> dnsHostname.parse('0') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: Full name must not be all numeric!

	A host name (label) MUST NOT start or end with a '-' (dash)

	>>> dnsHostname.parse('-') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: A host name or FQDN must start and end with a letter or number. In between additionally dashes, dots and underscores are allowed.
	"""

	LABEL = re.compile(r'^(?![0-9]+$|[_-])[a-zA-Z0-9_-]{1,63}(?<![_-])$')
	NUMERIC = re.compile(r'^[0-9.]+$')

	@classmethod
	def parse(self, text):
		text = super(dnsHostname, self).parse(text)
		if self.NUMERIC.match(text):
			raise univention.admin.uexceptions.valueError(_("Full name must not be all numeric!"))
		labels = (text[:-1] if text.endswith('.') else text).split('.')
		if not all(self.LABEL.match(label) for label in labels):
			raise univention.admin.uexceptions.valueError(_(
				"A host name or FQDN must start and end with a letter or number. In between additionally dashes, dots "
				"and underscores are allowed."
			))
		return text


class dnsName_umlauts(simple):
	u"""
	>>> dnsName_umlauts.parse(u'ä') == u'ä'
	True
	>>> dnsName_umlauts.parse('a_0-A')
	'a_0-A'
	>>> dnsName_umlauts.parse('0') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: A host name or FQDN must start and end with a letter or number. In between additionally dashes, dots and underscores are allowed.
	>>> dnsName_umlauts.parse('-') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: A host name or FQDN must start and end with a letter or number. In between additionally dashes, dots and underscores are allowed.
	>>> dnsName_umlauts.parse('_') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError: A host name or FQDN must start and end with a letter or number. In between additionally dashes, dots and underscores are allowed.
	"""

	min_length = 1
	max_length = 63
	regex = re.compile(r"^(?![0-9]+$|[_-])[\w_-]{1,63}(?<![_-])$", re.UNICODE)
	error_message = _(
		"A host name or FQDN must start and end with a letter or number. In between additionally dashes, dots "
		"and underscores are allowed."
	)


class keyAndValue(complex):
	"""
	Syntax for key-value-pairs separated by `=`.

	>>> keyAndValue.tostring(['key', 'value'])
	'key = value'
	>>> keyAndValue.tostring(['key'])
	''
	>>> keyAndValue.parse(('key',))  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	>>> keyAndValue.parse(('key', 'value', 'and then some'))  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	>>> keyAndValue.parse((None, 'value'))  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	>>> keyAndValue.parse(('key', 'value'))
	['key', 'value']
	"""
	delimiter = ' = '
	subsyntaxes = [(_('Key'), string), (_('Value'), string)]
	subsyntax_key_value = True
	all_required = 1


class dnsMX(complex):
	"""
	Syntax for |DNS| mail exchange record.

	>>> dnsMX.parse(('10', 'mail.my.domain'))
	['10', 'mail.my.domain']
	"""
	subsyntaxes = [(_('Priority'), integer), (_('Mail server'), dnsHostname)]
	subsyntax_names = ('priority', 'mailserver',)
	all_required = True


class dnsSRVName(complex):
	"""
	Syntax for the name of a |DNS| service record.

	>>> dnsSRVName.parse(('ldap', 'tcp'))
	['ldap', 'tcp']
	>>> dnsSRVName.parse(('ldap', 'tcp'))
	['ldap', 'tcp']

	.. seealso::
		* :py:class:`dnsSRVLocation`
	"""
	min_elements = 2
	all_required = False
	subsyntaxes = ((_('Service'), string), (_('Protocol'), ipProtocolSRV), (_('Extension'), string))
	subsyntax_names = ('service', 'protocol', 'extension')
	size = ('Half', 'Half', 'One')


class dnsPTR(simple):
	"""
	|DNS| pointer record.

	>>> dnsPTR.parse('1')
	'1'
	>>> dnsPTR.parse('1.2.3')
	'1.2.3'
	>>> dnsPTR.parse('f')
	'f'
	>>> dnsPTR.parse('1.2.3.4.5.6.7.8.9.a.b.c.d.e.f.0.1.2.3.4.5.6.7.8.9.a.b.c.d.e.f')
	'1.2.3.4.5.6.7.8.9.a.b.c.d.e.f.0.1.2.3.4.5.6.7.8.9.a.b.c.d.e.f'
	"""
	regexp = re.compile(
		r'''
		^    (?:[0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])
		(?:\.(?:[0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])){0,2}$
		|^    [0-9a-f]
		(?:\.[0-9a-f]){0,30}$
		''', re.VERBOSE
	)
	error_message = _("The reversed host name for IPv4 consists of the reversed host address (example: \"4.3\") or for IPv6 in nibble format (example: \"8.0.0.0.7.0.0.0.0.6.0.0.0.0.5.0\").")


class postalAddress(complex):
	"""
	Syntax for a postal address consisting of street, postal code and city name.

	>>> postalAddress.parse(('street', 'zip', 'city'))
	['street', 'zip', 'city']
	"""
	delimiter = ', '
	subsyntaxes = [(_('Street'), string), (_('Postal code'), OneThirdString), (_('City'), TwoThirdsString)]
	subsyntax_names = ('street', 'zipcode', 'city')
	all_required = True


class dnsSRVLocation(complex):
	"""
	Syntax for |DNS| service record.

	>>> dnsSRVLocation.parse(('10', '100', '389', 'server.my.domain'))
	['10', '100', '389', 'server.my.domain']
	"""
	subsyntaxes = [(_('Priority'), integer), (_('Weighting'), integer), (_('Port'), integer), (_('Server'), dnsHostname)]
	subsyntax_names = ('priority', 'weigtht', 'port', 'server',)
	size = ('OneThird', 'OneThird', 'OneThird', 'One')
	all_required = True


class unixTime(simple):
	"""
	Syntax for a UNIX time stamp - seconds since 1970-01-01.
	"""
	regex = re.compile('^[0-9]+$')
	error_message = _("Not a valid time format")

	type_class = univention.admin.types.DateTimeType


class TimeUnits(select):
	"""
	Syntax to select a time unit.
	"""
	size = 'Half'
	choices = (
		('seconds', _('seconds')),
		('minutes', _('minutes')),
		('hours', _('hours')),
		('days', _('days'))
	)


class TimeString(simple):
	"""
	Syntax for the time of day, e.g. hour, minute and optional seconds.

	>>> TimeString.parse('00:00')
	'00:00'
	>>> TimeString.parse('23:59:59')
	'23:59:59'
	"""
	error_message = _("Not a valid time format")
	regex = re.compile('^(?:[01][0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?$')

	type_class = univention.admin.types.TimeType


class UNIX_TimeInterval(complex):
	"""
	Syntax for a time interval.

	>>> UNIX_TimeInterval.parse(('1',))
	['1']
	>>> UNIX_TimeInterval.parse(('2', 'seconds'))
	['2', 'seconds']
	>>> UNIX_TimeInterval.parse(('3', 'minutes'))
	['3', 'minutes']
	>>> UNIX_TimeInterval.parse(('4', 'hours'))
	['4', 'hours']
	>>> UNIX_TimeInterval.parse(('5', 'days'))
	['5', 'days']
	>>> UNIX_TimeInterval.from_integer(3600)
	['3600', 'seconds']

	.. seealso::
		* :py:class:`UNIX_BoundedTimeInterval`
	"""
	min_elements = 1
	subsyntaxes = (('', integerOrEmpty), ('', TimeUnits))
	subsyntax_names = ('amount', 'unit')
	size = ('Half', 'Half')
	type_class = univention.admin.types.UnixTimeinterval

	@classmethod
	def parse(cls, texts):
		return super(UNIX_TimeInterval, cls).parse(texts)

	@classmethod
	def from_integer(cls, value):
		return [str(value), 'seconds']

	@classmethod
	def to_integer(cls, value):
		return {
			'seconds': lambda x: x,
			'minutes': lambda x: x * 60,
			'hours': lambda x: x * 60 * 60,
			'days': lambda x: x * 24 * 60 * 60,
		}[value[1]](int(value[0]))


class UNIX_BoundedTimeInterval(UNIX_TimeInterval):
	"""
	Syntax for a time interval with additional constraints.
	"""
	lower_bound = -1  # in seconds, -1 unbounded
	upper_bound = -1  # in seconds, -1 unbounded
	error_message = _("Value out of bounds (%d - %d seconds)")

	@classmethod
	def parse(cls, texts):
		parsed = super(UNIX_BoundedTimeInterval, cls).parse(texts)
		if parsed[0] is None:
			return [None, None]

		in_seconds = int(parsed[0])
		if len(parsed) > 1:
			in_seconds = cls.to_integer(parsed)

		msg = cls.error_message % (cls.lower_bound, cls.upper_bound)
		if cls.lower_bound != -1 and in_seconds < cls.lower_bound:
			raise univention.admin.uexceptions.valueError(msg)
		if cls.upper_bound != -1 and in_seconds > cls.upper_bound:
			raise univention.admin.uexceptions.valueError(msg)

		return parsed


class SambaMinPwdAge(UNIX_BoundedTimeInterval):
	"""
	Syntax for the minimum password age in Samba: 0..998 days
	>>> SambaMinPwdAge.parse((None, 'days'))
	[None, None]
	>>> SambaMinPwdAge.parse(('0', 'days'))
	['0', 'days']
	>>> SambaMinPwdAge.parse(('998', 'days'))
	['998', 'days']
	>>> SambaMinPwdAge.parse(('999', 'days')) # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	lower_bound = 0
	upper_bound = 998 * 24 * 60 * 60  # 998 days in seconds


class SambaMaxPwdAge(UNIX_BoundedTimeInterval):
	"""
	Syntax for the maximum password age in Samba: 0..999 days
	>>> SambaMaxPwdAge.parse((None, 'days'))
	[None, None]
	>>> SambaMaxPwdAge.parse(('0', 'days'))
	['0', 'days']
	>>> SambaMaxPwdAge.parse(('999', 'days'))
	['999', 'days']
	>>> SambaMaxPwdAge.parse(('1000', 'days')) # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	lower_bound = 0
	upper_bound = 999 * 24 * 60 * 60  # 999 days in seconds


class NetworkType(select):
	"""
	Syntax to select network technology type.
	"""
	choices = (('ethernet', _('Ethernet')), ('fddi', _('FDDI')), ('token-ring', _('Token-Ring')))


class MAC_Address(simple):
	"""
	Syntax to enter MAC address.
	The address is stored with octets separated by `:`.

	>>> MAC_Address.parse('86:f5:d1:f5:6b:3e')
	'86:f5:d1:f5:6b:3e'
	>>> MAC_Address.parse('86-f5-d1-f5-6b-3e')
	'86:f5:d1:f5:6b:3e'
	>>> MAC_Address.parse('86f5d1f56b3e')
	'86:f5:d1:f5:6b:3e'
	>>> MAC_Address.parse('86f5.d1f5.6b3e')
	'86:f5:d1:f5:6b:3e'
	>>> MAC_Address.parse('aa:bb:cc:dd:ee:gg') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	regexLinuxFormat = re.compile(r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$')
	regexWindowsFormat = re.compile(r'^([0-9a-fA-F]{2}-){5}[0-9a-fA-F]{2}$')
	regexRawFormat = re.compile(r'^[0-9a-fA-F]{12}$')
	regexCiscoFormat = re.compile(r'^([0-9a-fA-F]{4}\.){2}[0-9a-fA-F]{4}$')
	error_message = _('This is not a valid MAC address (valid examples are 86:f5:d1:f5:6b:3e, 86-f5-d1-f5-6b-3e, 86f5d1f56b3e, 86f5.d1f5.6b3e)')

	@classmethod
	def parse(self, text):
		if self.regexLinuxFormat.match(text) is not None:
			return text.lower()
		elif self.regexWindowsFormat.match(text) is not None:
			return text.replace('-', ':').lower()
		elif self.regexRawFormat.match(text) is not None:
			temp = []
			for i in range(0, len(text) - 1, 2):
				temp.append(text[i:i + 2])
			return ':'.join(temp).lower()
		elif self.regexCiscoFormat.match(text) is not None:
			tmpList = []
			tmpStr = text.replace('.', '')
			for i in range(0, len(tmpStr) - 1, 2):
				tmpList.append(tmpStr[i:i + 2])
			return ':'.join(tmpList).lower()
		else:
			raise univention.admin.uexceptions.valueError(self.error_message)


class DHCP_HardwareAddress(complex):
	"""
	Syntax to enter DHCP hardware address consisting of network technology type and MAC address.
	"""
	subsyntaxes = ((_('Type'), NetworkType), (_('Address'), MAC_Address))
	subsyntax_names = ('type', 'address')
	size = ('One', 'One')
	all_required = True


class Packages(UDM_Attribute):
	"""
	Syntax to select a Debian package name from lists stored in |LDAP| using :py:class:`univention.admin.handlers.settings.packages`.
	"""
	udm_module = 'settings/packages'
	attribute = 'packageList'
	label_format = '%(name)s: %($attribute$)s'


class PackagesRemove(Packages):
	"""
	Syntax to select a Debian package name from lists stored in |LDAP| using :py:class:`univention.admin.handlers.settings.packages`.
	This blacklists some important packages to prevent their removal.
	>>> PackagesRemove.parse('curl')
	'curl'
	>>> PackagesRemove.parse('openssh-client') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	@classmethod
	def parse(cls, text):
		text = super(PackagesRemove, cls).parse(text)
		if text in ['wget', 'screen', 'openssh-client', 'nmap', 'lsof', 'file']:
			# Bug #36711: don't allow to remove packages which would uninstall univention-server-master
			raise univention.admin.uexceptions.valueError(_('The package "%s" can not be removed as it would uninstall necessary components.') % (text,))
		return text


class userAttributeList(string):
	"""
	Syntax to enter a users attribute.

	.. note::

		unused
	>>> userAttributeList.parse('uid')
	'uid'
	"""
	@classmethod
	def parse(self, text):
		return text


class ldapDn(simple):
	"""
	LDAP distinguished name.

	>>> ldapDn.parse('dc=foo,dc=bar,dc=test')
	'dc=foo,dc=bar,dc=test'

	.. deprecated:: 3.1-0
		Use :py:class:`UDM_Objects`.
	"""
	regex = re.compile('^([^=,]+=[^=,]+,)*[^=,]+=[^=,]+$')
	error_message = _("Not a valid LDAP DN")

	type_class = univention.admin.types.DistinguishedNameType


class UMC_OperationSet(UDM_Objects):
	"""
	Syntax to select a |UMC| operation set from lists stored in |LDAP| using :py:class:`univention.admin.handlers.settings.umc_operationset`.
	"""
	udm_modules = ('settings/umc_operationset', )
	label = '%(description)s (%(name)s)'
	simple = True


class UMC_CommandPattern(complex):
	"""
	Syntax to enter a |UMC| command pattern.
	"""
	subsyntaxes = ((_('Command pattern'), string), (_('Option Pattern'), string))
	subsyntax_names = ('command', 'option')
	min_elements = 1
	all_required = False  # empty values are allowed
	size = ('One', 'One')


class LDAP_Server(UDM_Objects):
	"""
	Syntax to select a |LDAP| server.

	.. deprecated:: 4.4-0
		Use :py:class:`DomainController`.
	"""
	udm_modules = ('computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave')
	udm_filter = '!(univentionObjectFlag=docker)'
	label = '%(fqdn)s'
	simple = True


class IMAP_POP3(select):
	"""
	Syntax to select between |IMAP| and POP3.
	"""
	choices = (
		('IMAP', _('IMAP')),
		('POP3', _('POP3')),
	)


class IMAP_Right(select):
	"""
	Syntax to select an |IMAP| access control permission.
	"""
	choices = (
		('none', _('No access')),
		('read', _('Read')),
		('post', _('Post')),
		('append', _('Append')),
		('write', _('Write')),
		('all', _('All'))
	)


class UserMailAddress(UDM_Objects):
	"""
	Syntax to select a primary e-mail address of an user name from |LDAP|.
	"""
	udm_modules = ('users/user', )
	udm_filter = '(mailPrimaryAddress=*)'
	key = '%(mailPrimaryAddress)s'
	static_values = (('anyone', _('Anyone')), )
	regex = re.compile(r'^([^\s]+@[^\s]+|anyone)$')
	error_message = _('Not a valid e-mail address')


class GroupName(UDM_Objects):
	"""
	Syntax to select a group name from |LDAP|.
	"""
	udm_modules = ('groups/group', )
	key = '%(name)s'
	regex = re.compile('^.+$')
	simple = True
	use_objects = False


class UserName(UDM_Objects):
	"""
	Syntax to select an user name from |LDAP|.
	"""
	udm_modules = ('users/user', )
	key = '%(username)s'
	regex = re.compile('^.+$')
	simple = True
	use_objects = False


class SharedFolderUserACL(complex):
	"""
	Syntax to assign an |IMAP| access control permission for an user from |LDAP|.
	"""
	subsyntaxes = ((_('User'), UserMailAddress), (_('Access right'), IMAP_Right))
	#subsyntax_names = ('user', 'access-right')
	subsyntax_key_value = True


class SharedFolderGroupACL(complex):
	"""
	Syntax to assign an |IMAP| access control permission for a group from |LDAP|.
	"""
	subsyntaxes = ((_('Group'), GroupName), (_('Access right'), IMAP_Right))
	#subsyntax_names = ('group', 'access-right')
	subsyntax_key_value = True


class SharedFolderSimpleUserACL(complex):
	"""
	Syntax to assign an |IMAP| access control permission for any user.
	"""
	subsyntaxes = ((_('User'), string), (_('Access right'), IMAP_Right))
	#subsyntax_names = ('user', 'access-right')
	subsyntax_key_value = True


class SharedFolderSimpleGroupACL(complex):
	"""
	Syntax to assign an |IMAP| access control permission for any group.
	"""
	subsyntaxes = ((_('Group'), string), (_('Access right'), IMAP_Right))
	#subsyntax_names = ('group', 'access-right')
	subsyntax_key_value = True


class ldapDnOrNone(simple):
	"""
	LDAP distinguished name or `None`.

	>>> ldapDnOrNone.parse('dc=foo,dc=bar,dc=test')
	'dc=foo,dc=bar,dc=test'
	>>> ldapDnOrNone.parse('None')
	'None'
	>>> ldapDnOrNone.parse('dc=foo,,') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:

	.. deprecated:: 3.1-0
		Use :py:class:`UDM_Objects`.
	"""
	_re = re.compile('^([^=,]+=[^=,]+,)*[^=,]+=[^=,]+$')

	@classmethod
	def parse(self, text):
		if not text or text == 'None':
			return text
		if self._re.match(text) is not None:
			return text
		raise univention.admin.uexceptions.valueError(_("Not a valid LDAP DN"))


class ldapObjectClass(simple):
	"""
	Syntax to enter a |LDAP| objectClass name.
	>>> ldapObjectClass.parse('univentionObject')
	'univentionObject'
	"""
	@classmethod
	def parse(self, text):
		return text  # FIXME: allows anything


class ldapAttribute(simple):
	"""
	Syntax to enter a |LDAP| attribute name.
	>>> ldapAttribute.parse('cn')
	'cn'
	"""
	@classmethod
	def parse(self, text):
		return text  # FIXME: allows anything


class ldapFilter(simple):
	"""
	Syntax to enter a |LDAP| search filter.
	>>> ldapFilter.parse('uid=*')
	'uid=*'
	>>> ldapFilter.parse('(uid=*') # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""

	type_class = univention.admin.types.LDAPFilterType

	@classmethod
	def parse(cls, text):
		# use a unbound ldap connection to validate the search filter
		lo = ldap.initialize('')
		try:
			lo.search_ext_s('', ldap.SCOPE_BASE, text)
		except ldap.FILTER_ERROR:
			raise univention.admin.uexceptions.valueError(_('Not a valid LDAP search filter'))
		except ldap.SERVER_DOWN:
			pass
		finally:
			lo.unbind()
		return text


class XResolution(simple):
	"""
	Syntax to enter display resolution for X11.
	"""
	regex = re.compile('^[0-9]+x[0-9]+$')
	error_message = _("Value consists of two integer numbers separated by an \"x\" (e.g. \"1024x768\")")


class XSync(simple):
	"""
	Syntax to enter display timing settings for X11.
	"""
	regex = re.compile('^[0-9]+(-[0-9]+)?( +[0-9]+(-[0-9]+)?)*$')
	error_message = _("Value consists of two integer numbers separated by a \"-\" (e.g. \"30-70\")")


class XColorDepth(simple):
	"""
	Syntax to enter color depth for X11.
	"""
	regex = re.compile('^[0-9]+$')


class XModule(select):
	"""
	Syntax to select graphics driver for X11.
	"""
	choices = [
		('', ''),
		('apm', 'apm'),
		('ark', 'Ark'),
		('ati', 'ATI'),
		('chips', 'chips'),
		('cirrus', 'Cirrus'),
		('cyrix', 'Cyrix'),
		('dummy', 'dummy'),
		('fbdev', 'fbdev'),
		('fglrx', 'fglrx (AMD/ATI closed source)'),
		('geode', 'Geode GX2/LX'),
		('glide', 'glide'),
		('glint', 'glint'),
		('i128', 'I128'),
		('i740', 'I740'),
		('i810', 'I810'),
		('imstt', 'IMSTT'),
		('intel', 'Intel'),
		('mach64', 'Mach64 (ATI)'),
		('mga', 'MGA'),
		('neomagic', 'Neomagic'),
		('newport', 'Newport'),
		('nouveau', 'nouveau - new Nvidia OSS driver'),
		('nsc', 'NSC'),
		('nv', 'NV'),
		('nvidia', 'NVidia (closed source)'),
		('openchrome', 'OpenChrome (VIA)'),
		('r128', 'ATI Rage'),
		('radeonhd', 'Radeon (AMD/ATI)'),
		('rendition', 'Rendition'),
		('s3', 'S3'),
		('s3virge', 'S3 Virge'),
		('savage', 'S3 Savage'),
		('siliconmotion', 'Siliconmotion'),
		('sis', 'SiS'),
		('sisusb', 'SiS USB'),
		('tdfx', 'tdfx'),
		('tga', 'Tga'),
		('trident', 'Trident'),
		('tseng', 'Tseng'),
		('vesa', 'Vesa'),
		('vga', 'VGA'),
		('via', 'VIA'),
		('vmware', 'VMWare')
	]


class XMouseProtocol(select):
	"""
	Syntax to select mouse protocol for X11.
	"""
	choices = [
		('', ''),
		('Auto', 'Auto'),
		('IMPS/2', 'IMPS/2'),
		('PS/2', 'PS/2'),
		('ExplorerPS/2', 'ExplorerPS/2'),
		('usb', 'USB'),
		('ThinkingMouse', 'ThinkingMouse'),
		('ThinkingMousePS/2', 'ThinkingMousePS/2'),
		('NetScrollPS/2', 'NetScrollPS/2'),
		('IntelliMouse', 'IntelliMouse'),
		('NetMousePS/2', 'NetMousePS/2'),
		('GlidePoint', 'GlidePoint'),
		('GlidePointPS/2', 'GlidePointPS/2'),
		('MouseManPlusPS/2', 'MouseManPlusPS/2'),
		('ms', 'Serial')
	]


class XDisplayPosition(select):
	"""
	Syntax to select display position for X11.
	"""
	choices = [
		('', ''),
		('left', _('Left of primary display')),
		('right', _('Right of primary display')),
		('above', _('Above primary display')),
		('below', _('Below primary display'))
	]


class XMouseDevice(select):
	"""
	Syntax to select mouse device for X11.
	"""
	choices = [
		('', ''),
		('/dev/psaux', 'PS/2'),
		('/dev/input/mice', 'USB'),
		('/dev/ttyS0', 'Serial')
	]


class XKeyboardLayout(select):
	"""
	Syntax to select keyboard layout for X11.
	"""
	choices = [
		('', ''),
		('ad', 'Andorra'),
		('af', 'Afghanistan'),
		('al', 'Albania'),
		('am', 'Armenia'),
		('ara', 'Arabic'),
		('az', 'Azerbaijan'),
		('ba', 'Bosnia and Herzegovina'),
		('bd', 'Bangladesh'),
		('be', 'Belgium'),
		('bg', 'Bulgaria'),
		('brai', 'Braille'),
		('br', 'Brazil'),
		('bt', 'Bhutan'),
		('by', 'Belarus'),
		('ca', 'Canada'),
		('cd', 'Congo, Democratic Republic of the'),
		('ch', 'Switzerland'),
		('cn', 'China'),
		('cz', 'Czechia'),
		('de', 'Germany'),
		('dk', 'Denmark'),
		('ee', 'Estonia'),
		('epo', 'Esperanto'),
		('es', 'Spain'),
		('et', 'Ethiopia'),
		('fi', 'Finland'),
		('fo', 'Faroe Islands'),
		('fr', 'France'),
		('gb', 'United Kingdom'),
		('ge', 'Georgia'),
		('gh', 'Ghana'),
		('gn', 'Guinea'),
		('gr', 'Greece'),
		('hr', 'Croatia'),
		('hu', 'Hungary'),
		('ie', 'Ireland'),
		('il', 'Israel'),
		('in', 'India'),
		('iq', 'Iraq'),
		('ir', 'Iran'),
		('is', 'Iceland'),
		('it', 'Italy'),
		('jp', 'Japan'),
		('kg', 'Kyrgyzstan'),
		('kh', 'Cambodia'),
		('kr', 'Korea, Republic of'),
		('kz', 'Kazakhstan'),
		('la', 'Laos'),
		('latam', 'Latin American'),
		('lk', 'Sri Lanka'),
		('lt', 'Lithuania'),
		('lv', 'Latvia'),
		('ma', 'Morocco'),
		('mao', 'Maori'),
		('me', 'Montenegro'),
		('mk', 'Macedonia'),
		('mm', 'Myanmar'),
		('mn', 'Mongolia'),
		('mt', 'Malta'),
		('mv', 'Maldives'),
		('nec_vndr/jp', 'Japan (PC-98xx Series)'),
		('ng', 'Nigeria'),
		('nl', 'Netherlands'),
		('no', 'Norway'),
		('np', 'Nepal'),
		('pk', 'Pakistan'),
		('pl', 'Poland'),
		('pt', 'Portugal'),
		('ro', 'Romania'),
		('rs', 'Serbia'),
		('ru', 'Russia'),
		('se', 'Sweden'),
		('si', 'Slovenia'),
		('sk', 'Slovakia'),
		('sn', 'Senegal'),
		('sy', 'Syria'),
		('th', 'Thailand'),
		('tj', 'Tajikistan'),
		('tm', 'Turkmenistan'),
		('tr', 'Turkey'),
		('ua', 'Ukraine'),
		('us', 'USA'),
		('uz', 'Uzbekistan'),
		('vn', 'Vietnam'),
		('za', 'South Africa')
	]


class soundModule(select):
	"""
	Syntax to select ALSA audio device driver.
	"""
	choices = [
		('', ''),
		('auto', 'auto detect'),
		('snd-ad1816a', 'AD1816A, AD1815'),
		('snd-adlib', 'AdLib FM'),
		('snd-ak4114', 'AK4114 IEC958 (S/PDIF) receiver by Asahi Kasei'),
		('snd-ak4117', 'AK4117 IEC958 (S/PDIF) receiver by Asahi Kasei'),
		('snd-ali5451', 'ALI M5451'),
		('snd-opl3-synth', 'ALSA driver for OPL3 FM synth'),
		('snd-sb16-csp', 'ALSA driver for SB16 Creative Signal Processor'),
		('snd-sb-common', 'ALSA lowlevel driver for Sound Blaster cards'),
		('snd-interwave', 'AMD InterWave'),
		('snd-interwave-stb', 'AMD InterWave STB with TEA6330T'),
		('snd-ad1889', 'Analog Devices AD1889 ALSA sound driver'),
		('snd-atiixp', 'ATI IXP AC97 controller'),
		('snd-atiixp-modem', 'ATI IXP MC97 controller'),
		('aedsp16', 'Audio Excel DSP 16 Driver Version 1.3'),
		('snd-au8810', 'Aureal vortex 8810'),
		('snd-au8820', 'Aureal vortex 8820'),
		('snd-au8830', 'Aureal vortex 8830'),
		('snd-als100', 'Avance Logic ALS1X0'),
		('snd-als300', 'Avance Logic ALS300'),
		('snd-als4000', 'Avance Logic ALS4000'),
		('snd-azt3328', 'Aztech AZF3328 (PCI168)'),
		('snd-sgalaxy', 'Aztech Sound Galaxy'),
		('snd-azt2320', 'Aztech Systems AZT2320'),
		('snd-bt87x', 'Brooktree Bt87x audio driver'),
		('snd-ca0106', 'CA0106'),
		('snd-cs4232', 'Cirrus Logic CS4232'),
		('snd-cs4236', 'Cirrus Logic CS4235-9'),
		('snd-cs4281', 'Cirrus Logic CS4281'),
		('snd-cmi8330', 'C-Media CMI8330'),
		('snd-cmipci', 'C-Media CMI8x38 PCI'),
		('snd-vx-lib', 'Common routines for Digigram VX drivers'),
		('snd-cs5535audio', 'CS5535 Audio'),
		('snd-dt019x', 'Diamond Technologies DT-019X / Avance Logic ALS-007'),
		('snd-mixart', 'Digigram miXart'),
		('snd-pcxhr', 'Digigram pcxhr 0.8.4'),
		('snd-vx222', 'Digigram VX222 V2/Mic'),
		('snd-vxpocket', 'Digigram VXPocket'),
		('snd-dummy', 'Dummy soundcard (/dev/null)'),
		('snd-virmidi', 'Dummy soundcard for virtual rawmidi devices'),
		('snd-darla20', 'Echoaudio Darla20 soundcards driver'),
		('snd-darla24', 'Echoaudio Darla24 soundcards driver'),
		('snd-echo3g', 'Echoaudio Echo3G soundcards driver'),
		('snd-gina20', 'Echoaudio Gina20 soundcards driver'),
		('snd-gina24', 'Echoaudio Gina24 soundcards driver'),
		('snd-indigodj', 'Echoaudio Indigo DJ soundcards driver'),
		('snd-indigoio', 'Echoaudio Indigo IO soundcards driver'),
		('snd-indigo', 'Echoaudio Indigo soundcards driver'),
		('snd-layla20', 'Echoaudio Layla20 soundcards driver'),
		('snd-layla24', 'Echoaudio Layla24 soundcards driver'),
		('snd-mia', 'Echoaudio Mia soundcards driver'),
		('snd-mona', 'Echoaudio Mona soundcards driver'),
		('snd-emu10k1', 'EMU10K1'),
		('snd-emu10k1x', 'EMU10K1X'),
		('snd-emu8000-synth', 'Emu8000 synth plug-in routine'),
		('snd-ens1370', 'Ensoniq AudioPCI ES1370'),
		('snd-ens1371', 'Ensoniq/Creative AudioPCI ES1371+'),
		('snd-sscape', 'ENSONIQ SoundScape PnP driver'),
		('snd-es968', 'ESS AudioDrive ES968'),
		('snd-es18xx', 'ESS ES18xx AudioDrive'),
		('snd-es1688-lib', 'ESS ESx688 lowlevel module'),
		('snd-es1968', 'ESS Maestro'),
		('snd-maestro3', 'ESS Maestro3 PCI'),
		('snd-es1938', 'ESS Solo-1'),
		('snd-fm801', 'ForteMedia FM801'),
		('snd-ad1848', 'Generic AD1848/AD1847/CS4248'),
		('snd-cs4231', 'Generic CS4231'),
		('snd-es1688', 'Generic ESS ES1688/ES688 AudioDrive'),
		('snd-i2c', 'Generic i2c interface for ALSA'),
		('snd-util-mem', 'Generic memory management routines for soundcard memory allocation'),
		('snd-gusclassic', 'Gravis UltraSound Classic'),
		('snd-gusextreme', 'Gravis UltraSound Extreme'),
		('snd-gusmax', 'Gravis UltraSound MAX'),
		('snd-ice1712', 'ICEnsemble ICE1712 (Envy24)'),
		('snd-ice17xx-ak4xxx', 'ICEnsemble ICE17xx <-> AK4xxx AD/DA chip interface'),
		('snd-cs8427', 'IEC958 (S/PDIF) receiver & transmitter by Cirrus Logic'),
		('snd-intel8x0', 'Intel 82801AA,82901AB,i810,i820,i830,i840,i845,MX440; SiS 7012; Ali 5455'),
		('snd-intel8x0m', 'Intel 82801AA,82901AB,i810,i820,i830,i840,i845,MX440; SiS 7013; NVidia MCP/2/2S/3 modems'),
		('snd-hda-intel', 'Intel HDA driver'),
		('kahlua', 'Kahlua VSA1 PCI Audio'),
		('snd-korg1212', 'korg1212'),
		('snd-serial-u16550', 'MIDI serial u16550'),
		('snd-miro', 'Miro miroSOUND PCM1 pro, PCM12, PCM20 Radio'),
		('pss', 'Module for PSS sound cards (based on AD1848, ADSP-2115 and ESC614).'),
		('snd-mtpav', 'MOTU MidiTimePiece AV multiport MIDI'),
		('snd-mpu401', 'MPU-401 UART'),
		('snd-nm256', 'NeoMagic NM256AV/ZX'),
		('snd-opl4-lib', 'OPL4 driver'),
		('snd-opl4-synth', 'OPL4 wavetable synth driver'),
		('snd-opti92x-ad1848', 'OPTi92X - AD1848'),
		('snd-opti92x-cs4231', 'OPTi92X - CS4231'),
		('snd-opti93x', 'OPTi93X'),
		('sb', 'OSS Soundblaster ISA PnP and legacy sound driver'),
		('snd-riptide', 'riptide'),
		('snd-rme32', 'RME Digi32, Digi32/8, Digi32 PRO'),
		('snd-rme9652', 'RME Digi9652/Digi9636'),
		('snd-rme96', 'RME Digi96, Digi96/8, Digi96/8 PRO, Digi96/8 PST, Digi96/8 PAD'),
		('snd-hdsp', 'RME Hammerfall DSP'),
		('snd-hdspm', 'RME HDSPM'),
		('snd-sb16-dsp', 'Routines for control of 16-bit SoundBlaster cards and clones'),
		('snd-sb8-dsp', 'Routines for control of 8-bit SoundBlaster cards and clones'),
		('snd-ad1848-lib', 'Routines for control of AD1848/AD1847/CS4248'),
		('snd-opl3-lib', 'Routines for control of AdLib FM cards (OPL2/OPL3/OPL4 chips)'),
		('snd-ak4xxx-adda', 'Routines for control of AK452x / AK43xx AD/DA converters'),
		('snd-cs4231-lib', 'Routines for control of CS4231(A)/CS4232/InterWave & compatible chips'),
		('snd-cs4236-lib', 'Routines for control of CS4235/4236B/4237B/4238B/4239 chips'),
		('snd-emu10k1-synth', 'Routines for control of EMU10K1 WaveTable synth'),
		('snd-emux-synth', 'Routines for control of EMU WaveTable chip'),
		('snd-mpu401-uart', 'Routines for control of MPU-401 in UART mode'),
		('snd-tea575x-tuner', 'Routines for control of TEA5757/5759 Philips AM/FM radio tuner chips'),
		('snd-tea6330t', 'Routines for control of the TEA6330T circuit via i2c bus'),
		('snd-gus-lib', 'Routines for Gravis UltraSound soundcards'),
		('snd-sonicvibes', 'S3 SonicVibes PCI'),
		('snd-sb8', 'Sound Blaster 1.0/2.0/Pro'),
		('snd-sb16', 'Sound Blaster 16'),
		('snd-sbawe', 'Sound Blaster AWE'),
		('snd-pdaudiocf', 'Sound Core PDAudio-CF'),
		('snd-usb-usx2y', 'TASCAM US-X2Y Version 0.8.7.2'),
		('snd-trident', 'Trident 4D-WaveDX/NX & SiS SI7018'),
		('trident', 'Trident 4DWave/SiS 7018/ALi 5451 and Tvia/IGST CyberPro5050 PCI Audio Driver'),
		('snd-wavefront', 'Turtle Beach Wavefront'),
		('snd-ac97-codec', 'Universal interface for Audio Codec \'97'),
		('snd-ak4531-codec', 'Universal routines for AK4531 codec'),
		('snd-usb-audio', 'USB Audio'),
		('snd-usb-lib', 'USB Audio/MIDI helper module'),
		('snd-ice1724', 'VIA ICEnsemble ICE1724/1720 (Envy24HT/PT)'),
		('snd-via82xx', 'VIA VT82xx audio'),
		('snd-via82xx-modem', 'VIA VT82xx modem'),
		('snd-ymfpci', 'Yamaha DS-1 PCI'),
		('snd-opl3sa2', 'Yamaha OPL3SA2+'),
	]


class GroupDN(UDM_Objects):
	"""
	Syntax to select a group from |LDAP| by |DN|.

	.. seealso::
		* :py:class:`GroupID`
		* :py:class:`GroupDNOrEmpty`
	"""
	udm_modules = ('groups/group', )
	use_objects = False


class GroupDNOrEmpty(GroupDN):
	"""
	Syntax to select a group from |LDAP| by |DN| or none.

	.. seealso::
		* :py:class:`GroupID`
		* :py:class:`GroupDN`
	"""
	empty_value = True


class UserDN(UDM_Objects):
	"""
	Syntax to select an user from |LDAP| by |DN|.

	.. seealso::
		* :py:class:`UserID`
	"""
	udm_modules = ('users/user', )
	use_objects = False


class HostDN(UDM_Objects):
	"""
	Syntax to select a host from |LDAP| by |DN|.

	.. seealso::
		* :py:class:`IComputer_FQDN`
	"""
	udm_modules = ('computers/computer', )
	udm_filter = '!(univentionObjectFlag=docker)'


class UserID(UDM_Objects):
	"""
	Syntax to select an user from |LDAP| by numeric user identifier.

	.. seealso::
		* :py:class:`UserDN`.
	>>> UserID.parse('0')
	'0'
	>>> UserID.parse(0)
	'0'
	"""
	udm_modules = ('users/user', )
	key = '%(uidNumber)s'
	label = '%(username)s'
	regex = re.compile('^[0-9]+$')
	static_values = (('0', 'root'), )
	use_objects = False

	type_class = univention.admin.types.IntegerType

	@classmethod
	def parse(cls, text):
		if isinstance(text, int):
			text = str(text)
		return super(cls, cls).parse(text)


class GroupID(UDM_Objects):
	"""
	Syntax to select a group from |LDAP| by numeric user identifier.

	.. seealso::
		* :py:class:`GroupDN`
		* :py:class:`GroupDNOrEmpty`
	>>> GroupID.parse('5000')
	'5000'
	>>> GroupID.parse(5000)
	'5000'
	"""
	udm_modules = ('groups/group', )
	key = '%(gidNumber)s'
	label = '%(name)s'
	regex = re.compile('^[0-9]+$')
	static_values = (('0', 'root'), )
	use_objects = False

	type_class = univention.admin.types.IntegerType

	@classmethod
	def parse(cls, text):
		if isinstance(text, int):
			text = str(text)
		return super(cls, cls).parse(text)


class PortalComputer(UDM_Objects):
	"""
	Syntax to select a |UCS| host from |LDAP| by |FQDN| running the portal service.
	"""
	udm_modules = ('computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver')
	udm_filter = '!(univentionObjectFlag=docker)'
	use_objects = False


class IComputer_FQDN(UDM_Objects):
	"""
	Syntax to select a host from |LDAP| by |FQDN|.

	.. seealso::
		* :py:class:`HostDN`
	"""
	udm_modules = ()
	key = '%(name)s.%(domain)s'  # '%(fqdn)s' optimized for LDAP lookup. Has to be in sync with the computer handlers' info['fqdn']
	label = '%(name)s.%(domain)s'  # '%(fqdn)s'
	regex = re.compile(r'(?=^.{1,254}$)(^(?:(?!\d+\.)[a-zA-Z0-9_\-]{1,63}\.?)+(?:[a-zA-Z0-9]{2,})$)')  # '(^[a-zA-Z])(([a-zA-Z0-9-_]*)([a-zA-Z0-9]$))?$' )
	error_message = _('Not a valid FQDN')
	udm_filter = '!(univentionObjectFlag=docker)'
	simple = True


class DomainController(IComputer_FQDN):
	"""
	Syntax to select a |UCS| Directory Node from |LDAP| by |FQDN|.
	"""
	udm_modules = ('computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave')
	use_objects = False


class Windows_Server(IComputer_FQDN):
	"""
	Syntax to select a Windows server from |LDAP| by |FQDN|.
	"""
	udm_modules = ('computers/windows', 'computers/windows_domaincontroller')


class UCS_Server(IComputer_FQDN):
	"""
	Syntax to select a |UCS| host from |LDAP| by |FQDN|.
	"""
	udm_modules = ('computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver')
	use_objects = False


class ServicePrint_FQDN(IComputer_FQDN):
	"""
	Syntax to select a |UCS| host from |LDAP| by |FQDN| offering print services.

	.. seealso::
		* :py:class:`ServicePrint`
	"""
	udm_modules = ('computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver')
	udm_filter = '(&(!(univentionObjectFlag=docker))(service=Print))'


class MailHomeServer(IComputer_FQDN):
	"""
	Syntax to select a |UCS| host from |LDAP| by |FQDN| offering |IMAP| services.

	.. seealso::
		* :py:class:`ServiceMail`
	"""
	udm_modules = ('computers/computer', )
	udm_filter = '(&(!(univentionObjectFlag=docker))(objectClass=univentionHost)(service=IMAP))'
	empty_value = True


class KDE_Profile(UDM_Attribute):
	"""
	Syntax to select a KDE profile from lists stored in |LDAP| using :py:class:`univention.admin.handlers.settings.default`.
	"""
	udm_module = 'settings/default'
	attribute = 'defaultKdeProfiles'


class primaryGroup(ldapDn):
	"""
	Syntax to select a group from |LDAP|.

	.. deprecated:: 3.1-0
		Use :py:class:`GroupDN`.
	"""
	searchFilter = 'objectClass=posixGroup'
	description = _('Primary Group')


class primaryGroup2(ldapDn):
	"""
	Syntax to select a group from |LDAP|.

	.. deprecated:: 3.1-0
		Use :py:class:`GroupDN`.
	"""
	searchFilter = 'objectClass=posixGroup'
	description = _('Primary Group')


class network(UDM_Objects):
	"""
	Syntax to select a network declaration from |LDAP| using :py:class:`univention.admin.handlers.networks.network`.
	"""
	udm_modules = ('networks/network',)
	description = _('Network')
	label = '%(name)s'
	empty_value = True


class IP_AddressList(ipAddress, select):
	"""
	Syntax to select an IP address from the lists of addresses stored with the machine account.
	"""
	choices = ()
	depends = 'ip'


class IP_AddressListEmpty(IP_AddressList):
	"""
	Syntax to select no or an IP address from the lists of addresses stored with the machine account.
	"""
	choices = [('', _('From known-hosts pool'))]
	empty_value = True

	@classmethod
	def parse(cls, text):
		return super(IP_AddressListEmpty, cls).parse(text) if text else ''


class MAC_AddressList(MAC_Address, select):
	"""
	Syntax to select a MAC address from the lists of addresses stored with the machine account.
	"""
	choices = ()
	depends = 'mac'


class DNS_ForwardZone(UDM_Objects):
	"""
	Syntax to select no or one |DNS| forward zone from |LDAP| using :py:class:`univention.admin.handlers.dns.forward_zone`.

	.. seealso::
		* :py:class:`DNS_ReverseZone`
		* :py:class:`DNS_ForwardZoneNonempty`
	"""
	description = _('DNS forward zone')
	udm_modules = ('dns/forward_zone', )
	empty_value = True
	use_objects = False


class DNS_ReverseZone(UDM_Objects):
	"""
	Syntax to select no or one |DNS| reverse zone from |LDAP| using :py:class:`univention.admin.handlers.dns.reverse_zone`.

	.. seealso::
		* :py:class:`DNS_ForwardZone`
		* :py:class:`DNS_ReverseZoneNonempty`
	"""
	description = _('DNS reverse zone')
	udm_modules = ('dns/reverse_zone', )
	label = '%(subnet)s'
	empty_value = True
	use_objects = False


class DNS_ReverseZoneNonempty(DNS_ReverseZone):
	"""
	Syntax to select one |DNS| reverse zone from |LDAP| using :py:class:`univention.admin.handlers.dns.reverse_zone`.

	.. seealso::
		* :py:class:`DNS_ForwardZoneNonempty`
		* :py:class:`DNS_ReverseZone`
	"""
	empty_value = False


class DNS_ForwardZoneNonempty(DNS_ForwardZone):
	"""
	Syntax to select one |DNS| forward zone from |LDAP| using :py:class:`univention.admin.handlers.dns.forward_zone`.

	.. seealso::
		* :py:class:`DNS_ReverseZoneNonempty`
		* :py:class:`DNS_ForwardZone`
	"""
	empty_value = False


class dnsEntry(complex):
	"""
	Syntax to configure a |DNS| forward zone entry for a computer.
	"""
	description = _('DNS Entry')
	subsyntaxes = ((_('DNS forward zone'), DNS_ForwardZoneNonempty), (_('IP address'), IP_AddressList))
	subsyntax_names = ('forward-zone', 'ip')
	size = ('One', 'One')
	min_elements = 1


class dnsEntryReverse(complex):
	"""
	Syntax to configure a |DNS| reverse zone entry for a computer.
	"""
	description = _('DNS Entry Reverse')
	subsyntaxes = ((_('DNS reverse zone'), DNS_ReverseZoneNonempty), (_('IP address'), IP_AddressList))
	subsyntax_names = ('reverse-zone', 'ip')
	size = ('One', 'One')
	min_elements = 1


class DNS_ForwardZoneList(select):
	"""
	Syntax to select |DNS| forward zone for alias entries.
	>>> DNS_ForwardZoneList.parse('some name')
	'some name'
	"""
	depends = 'dnsEntryZoneForward'


class dnsEntryAlias(complex):
	"""
	Syntax to configure a |DNS| alias record.
	"""
	description = _('DNS Entry Alias')
	subsyntaxes = ((_('Zone of existing host record'), DNS_ForwardZoneList), (_('DNS forward zone'), DNS_ForwardZone), (_('Alias'), DNS_Name))
	subsyntax_names = ('zone', 'forward-zone', 'alias')
	size = ('TwoThirds', 'TwoThirds', 'TwoThirds')


class dhcpService(UDM_Objects):
	"""
	Syntax to select a |DHCP| service from |LDAP| using :py:class:`univention.admin.handlers.dhcp.service`.
	"""
	udm_modules = ('dhcp/service', )
	description = _('DHCP service')
	label = '%(name)s'
	empty_value = True


class dhcpEntry(complex):
	"""
	Syntax to configure a |DHCP| host entry.
	>>> dhcpEntry.parse(["cn=service", "aabbccddeeff"])
	['cn=service', '', 'aa:bb:cc:dd:ee:ff']
	>>> dhcpEntry.parse(["cn=service", "127.0.0.1", "aabbccddeeff"])
	['cn=service', '127.0.0.1', 'aa:bb:cc:dd:ee:ff']
	"""
	min_elements = 1
	all_required = False
	subsyntaxes = (
		(_('DHCP service'), dhcpService),
		(_('IP address'), IP_AddressListEmpty),
		(_('MAC address'), MAC_AddressList),
	)
	subsyntax_names = ('service', 'ip', 'mac')
	description = _('DHCP Entry')
	size = ('TwoThirds', 'TwoThirds', 'TwoThirds')

	@classmethod
	def parse(cls, text):
		service, ip, mac = text[0], '', ''
		try:
			mac = text[1:][-1]
			ip, mac = text[1:]
		except (IndexError, ValueError):
			pass
		return super(dhcpEntry, cls).parse([service, ip, mac])


class DHCP_Option(complex):
	"""
	Syntax to enter free-form |DHCP| options.
	"""
	subsyntaxes = ((_('Name'), string), (_('Value'), string))
	# subsyntax_names = ('name', 'value')
	subsyntax_key_value = True
	description = _('DHCP option')
	size = ('One', 'One')


class WritableShare(UDM_Objects):
	"""
	Syntax for selecting defined writeable |NFS| shares.

	.. seealso::
		* :py:class:`nfsShare`
	"""
	udm_modules = ('shares/share', )
	udm_filter = 'writeable=1'
	label = _('%(name)s (%(path)s on %(host)s)')  # ldap-optimized for shares/share.description()
	size = 'OneAndAHalf'
	empty_value = True
	use_objects = False

# class share(ldapDnOrNone):
# 	searchFilter='(objectClass=univentionShare)'
# 	description=_('Share')


class AllowDenyIgnore(select):
	"""
	Syntax class for a tri-state select between allow, deny and ignore.
	"""
	choices = [
		('', ''),
		('allow', _('allow')),
		('deny', _('deny')),
		('ignore', _('ignore'))
	]


class IStates(select):
	"""
	Base syntax to select item from list of choices with a mapping between Python and LDAP values.
	"""
	values = []  # type: Sequence[Tuple[Any, Tuple[str, str]]]
	"""Map Python type to 2-tuple (LDAP-value, translated-text)."""

	@ClassProperty
	def choices(cls):
		return list(map(lambda x: (x[1]), cls.values))

	@classmethod
	def parse(cls, text):
		for value, (choice, label) in cls.values:
			if text == value or text == choice:
				return choice
		raise univention.admin.uexceptions.valueInvalidSyntax(_('Invalid choice.'))

	@classmethod
	def get_object_property_filter(cls, object_property, object_property_value):
		try:
			state_of_object_property_value = [state for state, (ldap_value, _) in cls.values if ldap_value == object_property_value][0]
			if state_of_object_property_value not in (None, True, False):
				return ''
		except IndexError:
			return ''

		states_of_this_syntax = [state for state, _ in cls.values]
		not_set_filter = '(!(%s=*))' % object_property
		compare_filter = '%s=%s' % (object_property, object_property_value)
		if state_of_object_property_value is None:
			return not_set_filter
		elif state_of_object_property_value is False and None not in states_of_this_syntax:
			# This is for IStates that are shown as Checkboxes in the frontend.
			# If the user searches for False we also want to include objects where the property is not set in ldap.
			return '(|(%s)%s)' % (compare_filter, not_set_filter)
		else:
			return compare_filter

	@classmethod
	def sanitize_property_search_value(cls, search_value):
		if search_value in (True, False):
			# This is for IStates that are shown as Checkboxes in the frontend. In these cases we get a boolean as search value.
			# Map the boolean to the string that is stored in ldap
			for state, (ldap_value, _) in cls.values:
				if state == search_value:
					return ldap_value
		return search_value


class AllowDeny(IStates):
	"""
	Syntax class for a tri-state select between `None`, `"allow"` and `"deny"`.
	>>> AllowDeny.choices
	[('', ''), ('allow', 'allow'), ('deny', 'deny')]
	>>> AllowDeny.sanitize_property_search_value(True)
	'allow'
	>>> AllowDeny.sanitize_property_search_value(False)
	'deny'
	"""
	values = (
		(None, ('', '')),
		(True, ('allow', _('allow'))),
		(False, ('deny', _('deny')))
	)
	type_class = univention.admin.types.TriBooleanType


class booleanNone(IStates):
	"""
	Syntax class for a tri-state select between `None`, `"yes"` and `"no"`.
	>>> booleanNone.parse("yes")
	'yes'
	>>> booleanNone.parse("no")
	'no'
	>>> booleanNone.parse("maybe") #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	"""
	values = (
		(None, ('', '')),
		(True, ('yes', _('Yes'))),
		(False, ('no', _('No')))
	)
	type_class = univention.admin.types.TriBooleanType


class auto_one_zero(select):
	"""
	Syntax class for a tri-state select between `"Auto"`, `"Yes"` and `"No"`.
	"""
	choices = [
		('Auto', _('Auto')),
		('1', _('Yes')),
		('0', _('No'))
	]
	# type_class = univention.admin.types.TriBooleanType


class TrueFalse(IStates):
	"""
	Syntax class for a tri-state select between `None`, `"true"` and `"false"`.
	>>> TrueFalse.sanitize_property_search_value(True)
	'true'
	>>> TrueFalse.sanitize_property_search_value(False)
	'false'
	"""
	values = (
		(None, ('', '')),
		(True, ('true', _('True'))),
		(False, ('false', _('False')))
	)
	type_class = univention.admin.types.TriBooleanType


class TrueFalseUpper(IStates):
	"""
	Syntax class for a tri-state select between `None`, `"TRUE"` and `"FALSE"`.
	>>> TrueFalseUpper.sanitize_property_search_value(True)
	'TRUE'
	>>> TrueFalseUpper.sanitize_property_search_value(False)
	'FALSE'
	>>> TrueFalseUpper.get_object_property_filter("myAttr", "wrong...")
	''
	>>> TrueFalseUpper.get_object_property_filter("myAttr", "TRUE")
	'myAttr=TRUE'
	>>> TrueFalseUpper.get_object_property_filter("myAttr", "")
	'(!(myAttr=*))'
	"""
	values = (
		(None, ('', '')),
		(True, ('TRUE', _('True'))),
		(False, ('FALSE', _('False')))
	)
	type_class = univention.admin.types.TriBooleanType


class TrueFalseUp(IStates):
	"""
	Syntax for bool'ean value matching |LDAP| `boolean` (|OID| 1.3.6.1.4.1.1466.115.121.1.7).
	>>> TrueFalseUp.sanitize_property_search_value(True)
	'TRUE'
	>>> TrueFalseUp.sanitize_property_search_value(False)
	'FALSE'
	>>> TrueFalseUp.get_object_property_filter("myAttr", "FALSE")
	'(|(myAttr=FALSE)(!(myAttr=*)))'
	"""
	values = (
		(True, ('TRUE', _('True'))),
		(False, ('FALSE', _('False')))
	)
	type_class = univention.admin.types.BooleanType


class AppActivatedTrue(TrueFalseUp):
	pass


class OkOrNot(IStates):
	"""
	Syntax class to a boolean select between `"OK"` and `"Not"`.
	"""
	values = (
		(True, ('OK', _('OK'))),
		(False, ('Not', _('Not OK')))
	)
	type_class = univention.admin.types.BooleanType


class AppActivatedOK(OkOrNot):
	pass


class ddnsUpdateStyle(select):
	"""
	Syntax to select the |DHCP| dynamic |DNS| update style.
	"""
	choices = [
		('', ''),
		('ad-hoc', _('ad-hoc')),
		('interim', _('interim')),
		('none', _('none'))
	]


class ddnsUpdates(IStates):
	"""
	Syntax class for a tri-state select between `None`, `"on"` and `"off"`.
	"""
	values = (
		(None, ('', '')),
		(True, ('on', _('on'))),
		(False, ('off', _('off')))
	)
	type_class = univention.admin.types.TriBooleanType


class netbiosNodeType(select):
	"""
	Syntax to select the Windows name server mode.
	"""
	choices = [
		('', ''),
		('1', '1 B-node: Broadcast - no WINS'),
		('2', '2 P-node: Peer - WINS only'),
		('4', '4 M-node: Mixed - broadcast, then WINS'),
		('8', '8 H-node: Hybrid - WINS, then broadcast'),
	]


class kdeProfile(select):
	"""
	Syntax to select |KDE| profile type.
	"""
	choices = [
		('', 'none'),
		('/home/kde.restricted', 'restricted'),
		('/home/kde.lockeddown', 'locked down'),
	]


class language(select):
	"""
	Syntax for selecting a language by name.
	"""
	choices = [
		('', ''),
		('af_ZA', 'Afrikaans/South Africa'),
		('af_ZA.UTF-8', 'Afrikaans/South Africa(UTF-8)'),
		('sq_AL', 'Albanian/Albania'),
		('sq_AL.UTF-8', 'Albanian/Albania(UTF-8)'),
		('am_ET', 'Amharic/Ethiopia'),
		('ar_DZ', 'Arabic/Algeria'),
		('ar_DZ.UTF-8', 'Arabic/Algeria(UTF-8)'),
		('ar_BH', 'Arabic/Bahrain'),
		('ar_BH.UTF-8', 'Arabic/Bahrain(UTF-8)'),
		('ar_EG', 'Arabic/Egypt'),
		('ar_EG.UTF-8', 'Arabic/Egypt(UTF-8)'),
		('ar_IN', 'Arabic/India'),
		('ar_IQ', 'Arabic/Iraq'),
		('ar_IQ.UTF-8', 'Arabic/Iraq(UTF-8)'),
		('ar_JO', 'Arabic/Jordan'),
		('ar_JO.UTF-8', 'Arabic/Jordan(UTF-8)'),
		('ar_KW', 'Arabic/Kuwait'),
		('ar_KW.UTF-8', 'Arabic/Kuwait(UTF-8)'),
		('ar_LB', 'Arabic/Lebanon'),
		('ar_LB.UTF-8', 'Arabic/Lebanon(UTF-8)'),
		('ar_LY', 'Arabic/Libyan Arab Jamahiriya'),
		('ar_LY.UTF-8', 'Arabic/Libyan Arab Jamahiriya(UTF-8)'),
		('ar_MA', 'Arabic/Morocco'),
		('ar_MA.UTF-8', 'Arabic/Morocco(UTF-8)'),
		('ar_OM', 'Arabic/Oman'),
		('ar_OM.UTF-8', 'Arabic/Oman(UTF-8)'),
		('ar_QA', 'Arabic/Qatar'),
		('ar_QA.UTF-8', 'Arabic/Qatar(UTF-8)'),
		('ar_SA', 'Arabic/Saudi Arabia'),
		('ar_SA.UTF-8', 'Arabic/Saudi Arabia(UTF-8)'),
		('ar_SD', 'Arabic/Sudan'),
		('ar_SD.UTF-8', 'Arabic/Sudan(UTF-8)'),
		('ar_SY', 'Arabic/Syrian Arab Republic'),
		('ar_SY.UTF-8', 'Arabic/Syrian Arab Republic(UTF-8)'),
		('ar_TN', 'Arabic/Tunisia'),
		('ar_TN.UTF-8', 'Arabic/Tunisia(UTF-8)'),
		('ar_AE', 'Arabic/United Arab Emirates'),
		('ar_AE.UTF-8', 'Arabic/United Arab Emirates(UTF-8)'),
		('ar_YE', 'Arabic/Yemen'),
		('ar_YE.UTF-8', 'Arabic/Yemen(UTF-8)'),
		('an_ES', 'Aragonese/Spain'),
		('an_ES.UTF-8', 'Aragonese/Spain(UTF-8)'),
		('hy_AM', 'Armenian/Armenia'),
		('az_AZ', 'Azeri/Azerbaijan'),
		('eu_ES@euro', 'Basque/Spain'),
		('eu_ES.UTF-8', 'Basque/Spain(UTF-8)'),
		('be_BY', 'Belarusian/Belarus'),
		('be_BY.UTF-8', 'Belarusian/Belarus(UTF-8)'),
		('bn_BD', 'Bengali/BD'),
		('bn_IN', 'Bengali/India'),
		('bs_BA', 'Bosnian/Bosnia and Herzegowina'),
		('bs_BA.UTF-8', 'Bosnian/Bosnia and Herzegowina(UTF-8)'),
		('br_FR@euro', 'Breton/France'),
		('br_FR.UTF-8', 'Breton/France(UTF-8)'),
		('bg_BG', 'Bulgarian/Bulgaria'),
		('bg_BG.UTF-8', 'Bulgarian/Bulgaria(UTF-8)'),
		('ca_ES@euro', 'Catalan/Spain'),
		('ca_ES.UTF-8', 'Catalan/Spain(UTF-8)'),
		('zh_HK', 'Chinese/Hong Kong'),
		('zh_HK.UTF-8', 'Chinese/Hong Kong(UTF-8)'),
		('zh_CN', 'Chinese/P.R. of China'),
		('zh_CN.UTF-8', 'Chinese/P.R. of China(UTF-8)'),
		('zh_SG', 'Chinese/Singapore'),
		('zh_SG.UTF-8', 'Chinese/Singapore(UTF-8)'),
		('zh_TW', 'Chinese/Taiwan R.O.C.'),
		('zh_TW.UTF-8', 'Chinese/Taiwan R.O.C.(UTF-8)'),
		('kw_GB', 'Cornish/Britain'),
		('kw_GB.UTF-8', 'Cornish/Britain(UTF-8)'),
		('hr_HR', 'Croatian/Croatia'),
		('hr_HR.UTF-8', 'Croatian/Croatia(UTF-8)'),
		('cs_CZ', 'Czech/Czech Republic'),
		('cs_CZ.UTF-8', 'Czech/Czech Republic(UTF-8)'),
		('da_DK', 'Danish/Denmark'),
		('da_DK.UTF-8', 'Danish/Denmark(UTF-8)'),
		('nl_BE@euro', 'Dutch/Belgium'),
		('nl_BE.UTF-8', 'Dutch/Belgium(UTF-8)'),
		('nl_NL@euro', 'Dutch/Netherlands'),
		('nl_NL.UTF-8', 'Dutch/Netherlands(UTF-8)'),
		('en_AU', 'English/Australia'),
		('en_AU.UTF-8', 'English/Australia(UTF-8)'),
		('en_BW', 'English/Botswana'),
		('en_BW.UTF-8', 'English/Botswana(UTF-8)'),
		('en_CA', 'English/Canada'),
		('en_CA.UTF-8', 'English/Canada(UTF-8)'),
		('en_DK', 'English/Denmark'),
		('en_DK.UTF-8', 'English/Denmark(UTF-8)'),
		('en_GB', 'English/Great Britain'),
		('en_GB.UTF-8', 'English/Great Britain(UTF-8)'),
		('en_HK', 'English/Hong Kong'),
		('en_HK.UTF-8', 'English/Hong Kong(UTF-8)'),
		('en_IN', 'English/India'),
		('en_IE@euro', 'English/Ireland'),
		('en_IE.UTF-8', 'English/Ireland(UTF-8)'),
		('en_NZ', 'English/New Zealand'),
		('en_NZ.UTF-8', 'English/New Zealand(UTF-8)'),
		('en_PH', 'English/Philippines'),
		('en_PH.UTF-8', 'English/Philippines(UTF-8)'),
		('en_SG', 'English/Singapore'),
		('en_SG.UTF-8', 'English/Singapore(UTF-8)'),
		('en_ZA', 'English/South Africa'),
		('en_ZA.UTF-8', 'English/South Africa(UTF-8)'),
		('en_US', 'English/USA'),
		('en_US.UTF-8', 'English/USA(UTF-8)'),
		('en_ZW', 'English/Zimbabwe'),
		('en_ZW.UTF-8', 'English/Zimbabwe(UTF-8)'),
		('eo_EO', 'Esperanto/Esperanto'),
		('et_EE', 'Estonian/Estonia'),
		('et_EE.UTF-8', 'Estonian/Estonia(UTF-8)'),
		('fo_FO', 'Faroese/Faroe Islands'),
		('fo_FO.UTF-8', 'Faroese/Faroe Islands(UTF-8)'),
		('fi_FI@euro', 'Finnish/Finland'),
		('fi_FI.UTF-8', 'Finnish/Finland(UTF-8)'),
		('fr_BE@euro', 'French/Belgium'),
		('fr_BE.UTF-8', 'French/Belgium(UTF-8)'),
		('fr_CA', 'French/Canada'),
		('fr_CA.UTF-8', 'French/Canada(UTF-8)'),
		('fr_FR@euro', 'French/France'),
		('fr_FR.UTF-8', 'French/France(UTF-8)'),
		('fr_LU@euro', 'French/Luxemburg'),
		('fr_LU.UTF-8', 'French/Luxemburg(UTF-8)'),
		('fr_CH', 'French/Switzerland'),
		('fr_CH.UTF-8', 'French/Switzerland(UTF-8)'),
		('gl_ES@euro', 'Galician/Spain'),
		('gl_ES.UTF-8', 'Galician/Spain(UTF-8)'),
		('ka_GE', 'Georgian/Georgia'),
		('ka_GE.UTF-8', 'Georgian/Georgia(UTF-8)'),
		('de_AT@euro', 'German/Austria'),
		('de_AT.UTF-8', 'German/Austria(UTF-8)'),
		('de_BE@euro', 'German/Belgium'),
		('de_BE.UTF-8', 'German/Belgium(UTF-8)'),
		('de_DE', 'German/Germany'),
		('de_DE.UTF-8', 'German/Germany(UTF-8)'),
		('de_DE@euro', 'German/Germany(euro)'),
		('de_LU@euro', 'German/Luxemburg'),
		('de_LU.UTF-8', 'German/Luxemburg(UTF-8)'),
		('de_CH', 'German/Switzerland'),
		('de_CH.UTF-8', 'German/Switzerland(UTF-8)'),
		('el_GR@euro', 'Greek/Greece'),
		('el_GR.UTF-8', 'Greek/Greece(UTF-8)'),
		('kl_GL', 'Greenlandic/Greenland'),
		('kl_GL.UTF-8', 'Greenlandic/Greenland(UTF-8)'),
		('iw_IL', 'Hebrew/Israel'),
		('iw_IL.UTF-8', 'Hebrew/Israel(UTF-8)'),
		('he_IL', 'Hebrew/Israel'),
		('he_IL.UTF-8', 'Hebrew/Israel(UTF-8)'),
		('hi_IN', 'Hindi/India'),
		('hu_HU', 'Hungarian/Hungary'),
		('hu_HU.UTF-8', 'Hungarian/Hungary(UTF-8)'),
		('is_IS', 'Icelandic/Iceland'),
		('is_IS.UTF-8', 'Icelandic/Iceland(UTF-8)'),
		('id_ID', 'Indonesian/Indonesia'),
		('id_ID.UTF-8', 'Indonesian/Indonesia(UTF-8)'),
		('ga_IE@euro', 'Irish/Ireland'),
		('ga_IE.UTF-8', 'Irish/Ireland(UTF-8)'),
		('it_IT@euro', 'Italian/Italy'),
		('it_IT.UTF-8', 'Italian/Italy(UTF-8)'),
		('it_CH', 'Italian/Switzerland'),
		('it_CH.UTF-8', 'Italian/Switzerland(UTF-8)'),
		('ja_JP', 'Japanese/Japan'),
		('ko_KR', 'Korean/Republic of Korea'),
		('lo_LA', 'Lao/Laos'),
		('lv_LV', 'Latvian/Latvia'),
		('lv_LV.UTF-8', 'Latvian/Latvia(UTF-8)'),
		('lt_LT', 'Lithuanian/Lithuania'),
		('lt_LT.UTF-8', 'Lithuanian/Lithuania(UTF-8)'),
		('lug_UG', 'Luganda/Uganda'),
		('mk_MK', 'Macedonian/Macedonia'),
		('mk_MK.UTF-8', 'Macedonian/Macedonia(UTF-8)'),
		('ms_MY', 'Malay/Malaysia'),
		('ms_MY.UTF-8', 'Malay/Malaysia(UTF-8)'),
		('ml_IN', 'Malayalam/India'),
		('mt_MT', 'Maltese/malta'),
		('mt_MT.UTF-8', 'Maltese/malta(UTF-8)'),
		('gv_GB', 'Manx Gaelic/Britain'),
		('gv_GB.UTF-8', 'Manx Gaelic/Britain(UTF-8)'),
		('mi_NZ', 'Maori/New Zealand'),
		('mi_NZ.UTF-8', 'Maori/New Zealand(UTF-8)'),
		('mr_IN', 'Marathi/India'),
		('mn_MN', 'Mongolian/Mongolia'),
		('se_NO', 'Northern Saami/Norway'),
		('nn_NO', 'Norwegian, Nynorsk/Norway'),
		('nn_NO.UTF-8', 'Norwegian, Nynorsk/Norway(UTF-8)'),
		('no_NO', 'Norwegian/Norway'),
		('no_NO.UTF-8', 'Norwegian/Norway(UTF-8)'),
		('oc_FR', 'Occitan/France'),
		('oc_FR.UTF-8', 'Occitan/France(UTF-8)'),
		('fa_IR', 'Persian/Iran'),
		('pl_PL', 'Polish/Poland'),
		('pl_PL.UTF-8', 'Polish/Poland(UTF-8)'),
		('pt_BR', 'Portuguese/Brasil'),
		('pt_BR.UTF-8', 'Portuguese/Brasil(UTF-8)'),
		('pt_PT@euro', 'Portuguese/Portugal'),
		('pt_PT.UTF-8', 'Portuguese/Portugal(UTF-8)'),
		('ro_RO', 'Romanian/Romania'),
		('ro_RO.UTF-8', 'Romanian/Romania(UTF-8)'),
		('ru_RU', 'Russian/Russia'),
		('ru_RU.UTF-8', 'Russian/Russia(UTF-8)'),
		('ru_UA', 'Russian/Ukraine'),
		('ru_UA.UTF-8', 'Russian/Ukraine(UTF-8)'),
		('gd_GB', 'Scots Gaelic/Great Britain'),
		('gd_GB.UTF-8', 'Scots Gaelic/Great Britain(UTF-8)'),
		('sr_YU@cyrillic', 'Serbian/Yugoslavia'),
		('sk_SK', 'Slovak/Slovak'),
		('sk_SK.UTF-8', 'Slovak/Slovak(UTF-8)'),
		('sl_SI', 'Slovenian/Slovenia'),
		('sl_SI.UTF-8', 'Slovenian/Slovenia(UTF-8)'),
		('st_ZA', 'Sotho/South Africa'),
		('st_ZA.UTF-8', 'Sotho/South Africa(UTF-8)'),
		('es_AR', 'Spanish/Argentina'),
		('es_AR.UTF-8', 'Spanish/Argentina(UTF-8)'),
		('es_BO', 'Spanish/Bolivia'),
		('es_BO.UTF-8', 'Spanish/Bolivia(UTF-8)'),
		('es_CL', 'Spanish/Chile'),
		('es_CL.UTF-8', 'Spanish/Chile(UTF-8)'),
		('es_CO', 'Spanish/Colombia'),
		('es_CO.UTF-8', 'Spanish/Colombia(UTF-8)'),
		('es_CR', 'Spanish/Costa Rica'),
		('es_CR.UTF-8', 'Spanish/Costa Rica(UTF-8)'),
		('es_DO', 'Spanish/Dominican Republic'),
		('es_DO.UTF-8', 'Spanish/Dominican Republic(UTF-8)'),
		('es_EC', 'Spanish/Ecuador'),
		('es_EC.UTF-8', 'Spanish/Ecuador(UTF-8)'),
		('es_SV', 'Spanish/El Salvador'),
		('es_SV.UTF-8', 'Spanish/El Salvador(UTF-8)'),
		('es_GT', 'Spanish/Guatemala'),
		('es_GT.UTF-8', 'Spanish/Guatemala(UTF-8)'),
		('es_HN', 'Spanish/Honduras'),
		('es_HN.UTF-8', 'Spanish/Honduras(UTF-8)'),
		('es_MX', 'Spanish/Mexico'),
		('es_MX.UTF-8', 'Spanish/Mexico(UTF-8)'),
		('es_NI', 'Spanish/Nicaragua'),
		('es_NI.UTF-8', 'Spanish/Nicaragua(UTF-8)'),
		('es_PA', 'Spanish/Panama'),
		('es_PA.UTF-8', 'Spanish/Panama(UTF-8)'),
		('es_PY', 'Spanish/Paraguay'),
		('es_PY.UTF-8', 'Spanish/Paraguay(UTF-8)'),
		('es_PE', 'Spanish/Peru'),
		('es_PE.UTF-8', 'Spanish/Peru(UTF-8)'),
		('es_PR', 'Spanish/Puerto Rico'),
		('es_PR.UTF-8', 'Spanish/Puerto Rico(UTF-8)'),
		('es_ES@euro', 'Spanish/Spain'),
		('es_ES.UTF-8', 'Spanish/Spain(UTF-8)'),
		('es_US', 'Spanish/USA'),
		('es_US.UTF-8', 'Spanish/USA(UTF-8)'),
		('es_UY', 'Spanish/Uruguay'),
		('es_UY.UTF-8', 'Spanish/Uruguay(UTF-8)'),
		('es_VE', 'Spanish/Venezuela'),
		('es_VE.UTF-8', 'Spanish/Venezuela(UTF-8)'),
		('sv_FI@euro', 'Swedish/Finland'),
		('sv_FI.UTF-8', 'Swedish/Finland(UTF-8)'),
		('sv_SE', 'Swedish/Sweden'),
		('sv_SE.UTF-8', 'Swedish/Sweden(UTF-8)'),
		('tl_PH', 'Tagalog/Philippines'),
		('tl_PH.UTF-8', 'Tagalog/Philippines(UTF-8)'),
		('tg_TJ', 'Tajik/Tajikistan'),
		('tg_TJ.UTF-8', 'Tajik/Tajikistan(UTF-8)'),
		('ta_IN', 'Tamil/India'),
		('tt_RU', 'Tatar/Tatarstan'),
		('te_IN', 'Telgu/India'),
		('th_TH', 'Thai/Thailand'),
		('th_TH.UTF-8', 'Thai/Thailand(UTF-8)'),
		('ti_ER', 'Tigrigna/Eritrea'),
		('ti_ET', 'Tigrigna/Ethiopia'),
		('tr_TR', 'Turkish/Turkey'),
		('tr_TR.UTF-8', 'Turkish/Turkey(UTF-8)'),
		('uk_UA', 'Ukrainian/Ukraine'),
		('uk_UA.UTF-8', 'Ukrainian/Ukraine(UTF-8)'),
		('ur_PK', 'Urdu/Pakistan'),
		('uz_UZ', 'Uzbek/Uzbekistan'),
		('uz_UZ.UTF-8', 'Uzbek/Uzbekistan(UTF-8)'),
		('vi_VN', 'Vietnamese/Vietnam'),
		('wa_BE@euro', 'Walloon/Belgium'),
		('wa_BE.UTF-8', 'Walloon/Belgium(UTF-8)'),
		('cy_GB', 'Welsh/Great Britain'),
		('cy_GB.UTF-8', 'Welsh/Great Britain(UTF-8)'),
		('xh_ZA', 'Xhosa/South Africa'),
		('xh_ZA.UTF-8', 'Xhosa/South Africa(UTF-8)'),
		('yi_US', 'Yiddish/USA'),
		('yi_US.UTF-8', 'Yiddish/USA(UTF-8)'),
		('zu_ZA', 'Zulu/South Africa'),
		('zu_ZA.UTF-8', 'Zulu/South Africa(UTF-8)'),
	]


class Month(select):
	"""
	Syntax to select the month of a year.
	"""
	choices = [
		('', ''),
		('all', _('all')),
		('January', _('January')),
		('February', _('February')),
		('March', _('March')),
		('April', _('April')),
		('May', _('May')),
		('June', _('June')),
		('July', _('July')),
		('August', _('August')),
		('September', _('September')),
		('October', _('October')),
		('November', _('November')),
		('December', _('December')),
	]


class Weekday(select):
	"""
	Syntax to select the day of a week.
	"""
	choices = [
		('', ''),
		('all', _('all')),
		('Monday', _('Monday')),
		('Tuesday', _('Tuesday')),
		('Wednesday', _('Wednesday')),
		('Thursday', _('Thursday')),
		('Friday', _('Friday')),
		('Saturday', _('Saturday')),
		('Sunday', _('Sunday')),
	]


class Day(select):
	"""
	Syntax to select the day of a month.
	"""
	choices = [
		('', ''),
		('all', _('all')),
		('1', '1'),
		('2', '2'),
		('3', '3'),
		('4', '4'),
		('5', '5'),
		('6', '6'),
		('7', '7'),
		('8', '8'),
		('9', '9'),
		('10', '10'),
		('11', '11'),
		('12', '12'),
		('13', '13'),
		('14', '14'),
		('15', '15'),
		('16', '16'),
		('17', '17'),
		('18', '18'),
		('19', '19'),
		('20', '20'),
		('21', '21'),
		('22', '22'),
		('23', '23'),
		('24', '24'),
		('25', '25'),
		('26', '26'),
		('27', '27'),
		('28', '28'),
		('29', '29'),
		('30', '30'),
		('31', '31'),
	]


class Hour(select):
	"""
	Syntax to select the hour of a day or all or none.
	"""
	choices = [
		('', ''),
		('all', _('all')),
		('00', '0'),
		('1', '1'),
		('2', '2'),
		('3', '3'),
		('4', '4'),
		('5', '5'),
		('6', '6'),
		('7', '7'),
		('8', '8'),
		('9', '9'),
		('10', '10'),
		('11', '11'),
		('12', '12'),
		('13', '13'),
		('14', '14'),
		('15', '15'),
		('16', '16'),
		('17', '17'),
		('18', '18'),
		('19', '19'),
		('20', '20'),
		('21', '21'),
		('22', '22'),
		('23', '23'),
	]


class HourSimple(select):
	"""
	Syntax to select the hour of a day.
	"""
	choices = [
		('00', '0'),
		('1', '1'),
		('2', '2'),
		('3', '3'),
		('4', '4'),
		('5', '5'),
		('6', '6'),
		('7', '7'),
		('8', '8'),
		('9', '9'),
		('10', '10'),
		('11', '11'),
		('12', '12'),
		('13', '13'),
		('14', '14'),
		('15', '15'),
		('16', '16'),
		('17', '17'),
		('18', '18'),
		('19', '19'),
		('20', '20'),
		('21', '21'),
		('22', '22'),
		('23', '23'),
	]


class Minute(select):
	"""
	Syntax to select the minute of a hour or all or none.
	"""
	choices = [
		('', ''),
		('all', _('all')),
		('00', '0'),
		('5', '5'),
		('10', '10'),
		('15', '15'),
		('20', '20'),
		('25', '25'),
		('30', '30'),
		('35', '35'),
		('40', '40'),
		('45', '45'),
		('50', '50'),
		('55', '55'),
	]


class MinuteSimple(select):
	"""
	Syntax to select the minute of a hour.
	"""
	choices = [
		('00', '0'),
		('5', '5'),
		('10', '10'),
		('15', '15'),
		('20', '20'),
		('25', '25'),
		('30', '30'),
		('35', '35'),
		('40', '40'),
		('45', '45'),
		('50', '50'),
		('55', '55'),
	]


class UNIX_AccessRight(simple):
	"""
	Syntax to configure UNIX file permissions.

	.. seealso::
		* :py:class:`UNIX_AccessRight_extended`
	"""


class UNIX_AccessRight_extended(simple):
	r"""
	Syntax to configure UNIX file permissions including set\ |UID|, set\ |GID| and sticky bits.

	.. seealso::
		* :py:class:`UNIX_AccessRight`
	"""
	pass


class sambaGroupType(select):
	"""
	Syntax to select Samba group type.
	"""
	choices = [
		('', ''),
		('2', _('Domain Group')),
		('3', _('Local Group')),
		('5', _('Well-Known Group'))
	]


class adGroupType(select):
	"""
	Syntax to select Active Directory group type.
	"""
	choices = [
		('', ''),
		('-2147483643', _('Local (Type: Security)')),
		('-2147483646', _('Global (Type: Security)')),
		('-2147483640', _('Universal (Type: Security)')),
		('-2147483644', _('Domain local (Type: Security)')),
		('4', _('Local (Type: Distribution)')),
		('2', _('Global (Type: Distribution)')),
		('8', _('Universal (Type: Distribution)')),
	]


class SambaLogonHours(MultiSelect):
	"""
	Syntax to select hour slots per day for Samba login.
	>>> SambaLogonHours.parse("162 163")
	[162, 163]
	>>> SambaLogonHours.parse("5000") #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	choices = [(idx * 24 + hour, '%s %d-%d' % (day, hour, hour + 1)) for idx, day in ((0, _('Sun')), (1, _('Mon')), (2, _('Tue')), (3, _('Wed')), (4, _('Thu')), (5, _('Fri')), (6, _('Sat'))) for hour in range(24)]

	type_class = univention.admin.types.SambaLogonHours

	@classmethod
	def parse(self, value):
		# required for UDM CLI: in this case the keys MUST be of type int
		if isinstance(value, six.string_types):
			if len(value) == 42 and not value.strip('abcdef0123456789'):
				from univention.admin.handlers.users.user import logonHoursUnmap
				value = logonHoursUnmap([value.encode('ASCII')])
			else:
				value = list(map(lambda x: int(x), shlex.split(value)))

		return super(SambaLogonHours, self).parse(value)

	@classmethod
	def tostring(self, value):
		# type: (list) -> str
		if value is None:
			return value
		# better show the bit string. See Bug #33703
		from univention.admin.handlers.users.user import logonHoursMap
		value = logonHoursMap(value)
		if value is not None:
			value = value.decode('ASCII')
		return value


class SambaPrivileges(select):
	"""
	Syntax to select Samba privileges.
	"""
	empty_value = True
	choices = [
		('SeMachineAccountPrivilege', _('Add machines to domain')),
		('SeSecurityPrivilege', _('Manage auditing and security log')),
		('SeTakeOwnershipPrivilege', _('Take ownership of files or other objects')),
		('SeBackupPrivilege', _('Back up files and directories')),
		('SeRestorePrivilege', _('Restore files and directories')),
		('SeRemoteShutdownPrivilege', _('Force shutdown from a remote system')),
		('SePrintOperatorPrivilege', _('Manage printers')),
		('SeAddUsersPrivilege', _('Add users and groups to the domain')),
		('SeDiskOperatorPrivilege', _('Manage disk shares')),
	]


class UCSServerRole(select):
	"""
	Syntax to select |UCS| server role.
	>>> UCSServerRole.parse('Undefined')
	>>> UCSServerRole.parse('')
	>>> UCSServerRole.parse('domaincontroller_master')
	'domaincontroller_master'
	"""
	empty_value = True
	choices = [
		('domaincontroller_master', _('Primary Directory Node')),
		('domaincontroller_backup', _('Backup Directory Node')),
		('domaincontroller_slave', _('Replica Directory Node')),
		('memberserver', _('Managed Node')),
	]


class ServiceMail(UDM_Objects):
	"""
	Syntax to select a |UCS| host from |LDAP| by |DN| offering |SMTP| services.

	.. seealso::
		* :py:class:`MailHomeServer`
	"""
	udm_modules = ('computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver')
	udm_filter = '(&(!(univentionObjectFlag=docker))(service=SMTP))'


class ServicePrint(UDM_Objects):
	"""
	Syntax to select a |UCS| host from |LDAP| by |DN| offering print services.

	.. seealso::
		* :py:class:`ServicePrint_FQDN`
	"""
	udm_modules = ('computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver')
	udm_filter = '(&(!(univentionObjectFlag=docker))(service=Print))'


class Service(UDM_Objects):
	"""
	Syntax to select a |UCS| service types from |LDAP| using :py:class:`univention.admin.handlers.settings.service`.
	"""
	udm_modules = ('settings/service', )
	regex = None
	key = '%(name)s'
	label = '%(name)s'
	simple = True


class nfssync(select):
	"""
	Syntax to select the |NFS| synchronization type.
	"""
	choices = [
		('sync', _('synchronous')),
		('async', _('asynchronous'))
	]


class univentionAdminModules(select):
	"""
	Syntax for selecting an |UDM| module.

	>>> univention.admin.modules.update()
	>>> univentionAdminModules.parse('users/user')
	'users/user'
	>>> univentionAdminModules.parse('nonexistant') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	"""
	# we need a fallback
	choices = [
		('computers/domaincontroller_backup', 'Computer: Backup Directory Node'),
		('computers/domaincontroller_master', 'Computer: Primary Directory Node'),
		('computers/domaincontroller_slave', 'Computer: Replica Directory Node'),
		('computers/ipmanagedclient', 'Computer: IP Client'),
		('computers/linux', 'Computer: Linux'),
		('computers/macos', 'Computer: macOS Client'),
		('computers/memberserver', 'Computer: Managed Node'),
		('computers/trustaccount', 'Computer: Domain Trust Account'),
		('computers/ubuntu', 'Computer: Ubuntu'),
		('computers/windows', 'Computer: Windows'),
		('computers/windows_domaincontroller', 'Computer: Windows Domaincontroller'),
		('container/cn', 'Container: Container'),
		('container/dc', 'Container: Domain'),
		('container/ou', 'Container: Organizational Unit'),
		('dhcp/host', 'DHCP: Host'),
		('dhcp/pool', 'DHCP: Pool'),
		('dhcp/server', 'DHCP: Server'),
		('dhcp/service', 'DHCP: Service'),
		('dhcp/shared', 'DHCP: Shared Network'),
		('dhcp/sharedsubnet', 'DHCP: Shared Subnet'),
		('dhcp/subnet', 'DHCP: Subnet'),
		('dns/alias', 'DNS: Alias Record'),
		('dns/forward_zone', 'DNS: Forward Lookup Zone'),
		('dns/host_record', 'DNS: Host Record'),
		('dns/ns_record', 'DNS: NS Record'),
		('dns/ptr_record', 'DNS: Pointer'),
		('dns/reverse_zone', 'DNS: Reverse Lookup Zone'),
		('dns/srv_record', 'DNS: Service Record'),
		('dns/txt_record', 'DNS: TXT Record'),
		('groups/group', 'Group: Group'),
		('kerberos/kdcentry', 'Kerberos: KDC Entry'),
		('mail/domain', 'Mail: Mail Domains'),
		('mail/folder', 'Mail: IMAP Folder'),
		('mail/lists', 'Mail: Mailing Lists'),
		('nagios/nagios', 'Nagios object'),
		('nagios/service', 'Nagios service'),
		('nagios/timeperiod', 'Nagios time period'),
		('networks/network', 'Networks: Network'),
		('policies/admin_container', 'Policy: Univention Admin Container Settings'),
		('policies/desktop', 'Policy: Desktop'),
		('policies/dhcp_boot', 'Policy: DHCP Boot'),
		('policies/dhcp_dns', 'Policy: DHCP DNS'),
		('policies/dhcp_dnsupdate', 'Policy: DHCP DNS Update'),
		('policies/dhcp_leasetime', 'Policy: DHCP Lease Time'),
		('policies/dhcp_netbios', 'Policy: DHCP Netbios'),
		('policies/dhcp_routing', 'Policy: DHCP Routing'),
		('policies/dhcp_scope', 'Policy: DHCP Allow/Deny'),
		('policies/dhcp_statements', 'Policy: DHCP Statements'),
		('policies/ldapserver', 'Policy: LDAP Server'),
		('policies/maintenance', 'Policy: Maintenance'),
		('policies/masterpackages', 'Policy: Packages for Primary/Backup Nodes'),
		('policies/memberpackages', 'Policy: Packages for Managed Nodes'),
		('policies/nfsmounts', 'Policy: NFS mounts'),
		('policies/printserver', 'Policy: Print Server'),
		('policies/pwhistory', 'Policy: Password Policy'),
		('policies/registry', 'Policy: Univention Configuration Registry'),
		('policies/release', 'Policy: Release'),
		('policies/repositoryserver', 'Policy: Repository Server'),
		('policies/repositorysync', 'Policy: Repository Sync'),
		('policies/share_userquota', 'Policy: Userquota-Policy'),
		('policies/slavepackages', 'Policy: Packages for Replica Nodes'),
		('policies/umc', 'Policy: UMC'),
		('settings/cn', 'Univention Settings'),
		('settings/data', 'Data'),
		('settings/default', 'Preferences: Default'),
		('settings/directory', 'Preferences: Path'),
		('settings/extended_attribute', 'Settings: Extended attribute'),
		('settings/extended_options', 'Settings: Extended option'),
		('settings/ldapacl', 'Settings: LDAP ACL Extension'),
		('settings/ldapschema', 'Settings: LDAP Schema Extension'),
		('settings/license', 'Settings: License'),
		('settings/lock', 'Settings: Lock'),
		('settings/packages', 'Settings: Package List'),
		('settings/printermodel', 'Settings: Printer Driver List'),
		('settings/printeruri', 'Settings: Printer URI List'),
		('settings/prohibited_username', 'Settings: Prohibited Usernames'),
		('settings/sambaconfig', 'Settings: Samba Configuration'),
		('settings/sambadomain', 'Settings: Samba Domain'),
		('settings/service', 'Settings: Service'),
		('settings/settings', 'Preferences'),
		('settings/syntax', 'Settings: Syntax Definition'),
		('settings/udm_hook', 'Settings: UDM Hook'),
		('settings/udm_module', 'Settings: UDM Module'),
		('settings/udm_syntax', 'Settings: UDM Syntax'),
		('settings/umc_operationset', 'Settings: UMC operation set'),
		('settings/usertemplate', 'Settings: User Template'),
		('shares/printer', 'Print-Share: Printer'),
		('shares/printergroup', 'Print-Share: Printer Group'),
		('shares/share', 'Share: Directory'),
		('users/contact', 'Contact'),
		('users/ldap', 'Simple authentication account'),
		('users/passwd', 'User: Password'),
		('users/self', 'User: Self'),
		('users/user', 'User')
	]

	@classmethod
	def parse(self, text):
		for choice in self.choices:
			if choice[0] == text:
				return text
		raise univention.admin.uexceptions.valueInvalidSyntax(_('"%s" is not a Univention Admin Module.') % text)

# Unfortunately, Python doesn't seem to support (static) class methods;
# however, (static) class variables such as "choices" seem to work;
# so, we'll modify "choices" using this global method


def univentionAdminModules_update():
	"""
	Update internal list of |UDM| modules in :py:class:`univentionAdminModules`.
	"""
	temp = []
	for name, mod in univention.admin.modules.modules.items():
		if not univention.admin.modules.virtual(mod):
			temp.append((name, univention.admin.modules.short_description(mod)))

	univentionAdminModules.choices = sorted(temp, key=operator.itemgetter(1))


__register_choice_update_function(univentionAdminModules_update)


class UDM_PropertySelect(complex):
	"""
	Syntax to enter |UDM| module and property name.
	"""
	subsyntaxes = ((_('UDM module'), string), (_('property'), string))
	subsyntax_names = ('module', 'property')


class listAttributes(string):
	"""
	Syntax to enter |UDM| property name.

	.. deprecated::
		Old syntax required by :py:class:`univention.admin.handler.settings.syntax`.
		Should be removed after migrating to :py:class:`UDM_PropertySelect`.
	>>> listAttributes.parse("a value")
	'a value'
	"""

	@classmethod
	def parse(self, text):
		return text


class timeSpec(select):
	"""
	Time format used by :program:`at`.
	"""
	_times = [
		(_time, _time) for hour in range(0, 24)
		for minute in range(0, 60, 15)
		for _time in ('%02d:%02d' % (hour, minute),)
	]
	choices = [
		('', _('No Reboot')),
		('now', _('Immediately')),
	] + _times


class optionsUsersUser(select):
	"""
	Syntax to select options for |UDM| module :py:class:`univention.admin.handlers.users.user`.
	"""
	choices = [('pki', _('Public key infrastructure account'))]

	@classmethod
	def update_choices(cls):
		users = univention.admin.modules.get('users/user')
		if users:
			cls.choices = [(key, x.short_description) for key, x in users.options.items() if key != 'default']


__register_choice_update_function(optionsUsersUser.update_choices)


class nagiosHostsEnabledDn(UDM_Objects):
	"""
	Syntax to select Nagios enabled hosts from |LDAP|.
	"""
	udm_modules = ('computers/computer', )
	udm_filter = '(&(!(univentionObjectFlag=docker))(objectClass=univentionNagiosHostClass)(univentionNagiosEnabled=1)(aRecord=*))'


class nagiosServiceDn(UDM_Objects):
	"""
	Syntax to select a Nagios services from |LDAP| using :py:class:`univention.admin.handlers.nagios.service`.
	"""
	udm_modules = ('nagios/service', )


class UCR_Variable(complex):
	"""
	Syntax to enter |UCR| variable name and value.
	"""
	subsyntaxes = ((_('Variable'), string), (_('Value'), string))
	subsyntax_names = ('variable', 'value')
	subsyntax_key_value = True


class LDAP_Search(select):
	"""
	Selection list from LDAP search.

	Searches can be either defined dynamically via a UDM settings/syntax
	definition and using

		LDAP_Search( syntax_name = '<NAME>' )

	or programmatically by directly instantiating

		LDAP_Search( filter = '<LDAP-Search-Filter>', attribute = [ '<LDAP attributes>', ... ], value = '<LDAP attribute>', base = '<LDAP base>' )

	>>> from univention.admin.uldap import getMachineConnection
	>>> from univention.lib.misc import custom_username
	>>> syntax = LDAP_Search('mysyntax', '(univentionObjectType=users/user)', ['uid'])
	>>> if os.path.exists('/etc/machine.secret'):
	...     lo, pos = getMachineConnection()
	...     syntax._load(lo)
	...     syntax._prepare(lo)
	...     any(dn.startswith('uid=' + custom_username('Administrator')) for dn, value, attrs in syntax.values)
	... else:
	...     True
	True
	>>> syntax = LDAP_Search('mysyntax2', '(univentionObjectType=fantasy)', ['cn'])
	>>> if os.path.exists('/etc/machine.secret'):
	...     syntax._prepare(lo)
	...     syntax.values
	... else:
	...     []
	[]
	"""
	FILTER_PATTERN = '(&(objectClass=univentionSyntax)(cn=%s))'

	def __init__(self, syntax_name=None, filter=None, attribute=[], base='', value='dn', viewonly=False, addEmptyValue=False, appendEmptyValue=False):
		"""Creates an syntax object providing a list of choices defined
		by a LDAP objects

		:param syntax_name: name of the syntax LDAP object.

		:param filter: an LDAP filter to find the LDAP objects providing the
			list of choices. The filter may contain patterns, that are ...

		:param attribute: a list of UDM module attributes definitions like
			`shares/share: dn` to be used as human readable representation
			for each element of the choices.

		:param value: the UDM module attribute that will be stored to identify
			the selected element. The value is specified like `shares/share: dn`.

		:param viewonly: If set to True the values can not be changed.

		:param addEmptyValue: If set to True an empty value is add to the list
			of choices.

		:param appendEmptyValue: Same as addEmptyValue but added at the end.
			Used to automatically choose an existing entry in frontend.
		"""
		self.syntax = syntax_name
		if filter is not None:
			# programmatically
			self.syntax = None
			self.filter = filter
			self.attributes = attribute
			self.base = base
			self.value = value

		self.choices = []
		self.name = self.__class__.__name__
		self.viewonly = viewonly
		self.addEmptyValue = addEmptyValue
		self.appendEmptyValue = appendEmptyValue

	@classmethod
	def parse(self, text):
		return text

	def _load(self, lo):
		"""Loads an LDAP_Search object from the LDAP directory. If no
		syntax name is given the object is expected to be created with
		the required settings programmatically."""

		if not self.syntax:
			# programmatically
			if self.viewonly:
				self.value = 'dn'
			return

		# get values from UDM settings/syntax
		try:
			filter = filter_format(LDAP_Search.FILTER_PATTERN, [self.syntax])
			dn, attrs = lo.search(filter=filter)[0]
		except Exception:
			return

		if dn:
			self.__dn = dn  # needed?
			self.filter = attrs['univentionSyntaxLDAPFilter'][0].decode('utf-8')
			self.attributes = [x.decode('UTF-8') for x in attrs['univentionSyntaxLDAPAttribute']]
			if 'univentionSyntaxLDAPBase' in attrs:
				self.base = attrs['univentionSyntaxLDAPBase'][0].decode('utf-8')
			else:
				self.base = self.__base = ''  # unclear what __base is for
			self.value = attrs.get('univentionSyntaxLDAPValue', [b'dn'])[0].decode('utf-8')
			if attrs.get('univentionSyntaxViewOnly', [b'FALSE'])[0] == b'TRUE':
				self.viewonly = True
				self.value = 'dn'
			self.addEmptyValue = (attrs.get('univentionSyntaxAddEmptyValue', [b'0'])[0].upper() in [b'TRUE', b'1'])
			self.appendEmptyValue = (attrs.get('univentionSyntaxAppendEmptyValue', [b'0'])[0].upper() in [b'TRUE', b'1'])

	def _prepare(self, lo, filter=None):
		if filter is None:
			filter = self.filter
		self.choices = []
		self.values = []
		for dn in lo.searchDn(filter=filter, base=self.base):
			# self.attributes: pass on all display attributes so the frontend has a chance to supoport it some day
			if not self.viewonly:
				self.values.append((dn, self.value, self.attributes))
			else:
				self.values.append((dn, self.attributes))


class nfsShare(UDM_Objects):
	"""
	Syntax for selecting defined |NFS| shares.

	.. seealso::
		* :py:class:`WritableShare`
	"""
	udm_modules = ('shares/share', )
	label = '%(name)s (%(host)s)'  # '%(printablename)s' optimized for performance...
	udm_filter = 'objectClass=univentionShareNFS'
	use_objects = False


class nfsMounts(complex):
	"""
	Syntax to define a |NFS| mount point.
	"""
	subsyntaxes = [(_('NFS share'), nfsShare), ('Mount point', string)]
	subsyntax_names = ('nfs-share', 'mount-point')
	all_required = True


class languageCode(string):
	"""
	Syntax for a language, e.g. `language_COUNTRY`.
	>>> languageCode.parse("de_DE")
	'de_DE'
	>>> languageCode.parse("en_US")
	'en_US'
	>>> languageCode.parse("C") #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	>>> languageCode.parse("german") #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	min_length = 5
	max_length = 5
	_re = re.compile('^[a-z][a-z]_[A-Z][A-Z]$')

	@classmethod
	def parse(self, text):
		if self._re.match(text) is not None:
			return text
		else:
			raise univention.admin.uexceptions.valueError(_('Language code must be in format "xx_XX"!'))


class translationTuple(complex):
	"""
	Syntax for some translatable text.
	"""
	delimiter = ': '
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Text'), string)]
	subsyntax_key_value = True
	all_required = 1


class translationTupleShortDescription(translationTuple):
	"""
	Syntax for a translated short description of an |UDM| property.
	"""
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Translated short description'), string)]


class translationTupleLongDescription(translationTuple):
	"""
	Syntax for a translated long description of an |UDM| property.
	"""
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Translated long description'), string)]


class translationTupleTabName(translationTuple):
	"""
	Syntax for a translated |UMC| tab name for an |UDM| property.
	"""
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Translated tab name'), string)]


class I18N_GroupName(translationTuple):
	"""
	Syntax for a translated group name.
	"""
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Translated group name'), string)]


class disabled(boolean):
	"""
	Syntax to select account disabled state.
	>>> disabled.parse("none")
	'0'
	>>> disabled.parse("none2")
	'0'
	>>> disabled.parse("all")
	'1'
	>>> disabled.parse("posix_kerberos")
	'1'
	>>> disabled.parse("hallo") #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	@classmethod
	def parse(cls, text):
		if text in ('none', 'none2'):
			text = '0'
		elif text in ('all', 'windows', 'kerberos', 'posix', 'windows_posix', 'windows_kerberos', 'posix_kerberos'):
			text = '1'
		return super(disabled, cls).parse(text)


class locked(boolean):
	"""
	Syntax to select account locked state.
	>>> locked.parse("none")
	'0'
	>>> locked.parse("posix")
	'1'
	>>> locked.parse("windows")
	'1'
	>>> locked.parse("all")
	'1'
	>>> locked.parse("posix_kerberos") #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	>>> locked.parse("none2") #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	@classmethod
	def parse(cls, text):
		if text in ('all', 'windows', 'posix'):
			text = '1'
		elif text == 'none':
			text = '0'
		return super(locked, cls).parse(text)


# printing stuff


class Printers(UDM_Objects):
	"""
	Syntax to select a printers from |LDAP| using :py:class:`univention.admin.handlers.shares.printer`.

	.. seealso::
		* :py:class:`PrinterNames`
	"""
	udm_modules = ('shares/printer', )
	depends = 'spoolHost'
	simple = True
	key = '%(name)s'

	@classmethod
	def udm_filter(self, options):
		return '(|(spoolHost=%s))' % ')(spoolHost='.join(map(escape_filter_chars, options[Printers.depends]))


class PrinterNames(UDM_Objects):
	"""
	Syntax to select a printers from |LDAP| using :py:class:`univention.admin.handlers.shares.printer`.

	.. seealso::
		* :py:class:`Printers`
	>>> PrinterNames().type_class
	<class 'univention.admin.types.StringType'>
	"""
	udm_modules = ('shares/printer', )
	depends = 'spoolHost'
	simple = True
	key = '%(name)s'
	regex = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9_-]*([a-zA-Z0-9]$)')

	@classmethod
	def udm_filter(self, options):
		return '(|(spoolHost=%s))' % ')(spoolHost='.join(map(escape_filter_chars, options[Printers.depends]))


class PrintQuotaGroup(complex):
	"""
	Syntax to configure a page quota for all users of a group together.

	.. seealso::
		* :py:class:`PrintQuotaGroupPerUser`
		* :py:class:`PrintQuotaUser`
	"""
	subsyntaxes = ((_('Soft limit (pages)'), integer), (_('Hard limit (pages)'), integer), (_('Group'), GroupName))
	subsyntax_names = ('soft-limit', 'hard-limit', 'group')


class PrintQuotaGroupPerUser(complex):
	"""
	Syntax to configure a page quota for all individual users of a group.

	.. seealso::
		* :py:class:`PrintQuotaUser`
		* :py:class:`PrintQuotaGroup`
	"""
	subsyntaxes = ((_('Soft limit (pages)'), integer), (_('Hard limit (pages)'), integer), (_('Group'), GroupName))
	subsyntax_names = ('soft-limit', 'hard-limit', 'group')


class PrintQuotaUser(complex):
	"""
	Syntax to configure a page quota for an individual user.

	.. seealso::
		* :py:class:`PrintQuotaGroupPerUser`
		* :py:class:`PrintQuotaGroup`
	"""
	subsyntaxes = ((_('Soft limit (pages)'), integer), (_('Hard limit (pages)'), integer), (_('User'), UserName))
	subsyntax_names = ('soft-limit', 'hard-limit', 'group')


class printerName(simple):
	"""
	Syntax to enter a printer name.
	>>> printerName.parse("drucker1")
	'drucker1'
	>>> printerName.parse("drücker1") #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	min_length = 1
	max_length = 16
	_re = re.compile('(?u)(^[a-zA-Z0-9])[a-zA-Z0-9_-]*([a-zA-Z0-9]$)')

	@classmethod
	def parse(self, text):
		if self._re.match(text) is not None:
			return text
		else:
			raise univention.admin.uexceptions.valueError(_("Value may not contain other than numbers, letters, underscore (\"_\") and minus (\"-\")!"))


class printerModel(complex):
	"""
	Syntax to enter a printer model description.
	"""
	subsyntaxes = [(_('Driver'), string), (_('Description'), string)]
	subsyntax_names = ('driver', 'description')
	all_required = True


class PrinterDriverList(UDM_Attribute):
	"""
	Syntax to select a printer driver from |LDAP| using :py:class:`univention.admin.handlers.settings.printermodel`.
	"""
	udm_module = 'settings/printermodel'
	attribute = 'printmodel'
	is_complex = True
	key_index = 0
	label_index = 1
	udm_filter = 'dn'
	depends = 'producer'


class PrinterProducerList(UDM_Objects):
	"""
	Syntax to select a printer producer from |LDAP| using :py:class:`univention.admin.handlers.settings.printermodel`.
	"""
	udm_modules = ('settings/printermodel', )
	label = '%(name)s'


class PrinterProtocol(UDM_Attribute):
	"""
	Syntax to select a printer |URI| from |LDAP| using :py:class:`univention.admin.handlers.settings.printeruri`.
	"""
	udm_module = 'settings/printeruri'
	attribute = 'printeruri'
	is_complex = False


class PrinterURI(complex):
	"""
	Syntax to configure printer.
	>>> PrinterURI.parse(["uri://", "localhost"])
	['uri://', 'localhost']
	>>> PrinterURI.parse(["uri://", None]) #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	>>> PrinterURI.parse(["uri://", "localhost", "one more"]) #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	>>> PrinterURI.parse(["uri://"]) #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	"""
	subsyntaxes = ((_('Protocol'), PrinterProtocol), (_('Destination'), string))
	subsyntax_names = ('protocol', 'destination')

	@classmethod
	def parse(self, texts):
		parsed = []

		if self.min_elements is not None:
			count = self.min_elements
		else:
			count = len(self.subsyntaxes) if 'pdf' not in texts[0] else len(self.subsyntaxes) - 1

		if len(texts) < count:
			raise univention.admin.uexceptions.valueInvalidSyntax(_('Protocol and destination have to be specified.'))

		if len(texts) > len(self.subsyntaxes):
			raise univention.admin.uexceptions.valueInvalidSyntax(_("too many arguments"))

		for i in range(len(texts)):
			ud.debug(ud.ADMIN, ud.INFO, 'syntax.py: self.subsyntax[%s] is %s, texts is %s' % (i, self.subsyntaxes[i], texts))
			if not inspect.isclass(self.subsyntaxes[i][1]):
				s = self.subsyntaxes[i][1]
			else:
				s = self.subsyntaxes[i][1]()
			if texts[i] is None:
				if self.min_elements is None or (i + 1) < self.min_elements:
					raise univention.admin.uexceptions.valueInvalidSyntax(_("Invalid syntax"))
			p = s.parse(texts[i])
			if p:
				parsed.append(p)
		return parsed


class policyName(string):
	"""
	Syntax to enter |UDM| policy name.
	>>> policyName.parse('A valid name')
	'A valid name'
	>>> policyName.parse('An invalid name ') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	_re = re.compile(r'^[a-zA-Z0-9]{1}[a-zA-Z0-9 #!$%&/\|\^.~_-]*?[a-zA-Z0-9#!$%&/\|\^.~_-]{1}$')

	@classmethod
	def parse(self, text):
		if self._re.match(text):
			return text
		raise univention.admin.uexceptions.valueError(_(
			'May only contain letters (except umlauts), digits, space as well as the characters # ! $ % & | ^ . ~ _ -. Has to begin with a letter or digit and must not end with space.'
		))


class Portals(UDM_Objects):
	"""
	Syntax to select a portal from |LDAP| using :py:class:`univention.admin.handlers.settings.portal`.
	"""
	udm_modules = ('settings/portal', )
	label = '%(name)s'
	empty_value = True


class PortalEntries(UDM_Objects):
	"""
	Syntax to select a portal entries from |LDAP| using :py:class:`univention.admin.handlers.settings.portal_entry`.
	"""
	udm_modules = ('settings/portal_entry', )
	label = '%(name)s'
	empty_value = True


class PortalLinksPosition(select):
	"""
	Syntax to select the position of links on the portal.
	"""
	choices = [
		('footer', _('Footer')),
	]


class PortalLinks(complex):
	"""
	Syntax to configure links on the portal.
	"""
	delimiter = '$$'
	subsyntaxes = [(_('Position'), PortalLinksPosition), (_('Link'), string), (_('Locale'), languageCode), (_('Name'), string)]
	subsyntax_names = ('position', 'link', 'locale', 'name')
	all_required = True


class PortalCategory(select):
	"""
	Syntax to select a portal category version 1 from a static list with just 2 categories.

	.. seealso::
		* :py:class:`PortalCategoryV2`
	"""
	choices = [
		('admin', _('Shown in category "Administration"')),
		('service', _('Shown in category "Installed services"')),
	]


class PortalCategoryV2(UDM_Objects):
	"""
	Syntax to select a portal category version 2 from |LDAP| using :py:class:`univention.admin.handlers.settings.portal_category`.

	.. seealso::
		* :py:class:`PortalCategory`
	"""
	udm_modules = ('settings/portal_category', )
	label = '%(name)s'
	empty_value = True


class PortalEntrySelection(complex):
	"""
	Syntax to select a portal entry.
	"""
	subsyntaxes = [(_('Portal Entry'), PortalEntries)]
	subsyntax_names = ('portal-entry',)


class PortalCategorySelection(simple):
	r"""
	Syntax to select a portal category.
	>>> x = PortalCategorySelection.tostring([["cn=category1", []], ["cn=category2", ["cn=entry1", "cn=entry2"]]])
	>>> x.replace(' ','').replace('\n','')
	'[["cn=category1",[]],["cn=category2",["cn=entry1","cn=entry2"]]]'
	>>> PortalCategorySelection.parse('[["cn=category1",[]],["cn=category2",["cn=entry1","cn=entry2"]]]')
	[['cn=category1', []], ['cn=category2', ['cn=entry1', 'cn=entry2']]]
	>>> PortalCategorySelection.parse('[["cn=category1",[]],["",["cn=entry1","cn=entry2"]]]') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	>>> PortalCategorySelection.parse('[["cn=category1"]]') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	>>> PortalCategorySelection.parse('[["cn=category1",[], []]]') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	>>> PortalCategorySelection.parse('hallo') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueInvalidSyntax:
	"""
	subsyntaxes = [(_('Portal Category'), PortalCategoryV2), (_('Portal Entry'), PortalEntrySelection)]
	subsyntax_names = ('portal-category', 'portal-entry',)

	@classmethod
	def parse(self, texts, minn=None):
		if isinstance(texts, six.string_types):  # for UDM-CLI
			try:
				texts = json.loads(texts)
			except ValueError:
				raise univention.admin.uexceptions.valueInvalidSyntax(_("Value has to be in valid json format"))
		for text in texts:
			if len(text) < len(self.subsyntaxes):
				raise univention.admin.uexceptions.valueInvalidSyntax(_("not enough arguments"))
			elif len(text) > len(self.subsyntaxes):
				raise univention.admin.uexceptions.valueInvalidSyntax(_("too many arguments"))

			if len(text[1]) > 0 and not text[0]:
				raise univention.admin.uexceptions.valueInvalidSyntax(_("Portal entries can not be added to an empty category"))

			s = Portals()
			s.parse(text[0])

			s = PortalEntries()
			for portal_entry in text[1]:
				s.parse(portal_entry)
		return texts

	@classmethod
	def tostring(self, texts):
		# type: (Any) -> str
		return json.dumps(texts, indent=2)


class AuthRestriction(select):
	"""
	Syntax to select the authentication restriction for the portal.
	"""
	choices = [
		('admin', _('Visible for Admins only')),
		('authenticated', _('Visible for authenticated users')),
		('anonymous', _('Visible for everyone')),
	]


class PortalFontColor(select):
	"""
	Syntax to select the color of the font in the portal.
	"""
	choices = [
		('white', _('White')),
		('black', _('Black')),
	]


class PortalDefaultLinkTarget(select):
	choices = [
		('samewindow', _('Same tab')),
		('newwindow', _('New tab')),
	]


class PortalEntryLinkTarget(select):
	choices = [
		('useportaldefault', _('Use default of portal')),
		('samewindow', _('Same tab')),
		('newwindow', _('New tab')),
	]


class LocalizedDisplayName(translationTuple):
	"""
	Syntax for a translated display name of a portal entry.
	"""
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Display Name'), string)]


class LocalizedDescription(translationTuple):
	"""
	Syntax for a translated description of a portal entry.
	"""
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Description'), string)]


class LocalizedAnonymousEmpty(translationTuple):
	"""
	Syntax for a translated description of a portal entry.
	In addition to :py:class:`LocalizedDescription` it allows to specify a fallback for anonymous visitors.
	"""
	subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Message that is shown to anonymous visitors when the portal is empty'), TwoEditor)]


class mailHomeServer(LDAP_Search):
	"""
	Syntax to select UCS servers providing the |IMAP| service.

	.. deprecated:: 3.2-1
		Use :py:class:`MailHomeServer`.
	"""
	def __init__(self):
		LDAP_Search.__init__(
			self,
			filter='(&(!(univentionObjectFlag=docker))(objectClass=univentionHost)(univentionService=IMAP))',
			attribute=['computers/computer: fqdn'],
			value='computers/computer: fqdn',
			appendEmptyValue=True
		)


class hostname_or_ipadress_or_network(simple):
	"""
	Syntax for (fully qualified) host name or IP address or IP network.

	>>> hostname_or_ipadress_or_network.parse('hostname')
	'hostname'
	>>> hostname_or_ipadress_or_network.parse('10.10.10.0/24')
	'10.10.10.0/24'
	>>> hostname_or_ipadress_or_network.parse('10.10.10.0/255.255.255.0')
	'10.10.10.0/255.255.255.0'
	>>> hostname_or_ipadress_or_network.parse('illegalhostname$!"§%&/(') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	>>> hostname_or_ipadress_or_network.parse('10.10.10.0/') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	>>> hostname_or_ipadress_or_network.parse('/24') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	>>> hostname_or_ipadress_or_network.parse('10.10.10.0/255') #doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	...
	valueError:
	"""
	@classmethod
	def parse(self, text):
		try:
			if '/' in text:  # a network
				ipnetwork.parse(text)
			else:  # a hostname or ip address
				hostOrIP.parse(text)
		except univention.admin.uexceptions.valueError as exc:
			error = _('Error: %(text)s - %(exc)s')
			raise univention.admin.uexceptions.valueError(error % {'text': text, 'exc': exc})
		return text


class ObjectFlag(select):
	"""
	Syntax for |UDM| object flags.
	"""
	empty_value = True
	choices = [
		('hidden', _('Mark this object as hidden')),
		('temporary', _('Mark this object as temporary')),
		('functional', _('Ignore this object in standard UDM modules')),
		('docker', _('This object is related to a Docker App container')),
		('synced', _('This object is synchronized from Active Directory')),
	]


class Country(select):
	"""
	Syntax for selecting a country by name.
	Stored as  the `ISO 3166-1 two-letter country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.
	"""
	empty_value = True

	choices = []

	@classmethod
	def update_choices(cls):
		iso_3166 = localization.translation('iso_3166')
		iso_3166.set_language(str(translation.locale))
		_iso_3166 = iso_3166.translate

		cls.choices = [
			('AF', _iso_3166(u'Afghanistan')), ('AX', _iso_3166(u'\xc5land Islands')),
			('AL', _iso_3166(u'Albania')), ('DZ', _iso_3166(u'Algeria')),
			('AS', _iso_3166(u'American Samoa')), ('AD', _iso_3166(u'Andorra')),
			('AO', _iso_3166(u'Angola')), ('AI', _iso_3166(u'Anguilla')), ('AQ', _iso_3166(u'Antarctica')),
			('AG', _iso_3166(u'Antigua and Barbuda')), ('AR', _iso_3166(u'Argentina')),
			('AM', _iso_3166(u'Armenia')), ('AW', _iso_3166(u'Aruba')), ('AU', _iso_3166(u'Australia')),
			('AT', _iso_3166(u'Austria')), ('AZ', _iso_3166(u'Azerbaijan')), ('BS', _iso_3166(u'Bahamas')),
			('BH', _iso_3166(u'Bahrain')), ('BD', _iso_3166(u'Bangladesh')), ('BB', _iso_3166(u'Barbados')),
			('BY', _iso_3166(u'Belarus')), ('BE', _iso_3166(u'Belgium')), ('BZ', _iso_3166(u'Belize')),
			('BJ', _iso_3166(u'Benin')), ('BM', _iso_3166(u'Bermuda')), ('BT', _iso_3166(u'Bhutan')),
			('BO', _iso_3166(u'Bolivia, Plurinational State of')),
			('BQ', _iso_3166(u'Bonaire, Sint Eustatius and Saba')),
			('BA', _iso_3166(u'Bosnia and Herzegovina')), ('BW', _iso_3166(u'Botswana')),
			('BV', _iso_3166(u'Bouvet Island')), ('BR', _iso_3166(u'Brazil')),
			('IO', _iso_3166(u'British Indian Ocean Territory')),
			('BN', _iso_3166(u'Brunei Darussalam')), ('BG', _iso_3166(u'Bulgaria')),
			('BF', _iso_3166(u'Burkina Faso')), ('BI', _iso_3166(u'Burundi')),
			('KH', _iso_3166(u'Cambodia')), ('CM', _iso_3166(u'Cameroon')), ('CA', _iso_3166(u'Canada')),
			('CV', _iso_3166(u'Cabo Verde')), ('KY', _iso_3166(u'Cayman Islands')),
			('CF', _iso_3166(u'Central African Republic')), ('TD', _iso_3166(u'Chad')),
			('CL', _iso_3166(u'Chile')), ('CN', _iso_3166(u'China')),
			('CX', _iso_3166(u'Christmas Island')), ('CC', _iso_3166(u'Cocos (Keeling) Islands')),
			('CO', _iso_3166(u'Colombia')), ('KM', _iso_3166(u'Comoros')), ('CG', _iso_3166(u'Congo')),
			('CD', _iso_3166(u'Congo, The Democratic Republic of the')),
			('CK', _iso_3166(u'Cook Islands')), ('CR', _iso_3166(u'Costa Rica')),
			('CI', _iso_3166(u"C\xf4te d'Ivoire")), ('HR', _iso_3166(u'Croatia')),
			('CU', _iso_3166(u'Cuba')), ('CW', _iso_3166(u'Cura\xe7ao')), ('CY', _iso_3166(u'Cyprus')),
			('CZ', _iso_3166(u'Czechia')), ('DK', _iso_3166(u'Denmark')),
			('DJ', _iso_3166(u'Djibouti')), ('DM', _iso_3166(u'Dominica')),
			('DO', _iso_3166(u'Dominican Republic')), ('EC', _iso_3166(u'Ecuador')),
			('EG', _iso_3166(u'Egypt')), ('SV', _iso_3166(u'El Salvador')),
			('GQ', _iso_3166(u'Equatorial Guinea')), ('ER', _iso_3166(u'Eritrea')),
			('EE', _iso_3166(u'Estonia')), ('ET', _iso_3166(u'Ethiopia')),
			('FK', _iso_3166(u'Falkland Islands (Malvinas)')), ('FO', _iso_3166(u'Faroe Islands')),
			('FJ', _iso_3166(u'Fiji')), ('FI', _iso_3166(u'Finland')), ('FR', _iso_3166(u'France')),
			('GF', _iso_3166(u'French Guiana')), ('PF', _iso_3166(u'French Polynesia')),
			('TF', _iso_3166(u'French Southern Territories')), ('GA', _iso_3166(u'Gabon')),
			('GM', _iso_3166(u'Gambia')), ('GE', _iso_3166(u'Georgia')), ('DE', _iso_3166(u'Germany')),
			('GH', _iso_3166(u'Ghana')), ('GI', _iso_3166(u'Gibraltar')), ('GR', _iso_3166(u'Greece')),
			('GL', _iso_3166(u'Greenland')), ('GD', _iso_3166(u'Grenada')),
			('GP', _iso_3166(u'Guadeloupe')), ('GU', _iso_3166(u'Guam')), ('GT', _iso_3166(u'Guatemala')),
			('GG', _iso_3166(u'Guernsey')), ('GN', _iso_3166(u'Guinea')),
			('GW', _iso_3166(u'Guinea-Bissau')), ('GY', _iso_3166(u'Guyana')), ('HT', _iso_3166(u'Haiti')),
			('HM', _iso_3166(u'Heard Island and McDonald Islands')),
			('VA', _iso_3166(u'Holy See (Vatican City State)')), ('HN', _iso_3166(u'Honduras')),
			('HK', _iso_3166(u'Hong Kong')), ('HU', _iso_3166(u'Hungary')), ('IS', _iso_3166(u'Iceland')),
			('IN', _iso_3166(u'India')), ('ID', _iso_3166(u'Indonesia')),
			('IR', _iso_3166(u'Iran, Islamic Republic of')), ('IQ', _iso_3166(u'Iraq')),
			('IE', _iso_3166(u'Ireland')), ('IM', _iso_3166(u'Isle of Man')), ('IL', _iso_3166(u'Israel')),
			('IT', _iso_3166(u'Italy')), ('JM', _iso_3166(u'Jamaica')), ('JP', _iso_3166(u'Japan')),
			('JE', _iso_3166(u'Jersey')), ('JO', _iso_3166(u'Jordan')), ('KZ', _iso_3166(u'Kazakhstan')),
			('KE', _iso_3166(u'Kenya')), ('KI', _iso_3166(u'Kiribati')),
			('KP', _iso_3166(u"Korea, Democratic People's Republic of")),
			('KR', _iso_3166(u'Korea, Republic of')), ('KW', _iso_3166(u'Kuwait')),
			('KG', _iso_3166(u'Kyrgyzstan')),
			('LA', _iso_3166(u"Lao People's Democratic Republic")), ('LV', _iso_3166(u'Latvia')),
			('LB', _iso_3166(u'Lebanon')), ('LS', _iso_3166(u'Lesotho')), ('LR', _iso_3166(u'Liberia')),
			('LY', _iso_3166(u'Libya')), ('LI', _iso_3166(u'Liechtenstein')),
			('LT', _iso_3166(u'Lithuania')), ('LU', _iso_3166(u'Luxembourg')), ('MO', _iso_3166(u'Macao')),
			('MK', _iso_3166(u'Macedonia, Republic of')), ('MG', _iso_3166(u'Madagascar')),
			('MW', _iso_3166(u'Malawi')), ('MY', _iso_3166(u'Malaysia')), ('MV', _iso_3166(u'Maldives')),
			('ML', _iso_3166(u'Mali')), ('MT', _iso_3166(u'Malta')), ('MH', _iso_3166(u'Marshall Islands')),
			('MQ', _iso_3166(u'Martinique')), ('MR', _iso_3166(u'Mauritania')),
			('MU', _iso_3166(u'Mauritius')), ('YT', _iso_3166(u'Mayotte')), ('MX', _iso_3166(u'Mexico')),
			('FM', _iso_3166(u'Micronesia, Federated States of')),
			('MD', _iso_3166(u'Moldova, Republic of')), ('MC', _iso_3166(u'Monaco')),
			('MN', _iso_3166(u'Mongolia')), ('ME', _iso_3166(u'Montenegro')),
			('MS', _iso_3166(u'Montserrat')), ('MA', _iso_3166(u'Morocco')),
			('MZ', _iso_3166(u'Mozambique')), ('MM', _iso_3166(u'Myanmar')), ('NA', _iso_3166(u'Namibia')),
			('NR', _iso_3166(u'Nauru')), ('NP', _iso_3166(u'Nepal')), ('NL', _iso_3166(u'Netherlands')),
			('NC', _iso_3166(u'New Caledonia')), ('NZ', _iso_3166(u'New Zealand')),
			('NI', _iso_3166(u'Nicaragua')), ('NE', _iso_3166(u'Niger')), ('NG', _iso_3166(u'Nigeria')),
			('NU', _iso_3166(u'Niue')), ('NF', _iso_3166(u'Norfolk Island')),
			('MP', _iso_3166(u'Northern Mariana Islands')), ('NO', _iso_3166(u'Norway')),
			('OM', _iso_3166(u'Oman')), ('PK', _iso_3166(u'Pakistan')), ('PW', _iso_3166(u'Palau')),
			('PS', _iso_3166(u'Palestine, State of')), ('PA', _iso_3166(u'Panama')),
			('PG', _iso_3166(u'Papua New Guinea')), ('PY', _iso_3166(u'Paraguay')),
			('PE', _iso_3166(u'Peru')), ('PH', _iso_3166(u'Philippines')), ('PN', _iso_3166(u'Pitcairn')),
			('PL', _iso_3166(u'Poland')), ('PT', _iso_3166(u'Portugal')), ('PR', _iso_3166(u'Puerto Rico')),
			('QA', _iso_3166(u'Qatar')), ('RE', _iso_3166(u'R\xe9union')), ('RO', _iso_3166(u'Romania')),
			('RU', _iso_3166(u'Russian Federation')), ('RW', _iso_3166(u'Rwanda')),
			('BL', _iso_3166(u'Saint Barth\xe9lemy')),
			('SH', _iso_3166(u'Saint Helena, Ascension and Tristan da Cunha')),
			('KN', _iso_3166(u'Saint Kitts and Nevis')), ('LC', _iso_3166(u'Saint Lucia')),
			('MF', _iso_3166(u'Saint Martin (French part)')),
			('PM', _iso_3166(u'Saint Pierre and Miquelon')),
			('VC', _iso_3166(u'Saint Vincent and the Grenadines')), ('WS', _iso_3166(u'Samoa')),
			('SM', _iso_3166(u'San Marino')), ('ST', _iso_3166(u'Sao Tome and Principe')),
			('SA', _iso_3166(u'Saudi Arabia')), ('SN', _iso_3166(u'Senegal')), ('RS', _iso_3166(u'Serbia')),
			('SC', _iso_3166(u'Seychelles')), ('SL', _iso_3166(u'Sierra Leone')),
			('SG', _iso_3166(u'Singapore')), ('SX', _iso_3166(u'Sint Maarten (Dutch part)')),
			('SK', _iso_3166(u'Slovakia')), ('SI', _iso_3166(u'Slovenia')),
			('SB', _iso_3166(u'Solomon Islands')), ('SO', _iso_3166(u'Somalia')),
			('ZA', _iso_3166(u'South Africa')),
			('GS', _iso_3166(u'South Georgia and the South Sandwich Islands')),
			('ES', _iso_3166(u'Spain')), ('LK', _iso_3166(u'Sri Lanka')), ('SD', _iso_3166(u'Sudan')),
			('SR', _iso_3166(u'Suriname')), ('SS', _iso_3166(u'South Sudan')),
			('SJ', _iso_3166(u'Svalbard and Jan Mayen')), ('SZ', _iso_3166(u'Swaziland')),
			('SE', _iso_3166(u'Sweden')), ('CH', _iso_3166(u'Switzerland')),
			('SY', _iso_3166(u'Syrian Arab Republic')),
			('TW', _iso_3166(u'Taiwan, Province of China')), ('TJ', _iso_3166(u'Tajikistan')),
			('TZ', _iso_3166(u'Tanzania, United Republic of')), ('TH', _iso_3166(u'Thailand')),
			('TL', _iso_3166(u'Timor-Leste')), ('TG', _iso_3166(u'Togo')), ('TK', _iso_3166(u'Tokelau')),
			('TO', _iso_3166(u'Tonga')), ('TT', _iso_3166(u'Trinidad and Tobago')),
			('TN', _iso_3166(u'Tunisia')), ('TR', _iso_3166(u'Turkey')), ('TM', _iso_3166(u'Turkmenistan')),
			('TC', _iso_3166(u'Turks and Caicos Islands')), ('TV', _iso_3166(u'Tuvalu')),
			('UG', _iso_3166(u'Uganda')), ('UA', _iso_3166(u'Ukraine')),
			('AE', _iso_3166(u'United Arab Emirates')), ('GB', _iso_3166(u'United Kingdom')),
			('US', _iso_3166(u'United States')),
			('UM', _iso_3166(u'United States Minor Outlying Islands')),
			('UY', _iso_3166(u'Uruguay')), ('UZ', _iso_3166(u'Uzbekistan')), ('VU', _iso_3166(u'Vanuatu')),
			('VE', _iso_3166(u'Venezuela, Bolivarian Republic of')), ('VN', _iso_3166(u'Viet Nam')),
			('VG', _iso_3166(u'Virgin Islands, British')),
			('VI', _iso_3166(u'Virgin Islands, U.S.')), ('WF', _iso_3166(u'Wallis and Futuna')),
			('EH', _iso_3166(u'Western Sahara')), ('YE', _iso_3166(u'Yemen')), ('ZM', _iso_3166(u'Zambia')),
			('ZW', _iso_3166(u'Zimbabwe'))]
		cls.choices.sort(key=itemgetter(1))


class RadiusClientType(select):
	choices = [
		('other', _('other')),
		('cisco', _('cisco')),
		('computone', _('computone')),
		('livingston', _('livingston')),
		('juniper', _('juniper')),
		('max40xx', _('max40xx')),
		('multitech', _('multitech')),
		('netserver', _('netserver')),
		('pathras', _('pathras')),
		('patton', _('patton')),
		('portslave', _('portslave')),
		('tc', _('tc')),
		('usrhiper', _('usrhiper')),
	]


class mailinglist_name(gid):
	error_message = _(
		"A mailing list name must start and end with a letter, number or underscore. In between additionally spaces, "
		"dashes and dots are allowed."
	)


__register_choice_update_function(Country.update_choices)
Country.update_choices()
