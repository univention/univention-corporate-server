#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2022 Univention GmbH
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

import string

import pytest

from univentionunittests import import_module


_uldap = import_module('uldap', 'modules/', 'univention.uldap', use_installed=False)  # not needed. but we have to import it
univention_password = import_module('password', 'modules/', 'univention.password', use_installed=False)


@pytest.fixture
def mocked_ucr(mock_ucr, mocker):
	mock = mocker.patch.object(univention_password, 'ucr')
	mock.ucr = mock_ucr
	yield mock_ucr


@pytest.fixture(scope='class')
def password_config_default():
	cfg = univention_password.password_config()
	yield cfg


@pytest.fixture(scope='class')
def password_radius_config():
	cfg = univention_password.password_config('radius')
	yield cfg


def password_stats(cfg, password):
	"""
	Calculate password stats based on given configuration
	"""
	special_characters = string.punctuation
	forbidden_characters = cfg.get('forbidden') or ''
	digits = 0
	lower = 0
	other = 0
	upper = 0
	forbidden = 0

	for c in password:
		if '0' <= c <= '9':
			digits += 1
		elif 'a' <= c <= 'z':
			lower += 1
		elif 'A' <= c <= 'Z':
			upper += 1
		elif c in special_characters:
			other += 1
		if c in forbidden_characters:
			forbidden += 1

	return {'digits': digits, 'lower': lower, 'other': other, 'upper': upper, 'forbidden': forbidden}


def match_password_complexity(cfg, password):
	"""
	Test if given password matches complexity criteria.
	"""
	stats = password_stats(cfg, password)

	for stat in ['digits', 'lower', 'other', 'upper']:
		if cfg[stat] == 0 and stats[stat]:
			return False
		elif stats[stat] < cfg[stat]:
			return False
	return stats['forbidden'] == 0 and cfg['min_length'] <= len(password)


class TestPasswordConfigDefaults(object):
	"""
	Test all cases of no-scoped defaults
	"""

	def test_digit_count(self, password_config_default):
		assert password_config_default['digits'] == 6

	def test_lowercase_count(self, password_config_default):
		assert password_config_default['lower'] == 6

	def test_special_count(self, password_config_default):
		assert password_config_default['other'] == 0

	def test_uppercase(self, password_config_default):
		assert password_config_default['upper'] == 6

	def test_min_length(self, password_config_default):
		assert password_config_default['min_length'] == 24

	def test_special_characters(self, password_config_default):
		assert password_config_default['forbidden'] == '0Ol1I'


class TestScopedPasswordConfigDefaults(object):
	"""
	Test all cases of radius 'scope' defaults
	"""

	def test_radius_digit_count(self, password_radius_config):
		assert password_radius_config['digits'] == 6

	def test_radius_lowercase_count(self, password_radius_config):
		assert password_radius_config['lower'] == 6

	def test_radius_special_count(self, password_radius_config):
		assert password_radius_config['other'] == 0

	def test_radius_uppercase(self, password_radius_config):
		assert password_radius_config['upper'] == 6

	def test_radius_min_length(self, password_radius_config):
		assert password_radius_config['min_length'] == 24

	def test_radius_special_characters(self, password_radius_config):
		assert password_radius_config['forbidden'] == '0Ol1I'


class TestScopedPasswordConfigFallback(object):
	"""
	Set radius 'scoped' variables to None and check will they fallback to no-scoped defaults
	"""
	scope = 'radius'

	def test_digit_count(self, mocked_ucr):
		cfg = univention_password.password_config(self.scope)
		assert cfg['digits'] == 6

	def test_lowercase_count(self, mocked_ucr):
		cfg = univention_password.password_config(self.scope)
		assert cfg['lower'] == 6

	def test_special_count(self, mocked_ucr):
		cfg = univention_password.password_config(self.scope)
		assert cfg['other'] == 0

	def test_uppercase(self, mocked_ucr, password_config_default):
		cfg = univention_password.password_config(self.scope)
		assert cfg['upper'] == 6

	def test_min_length(self, mocked_ucr, password_config_default):
		cfg = univention_password.password_config(self.scope)
		assert cfg['min_length'] == 24

	def test_special_characters(self, mocked_ucr, password_config_default):
		cfg = univention_password.password_config(self.scope)
		assert cfg['forbidden'] == '0Ol1I'


class TestScopedPasswordConfigCustomizing(object):
	"""
	Set radius 'scoped' variables explicitely and checks value
	"""
	scope = 'radius'

	def test_digit_count(self, mocked_ucr):
		mocked_ucr['password/%s/quality/credit/digits' % self.scope] = '10'
		cfg = univention_password.password_config(self.scope)
		assert cfg['digits'] == 10

	def test_lowercase_count(self, mocked_ucr):
		mocked_ucr['password/%s/quality/credit/lower' % self.scope] = '11'
		cfg = univention_password.password_config(self.scope)
		assert cfg['lower'] == 11

	def test_special_count(self, mocked_ucr):
		mocked_ucr['password/%s/quality/credit/other' % self.scope] = '12'
		cfg = univention_password.password_config(self.scope)
		assert cfg['other'] == 12

	def test_uppercase(self, mocked_ucr, password_config_default):
		mocked_ucr['password/%s/quality/credit/upper' % self.scope] = '13'
		cfg = univention_password.password_config(self.scope)
		assert cfg['upper'] == 13

	def test_min_length(self, mocked_ucr, password_config_default):
		mocked_ucr['password/%s/quality/length/min' % self.scope] = '14'
		cfg = univention_password.password_config(self.scope)
		assert cfg['min_length'] == 14

	def test_special_characters(self, mocked_ucr, password_config_default):
		mocked_ucr['password/%s/quality/forbidden/chars' % self.scope] = ''
		cfg = univention_password.password_config(self.scope)
		assert cfg['forbidden'] == ''


class TestPasswordConfigDigitCount(object):

	def test_none(self):
		with pytest.raises(TypeError):
			cfg = {'digits': None, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			univention_password.generate_password(**cfg)

	def test_negative(self):
		with pytest.raises(ValueError, match="Number of digits, lower, upper or other characters can not be negative"):
			cfg = {'digits': -1, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			univention_password.generate_password(**cfg)

	def test_zero(self):
		digit_count = 0
		cfg = {'digits': digit_count, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = univention_password.generate_password(**cfg)

		assert (password_stats(cfg, pwd)['digits'] == digit_count)

	def test_positive_number(self):
		digit_count = 3
		cfg = {'digits': digit_count, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = univention_password.generate_password(**cfg)

		assert (password_stats(cfg, pwd)['digits'] >= digit_count)


class TestPasswordConfigLowerCaseCount(object):

	def test_none(self):
		with pytest.raises(TypeError):
			cfg = {'digits': 1, 'lower': None, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			univention_password.generate_password(**cfg)

	def test_negative(self):
		with pytest.raises(ValueError, match="Number of digits, lower, upper or other characters can not be negative"):
			cfg = {'digits': 1, 'lower': -1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			univention_password.generate_password(**cfg)

	def test_zero(self):
		lowercase_count = 0
		cfg = {'digits': 1, 'lower': lowercase_count, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = univention_password.generate_password(**cfg)

		assert (password_stats(cfg, pwd)['lower'] == lowercase_count)

	def test_positive_number(self):
		lowercase_count = 3
		cfg = {'digits': 1, 'lower': lowercase_count, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = univention_password.generate_password(**cfg)

		assert (password_stats(cfg, pwd)['lower'] >= lowercase_count)


class TestPasswordConfigSpecialCharacterCount(object):

	def test_none(self):
		with pytest.raises(TypeError):
			cfg = {'digits': 1, 'lower': 1, 'other': None, 'upper': 1, 'forbidden': None, 'min_length': 6}
			univention_password.generate_password(**cfg)

	def test_negative(self):
		with pytest.raises(ValueError, match="Number of digits, lower, upper or other characters can not be negative"):
			cfg = {'digits': 1, 'lower': 1, 'other': -1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			univention_password.generate_password(**cfg)

	def test_empty_pool(self):
		with pytest.raises(ValueError, match="There are 1 special characters requested but special characters pool is empty"):
			cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': string.punctuation, 'min_length': 6}
			univention_password.generate_password(**cfg)

	def test_zero(self):
		special_count = 0
		cfg = {'digits': 1, 'lower': 1, 'other': special_count, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = univention_password.generate_password(**cfg)

		assert (password_stats(cfg, pwd)['other'] == special_count)

	def test_positive_number(self):
		special_count = 3
		cfg = {'digits': 1, 'lower': 1, 'other': special_count, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = univention_password.generate_password(**cfg)

		assert (password_stats(cfg, pwd)['other'] >= special_count)


class TestPasswordConfigUpperCaseCount(object):

	def test_none(self):
		with pytest.raises(TypeError):
			cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': None, 'forbidden': None, 'min_length': 6}
			univention_password.generate_password(**cfg)

	def test_negative(self):
		with pytest.raises(ValueError, match="Number of digits, lower, upper or other characters can not be negative"):
			cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': -1, 'forbidden': None, 'min_length': 6}
			univention_password.generate_password(**cfg)

	def test_zero(self):
		uppercase_count = 0
		cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': uppercase_count, 'forbidden': None, 'min_length': 6}
		pwd = univention_password.generate_password(**cfg)

		assert (password_stats(cfg, pwd)['upper'] == uppercase_count)

	def test_positive_number(self):
		uppercase_count = 0
		cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': uppercase_count, 'forbidden': None, 'min_length': 6}
		pwd = univention_password.generate_password(**cfg)

		assert (password_stats(cfg, pwd)['upper'] >= uppercase_count)


class TestPasswordConfigExhaustedAvailableCharacterPool(object):

	def test_exhausted_digits_pool(self):
		with pytest.raises(ValueError, match="There are 1 digits requested but digits pool is empty"):
			cfg = {'digits': 1, 'lower': 0, 'other': 0, 'upper': 0, 'forbidden': string.digits, 'min_length': 2}
			univention_password.generate_password(**cfg)

	def test_exhausted_lowercase_pool(self):
		with pytest.raises(ValueError, match="There are 1 lowercase characters requested but lowercase pool is empty"):
			cfg = {'digits': 0, 'lower': 1, 'other': 0, 'upper': 0, 'forbidden': string.ascii_lowercase, 'min_length': 2}
			univention_password.generate_password(**cfg)

	def test_exhausted_special_character_pool(self):
		with pytest.raises(ValueError, match="There are 1 special characters requested but special characters pool is empty"):
			cfg = {'digits': 0, 'lower': 0, 'other': 1, 'upper': 0, 'forbidden': string.punctuation, 'min_length': 2}
			univention_password.generate_password(**cfg)

	def test_exhausted_uppercase_pool(self):
		with pytest.raises(ValueError, match="There are 1 uppercase characters requested but uppercase pool is empty"):
			cfg = {'digits': 0, 'lower': 0, 'other': 0, 'upper': 1, 'forbidden': string.ascii_uppercase, 'min_length': 2}
			univention_password.generate_password(**cfg)

	def test_exhausted_pool(self):
		with pytest.raises(ValueError, match="All available characters are excluded by.*"):
			cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': string.printable, 'min_length': 6}
			univention_password.generate_password(**cfg)

	def test_all_zeroes(self):
		with pytest.raises(ValueError, match="At least one from the: digits, lower, upper or other characters must be positive number"):
			cfg = {'digits': 0, 'lower': 0, 'other': 0, 'upper': 0, 'forbidden': '', 'min_length': 6}
			univention_password.generate_password(**cfg)


class TestRandomPasswordGenerator(object):
	iter_count = 100

	def test_all_digits(self):
		cfg = {'digits': 3, 'lower': 0, 'other': 0, 'upper': 0, 'forbidden': None, 'min_length': 12}
		pwd = univention_password.generate_password(**cfg)

		assert match_password_complexity(cfg, pwd)

	def test_all_digits_exclude_zero_and_one(self):
		cfg = {'digits': 3, 'lower': 0, 'other': 0, 'upper': 0, 'forbidden': '01', 'min_length': 12}

		for _ in range(0, self.iter_count):
			pwd = univention_password.generate_password(**cfg)

			assert match_password_complexity(cfg, pwd)
			assert "0" not in pwd
			assert "1" not in pwd

	def test_all_lowercase(self):
		cfg = {'digits': 0, 'lower': 3, 'other': 0, 'upper': 0, 'forbidden': None, 'min_length': 12}
		pwd = univention_password.generate_password(**cfg)

		assert match_password_complexity(cfg, pwd)

	def test_all_lowercase_exclude_a_and_b(self):
		cfg = {'digits': 0, 'lower': 3, 'other': 0, 'upper': 0, 'forbidden': 'ab', 'min_length': 12}

		for _ in range(0, self.iter_count):
			pwd = univention_password.generate_password(**cfg)

			assert match_password_complexity(cfg, pwd)
			assert "a" not in pwd
			assert "b" not in pwd

	def test_all_specials(self):
		cfg = {'digits': 0, 'lower': 0, 'other': 3, 'upper': 0, 'forbidden': None, 'min_length': 12}
		pwd = univention_password.generate_password(**cfg)

		assert password_stats(cfg, pwd)['other'] == len(pwd)

	def test_all_specials_exclude_pound_and_braces(self):
		cfg = {'digits': 0, 'lower': 0, 'other': 3, 'upper': 0, 'forbidden': '#()', 'min_length': 12}

		for _ in range(0, self.iter_count):
			pwd = univention_password.generate_password(**cfg)

			assert match_password_complexity(cfg, pwd)
			assert "#" not in pwd
			assert "(" not in pwd
			assert ")" not in pwd

	def test_all_uppercase(self):
		cfg = {'digits': 0, 'lower': 0, 'other': 0, 'upper': 3, 'forbidden': None, 'min_length': 12}
		pwd = univention_password.generate_password(**cfg)

		assert match_password_complexity(cfg, pwd)

	def test_all_uppercase_exclude_cap_a_and_cap_b(self):
		cfg = {'digits': 0, 'lower': 0, 'other': 0, 'upper': 3, 'forbidden': 'AB', 'min_length': 12}

		for _ in range(0, self.iter_count):
			pwd = univention_password.generate_password(**cfg)

			assert match_password_complexity(cfg, pwd)
			assert "A" not in pwd
			assert "B" not in pwd

	def test_radius_password_generate(self):
		cfg = univention_password.password_config('radius')

		for _ in range(0, self.iter_count):
			pwd = univention_password.generate_password(**cfg)

			assert password_stats(cfg, pwd)['other'] == 0
			assert "0" not in pwd
			assert "O" not in pwd
			assert "l" not in pwd
			assert "1" not in pwd
			assert "I" not in pwd

	def test_small_min_length(self):
		cfg = {'digits': 6, 'lower': 6, 'other': 0, 'upper': 0, 'forbidden': '', 'min_length': 6}
		pwd = univention_password.generate_password(**cfg)

		assert match_password_complexity(cfg, pwd)

	def test_zero_min_length(self):
		cfg = {'digits': 6, 'lower': 0, 'other': 0, 'upper': 0, 'forbidden': '', 'min_length': 0}
		pwd = univention_password.generate_password(**cfg)

		assert match_password_complexity(cfg, pwd)
