#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous
import locale
import subprocess

import pytest

from univention.config_registry import ucr as _ucr


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='authz not activated')


TRANSLATIONS = {
    'de_DE': {
        'Permission denied.': 'Zugriff verweigert.',
        'No such object:': 'Das Objekt existiert nicht:',
    },
    'en_US': {
        'Permission denied.': 'Permission denied.',
        'No such object:': 'No such object:',
    },
}


def translate(string: str) -> str:
    code, _ = locale.getlocale()
    return TRANSLATIONS.get(code, {}).get(string, string)


@pytest.fixture(autouse=True)
def restart_umc():
    yield
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service'])


@pytest.mark.parametrize('position, expected', [
    ('cn=users,{ldap_base}', False),
    ('cn=users,{ou_dn}', False),
    ('{ou_dn}', False),
    ('{ldap_base}', False),
])
def test_helpdesk_operator_cant_create(position, expected, ouhelpdeskoperator_umc_client, ou, ldap_base):
    res = ouhelpdeskoperator_umc_client.create_user(position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    if not expected:
        assert not res['success']
        assert res['details'] == translate('Permission denied.')
    else:
        assert res['success']
        position = position.format(ou_dn=ou.dn, ldap_base=ldap_base)


@pytest.mark.parametrize('position, changes, expected', [
    ('cn=users,{ou_dn}', {"guardianRoles": ["umc:udm:helpdesk-operator&umc:udm:ou=bremen"]}, False),
    ('cn=users,{ou_dn}', {'description': 'dsfdsf'}, False),
    ('uid=Administrator,cn=users,{ldap_base}', {'description': 'dsfdsf'}, False),
])
def test_helpdesk_operator_cant_modify_properties(ldap_base, ou, position, changes, expected, udm, ouhelpdeskoperator_umc_client):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    res = ouhelpdeskoperator_umc_client.modify_object(dn, changes, 'users/user')
    if not expected:
        assert not res['success']
        if dn.endswith(ou.dn):
            assert res['details'] == translate('Permission denied.')
        else:
            assert res['details'] == f'{translate("No such object:")} {dn}.'
    else:
        assert res['success']
        assert res['$dn$'] == dn


@pytest.mark.parametrize('position, expected', [
    ('{ldap_base}', False),
    ('cn=users,{ou_dn}', True),
])
def test_helpdesk_operator_can_reset_password(ldap_base, ou, position, expected, udm, random_username, ouhelpdeskoperator_umc_client):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    changes = {
        '$dn$': dn,
        'overridePWHistory': True,
        'overridePWLength': True,
        'password': 'univention',
        'unlock': False,
    }
    res = ouhelpdeskoperator_umc_client.modify_object(dn, changes, 'users/user')
    if not expected:
        assert not res['success']
        if dn.endswith(ou.dn):
            assert res['details'] == translate('Permission denied.')
        else:
            assert res['details'] == f'{translate("No such object:")} {dn}.'
    else:
        assert res['success']
        assert res['$dn$'] == dn
