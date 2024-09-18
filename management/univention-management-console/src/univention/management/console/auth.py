#!/usr/bin/python3
#
# Univention Management Console
#  authentication mechanisms
#
# SPDX-FileCopyrightText: 2014-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

import ldap
from ldap.filter import filter_format

import univention.admin.uexceptions as udm_errors
import univention.admin.handlers.users.user as udm_user
from univention.management.console.ldap import get_machine_connection, reset_cache
from univention.management.console.log import AUTH
from univention.management.console.pam import (
    AccountExpired, AuthenticationError, AuthenticationFailed, AuthenticationInformationMissing, PamAuth,
    PasswordChangeFailed, PasswordExpired,
)
from univention.management.console.config import ucr


class AuthenticationResult:

    def __init__(self, result: BaseException | dict[str, str], locale: str | None) -> None:
        self.credentials = None
        self.status = 200
        self.authenticated = not isinstance(result, BaseException)
        if self.authenticated:
            self.credentials = result
        self.message = None
        self.result: dict[str, Any] | None = None
        self.password_expired = False
        if isinstance(result, AuthenticationError):
            self.status = 401
            self.message = str(result)
            self.result = {}
            if isinstance(result, PasswordExpired):
                self.result['password_expired'] = True
            elif isinstance(result, AccountExpired):
                self.result['account_expired'] = True
            elif isinstance(result, AuthenticationInformationMissing):
                self.result['missing_prompts'] = result.missing_prompts
            elif isinstance(result, PasswordChangeFailed):
                self.result['password_change_failed'] = True
        elif isinstance(result, BaseException):
            self.status = 500
            self.message = str(result)
        else:
            self.result = {'username': result['username']}

    def __bool__(self) -> bool:
        return self.authenticated

    __nonzero__ = __bool__  # Python 2


class AuthHandler:

    def get_handler(self, locale):
        # PAM MUST be initialized outside of a thread. Otherwise it segfaults e.g. with pam_saml.so.
        # See http://pam-python.sourceforge.net/doc/html/#bugs
        return PamAuth(locale)

    def authenticate(self, pam, args):
        args.pop('pam', None)
        locale = args.pop('locale')
        args.setdefault('new_password', None)
        args.setdefault('username', '')
        args.setdefault('password', '')

        try:
            result = self.__authenticate_thread(pam, **args)
        except (AuthenticationFailed, AuthenticationInformationMissing, PasswordExpired, PasswordChangeFailed, AccountExpired) as exc:
            result = exc
        except BaseException as exc:
            result = exc
            AUTH.exception("Unexpected authentication error")

        if isinstance(result, tuple):
            username, password = result
            result = {'username': username, 'password': password, 'auth_type': args.get('auth_type')}
        return AuthenticationResult(result, locale)

    def __authenticate_thread(self, pam, username, password, new_password, auth_type=None, **custom_prompts):
        AUTH.info('Trying to authenticate user %r (auth_type: %r)', username, auth_type)
        username = self.__canonicalize_username(username)

        try:
            if new_password:
                self.__authenticate_ldap(username, password)
            else:
                pam.authenticate(username, password, **custom_prompts)
        except AuthenticationFailed as auth_failed:
            AUTH.error('%s', auth_failed)
            raise
        except PasswordExpired as pass_expired:
            AUTH.info(str(pass_expired))
            if new_password is None:
                raise

            try:
                # Change password using UDM
                self.__change_password_udm(username, new_password)
            except PasswordChangeFailed as change_failed:
                AUTH.error('%s', change_failed)
                raise
            else:
                AUTH.info('Password change for %r was successful', username)
                return (username, new_password)
        else:
            AUTH.info('Authentication for %r was successful', username)
            return (username, password)

    def __authenticate_ldap(self, username, password):
        machine_lo = get_machine_connection(write=False)[0]
        user_dn = machine_lo.searchDn(filter_format('(&(uid=%s)(objectClass=person))', (username,)))[0]
        AUTH.info("User dn: %s" % (user_dn,))
        AUTH.info("Authenticating user: %s" % (username,))
        try:
            machine_lo.lo.bind(user_dn, password)
            # expect ldap.INVALID_CREDENTIALS: {'msgtype': 97, 'msgid': 2, 'result': 49, 'desc': 'Invalid credentials', 'ctrls': [], 'info': 'password expired'}, but that's ok
        except (ldap.LDAPError, udm_errors.base) as exc:
            if isinstance(exc, ldap.INVALID_CREDENTIALS):
                if exc.args[0].get('info') == 'password expired':
                    raise PasswordExpired('Password expired')
            raise AuthenticationFailed('Failed to open LDAP connection for user %s: %s' % (username, exc))

    def __change_password_udm(self, username, new_password):
        AUTH.info("Setting new password for user: %s" % (username,))
        lo = get_machine_connection(write=True)[0]
        if lo:
            user_dn = lo.searchDn(filter_format('(&(uid=%s)(objectClass=person))', (username,)))[0]
            AUTH.info("User dn: %s" % (user_dn,))
            user = udm_user.object(None, lo, None, user_dn)
            user.open()
            user["password"] = new_password
            user["pwdChangeNextLogin"] = 0
            try:
                user.modify()
            except (udm_errors.pwToShort, udm_errors.pwQuality) as exc:
                language = ucr.get('locale/default', 'en').split('_', 1)[0]
                password_complexity_message = ucr.get('umc/login/password-complexity-message/%s' % (language,), ucr.get('umc/login/password-complexity-message/en', str(exc)))
                raise PasswordChangeFailed(password_complexity_message)
            except udm_errors.pwalreadyused as exc:
                raise PasswordChangeFailed(exc.message)
            except Exception as exc:
                AUTH.error(f"__change_password_udm(): failed to set password: {traceback.format_exc()}")
                raise PasswordChangeFailed(str(exc))
            else:
                AUTH.info("User modify succeeded!")
        else:
            raise PasswordChangeFailed("LDAP connection failed")

    def __canonicalize_username(self, username: str) -> str:
        try:
            lo, _po = get_machine_connection(write=False)
            result = None
            if lo:
                attr = 'mailPrimaryAddress' if '@' in username else 'uid'
                result = lo.search(filter_format('(&(%s=%s)(objectClass=person))', (attr, username)), attr=['uid'], unique=True)
            if result and result[0][1].get('uid'):
                username = result[0][1]['uid'][0].decode('utf-8')
                AUTH.info('Canonicalized username: %r', username)
        except (ldap.LDAPError, udm_errors.ldapError) as exc:
            # /etc/machine.secret missing or LDAP server not reachable
            AUTH.warning('Canonicalization of username was not possible: %s', exc)
            reset_cache()
        except Exception:
            AUTH.exception('Canonicalization of username failed')
        return username
