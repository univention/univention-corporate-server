#!/usr/bin/python3
#
# Univention Management Console
#  module: manages UDM modules
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2025 Univention GmbH
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

import functools
import re

from ldap import LDAPError

import univention.admin as udm
import univention.admin.syntax as udm_syntax
import univention.admin.uexceptions as udm_errors
from univention.directory.manager.rest.udm import (
    SearchLimitReached, UDM_Module as _UDM_Module, UMCError, read_syntax_choices,
)
from univention.management.console import Translation
from univention.management.console.config import ucr
from univention.management.console.ldap import get_user_connection, user_connection
from univention.management.console.log import MODULE


_ = Translation('univention-management-console-module-udm').translate


def calculate_bind_hash(request):
    return hash((request.username, request.password, request.auth_type))


def set_bind_hash(hash):
    global __bind_hash
    __bind_hash = hash


def get_bind_hash():
    return __bind_hash


def set_bind_function(connection_getter):
    global __bind_function
    __bind_function = connection_getter


def get_bind_function():
    return __bind_function


def LDAP_Connection(func):
    """
    Get a cached ldap connection bound to the user connection.

    .. deprecated :: UCS 4.4
            This must not be used in udm_ldap.py.
            Use something explicit like self.get_ldap_connection() instead.

    """
    @functools.wraps(func)
    def _decorated(*args, **kwargs):
        method = user_connection(func, bind=get_bind_function(), write=True, bindhash=get_bind_hash())
        try:
            return method(*args, **kwargs)
        except (LDAPError, udm_errors.ldapError):
            return method(*args, **kwargs)
    return _decorated


class UserWithoutDN(UMCError):

    def __init__(self, username):
        self._username = username
        super().__init__()

    def _error_msg(self):
        yield _('The LDAP DN of the user %s could not be determined.') % (self._username,)
        yield _('The following steps can help to solve this problem:')
        yield ' * ' + _('Ensure that the LDAP server on this system is running and responsive')
        yield ' * ' + _('Make sure the DNS settings of this server are correctly set up and the DNS server is responsive')
        if not self._is_master:
            yield ' * ' + _('Check the join status of this system by using the domain join UMC module')
        yield ' * ' + _('Make sure all join scripts were successfully executed')
        if self._updates_available:
            yield ' * ' + _('Install the latest software updates')
        yield _('If the problem persists additional hints about the cause can be found in the following log file(s):')
        yield ' * /var/log/univention/management-console-module-udm.log'
        yield ' * /var/log/univention/management-console-server.log'


class LDAP_AuthenticationFailed(UMCError):

    def __init__(self):
        super().__init__(status=401)

    def _error_msg(self):
        yield _('Authentication failed')


class UDM_Module(_UDM_Module):
    """Wraps UDM modules to provide a simple access to the properties and functions"""

    def get_ldap_connection(self, base=None):
        if ucr.is_true("umc/udm/delegation"):
            from univention.management.console.ldap import get_admin_connection
            self.ldap_connection, _po = get_admin_connection()
        elif get_bind_function():
            try:
                self.ldap_connection, _po = get_user_connection(bind=get_bind_function(), write=True, bindhash=get_bind_hash())
            except (LDAPError, udm_errors.ldapError):
                self.ldap_connection, _po = get_user_connection(bind=get_bind_function(), write=True, bindhash=get_bind_hash())
            self.ldap_position = udm.uldap.position(self.ldap_connection.base)
        return super().get_ldap_connection()

    def get_default_values(self, property_name):
        """
        Depending on the syntax of the given property a default
        search pattern/value is returned
        """
        MODULE.info('Searching for property %s' % property_name)
        ldap_connection, ldap_position = self.get_ldap_connection()
        for key, prop in getattr(self.module, 'property_descriptions', {}).items():
            if key == property_name:
                value = prop.syntax.widget_default_search_pattern
                if prop.syntax.search_widget in ('ComboBox', 'SuggestionBox'):
                    value = read_syntax_choices(prop.syntax, ldap_connection=ldap_connection, ldap_position=ldap_position)
                return value

    def properties(self, position_dn):
        props = [{'id': '$dn$', 'type': 'HiddenInput', 'label': '', 'searchable': False}]
        props.extend(super().properties(position_dn))
        props.append({'id': '$options$', 'type': 'WidgetGroup', 'widgets': self.get_options()})
        props.append({'id': '$references$', 'type': 'umc/modules/udm/ReferencingObjects', 'readonly': True, 'size': 'Two'})
        return props


LDAP_ATTR_RE = re.compile(r'^%\(([^)]*)\)s$')  # '%(username)s' -> 'username'


def search_syntax_choices_by_key(syn, key, ldap_connection, ldap_position):
    if issubclass(syn.__class__, udm_syntax.UDM_Objects):
        if syn.key == 'dn':
            try:
                return read_syntax_choices(syn, {'scope': 'base', 'container': key}, ldap_connection=ldap_connection, ldap_position=ldap_position)
            except udm_errors.base:  # TODO: which exception is raised here exactly?
                # invalid DN
                return []
        if syn.key is not None:
            match = LDAP_ATTR_RE.match(syn.key)
            if match:
                attr = match.groups()[0]
                options = {'objectProperty': attr, 'objectPropertyValue': key, 'allow_asterisks': False}
                return read_syntax_choices(syn, options, ldap_connection=ldap_connection, ldap_position=ldap_position)

    MODULE.warn('Syntax %r: No fast search function' % syn.name)
    # return them all, as there is no reason to filter after everything has loaded
    # frontend will cache it.
    return read_syntax_choices(syn, ldap_connection=ldap_connection, ldap_position=ldap_position)


def info_syntax_choices(syn, options=None, ldap_connection=None, ldap_position=None):
    if issubclass(syn.__class__, udm_syntax.UDM_Objects):
        size = 0
        if syn.static_values is not None:
            size += len(syn.static_values)
        for udm_module in syn.udm_modules:
            module = UDM_Module(udm_module, ldap_connection=ldap_connection, ldap_position=ldap_position)
            if module.module is None:
                continue
            filter_s = syn._create_ldap_filter(options or {}, module)
            if filter_s is not None:
                try:
                    size += len(module.search(filter=filter_s, simple=not syn.use_objects))
                except (udm_errors.ldapSizelimitExceeded, SearchLimitReached):
                    return {'performs_well': True, 'size_limit_exceeded': True}
        return {'size': size, 'performs_well': True}
    return {'size': 0, 'performs_well': False}


if __name__ == '__main__':
    set_bind_function(lambda lo: lo.bind('uid=Administrator,cn=users,%s' % (ucr['ldap/base'],), 'univention'))
