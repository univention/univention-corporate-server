#!/usr/bin/python3
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2024 Univention GmbH
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

from univention.management.console.config import ucr
from univention.management.console.ldap import get_connection, reset_cache  # noqa: F401


def get_user_ldap_write_connection(binddn, bindpw):
    return get_ldap_connection('user-write', binddn, bindpw)


def get_user_ldap_read_connection(binddn, bindpw):
    return get_ldap_connection('user-read', binddn, bindpw)


def get_machine_ldap_connection(type_):
    binddn = ucr.get(f'directory/manager/rest/ldap-connection/{type_}/binddn', ucr['ldap/hostdn'])
    with open(ucr.get(f'directory/manager/rest/ldap-connection/{type_}/password-file', '/etc/machine.secret')) as fd:
        password = fd.read().strip()
    return get_ldap_connection(type_, binddn, password)


def get_machine_ldap_write_connection():
    return get_machine_ldap_connection('machine-write')


def get_machine_ldap_read_connection():
    return get_machine_ldap_connection('machine-read')


def get_ldap_connection(type_, binddn, bindpw):
    default_uri = "ldap://%s:%d" % (ucr.get('ldap/master'), ucr.get_int('ldap/master/port', '7389'))
    uri = ucr.get(f'directory/manager/rest/ldap-connection/{type_}/uri', default_uri)
    start_tls = ucr.get_int('directory/manager/rest/ldap-connection/user-read/start-tls', 2)
    return get_connection(bind=None, binddn=binddn, bindpw=bindpw, host=None, port=None, base=ucr['ldap/base'], start_tls=start_tls, uri=uri)
