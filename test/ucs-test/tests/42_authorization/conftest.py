# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2025 Univention GmbH
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

import locale
import time
from types import SimpleNamespace

import pytest

from univention.admin.rest.client import UDM as UDM_REST, UnprocessableEntity
from univention.testing.strings import random_username
from univention.testing.umc import Client
from univention.testing.utils import UCSTestDomainAdminCredentials


TRANSLATIONS = {
    'de_DE': {
        'Permission denied.': 'Zugriff verweigert.',
        'No such object:': 'Das Objekt existiert nicht:',
    },
}


def translate(string: str) -> str:
    code, _ = locale.getlocale()
    return TRANSLATIONS.get(code, {}).get(string, string)


class RestClientHelper(UDM_REST):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_module = self.get('users/user')
        self.mail_domain_module = self.get('mail/domain')
        self.group_module = self.get('groups/group')

    def create_user(self, position: str):
        obj = self.user_module.new(position=position)
        obj.properties['username'] = random_username()
        obj.properties['password'] = 'univention'
        obj.properties['lastname'] = random_username()
        obj.save()
        return obj

    def delete_user(self, dn: str):
        obj = self.user_module.get(dn)
        obj.delete()
        with pytest.raises(UnprocessableEntity):
            self.user_module.get(dn)

    def search_user(self, filter_s: str, position: str | None = None):
        return list(self.user_module.search(filter_s, position=position))

    def move_user(self, dn: str, position: str):
        obj = self.user_module.get(dn)
        obj.move(position)
        return obj

    def modify_user(self, dn: str, changes: dict):
        obj = self.user_module.get(dn)
        for prop, value in changes.items():
            obj.properties[prop] = value
        obj.save()
        return obj

    def create_mail_domain(self):
        obj = self.mail_domain_module.new()
        obj.properties['name'] = random_username()
        obj.save()
        return obj

    def delete_mail_domain(self, dn: str):
        obj = self.mail_domain_module.get(dn)
        obj.delete()
        with pytest.raises(UnprocessableEntity):
            self.mail_domain_module.get(dn)

    def modify_group(self, dn: str, changes: dict):
        obj = self.group_module.get(dn)
        for prop, value in changes.items():
            obj.properties[prop] = value
        obj.save()
        return obj


class ClientHelper(Client):

    def wait_for_progress(self, progress_id: str, object_type: str):
        while True:
            req = self.umc_command('udm/progress', {'progress_id': progress_id}, object_type)
            res = req.result
            if res['finished']:
                return req
            time.sleep(1)

    def delete_object(self, dn: str, object_type: str) -> None:
        options = [{
            'object': dn,
            'options': {
                'cleanup': True,
                'recursive': True,
            },
        }]
        return self.umc_command('udm/remove', options, object_type).result[0]

    def move_object(self, dn: str, position: str, object_type: str):
        options = [{
            'object': dn,
            'options': {
                'container': position,
            },
        }]
        result = self.umc_command('udm/move', options, object_type).result
        return self.wait_for_progress(result['id'], object_type).result['intermediate'][0]

    def modify_object(self, dn: str, changes: dict, object_type: str):
        changes['$dn$'] = dn
        return self.umc_command('udm/put', [{'object': changes}], object_type).result[0]

    def get_object(self, dn: str, object_type: str):
        options = [dn]
        res = self.umc_command('udm/get', options, object_type)
        return res.result[0]

    def create_user(self, position: str):
        options = [{
            'object': {
                'lastname': random_username(),
                'username': random_username(),
                'password': 'univention',
            },
            'options': {
                'container': position,
                'objectType': 'users/user',
            },
        }]
        return self.umc_command('udm/add', options, 'users/user').result[0]

    def create_group(self, position: str):
        options = [{
            'object': {
                'name': random_username(),
                'description': random_username(),
            },
            'options': {
                'container': position,
                'objectType': 'groups/group',
            },
        }]
        return self.umc_command('udm/add', options, 'groups/group').result[0]

    def create_mail_domain(self, name: str, position: str):
        options = [{
            'object': {
                'name': name,
                '$policies$': {},
            },
            'options': {
                'container': position,
                'objectType': 'mail/domain',
                'objectTemplate': None,
            },
        }]
        return self.umc_command('udm/add', options, 'mail/domain').result[0]


@pytest.fixture
def admin_umc_client():
    client = ClientHelper.get_test_connection()
    return client


@pytest.fixture
def ouadmin_umc_client(ou):
    client = ClientHelper()
    client.authenticate(ou.admin_username, 'univention')
    return client


@pytest.fixture
def admin_rest_client(ucr):
    return RestClientHelper(
        'https://%(hostname)s.%(domainname)s/univention/udm/' % ucr,
        username=UCSTestDomainAdminCredentials().username,
        password=UCSTestDomainAdminCredentials().bindpw,
    )


@pytest.fixture
def ouadmin_rest_client(ucr, ou):
    return RestClientHelper(
        'https://%(hostname)s.%(domainname)s/univention/udm/' % ucr,
        username=ou.admin_username,
        password='univention',
    )


@pytest.fixture
def ou(ldap_base):
    return SimpleNamespace(
        dn=f'ou=ou1,{ldap_base}',
        dn2=f'ou=ou2,{ldap_base}',
        admin_username='ou1admin',
        admin_dn=f'uid=ou1admin,cn=users,{ldap_base}',
        user_username='user1-ou1',
        user_dn=f'uid=user1-ou1,cn=users,ou=ou1,{ldap_base}',
        user_default_container=f'cn=users,ou=ou1,{ldap_base}',
        group_default_container=f'cn=groups,ou=ou1,{ldap_base}',
    )
