#!/usr/share/ucs-test/runner /usr/bin/py.test-3 -s
# -*- coding: utf-8 -*-
## desc: Test univention.password.Check()
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python3-univention]

from __future__ import print_function

import pytest

import univention.config_registry
from univention.password import Check, CheckFailed
from univention.testing import ucr as _ucr, udm as _udm


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
