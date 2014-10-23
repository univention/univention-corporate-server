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

from PAM import (
	pam as PAM,
	error as PAMError,
	PAM_PROMPT_ECHO_OFF,
	PAM_PROMPT_ECHO_ON,
	PAM_CONV,
	PAM_NEW_AUTHTOK_REQD,
	PAM_ACCT_EXPIRED,
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

	def authenticate(self, username, password):
		answers = {
#			PAM_PROMPT_ECHO_ON: [password],
			PAM_PROMPT_ECHO_OFF: [password],
		}
		conversation = self._get_conversation(answers)

		pam = self.start(conversation)
		pam.set_item(PAM_USER, username)

		try:
			pam.authenticate()
		except PAMError as autherr:
			AUTH.error("PAM: authentication error: %s" % (autherr,))
			raise AuthenticationFailed(str(autherr[0]))

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

	def change_expired_password(self, username, old_password, new_password):
		prompts = []
		answers = {
			PAM_PROMPT_ECHO_ON: [username],
			PAM_PROMPT_ECHO_OFF: [old_password, new_password, new_password],  # old, new, retype
		}
		conversation = self._get_conversation(answers, prompts)

		pam = self.start(conversation)

		try:
			pam.chauthtok()
		except PAMError as pam_err:
			AUTH.warn('Changing password failed (%s). Prompts: %r' % (pam_err, prompts))
			message = self.parse_error_message_from(prompts)
			raise PasswordChangeFailed(message)

	def start(self, conversation):
		pam = PAM()
		pam.start('univention-management-console')
		pam.set_item(PAM_CONV, conversation)
		return pam

	def _get_conversation(self, answers, prompts=None):
		def conversation(auth, query_list, data):
			if prompts:
				prompts.extend([query for query, qt in query_list])
			return [(answers.get(qt, ['']).pop(0), 0) for query, qt in query_list]
		return conversation

	def parse_error_message_from(self, prompts):
		# okay, check prompts, maybe they have a hint why it failed?
		# prompts are localised, i.e. if the operating system uses German, the prompts are German!
		# try to be exhaustive. otherwise the errors will not be presented to the user.
		if not prompts:
			return 'no-prompts, please see /var/log/auth.log'
		important_prompt = prompts[-1]  # last prompt is some kind of internal error message
		return self.known_errors.get(important_prompt, important_prompt)
