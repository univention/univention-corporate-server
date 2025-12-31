# SPDX-FileCopyrightText: 2018-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, TypeVar

import ldap
from ldap.filter import filter_format

import univention.admin.uexceptions
import univention.admin.uldap
import univention.config_registry

from .exceptions import ConnectionError  # noqa: A004


if TYPE_CHECKING:
    from collections.abc import Callable


_T = TypeVar("_T")  # noqa: PYI018


class LDAP_connection:
    """Caching LDAP connection factory."""

    _ucr: univention.config_registry.ConfigRegistry = None
    _connection_admin: univention.admin.uldap.access | None = None
    _connection_account: dict[tuple[str, str, str | None, int | None, str | None], univention.admin.uldap.access] = {}

    @classmethod
    def _clear(cls) -> None:
        # used in tests
        cls._ucr = None
        cls._connection_admin = None
        cls._connection_account.clear()

    @classmethod
    def _wrap_connection(cls, func: Callable[..., _T], **kwargs: Any) -> _T:
        try:
            return func(**kwargs)
        except OSError:
            raise ConnectionError('Could not read secret file').with_traceback(sys.exc_info()[2])
        except univention.admin.uexceptions.authFail:
            raise ConnectionError('Credentials invalid').with_traceback(sys.exc_info()[2])
        except ldap.INVALID_CREDENTIALS:
            raise ConnectionError('Credentials invalid').with_traceback(sys.exc_info()[2])
        except ldap.CONNECT_ERROR:
            raise ConnectionError('Connection refused').with_traceback(sys.exc_info()[2])
        except ldap.SERVER_DOWN:
            raise ConnectionError('The LDAP Server is not running').with_traceback(sys.exc_info()[2])

    @classmethod
    def get_admin_connection(cls) -> univention.admin.uldap.access:
        if not cls._connection_admin:
            cls._connection_admin, _po = cls._wrap_connection(univention.admin.uldap.getAdminConnection)
        return cls._connection_admin

    @classmethod
    def get_machine_connection(cls, ldap_master: bool = True) -> univention.admin.uldap.access:
        # do not cache the machine connection as this breaks on server-password-change
        co, _po = cls._wrap_connection(univention.admin.uldap.getMachineConnection, ldap_master=ldap_master)
        return co

    @classmethod
    def get_credentials_connection(
            cls,
            identity: str,
            password: str,
            base: str | None = None,
            server: str | None = None,
            port: int | None = None,
    ) -> univention.admin.uldap.access:
        if not cls._ucr:
            cls._ucr = univention.config_registry.ConfigRegistry()
            cls._ucr.load()

        if '=' not in identity:
            lo = cls.get_machine_connection()
            dns = lo.searchDn(filter_format('uid=%s', (identity,)))
            try:
                identity = dns[0]
            except IndexError:
                raise ConnectionError('Cannot get DN for username').with_traceback(sys.exc_info()[2])

        access_kwargs = {'binddn': identity, 'bindpw': password, 'base': base or cls._ucr['ldap/base']}
        if server:
            access_kwargs['host'] = server
        if port:
            access_kwargs['port'] = port
        key = (identity, password, server, port, base)
        if key not in cls._connection_account:
            cls._connection_account[key] = cls._wrap_connection(univention.admin.uldap.access, **access_kwargs)
        return cls._connection_account[key]
