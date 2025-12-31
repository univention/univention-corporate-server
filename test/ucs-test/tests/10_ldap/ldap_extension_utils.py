#!/usr/bin/python3
# SPDX-FileCopyrightText: 2013-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess
import time

import ldap
import ldap.schema
import psutil

import univention.uldap
from univention.config_registry import ConfigRegistry
from univention.testing.strings import random_int, random_name


WAIT_FOR_LDAP_TIME = 30  # seconds


def wait_for_ldap():
    print("\n** Waiting for slapd")
    for count in range(WAIT_FOR_LDAP_TIME):
        try:
            pinfo = [proc.name() for proc in psutil.process_iter() if proc.name() == 'slapd' and proc.ppid() == 1]
        except psutil.NoSuchProcess:
            pass
        else:
            if pinfo:
                print("(%s) process is running now.\n" % pinfo[0])
                break
            else:
                time.sleep(1)
                print(count)


def get_package_name():
    return random_name()


def get_schema_name():
    return random_name()


def get_acl_name():
    return '62%s' % random_name()


def get_container_name():
    return random_name()


def get_schema_attribute_id():
    return random_int() + random_int() + random_int() + random_int() + random_int()


def call_join_script(join_script_name):
    print(f'call_join_script({join_script_name!r})')
    ucr = ConfigRegistry()
    ucr.load()

    join_script = '/usr/lib/univention-install/%s' % join_script_name

    return subprocess.call([join_script, '--binddn', ucr.get('tests/domainadmin/account'), '--bindpwdfile', ucr.get('tests/domainadmin/pwdfile')], shell=False)


def call_unjoin_script(unjoin_script_name):
    print(f'call_unjoin_script({unjoin_script_name!r})')
    ucr = ConfigRegistry()
    ucr.load()

    join_script = '/usr/lib/univention-uninstall/%s' % unjoin_script_name

    return subprocess.call([join_script, '--binddn', ucr.get('tests/domainadmin/account'), '--bindpwdfile', ucr.get('tests/domainadmin/pwdfile')], shell=False)


def __fetch_schema_from_uri(ldap_uri):
    ucr = ConfigRegistry()
    ucr.load()

    retry = ucr.get('ldap/client/retry/count', 15)
    attempts = int(retry) + 1

    i = 0
    while i < attempts:
        try:
            return ldap.schema.subentry.urlfetch(ldap_uri)
        except ldap.SERVER_DOWN:
            if i >= (attempts - 1):
                raise
            time.sleep(1)
        i += 1


def fetch_schema_from_ldap_master():
    ucr = ConfigRegistry()
    ucr.load()

    ldap_uri = 'ldap://%(ldap/master)s:%(ldap/master/port)s' % ucr
    return __fetch_schema_from_uri(ldap_uri)


def fetch_schema_from_local_ldap():
    ucr = ConfigRegistry()
    ucr.load()

    ldap_uri = 'ldap://%(hostname)s:%(domainname)s' % ucr

    return __fetch_schema_from_uri(ldap_uri)


def get_ldap_master_connection(user_dn):
    ucr = ConfigRegistry()
    ucr.load()

    return univention.uldap.access(host=ucr.get('ldap/master'), port=int(ucr.get('ldap/master/port', '7389')), base=ucr.get('ldap/base'), binddn=user_dn, bindpw='univention')


def set_container_description(user_dn, container):
    print(f'set_container_description({user_dn!r}, {container!r})')
    lo = get_ldap_master_connection(user_dn)
    lo.modify(container, [('description', b'', random_name().encode('UTF-8'))])
