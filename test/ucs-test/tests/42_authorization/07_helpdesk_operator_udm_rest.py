#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import pytest

from univention.admin.rest.client import Forbidden, UnprocessableEntity
from univention.config_registry import ucr as _ucr


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/rest/delegative-administration/enabled'), reason='authz not activated')


@pytest.mark.parametrize('position, expected', [
    ('cn=users,{ldap_base}', False),
    ('cn=users,{ou_dn}', False),
    ('{ou_dn}', False),
    ('{ldap_base}', False),
])
def test_helpdesk_operator_cant_create(position, expected, ou_helpdesk_operator_rest_client, ou, ldap_base):
    position = position.format(ou_dn=ou.dn, ldap_base=ldap_base)
    if expected:
        user = ou_helpdesk_operator_rest_client.create_user(position)
        user.delete()
    else:
        with pytest.raises(Forbidden):
            ou_helpdesk_operator_rest_client.create_user(position)


@pytest.mark.parametrize('user, changes, expected', [
    ('{normal_user}', {"guardianRoles": ["umc:udm:helpdesk-operator&umc:udm:ou=bremen"]}, False),
    ('{normal_user}', {'description': 'dsfdsf'}, False),
    ('uid=Administrator,cn=users,{ldap_base}', {'description': 'dsfdsf'}, False),
])
def test_helpdesk_operator_cant_modify_properties(ldap_base, ou, user, changes, expected, udm, ou_helpdesk_operator_rest_client):
    dn, _ = udm.create_user(position=ou.user_default_container)
    user_dn = user.format(normal_user=dn, ldap_base=ldap_base)

    if not expected:
        if user_dn.endswith(ou.dn):
            with pytest.raises(Forbidden):
                ou_helpdesk_operator_rest_client.modify_user(user_dn, changes)
        else:
            with pytest.raises(UnprocessableEntity):
                ou_helpdesk_operator_rest_client.modify_user(user_dn, changes)
    else:
        ou_helpdesk_operator_rest_client.modify_user(user_dn, changes)


@pytest.mark.parametrize('position, expected', [
    ('cn=users,{ou_dn}', True),
    ('cn=users,{ldap_base}', False),
])
def test_helpdesk_operator_can_reset_password(position, expected, ou_helpdesk_operator_rest_client, udm, ou, ldap_base):
    dn, _ = udm.create_user(position=position.format(ou_dn=ou.dn, ldap_base=ldap_base))
    changes = {
        'homeSharePath': '/home/ou',
        'overridePWHistory': True,
        'overridePWLength': True,
        'password': 'univention',
        'unlock': False,
    }
    if expected:
        ou_helpdesk_operator_rest_client.modify_user(dn, changes)
    else:
        if dn.endswith(ou.dn):
            with pytest.raises(Forbidden):
                ou_helpdesk_operator_rest_client.modify_user(dn, changes)
        else:
            with pytest.raises(UnprocessableEntity):
                ou_helpdesk_operator_rest_client.modify_user(dn, changes)
