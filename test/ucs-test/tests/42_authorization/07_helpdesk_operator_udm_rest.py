#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import pytest

from univention.admin.rest.client import Forbidden, NotFound
from univention.config_registry import ucr as _ucr


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/rest/delegative-administration/enabled'), reason='authz not activated')


@pytest.mark.parametrize('position, expected', [
    ('cn=users,{ldap_base}', False),
    ('cn=users,{ou_dn}', False),
    ('{ou_dn}', False),
    ('{ldap_base}', False),
])
def test_helpdesk_operator_cant_create(position, expected, ouhelpdeskoperator_rest_client, ou, ldap_base):
    position = position.format(ou_dn=ou.dn, ldap_base=ldap_base)
    if expected:
        user = ouhelpdeskoperator_rest_client.create_user(position)
        user.delete()
    else:
        with pytest.raises(Forbidden):
            ouhelpdeskoperator_rest_client.create_user(position)


@pytest.mark.parametrize('position, changes, expected', [
    ('cn=users,{ou_dn}', {"guardianRoles": ["umc:udm:helpdesk-operator&umc:udm:ou=bremen"]}, False),
    ('cn=users,{ou_dn}', {'description': 'dsfdsf'}, False),
    ('uid=Administrator,cn=users,{ldap_base}', {'description': 'dsfdsf'}, False),
])
def test_helpdesk_operator_cant_modify_properties(ldap_base, ou, position, changes, expected, udm, ouhelpdeskoperator_rest_client):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    if not expected:
        if dn.endswith(ou.dn):
            with pytest.raises(Forbidden):
                ouhelpdeskoperator_rest_client.modify_user(dn, changes)
        else:
            with pytest.raises(NotFound):
                ouhelpdeskoperator_rest_client.modify_user(dn, changes)
    else:
        ouhelpdeskoperator_rest_client.modify_user(dn, changes)


@pytest.mark.parametrize('position, expected', [
    ('cn=users,{ou_dn}', True),
    ('{ldap_base}', False),
])
def test_helpdesk_operator_can_reset_password(position, expected, ouhelpdeskoperator_rest_client, udm, ou, ldap_base):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    changes = {
        'homeSharePath': '/home/ou',
        'overridePWHistory': True,
        'overridePWLength': True,
        'password': 'univention',
        'unlock': False,
    }
    if expected:
        ouhelpdeskoperator_rest_client.modify_user(dn, changes)
    else:
        if dn.endswith(ou.dn):
            with pytest.raises(Forbidden):
                ouhelpdeskoperator_rest_client.modify_user(dn, changes)
        else:
            with pytest.raises(NotFound):
                ouhelpdeskoperator_rest_client.modify_user(dn, changes)
