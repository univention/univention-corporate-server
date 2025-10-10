#!/usr/bin/python3
#
# Univention Management Console
#
# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re
from re import Pattern
from typing import TYPE_CHECKING, Any

from PAM import (
    PAM_ACCT_EXPIRED, PAM_AUTH_ERR, PAM_AUTHTOK_ERR, PAM_AUTHTOK_RECOVER_ERR, PAM_CONV, PAM_ERROR_MSG,
    PAM_NEW_AUTHTOK_REQD, PAM_PROMPT_ECHO_OFF, PAM_PROMPT_ECHO_ON, PAM_TEXT_INFO, PAM_USER, PAM_USER_UNKNOWN,
    error as PAMError, pam as PAM,
)

from univention.lib.i18n import I18N_Error, Translation
from univention.management.console.config import ucr
from univention.management.console.log import AUTH


if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence


_ = Translation('univention.management.console').translate

_('The password is too short.')
_('The password is too long.')
_('The password is too simple.')
_('The password is a palindrome.')
_('The password is based on a dictionary word.')
_('The password was already used.')
_('The password does not contain enough different characters.')
_('The password has expired and must be renewed.')
_('The minimum password age is not reached yet.')
_('Make sure the kerberos service is functioning or inform an Administrator.')
_('The password is too similar to the old one.')
_('The password does not meet the password complexity requirements.')
_('The password contains user account name.')
_('The password contains parts of the full user name.')


class AuthenticationError(Exception):  # abstract base class
    pass


class AuthenticationFailed(AuthenticationError):
    pass


class AuthenticationInformationMissing(AuthenticationError):

    def __init__(self, message: str, missing_prompts: Any) -> None:
        self.missing_prompts = missing_prompts
        super().__init__(message)


class AccountExpired(AuthenticationError):
    pass


class PasswordExpired(AuthenticationError):
    pass


class PasswordChangeFailed(AuthenticationError):
    pass


class PamAuth:

    _known_errors: dict[str, list[str | Pattern[str]]] = {
        'Make sure the kerberos service is functioning or inform an Administrator.': [
            'Unable to reach any changepw server  in realm %s',
        ],
        'The password is too short.': [
            re.compile(r'Password too short, password must be at least (?P<minlen>\d+) characters long.', re.I),
            re.compile('^Password too short$'),
            'You must choose a longer password'
            'Password Too Short',
            'Password is too short',
            ': Es ist zu kurz',
            ': Es ist VIEL zu kurz',
            ': it is WAY too short',
            ': Password is too short',
            'BAD PASSWORD: it is WAY too short',
            'Schlechtes Passwort: Es ist zu kurz',
            'Schlechtes Passwort: Es ist VIEL zu kurz',
        ],
        'The password is too long.': [
            'You must choose a shorter password.',
            'Sie müssen ein kürzeres Passwort wählen.',
        ],
        'The password is too simple.': [
            ': Es ist zu einfach/systematisch',
            ': it is too simplistic/systematic',
            'BAD PASSWORD: is too simple',
            ': Password does not meet complexity requirements',
            'Schlechtes Passwort: ist zu einfach',
            'Error: Password does not meet complexity requirements',
            'Bad: new password is too simple',
            'Insufficient Password Quality',
            'Password Insufficient',
            'Password does not meet complexity requirements',
            'is too simple',
            "The passwort didn't pass quality check",
            "Password doesn't meet complexity requirement.",
            # 'contains the user name in some form'
        ],
        'The password is a palindrome.': [
            'is a palindrome',
            'Bad: new password cannot be a palindrome',
            ': is a palindrome',
            'Schlechtes Passwort: ist ein Palindrome',
            'Schlechtes Passwort: wurde gedreht',
        ],
        'The password is based on a dictionary word.': [
            ': Es basiert auf einem Wörterbucheintrag',
            ': it is based on a dictionary word',
            'Schlechtes Passwort: Es basiert auf einem (umgekehrten) W?rterbucheintrag',
            'Schlechtes Passwort: Es basiert auf einem (umgekehrten) Wörterbucheintrag',
            'Schlechtes Passwort: Es basiert auf einem W?rterbucheintrag',
            'Schlechtes Passwort: Es basiert auf einem Wörterbucheintrag',
        ],
        'The password was already used.': [
            re.compile(r'Password is already in password history. New password must not match any of your (?P<history>\d+) previous passwords.', re.I),
            re.compile('^Password is already in password history$'),
            ': Password already used',
            'Bad: new password must be different than the old one',
            'Password already used',
            'Password has been already used.',
            'Password has been already used. Choose another.',
            'is the same as the old one',
            'is rotated',
            'password unchanged',
            'Passwort nicht geändert',
        ],
        'The password does not contain enough different characters.': [
            ': Es enthält nicht genug unterschiedliche Zeichen',
            ': it does not contain enough DIFFERENT characters',
            'not enough character classes',
            'contains too many same characters consecutively',
            'contains too long of a monotonic character sequence',
        ],
        'The password is too similar to the old one.': [
            'case changes only',
            'Bad: new and old password must differ by more than just case',
            'is too similar to the old one',
            'Bad: new and old password are too similar',
            'Bad: new password is just a wrapped version of the old one',
            'Schlechtes Passwort: ist dem alten zu ?hnlich',
            'Schlechtes Passwort: ist dem alten zu ähnlich',
        ],
        'The minimum password age is not reached yet.': [
            'You must wait longer to change your password',
            'Password Too Young',
            'Password change rejected, password changes may not be permitted on this account, or the minimum password age may not have elapsed.',
        ],
        'The password does not meet the password complexity requirements.': [
            'Password does not meet the password complexity requirements.',
        ],
        'The password contains user account name.': [
            'Password contains user account name.',
        ],
        'The password contains parts of the full user name.': [
            'Password contains parts of the full user name.',
        ],
    }
    known_errors: dict[str | Pattern[str], str] = {
        response_message: user_friendly_response
        for user_friendly_response, possible_responses in _known_errors.items()
        for response_message in possible_responses
    }

    custom_prompts: tuple[str, ...] = ('OTP',)

    def __init__(self, locale: str | None = None) -> None:
        i18n = Translation('univention-management-console')
        try:
            i18n.set_language(locale or 'C')
        except (I18N_Error, AttributeError, TypeError):
            i18n.set_language('C')
        self._ = i18n.translate
        self._language = i18n.locale.language
        self.pam = self.init()

    def _get_password_complexity_message(self) -> str:
        return ucr.get(
            'umc/login/password-complexity-message/%s' % (self._language,),
            ucr.get('umc/login/password-complexity-message/en', ''),
        )

    def authenticate(self, username: str, password: str, **answers: Any) -> None:
        answers.update({
            PAM_TEXT_INFO: '',
            PAM_ERROR_MSG: '',
            PAM_PROMPT_ECHO_ON: username,
            PAM_PROMPT_ECHO_OFF: password,
        })
        missing: list = []
        self.start(username, (answers, [], missing))

        try:
            self.pam.authenticate()
            self.pam.acct_mgmt()
        except PAMError as pam_err:
            AUTH.error("PAM: authentication error: %s", pam_err)
            if pam_err.args[1] == PAM_NEW_AUTHTOK_REQD:  # error: ('Authentication token is no longer valid; new one required', 12)
                message = self.error_message(pam_err.args)
                raise PasswordExpired(("%s %s" % (message, self._get_password_complexity_message())).rstrip())
            if pam_err.args[1] == PAM_ACCT_EXPIRED:  # error: ('User account has expired', 13)
                raise AccountExpired(self.error_message(pam_err.args))
            if missing:
                message = self._('Please insert your one time password (OTP).')
                raise AuthenticationInformationMissing(message, missing)
            raise AuthenticationFailed(self.error_message(pam_err.args))

    def change_password(self, username: str, old_password: str, new_password: str) -> None:
        answers = {
            PAM_TEXT_INFO: '',
            PAM_ERROR_MSG: '',
            PAM_PROMPT_ECHO_ON: username,
            PAM_PROMPT_ECHO_OFF: [old_password, new_password, new_password],
            # pam_kerberos asks for the old password first and then twice for the new password.
            # 'Current Kerberos password: ', 'New password: ', 'Retype new password: '
        }
        prompts: list = []
        self.start(username, (answers, prompts, []))
        # we are parsing error messages. Best to get the english version. Unfortionately not all pam modules evaluate these variables
        self.pam.putenv('LC_ALL=en_US.UTF-8')
        self.pam.putenv('LC_MESSAGES=en_US.UTF-8')
        self.pam.putenv('LANG=en_US.UTF-8')

        try:
            self.pam.chauthtok()
        except PAMError as pam_err:
            AUTH.warning('Changing password failed (%s). Prompts: %r', pam_err, prompts)
            message = self._parse_error_message_from(pam_err.args, prompts)
            raise PasswordChangeFailed(
                ('%s %s %s' % (self._('Changing password failed.'), message, self._get_password_complexity_message())).rstrip(),
            )

    def init(self) -> PAM:
        pam = PAM()
        pam.start('univention-management-console')
        return pam

    def start(self, username: str, data: Any) -> None:
        self.pam.set_item(PAM_CONV, self.conversation)
        self.pam.set_item(PAM_USER, username)
        self.pam.setUserData(data)

    def end(self) -> None:
        # TODO: call pam_end() instead
        self.pam.set_item(PAM_CONV, lambda a, b, c: None)  # free self.conversation leaking
        del self.pam  # causes pam_end() to be called to free ldap connections

    def conversation(self, auth: Any, query_list: Any, data: Any) -> list:
        try:
            return list(self._conversation(auth, query_list, data))
        except BaseException:
            AUTH.exception('Unexpected error during PAM conversation')
            raise

    def _conversation(self, auth: Any, query_list: list[tuple[Any, Any]], data: Any) -> Iterator[tuple[str, int]]:
        answers, prompts, missing = data
        prompts.extend(query_list)
        for query, qt in query_list:
            prompt = qt
            if qt == PAM_PROMPT_ECHO_OFF and query.strip(':\t ') in self.custom_prompts:
                prompt = query

            response = ''
            try:
                response = answers[prompt]
                if isinstance(response, list):
                    response = response.pop(0)
            except KeyError as exc:
                AUTH.error('Missing answer for prompt: %r', str(exc))
                missing.append(query)
            except IndexError:
                AUTH.error('Unexpected prompt: %r', query)

            if qt in (PAM_TEXT_INFO, PAM_ERROR_MSG):
                AUTH.info('PAM says: %r', query)
            # AUTH.error('# PAM(%d) %s: answer=%r, qt, repr(query).strip("':\" "), response)
            yield (response, 0)

    def _parse_error_message_from(self, pam_err: tuple[Any, int], prompts: Sequence[tuple[str, int]]) -> str:
        # okay, check prompts, maybe they have a hint why it failed?
        # most often the last prompt contains a error message
        # prompts are localised, i.e. if the operating system uses German, the prompts are German!
        # try to be exhaustive. otherwise the errors will not be presented to the user.
        if pam_err[1] in (PAM_AUTHTOK_RECOVER_ERR,):
            # error: ('Authentifizierungsinformationen k?nnen nicht wiederhergestellt werden', 21)
            # error: ('Fehler beim \xc3\x84ndern des Authentifizierungstoken', 20)
            return self.error_message(pam_err)
        messages = []
        for prompt, errno in prompts[::-1]:
            error_message = self._parse_password_change_fail_reason(prompt)
            if error_message:
                return error_message
            if errno in (PAM_TEXT_INFO, PAM_ERROR_MSG):
                messages.append('%s.' % (self._(prompt).strip(': .'),))
        messages.append('Errorcode %s: %s' % (pam_err[1], self.error_message(pam_err)))
        return '%s. %s: %s' % (
            self._('The reason could not be determined'),
            self._('In case it helps, the raw error message will be displayed'),
            ' '.join(messages),
        )

    def error_message(self, pam_err: tuple[Any, int]) -> str:
        errors = {
            PAM_NEW_AUTHTOK_REQD: self._('The password has expired and must be renewed.'),
            PAM_ACCT_EXPIRED: self._('The account is expired and can not be used anymore.'),
            PAM_USER_UNKNOWN: self._('The authentication has failed, please login again.'),
            PAM_AUTH_ERR: self._('The authentication has failed, please login again.'),
            PAM_AUTHTOK_ERR: self._('The new password could not be set.'),
            PAM_AUTHTOK_RECOVER_ERR: self._('The entered password does not match the current one.'),
        }
        return errors.get(pam_err[1], self._(str(pam_err[0])))

    def _parse_password_change_fail_reason(self, prompt: str | bytes) -> str:
        if prompt in self.known_errors:
            return self._(self.known_errors[prompt])
        for pattern, error_message in self.known_errors.items():
            if isinstance(prompt, bytes):
                prompt = prompt.decode('utf-8', 'ignore')

            if isinstance(pattern, str):
                pattern = re.compile(re.escape(pattern), re.I)

            match = pattern.search(prompt) or pattern.search(prompt.encode('UTF-8').decode('latin-1')) or pattern.search(prompt.encode('latin-1', 'ignore').decode('utf-8', 'ignore'))
            if match:
                groups = match.groupdict()
                additional_message = ''
                for x, y in groups.items():
                    try:
                        additional_message = {
                            'minlen': ' ' + self._('The password must consist of at least %s characters.'),
                            'history': ' ' + self._('Choose a password which does not match any of your last %s passwords.'),
                        }[x] % (y,)
                    except KeyError:
                        pass
                return self._(error_message) + additional_message
