# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""
Library for AD/Samba connections.

Includes objects and functionality for:
* Users
* Shares
* Domain password settings

The library uses the CLI tools samba-tool and smbclient as backend.
"""

import re
import subprocess
from logging import getLogger
from pprint import pformat

from pydantic import BaseModel, Field

from univention.logging import Structured


log = Structured(getLogger().getChild(__name__))


class ActiveDirectoryException(Exception):
    def __str__(self):
        if self.args and len(self.args) == 1 and isinstance(self.args[0], dict):
            return '\n'.join('%s=%s' % (key, value) for key, value in self.args[0].items())
        else:
            return super().__str__(self)

    __repr__ = __str__


class SambaToolException(ActiveDirectoryException):
    pass


class SmbClientException(ActiveDirectoryException):
    pass


class LogonFailureException(ActiveDirectoryException):
    pass


class AccountLockedOutException(ActiveDirectoryException):
    pass


class NotLockedOutException(ActiveDirectoryException):
    pass


class ActiveDirectorySettings(BaseModel):
    host: str | None = Field(
        default=None,
        description='Host of the Samba/AD server e.g. my-samba-server.org',
    )
    admin_username: str | None = Field(
        default=None,
        description='The username of the Samba/AD admin account.',
    )
    admin_password: str | None = Field(
        default=None,
        description='The passwort from the admin user.',
    )
    is_local_connect: bool = Field(
        default=False,
        description='Flag to connect to local Samba without host and admin credentials.',
    )


class DomainPasswordsettingsData(BaseModel):
    password_complexity: str | None = Field(
        default=None,
        description='The password complexity (on | off)',
    )
    store_plaintext_passwords: str | None = Field(
        default=None,
        description="Store plaintext passwords where account have 'store passwords with reversible encryption' set (on | off)",
    )
    password_history_length: int | None = Field(
        default=None,
        description='The password history length.',
    )
    minimum_password_length: int | None = Field(
        default=None,
        description='The minimum password length.',
    )
    minimum_password_age: int | None = Field(
        default=None,
        description='The minimum password age.',
    )
    maximum_password_age: int | None = Field(
        default=None,
        description='The maximum password age.',
    )
    account_lockout_duration: int | None = Field(
        default=None,
        description=(
            'The length of time an account is locked out after exceeding the limit on bad password attempts in mins.'
        ),
    )
    account_lockout_threshold: int | None = Field(
        default=None,
        description=(
            'The number of bad password attempts allowed before locking out the account. 0 is never lock out.'
        ),
    )
    reset_account_lockout_after: int | None = Field(
        default=None,
        description='After this time is elapsed, the recorded number of attempts restarts from zero.',
    )


class SharesData(BaseModel):
    share_name: str | None = None
    type: str | None = None
    comment: str | None = None


class UserData(BaseModel):
    dn: str | None = None
    name: str | None = None
    password: str | None = None
    bad_pwd_count: int | None = Field(
        default=None,
        description=(
            'The number of times the user tried to log on to the account using an incorrect password. '
            'A value of 0 indicates that the value is unknown.',
        ),
    )
    bad_password_time: int | None = Field(
        default=None,
        description=(
            'The last time and date that an attempt to log on to this account was made with a password that '
            'is not valid. This value is stored as a large integer that represents the number of 100-nanosecond '
            'intervals since January 1, 1601 (UTC). A value of zero means that the last time an incorrect '
            'password was used is unknown.'
        ),
    )
    lockout_time: int | None = Field(
        default=None,
        description=(
            'The date and time (UTC) that this account was locked out. This value is stored as a large integer '
            'that represents the number of 100-nanosecond intervals since January 1, 1601 (UTC). A value of '
            'zero means that the account is not currently locked out.'
        ),
    )


class ActiveDirectory:
    def __init__(self, settings: ActiveDirectorySettings):
        self.settings = settings

    def parse_text(
        self,
        pattern: str,
        text: str,
        result_type: type[int | str],
        default: int | str | None = None,
    ) -> int | str | None:
        if re_match := re.search(pattern, text):
            if result_type is int:
                # Zero is here a valid digit and we have to check if it is None!
                return default if int(re_match.group(1)) is None else int(re_match.group(1))
            elif result_type is str:
                return str(re_match.group(1)) or default


class SambaTool(ActiveDirectory):
    def execute(self, arguments: list[str]) -> str:
        cmd = ['/usr/bin/samba-tool']
        cmd.extend(arguments)
        if not self.settings.is_local_connect:
            cmd.extend(
                [
                    f'--URL=ldap://{self.settings.host}',
                    f'--username={self.settings.admin_username}',
                    f'--password={self.settings.admin_password}',
                ],
            )
        log.debug('Execute: %s', (' '.join(cmd)))

        child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = child.communicate()
        stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

        if child.returncode:
            raise SambaToolException(
                {
                    'returncode': child.returncode,
                    'stdout': stdout,
                    'stderr': stderr,
                },
            )

        log.debug('Result: %s', stdout)

        return stdout


class SmbClient(ActiveDirectory):
    def execute(self, arguments: list[str]) -> str:
        cmd = ['/usr/bin/smbclient']
        cmd.extend(arguments)
        log.debug('Execute: %s', (' '.join(cmd)))

        child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = child.communicate()
        stdout, stderr = stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')

        if child.returncode:
            if (
                self.parse_text(
                    pattern=r'^session setup failed: (NT_STATUS_LOGON_FAILURE)$',
                    text=stdout,
                    result_type=str,
                )
                == 'NT_STATUS_LOGON_FAILURE'
            ):
                raise LogonFailureException
            elif (
                self.parse_text(
                    pattern=r'^session setup failed: (NT_STATUS_ACCOUNT_LOCKED_OUT)$',
                    text=stdout,
                    result_type=str,
                )
                == 'NT_STATUS_ACCOUNT_LOCKED_OUT'
            ):
                raise AccountLockedOutException
            else:
                raise SmbClientException(
                    {
                        'returncode': child.returncode,
                        'stdout': stdout,
                        'stderr': stderr,
                    },
                )

        log.debug('Result: %s', stdout)

        return stdout


class DomainPasswordSettings(SambaTool):
    def get(self) -> DomainPasswordsettingsData:
        res = self.execute(['domain', 'passwordsettings', 'show'])

        password_complexity = self.parse_text(
            pattern=r'Password complexity: (on|off)',
            text=res,
            result_type=str,
        )
        store_plaintext_passwords = self.parse_text(
            pattern=r'Store plaintext passwords: (on|off)',
            text=res,
            result_type=str,
        )
        password_history_length = self.parse_text(
            pattern=r'Password history length: ([0-9]+)',
            text=res,
            result_type=int,
        )
        minimum_password_length = self.parse_text(
            pattern=r'Minimum password length: ([0-9]+)',
            text=res,
            result_type=int,
        )
        minimum_password_age = self.parse_text(
            pattern=r'Minimum password age \(days\): ([0-9]+)',
            text=res,
            result_type=int,
        )
        maximum_password_age = self.parse_text(
            pattern=r'Maximum password age \(days\): ([0-9]+)',
            text=res,
            result_type=int,
        )
        account_lockout_duration = self.parse_text(
            pattern=r'Account lockout duration \(mins\): ([0-9]+)',
            text=res,
            result_type=int,
        )
        account_lockout_threshold = self.parse_text(
            pattern=r'Account lockout threshold \(attempts\): ([0-9]+)',
            text=res,
            result_type=int,
        )
        reset_account_lockout_after = self.parse_text(
            pattern=r'Reset account lockout after \(mins\): ([0-9]+)',
            text=res,
            result_type=int,
        )

        domain_passwordsettings = DomainPasswordsettingsData(
            password_complexity=password_complexity,
            store_plaintext_passwords=store_plaintext_passwords,
            password_history_length=password_history_length,
            minimum_password_length=minimum_password_length,
            minimum_password_age=minimum_password_age,
            maximum_password_age=maximum_password_age,
            account_lockout_duration=account_lockout_duration,
            account_lockout_threshold=account_lockout_threshold,
            reset_account_lockout_after=reset_account_lockout_after,
        )
        log.debug('domain_passwordsettings:\n%s\n', pformat(vars(domain_passwordsettings)))

        return domain_passwordsettings

    def set(self, domain_passwordsettings: DomainPasswordsettingsData):
        cmd_attributes = [
            'domain',
            'passwordsettings',
            'set',
        ]
        if domain_passwordsettings.password_complexity:
            cmd_attributes.append(f'--complexity={domain_passwordsettings.password_complexity}')
        if domain_passwordsettings.store_plaintext_passwords:
            cmd_attributes.append(f'--store-plaintext={domain_passwordsettings.store_plaintext_passwords}')
        if domain_passwordsettings.password_history_length:
            cmd_attributes.append(f'--history-length={domain_passwordsettings.password_history_length}')
        if domain_passwordsettings.minimum_password_length:
            cmd_attributes.append(f'--min-pwd-length={domain_passwordsettings.minimum_password_length}')
        if domain_passwordsettings.minimum_password_age:
            cmd_attributes.append(f'--min-pwd-age={domain_passwordsettings.minimum_password_age}')
        if domain_passwordsettings.maximum_password_age:
            cmd_attributes.append(f'--max-pwd-age={domain_passwordsettings.maximum_password_age}')
        if domain_passwordsettings.account_lockout_duration:
            cmd_attributes.append(f'--account-lockout-duration={domain_passwordsettings.account_lockout_duration}')
        if domain_passwordsettings.account_lockout_threshold:
            cmd_attributes.append(f'--account-lockout-threshold={domain_passwordsettings.account_lockout_threshold}')
        if domain_passwordsettings.reset_account_lockout_after:
            cmd_attributes.append(
                f'--reset-account-lockout-after={domain_passwordsettings.reset_account_lockout_after}',
            )

        self.execute(cmd_attributes)


class User(SambaTool):
    def create(self, username: str, password: str, use_username_as_cn: bool = True) -> UserData:
        cmd_attributes = [
            'user',
            'create',
            username,
            password,
        ]
        if use_username_as_cn:
            cmd_attributes.append('--use-username-as-cn')

        self.execute(cmd_attributes)

        user = self.get(username=username)
        user.password = password

        return user

    def delete(self, username: str):
        self.execute(['user', 'delete', username])

    def unlock(self, username: str):
        self.execute(['user', 'unlock', username])

    def get(self, username: str) -> UserData:
        res = self.execute(['user', 'show', username])

        dn = self.parse_text(
            pattern=r'dn: (.*)\n',
            text=res,
            result_type=str,
        )
        name = self.parse_text(
            pattern=r'name: (.*)\n',
            text=res,
            result_type=str,
        )
        bad_pwd_count = self.parse_text(
            pattern=r'badPwdCount: ([0-9]+)',
            text=res,
            result_type=int,
        )
        bad_password_time = self.parse_text(
            pattern=r'badPasswordTime: ([0-9]+)',
            text=res,
            result_type=int,
        )
        lockout_time = self.parse_text(
            pattern=r'lockoutTime: ([0-9]+)',
            text=res,
            result_type=int,
        )

        return UserData(
            dn=dn,
            name=name,
            bad_pwd_count=bad_pwd_count,
            bad_password_time=bad_password_time,
            lockout_time=lockout_time,
        )

    def set_password(self, username: str, password: str):
        self.execute(['user', 'setpassword', f'--new-password={password}', username])


class Shares(SmbClient):
    def list(self, username: str, password) -> list[SharesData]:
        cmd_attributes = [
            f'--list={"localhost" if self.settings.is_local_connect else self.settings.host}',
            f'--user={username}',
            f'--password={password}',
        ]
        res = self.execute(cmd_attributes)

        shares = []
        pattern = r'^[ \t]+(.*?)[ \t]+(.*?)[ \t]+(.*?)$'
        if match := re.findall(pattern=pattern, string=res, flags=re.MULTILINE):
            if len(match) > 2:
                for i in range(2, len(match)):
                    shares.append(
                        SharesData(
                            share_name=match[i][0],
                            type=match[i][1],
                            comment=match[i][2],
                        ),
                    )

        return shares
