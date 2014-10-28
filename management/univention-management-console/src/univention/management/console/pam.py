#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#
# Copyright 2014 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import traceback

from PAM import (
	pam as PAM,
	error as PAMError,
	PAM_PROMPT_ECHO_OFF,
	PAM_PROMPT_ECHO_ON,
	PAM_CONV,
	PAM_NEW_AUTHTOK_REQD,
	PAM_ACCT_EXPIRED,
	PAM_TEXT_INFO,
	PAM_ERROR_MSG,
	PAM_USER
)

from univention.management.console.log import AUTH


class AuthenticationFailed(Exception):
	pass


class PasswordExpired(Exception):
	pass


class PasswordChangeFailed(Exception):
	pass


class PamAuth(object):
	known_errors = [
		([': Es ist zu kurz', ': Es ist VIEL zu kurz', ': it is WAY too short', ': Password is too short'], 'The password is too short'),
		([': Es ist zu einfach/systematisch', ': it is too simplistic/systematic', ': Password does not meet complexity requirements'], 'The password is too simple'),
		([': is a palindrome'], 'The password is a palindrome'),
		([': Es basiert auf einem Wörterbucheintrag', ': it is based on a dictionary word'], 'The password is based on a dictionary word'),
		([': Password already used'], 'The password was already used'),
		([': Es enthält nicht genug unterschiedliche Zeichen', ': it does not contain enough DIFFERENT characters'], 'The password does not contain enough different characters'),
	]
	known_errors = dict(
		(response_message, user_friendly_response)
		for possible_responses, user_friendly_response in known_errors
		for response_message in possible_responses
	)

	def __init__(self):
		self.__workaround_pw_expired = False

	def authenticate(self, username, password):
		answers = {
			# 'Your password will expire at ...\n', 'Changing password', 'Error: Password does not meet complexity requirements\n'
			PAM_TEXT_INFO: ['', '', ''],

			# 'Password: ', 'New password: ', 'Repeat new password: '
			PAM_PROMPT_ECHO_OFF: [password],

			# 'You are required to change your password immediately (password aged)'
			PAM_ERROR_MSG: ['']
		}
		conversation = self._get_conversation(answers)

		pam = self.start(conversation, username)

		try:
			pam.authenticate()
		except PAMError as autherr:
			AUTH.error("PAM: authentication error: %s" % (autherr,))

			if self.__workaround_pw_expired:
				self._validate_account(pam)

			raise AuthenticationFailed(str(autherr[0]))
		self.__workaround_pw_expired = False

		self._validate_account(pam)

	def _validate_account(self, pam):
		try:
			pam.acct_mgmt()
		except PAMError as pam_err:
			if pam_err[1] == PAM_NEW_AUTHTOK_REQD:  # error: ('Authentication token is no longer valid; new one required', 12)
				raise PasswordExpired(str(pam_err[0]))
			if pam_err[1] == PAM_ACCT_EXPIRED:  # error: ('User account has expired', 13)
				raise AuthenticationFailed(str(pam_err[0]))
			raise

	def change_password(self, username, old_password, new_password):
		prompts = []
		answers = {
			PAM_PROMPT_ECHO_ON: [username],  # 'login:'
			PAM_TEXT_INFO: [''],  # 'Your password will expire at Thu Jan  1 01:00:00 1970\n'
			# 'Current Kerberos password: ', 'New password: ', 'Retype new password: '
			PAM_PROMPT_ECHO_OFF: [old_password, new_password, new_password],
		}
		conversation = self._get_conversation(answers, prompts)

		pam = self.start(conversation, username)

		try:
			pam.chauthtok()
		except PAMError as pam_err:
			AUTH.warn('Changing password failed (%s). Prompts: %r' % (pam_err, prompts))
			message = self._parse_error_message_from(pam_err, prompts)
			raise PasswordChangeFailed(message)

	def start(self, conversation, username):
		pam = PAM()
		pam.start('univention-management-console')
		pam.set_item(PAM_CONV, conversation)
		pam.set_item(PAM_USER, username)
		return pam

	def _get_conversation(self, answers, prompts=None):
		def conversation(auth, query_list, data):
			try:
				if any(b == PAM_TEXT_INFO or b == PAM_ERROR_MSG for a, b in query_list):
					self.__workaround_pw_expired = True
				if prompts is not None:
					prompts.extend([query for query, qt in query_list])
					#AUTH.error('### prompts = %r' % (prompts,))
				answer = [(answers.get(qt, ['']).pop(0), 0) for query, qt in query_list]
			except:
				#AUTH.error('## query_list=%r, auth=%r, data=%r' % (query_list, auth, data))
				AUTH.error(traceback.format_exc())
				raise
			AUTH.error('### query_list=%r, auth=%r, data=%r, answer=%r' % (query_list, auth, data, answer))
			return answer
		return conversation

	def _parse_error_message_from(self, pam_err, prompts):
		# okay, check prompts, maybe they have a hint why it failed?
		# prompts are localised, i.e. if the operating system uses German, the prompts are German!
		# try to be exhaustive. otherwise the errors will not be presented to the user.
		if not prompts:
			important_prompt = str(pam_err[0])
		else:
			# FIXME / TODO: check if this still can occur in UCS4?!
			important_prompt = prompts[-1]  # last prompt is some kind of internal error message
		return self.known_errors.get(important_prompt, important_prompt)
