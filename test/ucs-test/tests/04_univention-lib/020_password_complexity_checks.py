#!/usr/share/ucs-test/runner /usr/bin/py.test-3 -s
# -*- coding: utf-8 -*-
## desc: Test univention.password.Check()
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python3-univention]

from __future__ import print_function

from univention.password import Check, CheckFailed, password_config, generate_password
import univention.config_registry
import pytest
from _pytest.monkeypatch import MonkeyPatch
import string
from univention.testing import udm as _udm
from univention.testing import ucr as _ucr


class Password(object):
	'''Just a namespace for password providers'''

	@staticmethod
	def upperLower10(username=None):
		return "Univention"

	@classmethod
	def upperLowerOther(cls, username=None):
		return cls.upperLower10() + "."

	@classmethod
	def upperLowerDigit(cls, username=None):
		return cls.upperLower10() + "1"

	@classmethod
	def upperLowerDigitOther(cls, username=None):
		return cls.upperLower10() + "." + "1"

	@classmethod
	def lowercaseonly10(cls, username=None):
		return cls.upperLower10().lower()

	@classmethod
	def lowerDigit(cls, username=None):
		return cls.lowercaseonly10() + "1"

	@classmethod
	def lowerOther(cls, username=None):
		return cls.lowercaseonly10() + "."

	@classmethod
	def lowerOtherDigit(cls, username=None):
		return cls.lowercaseonly10() + "." + "1"

	@staticmethod
	def cracklib_waytooshort(username=None):
		return "U.1"

	@classmethod
	def cracklib_toosystematic(cls, username=None):
		return cls.upperLowerDigitOther() + 10 * "a"

	@staticmethod
	def cracklib_socialsecuritynumberformat(username=None):
		return "ab123456c"

	@staticmethod
	def cracklib_whitespace(username=None):
		return 10 * " "

	@classmethod
	def palindrome(cls, username=None):
		word = cls.upperLowerDigitOther()
		return word[::-1] + word

	@classmethod
	def startswith_username(cls, username):
		return username + cls.upperLowerDigitOther()

	@classmethod
	def contains_username(cls, username):
		word = cls.upperLowerDigitOther()
		return word[:4] + username + word[4:]


class PasswordType(object):
	'''Just a namespace for PasswordType providers
	to avoid collision with parameter fixture names.
	'''

	@staticmethod
	def password_conforming_to_mspolicy():
		return [
			Password.lowerOtherDigit,
			Password.upperLowerDigit,
			Password.upperLowerOther,
			Password.upperLowerDigitOther,
		]

	@staticmethod
	def password_not_conforming_to_mspolicy():
		return [
			Password.lowercaseonly10,
			Password.lowerDigit,
			Password.lowerOther,
			Password.upperLower10,
		]

	@classmethod
	def password_not_conforming_to_mspolicy_with_username(cls):
		return cls.password_not_conforming_to_mspolicy() + [
			Password.startswith_username,
			Password.contains_username,
		]

	@classmethod
	def password_conforming_to_cracklib(cls):
		return cls.password_conforming_to_mspolicy()  # not quite right, be would need to check for adjusted UCR password/quality/* and minimal length

	@classmethod
	def password_not_conforming_to_cracklib(cls):
		return [
			Password.cracklib_waytooshort,
			# Password.cracklib_toosystematic,  # apparently not (yet?) checked in out version of cracklib
			Password.cracklib_whitespace,
			Password.palindrome,
			Password.cracklib_socialsecuritynumberformat,
		]

	@classmethod
	def password_not_conforming_to_cracklib_with_mandatory_UpperLowerDigitOther(cls):
		return cls.password_not_conforming_to_cracklib() + cls.password_not_conforming_to_mspolicy()

	@classmethod
	def password_conforming_to_mspolicy_plus_cracklib(cls):
		return cls.password_conforming_to_mspolicy()  # not quite right, be would need to check for adjusted UCR password/quality/* and minimal length

	@classmethod
	def password_not_conforming_to_mspolicy_plus_cracklib(cls):
		return cls.password_not_conforming_to_mspolicy_with_username() + cls.password_not_conforming_to_cracklib()


# I want the udm user to live on module scope here
@pytest.fixture(scope="module")
def udm():
	with _udm.UCSTestUDM() as udm:
		yield udm


@pytest.fixture(scope="module")
def existing_username(udm):
	dn, username = udm.create_user()
	yield username
	# No explicit teardown required


# I want the ucr to live on class scope here
@pytest.fixture(scope="class")
def ucr():
	with _ucr.UCSTestConfigRegistry() as ucr:
		yield ucr


@pytest.fixture(scope="class")
def pwc_default(ucr, existing_username):
	pwc = Check(None, username=existing_username)
	pwc.enableQualityCheck = True  # may have been overridden by univentionPolicyPWHistory
	yield pwc


@pytest.fixture(scope="class")
def pwc_with_mspolicy(ucr, existing_username):
	univention.config_registry.handler_set(["password/quality/mspolicy=yes"])
	univention.config_registry.handler_set(["password/quality/length/min=8"])
	# Set the UCS defaults, just to be safe
	univention.config_registry.handler_unset([
		"password/quality/credit/digits", "password/quality/credit/upper", "password/quality/credit/lower", "password/quality/credit/other",
		"password/quality/forbidden/chars", "password/quality/required/chars"
	])
	pwc = Check(None, username=existing_username)
	pwc.enableQualityCheck = True  # may have been overridden by univentionPolicyPWHistory
	pwc.min_length = 8  # may have been overridden by univentionPolicyPWHistory
	yield pwc


@pytest.fixture(scope="class")
def pwc_with_mspolicy_only(ucr, existing_username):
	univention.config_registry.handler_set(["password/quality/mspolicy=sufficient"])
	univention.config_registry.handler_set(["password/quality/length/min=8"])
	# Set these variables, but they must get ingored
	univention.config_registry.handler_set([
		"password/quality/credit/digits=1", "password/quality/credit/upper=1", "password/quality/credit/lower=1", "password/quality/credit/other=1"
	])
	pwc = Check(None, username=existing_username)
	pwc.enableQualityCheck = True  # may have been overridden by univentionPolicyPWHistory
	pwc.min_length = 8  # may have been overridden by univentionPolicyPWHistory
	yield pwc


@pytest.fixture(scope="class")
def pwc_with_cracklib_mandatory_character_classes(ucr, existing_username):
	# mspolicy muts not be 'sufficient' for test_not_conforming_to_cracklib_with_mandatory_classes, but can be unset or true-ish, probably doesn't matter here
	# univention.config_registry.handler_unset(["password/quality/mspolicy"])
	univention.config_registry.handler_set(["password/quality/length/min=8"])
	univention.config_registry.handler_set([
		"password/quality/credit/digits=1", "password/quality/credit/upper=1", "password/quality/credit/lower=1", "password/quality/credit/other=1"
	])
	pwc = Check(None, username=existing_username)
	pwc.enableQualityCheck = True  # may have been overridden by univentionPolicyPWHistory
	pwc.min_length = 8  # may have been overridden by univentionPolicyPWHistory
	yield pwc


# Ugly, each parameter has to have a fixture of the same name
# We dispatch to the passwort provider method passed as request.param
@pytest.fixture(scope="module")
def password_conforming_to_mspolicy(request, existing_username):
	return request.param(existing_username)


@pytest.fixture(scope="module")
def password_not_conforming_to_mspolicy_with_username(request, existing_username):
	return request.param(existing_username)


@pytest.fixture(scope="module")
def password_not_conforming_to_mspolicy_plus_cracklib(request, existing_username):
	return request.param(existing_username)


@pytest.fixture(scope="module")
def password_conforming_to_mspolicy_plus_cracklib(request, existing_username):
	return request.param(existing_username)


@pytest.fixture(scope="module")
def password_not_conforming_to_cracklib(request, existing_username):
	return request.param(existing_username)


@pytest.fixture(scope="module")
def password_conforming_to_cracklib(request, existing_username):
	return request.param(existing_username)


@pytest.fixture(scope="module")
def password_not_conforming_to_cracklib_with_mandatory_UpperLowerDigitOther(request, existing_username):
	return request.param(existing_username)


PASSWORD_TYPE_PROVIDERS = [f for f in dir(PasswordType) if callable(getattr(PasswordType, f))]


# This parameterizes the password_* arguments with the result of the corresponding methods at setup time
def pytest_generate_tests(metafunc):
	for parameter in PASSWORD_TYPE_PROVIDERS:
		if parameter in metafunc.fixturenames:
			passwordtype_provider = getattr(PasswordType, parameter)
			password_provider_list = passwordtype_provider()
			metafunc.parametrize(parameter, password_provider_list, indirect=True)  # pass each password_provider as request.param to the fixture at collection time
			break


class Test_PasswordPolicyCheck_default(object):
	def test_not_conforming_to_cracklib(self, pwc_default, password_not_conforming_to_cracklib, existing_username):
		with pytest.raises(CheckFailed):
			pwc_default.check(password_not_conforming_to_cracklib)

	def test_conforming_to_cracklib(self, pwc_default, password_conforming_to_cracklib, existing_username):
		pwc_default.check(password_conforming_to_cracklib)


class Test_PasswordPolicyCheck_with_mspolicy_only(object):
	def test_not_conforming_to_mspolicy_only(self, pwc_with_mspolicy_only, password_not_conforming_to_mspolicy_with_username, existing_username):
		with pytest.raises(CheckFailed):
			pwc_with_mspolicy_only.check(password_not_conforming_to_mspolicy_with_username)

	def test_conforming_to_mspolicy_only(self, pwc_with_mspolicy_only, password_conforming_to_mspolicy, existing_username):
		pwc_with_mspolicy_only.check(password_conforming_to_mspolicy)


class Test_PasswordPolicyCheck_with_mspolicy_plus_cracklib(object):
	def test_not_conforming_to_mspolicy_plus_cracklib(self, pwc_with_mspolicy, password_not_conforming_to_mspolicy_plus_cracklib, existing_username):
		with pytest.raises(CheckFailed):
			pwc_with_mspolicy.check(password_not_conforming_to_mspolicy_plus_cracklib)

	def test_conforming_to_mspolicy_plus_cracklib(self, pwc_with_mspolicy, password_conforming_to_mspolicy_plus_cracklib, existing_username):
		pwc_with_mspolicy.check(password_conforming_to_mspolicy_plus_cracklib)


class Test_PasswordPolicyCheck_with_mandatory_classes(object):
	def test_not_conforming_to_cracklib_with_mandatory_classes(self, pwc_with_cracklib_mandatory_character_classes, password_not_conforming_to_cracklib_with_mandatory_UpperLowerDigitOther, existing_username):
		with pytest.raises(CheckFailed):
			pwc_with_cracklib_mandatory_character_classes.check(password_not_conforming_to_cracklib_with_mandatory_UpperLowerDigitOther)


@pytest.fixture(scope='class')
def password_config_default():
	cfg = password_config()
	yield cfg


@pytest.fixture(scope='class')
def password_radius_config():
	cfg = password_config('radius')
	yield cfg


def password_stats(cfg, password):
	"""
	Calculate password stats based on given configuration
	"""
	special_characters = string.punctuation
	forbidden_characters = cfg.get('forbidden', '')
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
		elif c in forbidden_characters:
			forbidden += 1

	return {'digits': digits, 'lower': lower, 'other': other, 'upper': upper, 'forbidden': forbidden}


def match_password_complexity(cfg, password):
	"""
	Test if given password matches complexity criteria.
	"""
	if not password or set(password) <= set(string.whitespace):
		return False

	stats = password_stats(cfg, password)
	digits = stats['digits']
	lower = stats['lower']
	other = stats['other']
	upper = stats['upper']
	forbidden = stats['forbidden']

	return 0 == forbidden and digits >= cfg['digits'] and lower >= cfg['lower'] and other >= cfg['other'] and upper >= cfg['upper']


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
		assert password_config_default['forbidden'] == ''


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

	def test_digit_count(self):
		with MonkeyPatch.context() as mp:
			mp.setattr("univention.config_registry.ucr", {'password/%s/quality/credit/digits' % self.scope: None}, raising=True)
			cfg = password_config(self.scope)
			assert cfg['digits'] == 6

	def test_lowercase_count(self):
		with MonkeyPatch.context() as mp:
			mp.setattr("univention.config_registry.ucr", {'password/%s/quality/credit/lower' % self.scope: None}, raising=True)
			cfg = password_config(self.scope)
			assert cfg['lower'] == 6

	def test_special_count(self):
		with MonkeyPatch.context() as mp:
			mp.setattr("univention.config_registry.ucr", {'password/%s/quality/credit/other' % self.scope: None}, raising=True)
			cfg = password_config(self.scope)
			assert cfg['other'] == 0

	def test_uppercase(self, password_config_default):
		with MonkeyPatch.context() as mp:
			mp.setattr("univention.config_registry.ucr", {'password/%s/quality/credit/upper' % self.scope: None}, raising=True)
			cfg = password_config(self.scope)
			assert cfg['upper'] == 6

	def test_min_length(self, password_config_default):
		with MonkeyPatch.context() as mp:
			mp.setattr("univention.config_registry.ucr", {'password/%s/quality/length/min' % self.scope: None}, raising=True)
			cfg = password_config(self.scope)
			assert cfg['min_length'] == 24

	def test_special_characters(self, password_config_default):
		with MonkeyPatch.context() as mp:
			mp.setattr("univention.config_registry.ucr", {'password/%s/quality/forbidden/chars' % self.scope: None}, raising=True)
			cfg = password_config(self.scope)
			assert cfg['forbidden'] == '0Ol1I'


class TestPasswordConfigDigitCount(object):

	def test_none(self):
		with pytest.raises(TypeError):
			cfg = {'digits': None, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_negative(self):
		with pytest.raises(ValueError, match="Number of digits, lower, upper or other characters can not be negative"):
			cfg = {'digits': -1, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_empty_string(self):
		with pytest.raises(ValueError, match="invalid literal for int()*"):
			cfg = {'digits': '', 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_zero(self):
		digit_count = 0
		cfg = {'digits': digit_count, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['digits'] == digit_count)

	def test_positive_number(self):
		digit_count = 3
		cfg = {'digits': digit_count, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['digits'] >= digit_count)

	def test_valid_string(self):
		digit_count = "3"
		cfg = {'digits': digit_count, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['digits'] >= int(digit_count))


class TestPasswordConfigLowerCaseCount(object):

	def test_none(self):
		with pytest.raises(TypeError):
			cfg = {'digits': 1, 'lower': None, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_negative(self):
		with pytest.raises(ValueError, match="Number of digits, lower, upper or other characters can not be negative"):
			cfg = {'digits': 1, 'lower': -1, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_empty_string(self):
		with pytest.raises(ValueError, match="invalid literal for int()*"):
			cfg = {'digits': 1, 'lower': '', 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_zero(self):
		lowercase_count = 0
		cfg = {'digits': 1, 'lower': lowercase_count, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['lower'] == lowercase_count)

	def test_positive_number(self):
		lowercase_count = 3
		cfg = {'digits': 1, 'lower': lowercase_count, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['lower'] >= lowercase_count)

	def test_valid_string(self):
		lowercase_count = "3"
		cfg = {'digits': 1, 'lower': lowercase_count, 'other': 1, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['lower'] >= int(lowercase_count))


class TestPasswordConfigSpecialCharacterCount(object):

	def test_none(self):
		with pytest.raises(TypeError):
			cfg = {'digits': 1, 'lower': 1, 'other': None, 'upper': 1, 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_negative(self):
		with pytest.raises(ValueError, match="Number of digits, lower, upper or other characters can not be negative"):
			cfg = {'digits': 1, 'lower': 1, 'other': -1, 'upper': 1, 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_empty_string(self):
		with pytest.raises(ValueError, match="invalid literal for int()*"):
			cfg = {'digits': 1, 'lower': 1, 'other': '', 'upper': 1, 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_empty_pool(self):
		with pytest.raises(ValueError, match="There are 1 special characters requested but special characters pool is empty"):
			cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': string.punctuation, 'min_length': 6}
			generate_password(**cfg)

	def test_zero(self):
		special_count = 0
		cfg = {'digits': 1, 'lower': 1, 'other': special_count, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['other'] == special_count)

	def test_positive_number(self):
		special_count = 3
		cfg = {'digits': 1, 'lower': 1, 'other': special_count, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['other'] >= special_count)

	def test_valid_string(self):
		special_count = "3"
		cfg = {'digits': 1, 'lower': 1, 'other': special_count, 'upper': 1, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['other'] >= int(special_count))


class TestPasswordConfigUpperCaseCount(object):

	def test_none(self):
		with pytest.raises(TypeError):
			cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': None, 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_negative(self):
		with pytest.raises(ValueError, match="Number of digits, lower, upper or other characters can not be negative"):
			cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': -1, 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_empty_string(self):
		with pytest.raises(ValueError, match="invalid literal for int()*"):
			cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': '', 'forbidden': None, 'min_length': 6}
			generate_password(**cfg)

	def test_zero(self):
		uppercase_count = 0
		cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': uppercase_count, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['upper'] == uppercase_count)

	def test_positive_number(self):
		uppercase_count = 0
		cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': uppercase_count, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['upper'] >= uppercase_count)

	def test_valid_string(self):
		uppercase_count = "3"
		cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': uppercase_count, 'forbidden': None, 'min_length': 6}
		pwd = generate_password(**cfg)

		assert (password_stats(cfg, pwd)['upper'] >= int(uppercase_count))


class TestPasswordConfigExhaustedAvailableCharacterPool(object):

	def test_exhausted_digits_pool(self):
		with pytest.raises(ValueError, match="There are 1 digits requested but digits pool is empty"):
			cfg = {'digits': 1, 'lower': 0, 'other': 0, 'upper': 0, 'forbidden': string.digits, 'min_length': 2}
			generate_password(**cfg)

	def test_exhausted_lowercase_pool(self):
		with pytest.raises(ValueError, match="There are 1 lowercase characters requested but lowercase pool is empty"):
			cfg = {'digits': 0, 'lower': 1, 'other': 0, 'upper': 0, 'forbidden': string.ascii_lowercase, 'min_length': 2}
			generate_password(**cfg)

	def test_exhausted_special_character_pool(self):
		with pytest.raises(ValueError, match="There are 1 special characters requested but special characters pool is empty"):
			cfg = {'digits': 0, 'lower': 0, 'other': 1, 'upper': 0, 'forbidden': string.punctuation, 'min_length': 2}
			generate_password(**cfg)

	def test_exhausted_uppercase_pool(self):
		with pytest.raises(ValueError, match="There are 1 uppercase characters requested but uppercase pool is empty"):
			cfg = {'digits': 0, 'lower': 0, 'other': 0, 'upper': 1, 'forbidden': string.ascii_uppercase, 'min_length': 2}
			generate_password(**cfg)

	def test_exhausted_pool(self):
		with pytest.raises(ValueError, match="All available characters are excluded by.*"):
			cfg = {'digits': 1, 'lower': 1, 'other': 1, 'upper': 1, 'forbidden': string.printable, 'min_length': 6}
			generate_password(**cfg)

	def test_all_zeroes(self):
		with pytest.raises(ValueError, match="At least one from the: digits, lower, upper or other characters must be positive number"):
			cfg = {'digits': 0, 'lower': 0, 'other': 0, 'upper': 0, 'forbidden': '', 'min_length': 6}
			generate_password(**cfg)


class TestRandomPasswordGenerator(object):
	iter_count = 100

	def test_all_digits(self):
		cfg = {'digits': 3, 'lower': 0, 'other': 0, 'upper': 0, 'forbidden': None, 'min_length': 12}
		pwd = generate_password(**cfg)

		assert match_password_complexity(cfg, pwd)
		assert password_stats(cfg, pwd)['digits'] == len(pwd)

	def test_all_digits_exclude_zero_and_one(self):
		cfg = {'digits': 3, 'lower': 0, 'other': 0, 'upper': 0, 'forbidden': '01', 'min_length': 12}

		for _ in range(0, self.iter_count):
			pwd = generate_password(**cfg)

			assert match_password_complexity(cfg, pwd)
			assert "0" not in pwd
			assert "1" not in pwd

	def test_all_lowercase(self):
		cfg = {'digits': 0, 'lower': 3, 'other': 0, 'upper': 0, 'forbidden': None, 'min_length': 12}
		pwd = generate_password(**cfg)

		assert match_password_complexity(cfg, pwd)
		assert password_stats(cfg, pwd)['lower'] == len(pwd)

	def test_all_lowercase_exclude_a_and_b(self):
		cfg = {'digits': 0, 'lower': 3, 'other': 0, 'upper': 0, 'forbidden': 'ab', 'min_length': 12}

		for _ in range(0, self.iter_count):
			pwd = generate_password(**cfg)

			assert match_password_complexity(cfg, pwd)
			assert "a" not in pwd
			assert "b" not in pwd

	def test_all_specials(self):
		cfg = {'digits': 0, 'lower': 0, 'other': 3, 'upper': 0, 'forbidden': None, 'min_length': 12}
		pwd = generate_password(**cfg)

		assert password_stats(cfg, pwd)['other'] == len(pwd)

	def test_all_specials_exclude_pound_and_braces(self):
		cfg = {'digits': 0, 'lower': 0, 'other': 3, 'upper': 0, 'forbidden': '#()', 'min_length': 12}

		for _ in range(0, self.iter_count):
			pwd = generate_password(**cfg)

			assert match_password_complexity(cfg, pwd)
			assert "#" not in pwd
			assert "(" not in pwd
			assert ")" not in pwd

	def test_all_uppercase(self):
		cfg = {'digits': 0, 'lower': 0, 'other': 0, 'upper': 3, 'forbidden': None, 'min_length': 12}
		pwd = generate_password(**cfg)

		assert match_password_complexity(cfg, pwd)
		assert password_stats(cfg, pwd)['upper'] == len(pwd)

	def test_all_uppercase_exclude_cap_a_and_cap_b(self):
		cfg = {'digits': 0, 'lower': 0, 'other': 0, 'upper': 3, 'forbidden': 'AB', 'min_length': 12}

		for _ in range(0, self.iter_count):
			pwd = generate_password(**cfg)

			assert match_password_complexity(cfg, pwd)
			assert "A" not in pwd
			assert "B" not in pwd

	def test_radius_password_generate(self):
		cfg = password_config('radius')

		for _ in range(0, self.iter_count):
			pwd = generate_password(**cfg)

			assert password_stats(cfg, pwd)['other'] == 0
			assert "0" not in pwd
			assert "O" not in pwd
			assert "l" not in pwd
			assert "1" not in pwd
			assert "I" not in pwd
