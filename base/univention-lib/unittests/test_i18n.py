#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2020 Univention GmbH
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

import pytest

from .conftest import import_lib_module

i18n = import_lib_module('i18n')


class TestLocale(object):
	def test_init(self):
		locale = i18n.Locale()
		assert locale.language is None
		assert locale.territory is None
		assert locale.codeset is None
		assert locale.modifier is None
		locale = i18n.Locale('de_DE.UTF-8:UTF-8@euro')
		assert locale.language == 'de'
		assert locale.territory == 'DE'
		assert locale.codeset == 'UTF-8'
		assert locale.modifier == 'euro'
		locale = i18n.Locale('en_US')
		assert locale.language == 'en'
		assert locale.territory == 'US'
		assert locale.codeset == 'UTF-8'
		assert locale.modifier is None

	def test_malformed(self):
		with pytest.raises(i18n.I18N_Error):
			i18n.Locale('')
		with pytest.raises(TypeError):
			i18n.Locale(0)

	@pytest.mark.xfail
	def test_malformed2(self):
		with pytest.raises(i18n.I18N_Error):
			i18n.Locale('deu_GER')
		with pytest.raises(i18n.I18N_Error):
			i18n.Locale('german')

	def test_bool(self):
		locale = i18n.Locale()
		assert bool(locale) is False
		locale = i18n.Locale('de_DE.UTF-8')
		assert bool(locale) is True
		locale = i18n.Locale('C')
		assert bool(locale) is True

	def test_str(self):
		locale = i18n.Locale('de_DE.UTF-8')
		assert str(locale) == 'de_DE.UTF-8'
		locale = i18n.Locale('be_BY.UTF-8@latin')
		assert str(locale) == 'be_BY.UTF-8@latin'

	@pytest.mark.xfail
	def test_str_modifier(self):
		locale = i18n.Locale('ca_ES@valencia')
		assert str(locale) == 'ca_ES@valencia'
		locale = i18n.Locale('C')
		assert str(locale) == 'C'

	@pytest.mark.xfail
	def test_str_empty(self):
		locale = i18n.Locale()
		assert str(locale) == ''


class TestNullTranslation(object):
	def test_init(self):
		translation = i18n.NullTranslation(None)
		assert translation._domain is None
		assert translation.locale is None
		translation = i18n.NullTranslation('univention')
		assert translation._domain == 'univention'
		assert translation._translation is None
		assert translation.locale is None
		translation = i18n.NullTranslation('univention.lib', 'de_DE')
		assert translation._domain == 'univention-lib'
		assert translation._translation is None
		assert translation.locale is None


class TestTranslation(object):
	def test_init(self):
		i18n.Translation.locale = i18n.Locale()
		translation = i18n.Translation(None)
		assert translation._domain is None
		assert translation.locale.language == 'C'
		translation = i18n.Translation('univention')
		assert translation._domain == 'univention'
		assert translation.locale.language == 'C'
		translation = i18n.Translation('univention.lib')
		assert translation._domain == 'univention-lib'

	def test_set_language(self):
		i18n.Translation.locale = i18n.Locale()
		translation = i18n.Translation('univention.lib')
		translation.set_language('de_DE')
		assert str(translation.locale) == 'de_DE.UTF-8'
		assert translation._translation is not None
		translation.set_language('en_US')
		assert str(translation.locale) == 'en_US.UTF-8'
		assert translation._translation is None
