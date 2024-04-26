#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2024 Univention GmbH
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

import subprocess
import time
from typing import TYPE_CHECKING, Tuple

import ldap
import ldap.schema
import psutil
from retrying import retry

import univention.uldap
from univention.config_registry import ConfigRegistry, ucs_live as ucr
from univention.testing.strings import random_int, random_name
from univention.testing.utils import UCSTestDomainAdminCredentials


if TYPE_CHECKING:
    import ldap.schema.subentry


WAIT_FOR_LDAP_TIME = 30  # seconds


def wait_for_ldap() -> None:
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


def get_package_name() -> str:
    return random_name()


def get_schema_name() -> str:
    return random_name()


def get_acl_name() -> str:
    return '62%s' % random_name()


def get_container_name() -> str:
    return random_name()


def get_schema_attribute_id() -> str:
    return random_int() + random_int() + random_int() + random_int() + random_int()


def call_join_script(join_script_name: str) -> int:
    print(f'call_join_script({join_script_name!r})')
    join_script = '/usr/lib/univention-install/%s' % join_script_name
    account = UCSTestDomainAdminCredentials()
    return subprocess.call([join_script, '--binddn', account.binddn, '--bindpwdfile', account.pwdfile])


def call_unjoin_script(unjoin_script_name: str) -> int:
    print(f'call_unjoin_script({unjoin_script_name!r})')
    join_script = '/usr/lib/univention-uninstall/%s' % unjoin_script_name
    account = UCSTestDomainAdminCredentials()
    return subprocess.call([join_script, '--binddn', account.binddn, '--bindpwdfile', account.pwdfile])


@retry(retry_on_exception=ldap.SERVER_DOWN, stop_max_attempt_number=ucr.get_int('ldap/client/retry/count', 15) + 1)
def __fetch_schema_from_uri(ldap_uri: str) -> Tuple[str, ldap.schema.subentry.SubSchema]:
    return ldap.schema.subentry.urlfetch(ldap_uri)


def fetch_schema_from_ldap_master() -> Tuple[str, ldap.schema.subentry.SubSchema]:
    ucr = ConfigRegistry()
    ucr.load()

    ldap_uri = 'ldap://%(ldap/master)s:%(ldap/master/port)s' % ucr
    return __fetch_schema_from_uri(ldap_uri)


def fetch_schema_from_local_ldap() -> Tuple[str, ldap.schema.subentry.SubSchema]:
    ucr = ConfigRegistry()
    ucr.load()

    ldap_uri = 'ldap://%(hostname)s:%(domainname)s' % ucr

    return __fetch_schema_from_uri(ldap_uri)


def get_ldap_master_connection(user_dn: str) -> univention.uldap.access:
    ucr = ConfigRegistry()
    ucr.load()

    return univention.uldap.access(host=ucr.get('ldap/master'), port=ucr.get_int('ldap/master/port', 7389), base=ucr.get('ldap/base'), binddn=user_dn, bindpw='univention')


def set_container_description(user_dn: str, container: str) -> None:
    print(f'set_container_description({user_dn!r}, {container!r})')
    lo = get_ldap_master_connection(user_dn)
    lo.modify(container, [('description', b'', random_name().encode('UTF-8'))])
