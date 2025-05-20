#!/usr/bin/python3
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.config_registry import ucr
from univention.management.console.ldap import get_connection, reset_cache  # noqa: F401


def get_user_ldap_write_connection(auth_type, binddn, bindpw):
    return get_ldap_connection('user-write', auth_type, binddn, bindpw)


def get_user_ldap_read_connection(auth_type, binddn, bindpw):
    return get_ldap_connection('user-read', auth_type, binddn, bindpw)


def get_machine_ldap_connection(type_):
    binddn = ucr.get(f'directory/manager/rest/ldap-connection/{type_}/binddn', ucr['ldap/hostdn'] if type_.startswith('machine-') else f'cn=admin,{ucr["ldap/base"]}')
    with open(ucr.get(f'directory/manager/rest/ldap-connection/{type_}/password-file', '/etc/machine.secret' if type_.startswith('machine-') else '/etc/ldap.secret')) as fd:
        password = fd.read().strip()
    return get_ldap_connection(type_, None, binddn, password)


def get_machine_ldap_write_connection():
    return get_machine_ldap_connection('machine-write')


def get_machine_ldap_read_connection():
    return get_machine_ldap_connection('machine-read')


def get_admin_ldap_write_connection():
    return get_machine_ldap_connection('admin-write')


def get_admin_ldap_read_connection():
    return get_machine_ldap_connection('admin-read')


def get_ldap_connection(type_, auth_type, binddn, bindpw):
    default_uri = "ldap://%s:%d" % (ucr.get('ldap/master'), ucr.get_int('ldap/master/port', '7389'))
    uri = ucr.get(f'directory/manager/rest/ldap-connection/{type_}/uri', default_uri)
    start_tls = ucr.get_int('directory/manager/rest/ldap-connection/user-read/start-tls', 2)
    if auth_type == 'Bearer':
        return get_connection(bind=lambda lo: lo.bind_oauthbearer(binddn, bindpw), bindhash=hash((binddn, bindpw)), binddn=None, bindpw=None, host=None, port=None, base=ucr['ldap/base'], start_tls=start_tls, uri=uri)
    return get_connection(bind=None, binddn=binddn, bindpw=bindpw, host=None, port=None, base=ucr['ldap/base'], start_tls=start_tls, uri=uri)
