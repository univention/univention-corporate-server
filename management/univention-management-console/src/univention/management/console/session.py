#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  session handling
#
# Copyright 2022-2024 Univention GmbH
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

import asyncio
import errno
import functools
import traceback

import ldap
import tornado.gen
from ldap.filter import filter_format

import univention.admin.uexceptions as udm_errors

from .acl import ACLs, LDAP_ACLs
from .auth import AuthHandler
from .category import Manager as CategoryManager
from .config import MODULE_DEBUG_LEVEL, ucr
from .error import ServiceUnavailable
from .ldap import get_machine_connection, reset_cache as reset_ldap_connection_cache
from .log import CORE
from .message import Request
from .module import Manager as ModuleManager


try:
    from time import monotonic
except ImportError:
    from monotonic import monotonic

moduleManager = ModuleManager()
categoryManager = CategoryManager()
_session_timeout = ucr.get_int('umc/http/session/timeout', 300)


class User(object):
    """Information about the authenticated user"""

    __slots__ = ('ip', 'authenticated', 'username', 'password', 'user_dn', 'auth_type', 'session_end_time', '_locale')

    def __init__(self):
        self.ip = None
        self.authenticated = False
        self.username = None
        self.username = None
        self.password = None
        self.auth_type = None
        self.user_dn = None
        self.session_end_time = None
        self._locale = None  # don't use!

    def __repr__(self):
        return '<User(authenticated=%r name=%r ip=%r dn=%r auth_type=%r session_end_time=%r password="keep dreaming :-P")>' % (self.authenticated, self.username, self.ip, self.user_dn, self.auth_type, self.session_end_time)


class Session(object):
    """A interface to session data"""

    __slots__ = ('session_id', 'acls', 'user', 'saml', 'oidc', 'processes', '_timeout_id', '_active_requests', '_')
    __auth = AuthHandler()
    sessions = {}

    @classmethod
    def get_or_create(cls, session_id):
        session = cls.sessions.get(session_id)
        if not session:
            session = cls(session_id)
        return session

    @classmethod
    def put(cls, session_id, session):
        session.session_id = session_id
        session.reset_timeout()
        cls.sessions[session_id] = session

    @classmethod
    def expire(cls, session_id):
        """Removes a session when the connection to the UMC server has died or the session is expired"""
        try:
            del cls.sessions[session_id]
            CORE.info('Cleaning up session %r' % (session_id,))
        except KeyError:
            CORE.info('Session %r not found' % (session_id,))

    def __init__(self, session_id):
        self.session_id = session_id
        self.user = User()
        self.saml = None
        self.oidc = None
        self.acls = IACLs(self)
        self.processes = Processes(self)
        self._timeout_id = None
        self._active_requests = set()
        self._ = None

    def renew(self):
        CORE.info('Renewing session')
        self.acls = IACLs(self)
        self.processes = Processes(self)

    async def authenticate(self, args):
        from .server import pool
        pam = self.__auth.get_handler(args['locale'])
        future = pool.submit(self.__auth.authenticate, pam, args)
        result = await asyncio.wrap_future(future)
        pam.end()

        if (
            self.user.authenticated
            and self.user.username
            and result.credentials
            and result.credentials.get('username')
            and self.user.username.casefold() != result.credentials['username'].casefold()
        ):
            # re-authentication with a different username
            self.renew()

        authenticated = bool(result)
        if authenticated:
            self.set_credentials(**result.credentials)
        else:
            self.user = User()
            self.renew()
        return result

    async def change_password(self, args):
        from .server import pool
        pam = self.__auth.get_handler(args['locale'])
        username = args['username']
        password = args['password']
        new_password = args['new_password']
        future = pool.submit(pam.change_password, username, password, new_password)
        await asyncio.wrap_future(future)
        pam.end()
        self.set_credentials(username, new_password, None)

    def set_credentials(self, username, password, auth_type):
        self.user.authenticated = True
        self.user.username = username
        self.user.auth_type = auth_type
        if self.user.auth_type is None:
            # important! there might be a password already. in case of SAML we must not set/overwrite the password.
            self.user.password = password
        self._search_user_dn()

        # TODO: send reload signal to all other processes?
        CORE.info('Reloading resources: UCR, modules, categories')
        ucr.load()
        moduleManager.load()
        categoryManager.load()

        self.acls._reload_acls_and_permitted_commands()

    def _search_user_dn(self):
        lo = get_machine_connection(write=False)[0]
        if lo and self.user.username:
            # get the LDAP DN of the authorized user
            try:
                ldap_dn = lo.searchDn(filter_format('(&(uid=%s)(objectClass=person))', (self.user.username,)))
            except (ldap.LDAPError, udm_errors.base):
                reset_ldap_connection_cache(lo)
                ldap_dn = None
                CORE.error('Could not get uid for %r: %s' % (self.user.username, traceback.format_exc()))
            if ldap_dn:
                self.user.user_dn = ldap_dn[0]
                CORE.info('The LDAP DN for user %s is %s' % (self.user.username, self.user.user_dn))

        if not self.user.user_dn and self.user.username not in ('root', '__systemsetup__', None):
            CORE.error('The LDAP DN for user %s could not be found (lo=%r)' % (self.user.username, lo))

    def get_user_ldap_connection(self, **kwargs):
        base = Request('')
        base.auth_type = self.get_umc_auth_type()
        base.username = self.user.username
        base.user_dn = self.user.user_dn
        base.password = self.get_umc_password()
        return base.get_user_ldap_connection(**kwargs)

    def is_saml_user(self):
        # self.saml indicates that it was originally a
        # SAML user. but it may have upgraded and got a
        # real password. the saml user object is still there,
        # though
        return self.user.password is None and self.saml

    def is_oidc_user(self):
        # self.oidc indicates that it was originally a
        # oidc user. but it may have upgraded and got a
        # real password. the oidc user object is still there,
        # though
        return self.user.password is None and self.oidc

    def get_umc_password(self):
        if self.is_oidc_user():
            return self.oidc.access_token
        if self.is_saml_user():
            return self.saml.message
        else:
            return self.user.password

    def get_umc_auth_type(self):
        if self.is_oidc_user():
            return "OIDC"
        elif self.is_saml_user():
            return "SAML"
        else:
            return None

    def logout(self):
        CORE.info('User %r logged out' % (self.user.username,))
        self.on_logout()
        self.expire(self.session_id)

    def _session_timeout_timer(self):
        if self._active_requests:
            CORE.info('There are still open requests. Deferring session timeout.')
            self.user.session_end_time = monotonic() + 1
            ioloop = tornado.ioloop.IOLoop.current()
            self._timeout_id = ioloop.call_later(1, self._session_timeout_timer)
            return

        CORE.info('session %r timed out' % (self.session_id,))
        self.expire(self.session_id)
        self.on_logout()
        return False

    def reset_timeout(self):
        self.disconnect_timer()
        self.user.session_end_time = monotonic() + _session_timeout
        ioloop = tornado.ioloop.IOLoop.current()
        when = int(self.session_end_time - monotonic())
        CORE.debug('reset_timeout(): new session expiration in %s seconds' % (when,))
        self._timeout_id = ioloop.call_later(when, self._session_timeout_timer)

    def disconnect_timer(self):
        if self._timeout_id is not None:
            ioloop = tornado.ioloop.IOLoop.current()
            ioloop.remove_timeout(self._timeout_id)

    def timed_out(self, now=None, session_end_time=None):
        now = now if now else monotonic()
        session_end_time = session_end_time if session_end_time else self.session_end_time
        return session_end_time < now

    @property
    def session_end_time(self):
        if self.is_oidc_user() and self.oidc.session_end_time:
            return self.oidc.session_end_time
        if self.is_saml_user() and self.saml.session_end_time:
            return self.saml.session_end_time
        return self.user.session_end_time

    def on_logout(self):
        self.disconnect_timer()
        if self.saml:
            self.saml.on_logout()

    def __repr__(self):
        return '<Session id=%r %s processes=%r>' % (self.session_id, self.user, self.processes)


class IACLs(object):
    """Interface for UMC-ACL information"""

    @property
    def acls(self):
        if self.__acls is None:
            self._reload_acls_and_permitted_commands()
        return self.__acls

    def __init__(self, session):
        self.session = session
        self.__acls = None
        self.__permitted_commands = None

    def _reload_acls_and_permitted_commands(self):
        self.__acls = self._get_acls()
        if isinstance(self.acls, LDAP_ACLs):
            lo, po = get_machine_connection(write=False)
            try:
                self.acls.reload(lo)
            except (ldap.LDAPError, udm_errors.ldapError):
                reset_ldap_connection_cache(lo)
                raise
        else:
            self.acls.reload()
        self.__permitted_commands = None
        self.get_permitted_commands(moduleManager)

    def _get_acls(self):
        if not self.session.user.authenticated:
            # We need to set empty ACL's for unauthenticated requests
            return ACLs()
        else:
            return LDAP_ACLs(self.session.user.username, ucr['ldap/base'])

    def is_command_allowed(self, command, options, flavor):
        if not isinstance(options, dict):
            options = {}
        return moduleManager.is_command_allowed(self.acls, command, None, options, flavor)

    def get_permitted_commands(self, moduleManager):
        if self.__permitted_commands is None:
            # fixes performance leak?
            self.__permitted_commands = moduleManager.permitted_commands(ucr['hostname'], self.acls)
        return self.__permitted_commands

    def is_module_singleton(self, module_name):
        return moduleManager.is_singleton(module_name)

    def get_module_proxy_address(self, module_name):
        return moduleManager.proxy_address(module_name)

    def get_module_providing(self, moduleManager, command):
        permitted_commands = self.get_permitted_commands(moduleManager)
        module_name = moduleManager.module_providing(permitted_commands, command)

        try:
            # check if the module exists in the module manager
            moduleManager[module_name]
        except KeyError:
            # the module has been removed from moduleManager (probably through a reload)
            CORE.warn('Module %r (command=%r) does not exists anymore' % (module_name, command))
            moduleManager.load()
            self._reload_acls_and_permitted_commands()
            module_name = None
        return module_name

    def get_method_name(self, moduleManager, module_name, command):
        module = self.get_permitted_commands(moduleManager)[module_name]
        methods = (cmd.method for cmd in module.commands if cmd.name == command)
        for method in methods:
            return method

    def __repr__(self):
        return '<ACLs from-ldap=%r>' % (isinstance(self.__acls, LDAP_ACLs),)


class Processes(object):
    """Interface for module processes"""

    singletons = {}

    def __init__(self, session):
        self.session = session
        self.__processes = {}

    def processes(self, module_name):
        return self.singletons if self.session.acls.is_module_singleton(module_name) else self.__processes

    def get_process(self, module_name, accepted_language, no_daemonize_module_processes=False):
        from .resources import ModuleProcess, ModuleProxy
        proxy_address = self.session.acls.get_module_proxy_address(module_name)
        if proxy_address:
            return ModuleProxy(proxy_address)

        processes = self.processes(module_name)
        if module_name not in processes:
            CORE.info('Starting new module process %s' % (module_name,))
            try:
                mod_proc = ModuleProcess(module_name, debug=MODULE_DEBUG_LEVEL, locale=accepted_language, no_daemonize_module_processes=no_daemonize_module_processes)
            except OSError as exc:
                _ = self.session._
                message = _('Could not open the module. %s Please try again later.') % {
                    errno.ENOMEM: _('There is not enough memory available on the server.'),
                    errno.EMFILE: _('There are too many opened files on the server.'),
                    errno.ENFILE: _('There are too many opened files on the server.'),
                    errno.ENOSPC: _('There is not enough free space on the server.'),
                    errno.ENOENT: _('The executable was not found.'),
                }.get(exc.errno, _('An unknown operating system error occurred (%s).') % (exc,))
                raise ServiceUnavailable(message)
            processes[module_name] = mod_proc
            mod_proc.set_exit_callback(functools.partial(self.process_exited, module_name))

        return processes[module_name]

    def stop_process(self, module_name):
        proc = self.processes(module_name).pop(module_name, None)
        if proc:
            proc.stop()

    def process_exited(self, module_name, exit_code):
        proc = self.processes(module_name).pop(module_name, None)
        if proc:
            proc._died(exit_code)

    def has_active_module_processes(self):
        return self.__processes

    def __repr__(self):
        return '<Processes for=%s>' % (', '.join(self.__processes),)
