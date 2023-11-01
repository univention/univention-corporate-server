# -*- coding: utf-8 -*-
#
# Univention Management Console
#  LDAP Connection Cache
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2015-2023 Univention GmbH
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

"""
Decorators for common ldap functionality.
Example usage::

    @machine_connection(write=True)
    def foobar(self, ldap_connection=None, ldap_position=None):
        return ldap_connection.search('uid=Administrator')

    def foobar():
        def bind(lo):
            lo.bind('Administrator', 'univention')
        lo, po = get_user_connection(bind=bind, write=True)
        return lo.search('uid=Administrator')

"""


import functools
from errno import ENOENT

import ldap

import univention.admin.uexceptions as udm_errors
from univention.admin.uldap import (
    access as _access, getAdminConnection as _getAdminConnection, getMachineConnection as _getMachineConnection,
    position as _position,
)
from univention.management.console.config import ucr
from univention.uldap import getBackupConnection as _getBackupConnection


__all__ = ('connection', 'get_connection', 'user_connection', 'get_user_connection', 'machine_connection', 'get_machine_connection', 'admin_connection', 'get_admin_connection')


class LDAP(object):

    _LDAP_CONNECTION = 'ldap_connection'
    _LDAP_POSITION = 'ldap_position'

    def __init__(self):
        self.__ldap_connections = {}

    def user_connection(self, func=None, bind=None, write=True, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, no_cache=False, **kwargs):
        host = ucr.get('ldap/master' if write else 'ldap/server/name')
        port = ucr.get_int('ldap/master/port' if write else 'ldap/server/port', 7389)
        base = ucr.get('ldap/base')
        return self.connection(func, bind, host, port, base, loarg, poarg, no_cache, **kwargs)

    def connection(self, func=None, bind=None, host=None, port=None, base=None, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, no_cache=False, **kwargs):
        hash_ = ('connection', no_cache, bind, host, port, base, tuple(kwargs.items()))

        def connection():
            lo = _access(host=host, port=port, base=base, **kwargs)
            if bind is not None:
                bind(lo)
            return lo, _position(lo.base)
        return self._wrapped(func, hash_, connection, loarg, poarg, no_cache)

    def machine_connection(self, func=None, write=True, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, no_cache=False, **kwargs):
        hash_ = ('machine', no_cache, bool(write), tuple(kwargs.items()))
        kwargs.update({'ldap_master': write})

        def connection():
            try:
                return _getMachineConnection(**kwargs)
            except OSError as exc:
                if exc.errno == ENOENT:
                    return  # /etc/machine.secret does not exists
                raise
        return self._wrapped(func, hash_, connection, loarg, poarg, no_cache)

    def admin_connection(self, func=None, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, no_cache=False, **kwargs):
        hash_ = ('admin', no_cache, tuple(kwargs.items()))

        def connection():
            try:
                return _getAdminConnection(**kwargs)
            except OSError as exc:
                if exc.errno == ENOENT:
                    return  # /etc/ldap.secret does not exists
                raise
        return self._wrapped(func, hash_, connection, loarg, poarg, no_cache)

    def backup_connection(self, func=None, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, no_cache=False, **kwargs):
        hash_ = ('backup', no_cache, tuple(kwargs.items()))

        def connection():
            lo = _getBackupConnection(**kwargs)
            return _access(lo=lo), _position(lo.base)
        return self._wrapped(func, hash_, connection, loarg, poarg, no_cache)

    def get_connection(self, *args, **kwargs):
        @self.connection(*args, **kwargs)
        def connection(ldap_connection=None, ldap_position=None):
            return ldap_connection, ldap_position
        return connection()

    def get_user_connection(self, *args, **kwargs):
        @self.user_connection(*args, **kwargs)
        def connection(ldap_connection=None, ldap_position=None):
            return ldap_connection, ldap_position
        return connection()

    def get_machine_connection(self, *args, **kwargs):
        @self.machine_connection(*args, **kwargs)
        def connection(ldap_connection=None, ldap_position=None):
            return ldap_connection, ldap_position
        return connection()

    def get_admin_connection(self, *args, **kwargs):
        @self.admin_connection(*args, **kwargs)
        def connection(ldap_connection=None, ldap_position=None):
            return ldap_connection, ldap_position
        return connection()

    def get_backup_connection(self, *args, **kwargs):
        @self.backup_connection(*args, **kwargs)
        def connection(ldap_connection=None, ldap_position=None):
            return ldap_connection, ldap_position
        return connection()

    def reset_cache(self, *connections):
        """
        Remove cached LDAP connections.

        :param connections: Either remove every connection or only the specified ones.
        """
        if not connections:
            self.__ldap_connections.clear()
        else:
            for key, conn in list(self.__ldap_connections.items()):
                if conn[0] in connections:
                    self.__ldap_connections.pop(key, None)

    def _wrapped(self, func, hash_, connection, loarg, poarg, no_cache=False):
        def setter(conn):
            if conn is None:
                self.__ldap_connections.pop(hash_, None)
            else:
                self.__ldap_connections[hash_] = conn

        def getter():
            try:
                try:
                    lo, po = self.__ldap_connections[hash_]
                except KeyError:
                    # security! it must not be possible to get a traceback with the hash
                    # e.g. when the new connection could not be established.
                    # Since Python 3 tracebacks contain the whole exception chain
                    lo, po = None, None
                if lo is None:
                    raise KeyError()
            except KeyError:
                conn = connection()
                try:
                    lo, po = conn
                except (TypeError, ValueError):
                    lo, po = None, None
            return lo, po

        def _decorator(func):
            @functools.wraps(func)
            def _decorated(*args, **kwargs):
                kwargs[loarg], kwargs[poarg] = lo, po = getter()

                try:
                    result = func(*args, **kwargs)
                    if not no_cache:
                        setter((lo, po))
                    return result
                except (ldap.LDAPError, udm_errors.ldapError):
                    setter(None)
                    raise
            return _decorated
        if func is None:
            return _decorator
        return _decorator(func)


_LDAP = LDAP()
machine_connection = _LDAP.machine_connection
get_machine_connection = _LDAP.get_machine_connection
admin_connection = _LDAP.admin_connection
get_admin_connection = _LDAP.get_admin_connection
backup_connection = _LDAP.backup_connection
get_backup_connection = _LDAP.get_backup_connection
user_connection = _LDAP.user_connection
get_user_connection = _LDAP.get_user_connection
connection = _LDAP.connection
get_connection = _LDAP.get_connection
reset_cache = _LDAP.reset_cache
del _LDAP
