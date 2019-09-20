# -*- coding: utf-8 -*-
#
# Univention Management Console
#  i18n utils
#
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

"""
Locales
=======

The translations provided by the UMC server are technically based on
gettext library. As the server needs to provide translations for several
different components that deliver their own translation files this
module provides a simple way for the UMC server to get the required
translations. Components that provide their own translation files:

* the UMC core --- python code directly imported by the UMC server
* categories
* module definitions
"""

from locale import getdefaultlocale
from struct import error as StructError
import os
import traceback

import polib

from .log import LOCALE

from univention.lib.i18n import Locale

'''
usage:
obj = univention.management.console.Translation()
_ = obj.translate
'''


class I18N(object):

	"""
	Provides a translation function for a given language and translation domain.

	:param str locale: the locale to provide
	:param str domain: the translation domain to use
	"""
	LOCALE_DIR = '/usr/share/univention-management-console/i18n/'

	def __init__(self, locale=None, domain=None):
		self.mofile = None
		self.domain = domain
		self.locale = locale
		self.load(locale, domain)

	def load(self, locale=None, domain=None):
		"""
		Tries to load the translation file specified by the given locale
		and domain. If the given locale could not be found the method
		tries to find the translation domain for the systems default
		locale. No translation is provided when this fails too.

		:param str locale: the locale to provide
		:param str domain: the translation domain to use
		"""
		if locale is not None:
			self.locale = locale
		if domain is not None:
			self.domain = domain
		if self.locale is None or self.domain is None:
			LOCALE.info('Locale or domain missing. Stopped loading of translation')
			return

		LOCALE.info('Loading locale %s for domain %s' % (self.locale, self.domain))
		filename = os.path.join(I18N.LOCALE_DIR, self.locale.language, '%s.mo' % self.domain)
		if not os.path.isfile(filename):
			filename = os.path.join(I18N.LOCALE_DIR, '%s_%s' % (self.locale.language, self.locale.territory), '%s.mo' % self.domain)
			if not os.path.isfile(filename):
				LOCALE.warn('Could not find translation file: %r' % (os.path.basename(filename),))
				self.mofile = None
				return

		LOCALE.info('Found translation file %s' % (filename,))
		self.mofile = None
		try:
			self.mofile = polib.mofile(filename)
		except (ValueError, MemoryError) as exc:
			LOCALE.error('Corrupt translation file %r: %s' % (filename, exc))
		except (KeyboardInterrupt, SystemExit, SyntaxError) as exc:
			raise
		except Exception as exc:
			LOCALE.error('Corrupt translation file %r: %s' % (filename, exc))
			LOCALE.error(traceback.format_exc())

	def exists(self, message):
		"""
		Verifies if the translation file contains a translation for the given text.

		:param str message: the text to search for
		:rtype: bool
		"""
		return self.mofile is not None and self.mofile.find(message, by='msgid')

	def _(self, message):
		"""
		Translates the given text if a translation is
		available. Otherwise the given text is returned.

		:param str message: text to translate
		:rtype: str
		"""
		if self.mofile:
			entry = self.mofile.find(message, by='msgid')
			if entry is not None:
				return entry.msgstr

		return message


class I18N_Manager(dict):

	"""
	This class handles the :class:`.I18N` instances within an UMC
	session.

	As the UMC server handles all sessions opened on a system that may
	all use a different language it uses one :class:`.I18N_Manager` per
	session.
	"""

	def __init__(self):
		lang, codeset = getdefaultlocale()
		if lang is None:
			lang = 'C'
		self.locale = Locale(lang)

	def set_locale(self, locale):
		"""
		Sets the locale to use within the :class:`.I18N_Manager`.

		:param str locale: locale to use
		"""
		LOCALE.info('Setting locale to %s' % locale)
		self.locale.parse(locale)
		for domain, i18n in self.items():
			LOCALE.info('Loading translation for domain %s' % domain)
			i18n.load(locale=self.locale)

	def __setitem__(self, key, value):
		value.domain = key
		dict.__setitem__(self, key, value)

	def _(self, message, domain=None):
		"""
		Translates the given text. Therefore all known translation
		domains or if not None the given domain is searched for a
		translation.

		:param str message: text to translation
		:param str domain: translation domain
		"""
		LOCALE.info('Searching for %s translation of "%s' % (str(self.locale), message))
		try:
			if domain is not None:
				if domain not in self:
					self[domain] = I18N(self.locale, domain)
				return self[domain]._(message)
			for domain, i18n in self.items():
				LOCALE.info('Checking domain %s for translation' % domain)
				if i18n.exists(message):
					return i18n._(message)
		except (StructError, IOError) as exc:
			# StructError: empty .mo file
			# IOError raised by polib if the file is no .mo file
			LOCALE.error('Corrupted .mo file detected for translation domain %r: %s' % (domain, exc))

		return message
