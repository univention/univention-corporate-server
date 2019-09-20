#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Internationalization (i18n) utilities.
"""
# Copyright 2006-2019 Univention GmbH
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

import gettext
from locale import getlocale, Error, LC_MESSAGES
import re

import six


class I18N_Error(Exception):
	"""
	Error in Internationalization.
	"""
	pass


class Locale(object):
	"""
	Represents a locale specification and provides simple access to
	language, territory, codeset and modifier.

	:param locale: The locale string `language[_territory][.codeset][@modifier]`.
	:type locale: str or None
	"""

	REGEX = re.compile('(?P<language>([a-z]{2}|C|POSIX))(_(?P<territory>[A-Z]{2}))?(.(?P<codeset>[a-zA-Z-0-9]+)(@(?P<modifier>.+))?)?')

	def __init__(self, locale=None):
		# type: (Optional[str]) -> None
		self.__reset()
		if locale is not None:
			self.parse(locale)

	def __reset(self):
		# type: () -> None
		self.language = None  # type: Optional[str]
		self.territory = None  # type: Optional[str]
		self.codeset = None  # type: Optional[str]
		self.modifier = None  # type: Optional[str]

	def parse(self, locale):
		# type: (str) -> None
		"""
		Parse locale string.

		:param str locale: The locale string `language[_territory][.codeset][@modifier]`.
		:raises TypeError: if `locale` is not a string.
		:raises I18N_Error: if `locale` does not match the format.
		"""
		if not isinstance(locale, six.string_types):
			raise TypeError('locale must be of type string')
		self.__reset()
		regex = Locale.REGEX.match(locale)
		if not regex:
			raise I18N_Error('attribute does not match locale specification language[_territory][.codeset][@modifier]')

		self.codeset = 'UTF-8'  # default encoding
		for key, value in regex.groupdict().items():
			if value is None:
				continue
			setattr(self, key, value)

	def __bool__(self):
		# type: () -> bool
		return self.language is not None
	__nonzero__ = __bool__

	def __str__(self):
		# type: () -> str
		text = self.language
		if self.language not in ('C', 'POSIX'):
			if self.territory is not None:
				text += '_%s' % self.territory
			if self.codeset is not None:
				text += '.%s' % self.codeset
			if self.modifier is not None:
				text += '@%s' % self.modifier
		return text is None and '' or text


class NullTranslation(object):
	"""
	Dummy translation.

	:param str namespace: The name of the translation domain.
	:param str locale_spec: The selected locale.
	:param str localedir: The name of the directory containing the translation files.
	"""

	def __init__(self, namespace, locale_spec=None, localedir=None):
		# type: (str, Optional[str], Optional[str]) -> None
		self.domain = namespace  # type: Optional[str]
		self._translation = None  # type: Optional[gettext.NullTranslations]
		self._localedir = localedir  # type: Optional[str]
		self._localespec = None  # type: Optional[Locale]
		self._locale = locale_spec  # type: Optional[str]
		if not self._locale:
			self.set_language()

	def _set_domain(self, namespace):
		# type: (str) -> None
		"""
		Select translation domain.

		:param str namespace: The name of the translation domain.
		"""
		if namespace is not None:
			self._domain = namespace.replace('/', '-').replace('.', '-')
		else:
			self._domain = None

	domain = property(fset=_set_domain)

	def set_language(self, language=None):
		# type: (Optional[str]) -> None
		"""
		Select language.

		:param str language: The language code.
		"""
		pass

	def _get_locale(self):
		# type: () -> Optional[Locale]
		"""
		Return currently selected locale.

		:returns: The currently selected locale.
		:rtype: Locale
		"""
		return self._localespec

	def _set_locale(self, locale_spec=None):
		# type: (Optional[str]) -> None
		"""
		Select new locale.

		:param str locale_spec: The new locale specification.
		"""
		if locale_spec is None:
			return
		self._localespec = Locale(locale_spec)

	locale = property(fget=_get_locale, fset=_set_locale)

	def translate(self, message):
		# type: (str) -> unicode
		"""
		Translate message.

		:param str message: The message to translate.
		:returns: The localized message.
		:rtype: str
		"""
		if self._translation is None:
			return message
		return self._translation.ugettext(message)

	_ = translate


class Translation(NullTranslation):
	"""
	Translation.
	"""
	locale = Locale()

	def set_language(self, language=None):
		# type: (Optional[str]) -> None
		"""
		Select language.

		:param str language: The language code.
		:raises I18N_Error: if the given locale is not valid.
		"""
		if language is not None:
			Translation.locale.parse(language)

		if not Translation.locale:
			try:
				lang = getlocale(LC_MESSAGES)
				if lang[0] is None:
					language = 'C'
				else:
					language = lang[0]
				Translation.locale.parse(language)
			except Error as e:
				raise I18N_Error('The given locale is not valid: %s' % str(e))

		if not self._domain:
			return

		try:
			self._translation = gettext.translation(self._domain, languages=(Translation.locale.language, ), localedir=self._localedir)
		except IOError as e:
			try:
				self._translation = gettext.translation(self._domain, languages=('%s_%s' % (Translation.locale.language, Translation.locale.territory), ), localedir=self._localedir)
			except IOError:
				self._translation = None
