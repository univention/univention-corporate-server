#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous
import locale
import subprocess
import time
from types import SimpleNamespace

import pytest

from univention.config_registry import ucr as _ucr
from univention.testing.umc import Client


check_delegation = pytest.mark.skipif(not _ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='directory/manager/web/delegative-administration/enabled not activated')


TRANSLATIONS = {
    'de_DE': {
        'Permission denied.': 'Zugriff verweigert.',
        'No such object:': 'Das Objekt existiert nicht:',
    },
}


def _(string: str) -> str:
    code, _ = locale.getlocale()
    return TRANSLATIONS.get(code, {}).get(string, string)


@pytest.fixture(autouse=True)
def restart_umc():
    yield
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service'])


@pytest.fixture
def ou(ldap_base):
    return SimpleNamespace(
        dn=f'ou=ou1,{ldap_base}',
        admin_username='ou1-admin',
        admin_dn=f'uid=ou1-admin,cn=users,{ldap_base}',
        user_username='user1-ou1',
        user_dn=f'uid=user1-ou1,cn=users,ou=ou1,{ldap_base}',
        user_default_container=f'cn=users,ou=ou1,{ldap_base}',
        group_default_container=f'cn=groups,ou=ou1,{ldap_base}',
        helpdesk_operator_username='ou1-helpdesk-operator',
        helpdesk_operator_dn=f'uid=ou1-helpdesk-operator,cn=users,{ldap_base}',
    )


@check_delegation
@pytest.mark.parametrize('position, expected', [
    ('cn=users,{ldap_base}', False),
    ('cn=users,{ou_dn}', False),
    ('{ou_dn}', False),
    ('{ldap_base}', False),
])
def test_helpdesk_operator_cant_create(ou, ldap_base, random_username, position, expected):
    client = Client()
    client.authenticate(ou.helpdesk_operator_username, 'univention')
    options = [{
        'object': {
            'lastname': random_username(),
            'username': random_username(),
            'password': 'univention',
        },
        "options": {
            "container": position.format(ou_dn=ou.dn, ldap_base=ldap_base),
            "objectType": "users/user",
        },
    }]
    res = client.umc_command('udm/add', options, 'users/user').result[0]
    if not expected:
        assert not res['success']
        assert res['details'] == _('Permission denied.')
    else:
        assert res['success']


def wait_for_progress(client, progress_id):
    while True:
        req = client.umc_command('udm/progress', {"progress_id": progress_id}, 'users/user')
        res = req.result
        if res['finished']:
            return req
        time.sleep(1)


@check_delegation
@pytest.mark.parametrize('position, expected', [
    ('{ldap_base}', False),
    ('cn=users,{ou_dn}', True),
])
def test_helpdesk_operator_can_reset_password(ldap_base, ou, position, expected, udm, random_username):
    dn = udm.create_object(
        'users/user',
        lastname=random_username(),
        username=random_username(),
        password='univention',
        homeSharePath='/home/ou',
        overridePWHistory=None,
        overridePWLength=None,
        unlock="0",
        position=position.format(ou_dn=ou.dn, ldap_base=ldap_base),
    )
    client = Client()
    client.authenticate(ou.helpdesk_operator_username, 'univention')
    changes = {}
    changes['$dn$'] = dn
    changes["overridePWHistory"] = True
    changes["overridePWLength"] = True
    changes["password"] = 'univention'
    changes["unlock"] = "0"
    res = client.umc_command('udm/put', [{'object': changes}], 'users/user').result[0]
    if not expected:
        assert not res['success']
        if dn.endswith(ou.dn):
            assert res['details'] == _('Permission denied.')
        else:
            assert res['details'] == f'{_("No such object:")} {dn}.'
    else:
        assert res['success']
        assert res['$dn$'] == dn


@check_delegation
@pytest.mark.parametrize('user, changes, expected', [
    ('{normal_user}', {"guardianRoles": ["umc:udm:helpdesk-operator&umc:udm:ou=bremen"]}, False),
    ('{normal_user}', {'description': 'dsfdsf'}, False),
    ('uid=Administrator,cn=users,{ldap_base}', {'description': 'dsfdsf'}, False),
])
def test_helpdesk_operator_cant_modify_properties(ldap_base, ou, user, changes, expected, udm, random_username):
    dn = udm.create_object(
        'users/user',
        lastname=random_username(),
        username=random_username(),
        password='univention',
        position=ou.user_default_container,
    )
    client = Client()
    client.authenticate(ou.helpdesk_operator_username, 'univention')
    user_dn = user.format(normal_user=dn, ldap_base=ldap_base)
    changes['$dn$'] = user_dn
    res = client.umc_command('udm/put', [{'object': changes}], 'users/user').result[0]
    if not expected:
        assert not res['success']
        if user_dn.endswith(ou.dn):
            assert (res['details'] == _('Permission denied.')) or (res['details'] == f'{_("No such object:")} {user_dn}.')
        else:
            assert res['details'] == f'{_("No such object:")} {user_dn}.'
    else:
        assert res['success']
        assert res['$dn$'] == user_dn
