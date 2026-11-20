#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration of user templates in UMC
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous
import subprocess

import pytest
from conftest import cerbos_only, translate

from univention.config_registry import ucr as _ucr
from univention.lib.umc import BadRequest


pytestmark = [
    pytest.mark.skipif(not _ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='authz not activated'),
    cerbos_only,
]


@pytest.fixture(autouse=True)
def restart_umc():
    yield
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service'])


def test_usertemplate_remove(ldap_base, random_username, udm, ouadmin_umc_client):
    usertemplate_dn = udm.create_object('settings/usertemplate', name=random_username(), position=f'cn=templates,cn=univention,{ldap_base}')
    res = ouadmin_umc_client.delete_object('settings/usertemplate', usertemplate_dn)
    assert not res['success']


def test_usertemplate_create(ldap_base, random_username, ouadmin_umc_client):
    options = [{
        'object': {
            'name': random_username(),
            '$policies$': {},
        },
        'options': {
            'container': f'cn=templates,cn=univention,{ldap_base}',
            'objectType': 'settings/usertemplate',
            'objectTemplate': None,
        },
    }]
    res = ouadmin_umc_client.umc_command('udm/add', options, 'settings/usertemplate').result[0]
    assert not res['success']
    assert res['details'] == translate('Permission denied.')


@pytest.mark.parametrize('position, has_access', [
    ('{ldap_base}', False),
    ('cn=templates,cn=univention,{ldap_base}', True),
])
def test_query_and_read_usertemplate(udm, ldap_base, ou, random_username, position, has_access, ouadmin_umc_client):
    position = position.format(ldap_base=ldap_base)
    name = random_username()
    object_dn = f'cn={name},{position}'
    query_options = {
        'container': 'all',
        'hidden': False,
        'objectType': 'settings/usertemplate',
        'objectProperty': 'None',
        'objectPropertyValue': '',
        'fields': ['name', 'labelObjectType', 'path'],
    }

    with pytest.raises(BadRequest):
        ouadmin_umc_client.umc_command('udm/get', [object_dn], 'settings/usertemplate')  # type: ignore[call-arg]

    udm.create_object('settings/usertemplate', name=name, position=position)

    res = ouadmin_umc_client.umc_command('udm/query', query_options, 'navigation').result  # type: ignore[call-arg]
    templates = ouadmin_umc_client.umc_command('udm/templates', {'objectType': 'users/user'}, 'users/user').result  # type: ignore[call-arg]
    if has_access:
        assert object_dn in [x['$dn$'] for x in res]
        assert object_dn in [x['id'] for x in templates]
        res = ouadmin_umc_client.umc_command('udm/get', [object_dn], 'settings/usertemplate').result  # type: ignore[call-arg]
        assert len(res) == 1
        assert res[0]['$dn$'] == object_dn
    else:
        assert object_dn not in [x['$dn$'] for x in res]
        assert object_dn not in [x['id'] for x in templates]
        with pytest.raises(BadRequest):
            ouadmin_umc_client.umc_command('udm/get', [object_dn], 'settings/usertemplate')  # type: ignore[call-arg]

    udm.remove_object('settings/usertemplate', dn=object_dn)

    res = ouadmin_umc_client.umc_command('udm/query', query_options, 'navigation').result  # type: ignore[call-arg]
    assert object_dn not in [x['$dn$'] for x in res]
    with pytest.raises(BadRequest):
        ouadmin_umc_client.umc_command('udm/get', [object_dn], 'settings/usertemplate')  # type: ignore[call-arg]
