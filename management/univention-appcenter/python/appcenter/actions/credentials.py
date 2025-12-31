#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for actions needing credentials
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import time
from argparse import SUPPRESS
from contextlib import contextmanager
from copy import deepcopy
from getpass import getpass, getuser
from tempfile import NamedTemporaryFile

import ldap

from univention.appcenter.actions import UniventionAppAction
from univention.appcenter.exceptions import (
    ConnectionFailed, ConnectionFailedConnectError, ConnectionFailedInvalidAdminCredentials,
    ConnectionFailedInvalidMachineCredentials, ConnectionFailedInvalidUserCredentials, ConnectionFailedSecretFile,
    ConnectionFailedServerDown, CredentialsNoPasswordError, CredentialsNoUsernameError,
)
from univention.appcenter.ucr import ucr_get
from univention.appcenter.udm import get_admin_connection, get_connection, get_machine_connection, search_objects


class CredentialsAction(UniventionAppAction):

    def __init__(self):
        super().__init__()
        self._username = None
        self._userdn = None
        self._password = None

    def setup_parser(self, parser):
        parser.add_argument('--noninteractive', action='store_true', help='Do not prompt for anything, just agree or skip')
        parser.add_argument('--username', default='Administrator', help='The username used for registering the app. Default: %(default)s')
        parser.add_argument('--pwdfile', help='Filename containing the password for registering the app. See --username')
        parser.add_argument('--password', help=SUPPRESS)

    def check_user_credentials(self, args):
        try:
            _lo, _pos = self._get_ldap_connection(args, allow_machine_connection=False, allow_admin_connection=False)
        except ConnectionFailed:
            return False
        else:
            return True

    def _get_username(self, args):
        if self._username is not None:
            return self._username
        if args.username:
            return args.username
        if not args.noninteractive:
            try:
                username = input('Username [Administrator]: ') or 'Administrator'
            except (EOFError, KeyboardInterrupt):
                raise CredentialsNoUsernameError()
            self._username = username
            return username

    def _get_password(self, args, ask=True):
        username = self._get_username(args)
        if not username:
            return None
        if self._password is not None:
            return self._password
        if args.password:
            return args.password
        if args.pwdfile:
            password = open(args.pwdfile).read().rstrip('\n')
            return password
        if ask and not args.noninteractive:
            self._password = self._get_password_for(username)
        return self._password

    def _get_password_for(self, username):
        try:
            return getpass('Password for %s: ' % username)
        except (EOFError, KeyboardInterrupt):
            raise CredentialsNoPasswordError()

    @contextmanager
    def _get_password_file(self, args=None, password=None):
        if password is None:
            password = self._get_password(args)
        if not password:
            yield None
        else:
            with NamedTemporaryFile('w') as password_file:
                password_file.write(password)
                password_file.flush()
                yield password_file.name

    def _get_userdn(self, args):
        username = self._get_username(args)
        if not username:
            return None
        lo, pos = self._get_ldap_connection(args=None, allow_machine_connection=True)
        users = search_objects('users/user', lo, pos, uid=username)
        if users:
            return users[0].dn
        else:
            self.fatal('Cannot find user %s' % username)

    def _get_machine_connection(self):
        try:
            return get_machine_connection()
        except OSError:
            raise ConnectionFailedSecretFile()
        except ldap.INVALID_CREDENTIALS:
            raise ConnectionFailedInvalidMachineCredentials()
        except ldap.CONNECT_ERROR as exc:
            raise ConnectionFailedConnectError(exc)
        except ldap.SERVER_DOWN:
            raise ConnectionFailedServerDown()

    def _get_admin_connection(self):
        try:
            return get_admin_connection()
        except OSError:
            raise ConnectionFailedSecretFile()
        except ldap.INVALID_CREDENTIALS:
            raise ConnectionFailedInvalidAdminCredentials()
        except ldap.CONNECT_ERROR as exc:
            raise ConnectionFailedConnectError(exc)
        except ldap.SERVER_DOWN:
            raise ConnectionFailedServerDown()

    def _get_ldap_connection(self, args, allow_machine_connection=False, allow_admin_connection=True):
        if allow_admin_connection and ucr_get('server/role') == 'domaincontroller_master' and getuser() == 'root':
            try:
                return self._get_admin_connection()
            except ConnectionFailed:
                if allow_machine_connection or args is not None:
                    # try to get another connection
                    pass
                else:
                    raise
        if allow_machine_connection:
            try:
                return self._get_machine_connection()
            except ConnectionFailed:
                if args is not None:
                    # try to get another connection
                    pass
                else:
                    raise
        attempts = 0
        if args is not None:
            args = deepcopy(args)
            while attempts < 3:
                attempts += 1
                userdn = self._get_userdn(args)
                password = self._get_password(args)
                try:
                    if not userdn or not password:
                        raise ldap.INVALID_CREDENTIALS()
                    return get_connection(userdn, password)
                except ldap.CONNECT_ERROR as exc:
                    raise ConnectionFailedConnectError(exc)
                except ldap.SERVER_DOWN:
                    raise ConnectionFailedServerDown()
                except ldap.INVALID_CREDENTIALS:
                    time.sleep(0.1)
                    self.warn('Invalid credentials')
                    args.username = None
                    self._username = None
                    args.pwdfile = None
                    self._password = None
            raise ConnectionFailedInvalidUserCredentials()
        raise ConnectionFailed()
