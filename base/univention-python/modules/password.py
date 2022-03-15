# -*- coding: utf-8 -*-
#
# Copyright 2010-2022 Univention GmbH
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

import cracklib
import os
from random import SystemRandom
import re
import string
import univention.uldap
import univention.debug as ud
import univention.config_registry as ucr
from ldap.filter import filter_format

try:
	from samba import check_password_quality as samba_check_password_quality
except ImportError:
	def samba_check_password_quality(*args, **kwargs):
		ud.debug(ud.LDAP, ud.ERROR, 'samba_check_password_quality() is not available in Python 2. Not checking password quality.')
		return True  # not available, use Python 3


class CheckFailed(Exception):
	pass


class Check(object):

	def __init__(self, lo, username=None):
		self.ConfigRegistry = ucr.ConfigRegistry()
		self.ConfigRegistry.load()

		self.username = username
		self.enableQualityCheck = False
		self.checkHistory = False
		self.min_length = -1
		if not lo:
			self._getConnection()
		else:
			self.lo = lo

		self._systemPolicy()

		if self.username:
			self._userPolicy(self.username)

	def _getConnection(self):
		if os.path.exists('/etc/ldap.secret'):
			self.lo = univention.uldap.getAdminConnection()
		elif os.path.exists('/etc/machine.secret'):
			self.lo = univention.uldap.getMachineConnection(start_tls=2)
		else:
			self.lo = univention.uldap.access(host=self.ConfigRegistry.get('ldap/master'), base=self.ConfigRegistry.get('ldap/base'), start_tls=2)

	def _systemPolicy(self):
		if self.ConfigRegistry.get('password/quality/credit/digits', '0'):
			cracklib.DIG_CREDIT = int(self.ConfigRegistry.get('password/quality/credit/digits', '0')) * -1
		if self.ConfigRegistry.get('password/quality/credit/upper', '0'):
			cracklib.UP_CREDIT = int(self.ConfigRegistry.get('password/quality/credit/upper', '0')) * -1
		if self.ConfigRegistry.get('password/quality/credit/lower', '0'):
			cracklib.LOW_CREDIT = int(self.ConfigRegistry.get('password/quality/credit/lower', '0')) * -1
		if self.ConfigRegistry.get('password/quality/credit/other', '0'):
			cracklib.OTH_CREDIT = int(self.ConfigRegistry.get('password/quality/credit/other', '0')) * -1
		self.forbidden_chars = self.ConfigRegistry.get('password/quality/forbidden/chars', '')
		self.required_chars = self.ConfigRegistry.get('password/quality/required/chars', '')

		# to be compatible with UCS 2.3 kerberos check_cracklib.py
		if self.ConfigRegistry.get('password/quality/length/min', None):
			self.min_length = int(self.ConfigRegistry.get('password/quality/length/min'))
		if self.ConfigRegistry.get('password/quality/ascii_lowercase', None):
			cracklib.ASCII_LOWERCASE = self.ConfigRegistry.get('password/quality/ascii_lowercase')
		if self.ConfigRegistry.get('password/quality/ascii_uppercase', None):
			cracklib.ASCII_UPPERCASE = self.ConfigRegistry.get('password/quality/ascii_uppercase')
		if self.ConfigRegistry.get('password/quality/diff_ok', None):
			cracklib.DIFF_OK = int(self.ConfigRegistry.get('password/quality/diff_ok'))

		# optionally activate Microsoft standard criteria
		self.mspolicy = self.ConfigRegistry.get('password/quality/mspolicy', None)
		# normalize True values
		self.mspolicy = self.ConfigRegistry.is_true(value=self.mspolicy) or self.mspolicy

	def _userPolicy(self, username):
		# username or kerberos principal
		try:
			if '@' in self.username:
				dn = self.lo.searchDn(filter_format('krb5PrincipalName=%s', [username]))[0]
			else:
				dn = self.lo.searchDn(filter_format('(&(uid=%s)(|(&(objectClass=posixAccount)(objectClass=shadowAccount))(objectClass=sambaSamAccount)(&(objectClass=person)(objectClass=organizationalPerson)(objectClass=inetOrgPerson))))', [username]))[0]
		except IndexError:
			raise CheckFailed('User was not found.')

		policy_result = self.lo.getPolicies(dn)
		self.min_length = -1
		self.history_length = -1
		if policy_result.get('univentionPolicyPWHistory'):
			if policy_result['univentionPolicyPWHistory'].get('univentionPWLength'):
				self.min_length = int(policy_result['univentionPolicyPWHistory']['univentionPWLength']['value'][0])
			if policy_result['univentionPolicyPWHistory'].get('univentionPWHistoryLen'):
				self.history_length = int(policy_result['univentionPolicyPWHistory']['univentionPWHistoryLen']['value'][0])
			if policy_result['univentionPolicyPWHistory'].get('univentionPWQualityCheck'):
				univentionPasswordQualityCheck = policy_result['univentionPolicyPWHistory']['univentionPWQualityCheck']['value'][0].decode('ASCII', 'replace')
				self.enableQualityCheck = self.ConfigRegistry.is_true(value=univentionPasswordQualityCheck)
		self.pwhistory = self.lo.search(base=dn, attr=['pwhistory'])[0][1].get('pwhistory')

	def check(self, password, username=None, displayname=None):
		if self.min_length > 0:
			if len(password) < self.min_length:
				raise CheckFailed('Password is too short')
		else:
			cracklib.MIN_LENGTH = 4  # this seems to be the lowest valid value

		# Workaround for users/user, which instanciates Check() without a username:
		# We need the username here, but if we would pass it to Check() then
		# _userPolicy would be run, changing the behavior in users/user.
		if not username:
			username = self.username

		# Todo: check history

		if self.enableQualityCheck:
			if self.mspolicy in (True, 'sufficient'):
				# See https://docs.microsoft.com/de-de/windows/security/threat-protection/security-policy-settings/password-must-meet-complexity-requirements
				if not samba_check_password_quality(password):
					raise CheckFailed('Password does not meet the password complexity requirements.')
				if username and len(username) > 3 and username.lower() in password.lower():
					raise CheckFailed('Password contains user account name.')
				if displayname:
					for namepart in re.split('[-,._# \t]+', displayname):
						if len(namepart) > 3 and namepart.lower() in password.lower():
							raise CheckFailed('Password contains parts of the full user name.')
			if self.mspolicy == 'sufficient':
				return True  # skip all other checks
			for c in self.forbidden_chars:
				if c in password:
					raise CheckFailed('Password contains forbidden characters')
			if self.required_chars:
				for c in self.required_chars:
					if c in password:
						break
				else:
					raise CheckFailed('Password does not contain one of required characters: "%s"' % self.required_chars)

			cracklib.MIN_LENGTH = self.min_length

			try:
				if cracklib.VeryFascistCheck(password) == password:
					return True
			except ValueError as exc:
				raise CheckFailed(str(exc))


# def test_case1():
#	pwdCheck = univention.password.Check(univention.uldap.getMachineConnection(), 'stefan')
#	pwdCheck.check('univention')
#
# def test_case2():
#	pwdCheck = univention.password.Check(univention.uldap.getMachineConnection(), None)
# self.enableQualityCheck = False #True
#	self.pwhistory = ['xxxx yyyy']
#	self.min_length = 8
#	self.history_length = 3
#	pwdCheck.check('univention')
#
# def test_case3():
#	pwdCheck = univention.password.Check(univention.uldap.getMachineConnection(), None)
#	self.enableQualityCheck = True
#	pwdCheck.check('univention')


def password_config(scope=None):
	"""
	Read password configuration options from UCR.

	:param scope: UCR scope in which password configuration options are searched for. Default is None.
	:type scope: :class:`str`

	:return: Password configuration options.
	:rtype: :class:`dict`
	"""
	default_cfg = {
		'digits': ucr.ucr.get_int('password/quality/credit/digits', 6),
		'lower': ucr.ucr.get_int('password/quality/credit/lower', 6),
		'other': ucr.ucr.get_int('password/quality/credit/other', 0),
		'upper': ucr.ucr.get_int('password/quality/credit/upper', 6),
		'forbidden': ucr.ucr.get_int('password/quality/forbidden/chars', '0Ol1I'),
		'min_length': ucr.ucr.get_int('password/quality/length/min', 24),
	}

	if scope:
		cfg = {
			'digits': ucr.ucr.get_int('password/%s/quality/credit/digits' % scope, default_cfg.get('digits')),
			'lower': ucr.ucr.get_int('password/%s/quality/credit/lower' % scope, default_cfg.get('lower')),
			'other': ucr.ucr.get_int('password/%s/quality/credit/other' % scope, default_cfg.get('other')),
			'upper': ucr.ucr.get_int('password/%s/quality/credit/upper' % scope, default_cfg.get('upper')),
			'forbidden': ucr.ucr.get('password/%s/quality/forbidden/chars' % scope, default_cfg.get('forbidden')),
			'min_length': ucr.ucr.get_int('password/%s/quality/length/min' % scope, default_cfg.get('min_length')),
		}
	else:
		cfg = default_cfg

	return cfg


def generate_password(digits=6, lower=6, other=0, upper=6, forbidden='', min_length=24):
	"""
	Generate random password using given parameters. Whitespaces are implicitly forbidden.

	:param digits: Minimal number of digits in generated password. 0 excludes it from the password.
	:type digits: :class:`int`

	:param lower: Minimal number of lowercase ASCII letters in generated password. 0 excludes it from the password.
	:type lower: :class:`int`

	:param other: Minimal number of special characters in generated password. 0 excludes it from the password.
	:type other: :class:`int`

	:param upper: Minimal number of uppercase ASCII letters in generated password. 0 excludes it from the password.
	:type upper: :class:`int`

	:param forbidden: Forbidden characters in generated password.
	:type forbidden: :class:`str`

	:param min_length: Minimal length of generated password.
	:type min_length: :class:`int`

	:return: Randomly generated password.
	:rtype: :class:`str`

	:raises ValueError: In case any password quality precondition fails.
	"""
	special_characters = string.punctuation
	forbidden_chars = forbidden or ''
	exclude_characters = set(forbidden_chars) | string.whitespace

	if 0 > digits or 0 > lower or 0 > other or 0 > upper:
		raise ValueError('Number of digits, lower, upper or other characters can not be negative')
	elif 0 >= digits + lower + other + upper:
		raise ValueError('At least one from the: digits, lower, upper or other characters must be positive number')

	available_chars = set(string.printable) - exclude_characters
	if not available_chars:
		raise ValueError('All available characters are excluded by the rule: %r', (exclude_characters,))

	rnd = SystemRandom()

	digit_characters = ''.join(set(string.digits) - set(exclude_characters)) if digits > 0 else ''
	ascii_lowercase = ''.join(set(string.ascii_lowercase) - set(exclude_characters)) if lower > 0 else ''
	ascii_uppercase = ''.join(set(string.ascii_uppercase) - set(exclude_characters)) if upper > 0 else ''
	special_characters = ''.join(set(special_characters) - set(exclude_characters)) if other > 0 else ''

	random_list = []
	if digits > 0:
		if digit_characters:
			random_list.extend(rnd.choices(digit_characters, k=digits))
		else:
			raise ValueError('There are %s digits requested but digits pool is empty' % (digits,))

	if lower > 0:
		if ascii_lowercase:
			random_list.extend(rnd.choices(ascii_lowercase, k=lower))
		else:
			raise ValueError('There are %s lowercase characters requested but lowercase pool is empty' % (lower,))

	if upper > 0:
		if ascii_uppercase:
			random_list.extend(rnd.choices(ascii_uppercase, k=upper))
		else:
			raise ValueError('There are %s uppercase characters requested but uppercase pool is empty' % (upper,))

	if other > 0:
		if special_characters:
			random_list.extend(rnd.choices(special_characters, k=other))
		else:
			raise ValueError('There are %s special characters requested but special characters pool is empty' % (other,))

	if min_length > len(random_list):
		available_char_pool = ''.join(set(digit_characters + ascii_lowercase + ascii_uppercase + special_characters))
		random_list.extend(rnd.choices(available_char_pool, k=min_length - len(random_list)))

	rnd.shuffle(random_list)
	res = ''.join(random_list)

	return res
