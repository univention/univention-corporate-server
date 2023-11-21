#!/usr/bin/python3

from __future__ import annotations

import json
import os.path
import re
import sqlite3
import subprocess
import time
from itertools import islice
from typing import Callable

from ldap.filter import filter_format


try:
    from typing_extensions import ParamSpec  # Python 3.10+
    P = ParamSpec("P")
except ImportError:
    pass

import univention.testing.udm as udm_test
import univention.uldap
from ucsschool.importer.mass_import import user_import
from univention.config_registry import ucr


CONNECTOR_WAIT_INTERVAL = 12
CONNECTOR_WAIT_SLEEP = 5
CONNECTOR_WAIT_TIME = CONNECTOR_WAIT_SLEEP * CONNECTOR_WAIT_INTERVAL

lo: univention.uldap.access | None = None


def import_users(file: str) -> int:
    subprocess.check_call(['/usr/share/ucs-school-import/scripts/ucs-school-import', file])
    return 0


def import_users_new(args: list[str]) -> int:
    print(f'*** import_users_new({args!r})')
    subprocess.check_call(['/usr/share/ucs-school-import/scripts/ucs-school-testuser-import'] + args)
    return 0


def create_ous(names_of_ous: list[str]) -> int:
    for school_name in names_of_ous:
        subprocess.check_call(['/usr/share/ucs-school-import/scripts/create_ou', school_name])
    return 0


def remove_ous(names_of_ous: list[str]) -> int:
    for school_name in names_of_ous:
        subprocess.check_call(['udm', 'container/ou', 'remove', f'--dn={school_name}'])
    return 0


def _start_time() -> float:
    return time.time()


def _stop_time(startTime: float) -> float:
    return time.time() - startTime


def _ldap_replication_complete() -> bool:
    return subprocess.call('/usr/lib/nagios/plugins/check_univention_replication') == 0


def _get_usn() -> str:
    ldbsearch = subprocess.Popen(["ldbsearch", "-H", "/var/lib/samba/private/sam.ldb", "-s", "base", "-b", "", "highestCommittedUSN"], stdout=subprocess.PIPE)
    assert ldbsearch.stdout is not None
    for chunk in ldbsearch.stdout:
        line = chunk.decode('UTF-8', 'replace').strip()
        key, _, value = line.partition(": ")
        if key == "highestCommittedUSN":
            return value
    return ""


def wait_for_s4connector() -> int:
    conn = sqlite3.connect('/etc/univention/connector/s4internal.sqlite')
    c = conn.cursor()

    previous_lastUSN = lastUSN = highestCommittedUSN = previous_highestCommittedUSN = ""

    static_count = 0
    while static_count < CONNECTOR_WAIT_INTERVAL:
        print(f'Try {static_count}/{CONNECTOR_WAIT_INTERVAL} [plUSN={previous_lastUSN} lUSN={lastUSN} hcUSN={highestCommittedUSN} phcUSN={previous_highestCommittedUSN}]')
        time.sleep(CONNECTOR_WAIT_SLEEP)

        if not _ldap_replication_complete():
            continue

        previous_highestCommittedUSN = highestCommittedUSN

        highestCommittedUSN = _get_usn()
        print(highestCommittedUSN)

        previous_lastUSN = lastUSN
        try:
            c.execute('SELECT value FROM S4 WHERE key="lastUSN"')
        except sqlite3.OperationalError as exc:
            static_count = 0
            print(f'Reset counter: sqlite3.OperationalError: {exc}')
            continue

        conn.commit()
        lastUSN = c.fetchone()[0]

        if previous_lastUSN == lastUSN == highestCommittedUSN == previous_highestCommittedUSN:
            static_count += 1
        else:
            static_count = 0

    conn.close()
    return 0


def test_umc_admin_auth() -> int:
    return subprocess.call(['umc-command', '-U', 'Administrator', '-P', 'univention', 'ucr/get', '-l', '-o', "apache2/autostart"])


def test_umc_admin_auth_udm_load() -> int:
    return subprocess.call(['umc-command', '-U', 'Administrator', '-P', 'univention', 'udm/get', '-f', 'users/user', '-l', '-o', f"uid=Administrator,cn=users,{ucr['ldap/base']}"])


def s4_user_auth(username: str, password: str) -> int:
    return subprocess.call(['smbclient', '-U', f"{username}%{password}", '//localhost/sysvol', '-c', 'ls'])


def reset_passwords(user_dns: list[str]) -> int:
    for dn in user_dns:
        subprocess.call(['udm', 'users/user', 'modify', '--dn', dn, '--set', "password=Univention.991"])
    wait_for_s4connector()
    return 0


def get_user_dn(username: str) -> str:
    global lo
    if not lo:
        lo = univention.uldap.getMachineConnection()
    dn = lo.searchDn(filter_format('(&(uid=%s)(objectClass=sambaSamAccount))', [username]))
    return dn[0]


def get_user_dn_list(CSV_IMPORT_FILE: str, count: int = 40) -> list[str]:
    return [
        get_user_dn(line.split('\t')[1])
        for line in islice(open(CSV_IMPORT_FILE), count)
    ]


def get_user_dn_list_new(CSV_IMPORT_FILE: str, count: int = 40) -> list[str]:
    # must import ucsschool.importer.utils.shell *after* creating ~/.import_shell_config
    with open('/usr/share/ucs-school-import/configs/ucs-school-testuser-import.json') as fp:
        config = json.load(fp)
    config['input']['filename'] = CSV_IMPORT_FILE
    with open(os.path.expanduser('~/.import_shell_config'), 'w') as fp:
        json.dump(config, fp)

    # this will setup a complete import system configuration
    from ucsschool.importer.utils.shell import logger  # noqa: F401
    up = user_import.UserImport()
    imported_users = up.read_input()
    user_dns = []
    for user in islice(imported_users, count):
        user.make_username()
        username = user.name[:-1] if re.match('.*\\d$', user.name) else user.name
        try:
            user_dns.append(get_user_dn(username))
        except IndexError:
            # username calculated differently when importing and now, can happen, ignore
            pass
    return user_dns


def create_test_user() -> int:
    udm = udm_test.UCSTestUDM()
    username = udm.create_user(wait_for_replication=False)[1]
    wait_for_s4connector()
    return s4_user_auth(username, 'univention')


def execute_timing(description: str, allowedTime: float, callback: Callable[P, int], *args: P.args) -> bool:  # type: ignore[valid-type] # Python 3.10+
    print('Starting', description)

    startTime = _start_time()
    try:
        result = callback(*args)
    finally:
        duration = _stop_time(startTime)
        print(f'INFO: {description} took {duration:.0f} seconds (allowed time: {allowedTime:.0f} seconds)')

    if result != 0:
        print(f'Error: callback returned: {result}')
        return False

    if duration > allowedTime:
        print(f'ERROR: {description} took too long: {duration:.0f} > {allowedTime:.0f}')
        return False

    return True


def count_ldap_users() -> int:
    global lo
    if not lo:
        lo = univention.uldap.getMachineConnection()

    count = len(lo.search('(&(uid=*)(!(uid=*$))(objectClass=sambaSamAccount))', attr=['dn']))
    print(f'INFO: Found {count} OpenLDAP users')
    return count


def count_samba4_users() -> int:
    ldbsearch = subprocess.Popen(["ldbsearch", "-H", "/var/lib/samba/private/sam.ldb", "objectClass=user", "dn"], stdout=subprocess.PIPE)
    assert ldbsearch.stdout is not None
    count = sum(
        1
        for line in ldbsearch.stdout
        if line.decode('UTF-8', 'replace').strip().startswith("dn: ")
    )
    print(f'INFO: Found {count} Samba4 users')
    return count


def count_users(needed: int) -> bool:
    users = count_ldap_users()
    if users < needed:
        print('ERROR: Not all users were found in OpenLDAP')
        return False

    users = count_samba4_users()
    if users < needed:
        print('ERROR: Not all users were found in Samba4')
        return False

    return True
