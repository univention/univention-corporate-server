#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2024 Univention GmbH
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
    def test_init(self, i18n, spec, language, territory, codeset, modifier):
        locale = i18n.Locale(spec)
        assert locale.language == language
        assert locale.territory == territory
        assert locale.codeset == codeset
        assert locale.modifier == modifier

    @pytest.mark.parametrize("spec,exc_type", [
        ("", None),
        (0, TypeError),
        ("deu_GER", None),
        ("german", None),
    ])
    def test_malformed(self, i18n, spec, exc_type):
        with pytest.raises(exc_type or i18n.I18N_Error):
            i18n.Locale(spec)

    @pytest.mark.parametrize("spec,value", [
        (None, False),
        ("de_DE.UTF-8", True),
        ("C", True),
    ])
    def test_bool(self, i18n, spec, value):
        locale = i18n.Locale(spec)
        assert bool(locale) is value

    @pytest.mark.parametrize("spec,txt", [
        ("de_DE.UTF-8", "de_DE.UTF-8"),
        ("be_BY.UTF-8@latin", "be_BY.UTF-8@latin"),
        ("C.UTF-8", "C.UTF-8"),
        ("ca_ES@valencia", "ca_ES.UTF-8@valencia"),
        (None, ""),
    ])
    def test_str(self, i18n, spec, txt):
        locale = i18n.Locale(spec)
        assert str(locale) == txt


class TestNullTranslation(object):
    @pytest.mark.parametrize("args,domain", [
        ((None,), None),
        (("univention",), "univention"),
        (("univention.lib", "de_DE"), "univention-lib"),
    ])
    def test_init(self, i18n, args, domain):
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
    def test_init(self, i18n, spec, domain, language):
        i18n.Translation.locale = i18n.Locale()

        translation = i18n.Translation(spec)
        assert translation._domain == domain
        assert translation.locale.language == language

    @pytest.mark.parametrize("spec,locale,trans", [
        ("de_DE", "de_DE.UTF-8", True),
        ("en_US", "en_US.UTF-8", False),
    ])
    def test_set_language(self, i18n, spec, locale, trans):
        i18n.Translation.locale = i18n.Locale()
        translation = i18n.Translation("univention-lib-unittest", localedir=dirname(__file__))

        translation.set_language(spec)
        assert str(translation.locale) == locale
        if trans:
            assert translation._translation is not None
        else:
            assert translation._translation is None

    def test_set_all_language(self, i18n):
        translation = i18n.Translation("univention-lib-unittest", localedir=dirname(__file__))
        translation.set_language('en_US')
        i18n.Translation.set_all_languages('de_DE')
        assert str(translation.locale) == 'de_DE.UTF-8'
