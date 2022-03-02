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
import re
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
		if policy_result.get('univentionPolicyPWHistory'):
			self.min_length = int(policy_result['univentionPolicyPWHistory']['univentionPWLength']['value'][0])
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
