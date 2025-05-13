import subprocess
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def restart_umc():
    yield
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service'])


@pytest.fixture
def test_ou_index():
    """Return the index of the OU to use for testing"""
    return 1  # Using ou1 for tests


@pytest.fixture
def ou(test_ou_index, ldap_base):
    ou_index = test_ou_index
    return SimpleNamespace(
        dn=f'ou=ou{ou_index},{ldap_base}',
        admin_username=f'ou{ou_index}admin',
        admin_dn=f'uid=ou{ou_index}admin,cn=users,{ldap_base}',
        lesser_admin_username=f'ou{ou_index}lesseradmin',
        lesser_admin_dn=f'uid=ou{ou_index}lesseradmin,cn=users,{ldap_base}',
        user_username=f'user1-ou{ou_index}',
        user_dn=f'uid=user1-ou{ou_index},cn=users,ou=ou{ou_index},{ldap_base}',
        user_default_container=f'cn=users,ou=ou{ou_index},{ldap_base}',
        group_dn=f'cn=groups,ou=ou{ou_index},{ldap_base}',
        group_username=f'group1-ou{ou_index}',
        group_default_container=f'cn=groups,ou=ou{ou_index},{ldap_base}',
    )
