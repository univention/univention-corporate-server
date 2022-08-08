#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
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

from os.path import dirname

import pytest

from .conftest import import_lib_module

i18n = import_lib_module('i18n')


class TestLocale(object):
	@pytest.mark.parametrize("spec,language,territory,codeset,modifier", [
		(None, "", "", "", ""),
		("de_DE.UTF-8@euro", "de", "DE", "UTF-8", "euro"),
		("en_US", "en", "US", "UTF-8", ""),
		("C", "C", "", "UTF-8", ""),
		("C.UTF-8", "C", "", "UTF-8", ""),
		("POSIX", "POSIX", "", "UTF-8", ""),
		("POSIX.UTF-8", "POSIX", "", "UTF-8", ""),
	])
	def test_init(self, spec, language, territory, codeset, modifier):
		locale = i18n.Locale(spec)
		assert locale.language == language
		assert locale.territory == territory
		assert locale.codeset == codeset
		assert locale.modifier == modifier

	@pytest.mark.parametrize("spec,exc_type", [
		("", i18n.I18N_Error),
		(0, TypeError),
		("deu_GER", i18n.I18N_Error),
		("german", i18n.I18N_Error),
	])
	def test_malformed(self, spec, exc_type):
		with pytest.raises(exc_type):
			i18n.Locale(spec)

	@pytest.mark.parametrize("spec,value", [
		(None, False),
		("de_DE.UTF-8", True),
		("C", True),
	])
	def test_bool(self, spec, value):
		locale = i18n.Locale(spec)
		assert bool(locale) is value

	@pytest.mark.parametrize("spec,txt", [
		("de_DE.UTF-8", "de_DE.UTF-8"),
		("be_BY.UTF-8@latin", "be_BY.UTF-8@latin"),
		("C.UTF-8", "C.UTF-8"),
		("ca_ES@valencia", "ca_ES.UTF-8@valencia"),
		(None, "")
	])
	def test_str(self, spec, txt):
		locale = i18n.Locale(spec)
		assert str(locale) == txt


class TestNullTranslation(object):
	@pytest.mark.parametrize("args,domain", [
		((None,), None),
		(("univention",), "univention"),
		(("univention.lib", "de_DE"), "univention-lib"),
	])
	def test_init(self, args, domain):
		translation = i18n.NullTranslation(*args)
		assert translation._domain == domain
		assert translation._translation is None
		assert translation.locale is None


class TestTranslation(object):
	@pytest.mark.parametrize("spec,domain,language", [
		(None, None, "C"),
		("univention", "univention", "C"),
		("univention.lib", "univention-lib", "C"),
	])
	def test_init(self, spec, domain, language):
		i18n.Translation.locale = i18n.Locale()

		translation = i18n.Translation(spec)
		assert translation._domain == domain
		assert translation.locale.language == language

	@pytest.mark.parametrize("spec,locale,trans", [
		("de_DE", "de_DE.UTF-8", True),
		("en_US", "en_US.UTF-8", False),
	])
	def test_set_language(self, spec, locale, trans):
		i18n.Translation.locale = i18n.Locale()
		translation = i18n.Translation("univention-lib-unittest", localedir=dirname(__file__))

		translation.set_language(spec)
		assert str(translation.locale) == locale
		if trans:
			assert translation._translation is not None
		else:
			assert translation._translation is None
