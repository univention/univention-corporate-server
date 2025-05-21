#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import pytest

from univention.admin.rest.client import UDM as UDM_REST, BadRequest, Forbidden
from univention.config_registry import ucr as _ucr
from univention.testing import utils


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/rest/enable-delegative-administration'), reason='authz not activated')


def create_udm_rest_client(username):
    return UDM_REST('https://%(hostname)s.%(domainname)s/univention/udm/' % _ucr, username=username, password=utils.UCSTestDomainAdminCredentials().bindpw)


def generate_user(user_module, position, username):
    new_user = user_module.new(position=position)
    new_user.properties['username'] = username
    new_user.properties['password'] = 'univention'
    new_user.properties['lastname'] = 'foo'
    new_user.save()
    return new_user


@pytest.fixture
def dummy_username(random_username):
    udm = create_udm_rest_client('Administrator')
    user_module = udm.get('users/user')
    username = random_username()
    user = generate_user(user_module, 'cn=users,ou=ou1,dc=ucs,dc=test', username)
    yield username
    user.reload()
    user.delete()


@pytest.fixture
def dummy_groupname(random_username):
    udm = create_udm_rest_client('Administrator')
    group_module = udm.get('groups/group')
    group_name = random_username()
    group = group_module.new(position='cn=groups,ou=ou1,dc=ucs,dc=test')
    group.properties['name'] = group_name
    group.save()
    yield group_name
    group.reload()
    group.delete()


@pytest.mark.parametrize('username, position, expected', [
    ('Administrator', 'cn=users,dc=ucs,dc=test', True),
    ('Administrator', 'cn=users,ou=ou1,dc=ucs,dc=test', True),
    ('Administrator', 'ou=ou1,dc=ucs,dc=test', True),
    ('Administrator', 'dc=ucs,dc=test', True),
    ('ou1admin', 'cn=users,ou=ou1,dc=ucs,dc=test', True),
    ('ou1admin', 'ou=ou1,dc=ucs,dc=test', True),
    ('ou1admin', 'cn=users,dc=ucs,dc=test', False),
    ('ou1admin', 'dc=ucs,dc=test', False),
])
def test_create(username, position, expected, random_username):
    udm_rest = create_udm_rest_client(username)
    user_module = udm_rest.get('users/user')
    test_username = random_username()

    if expected:
        new_user = user_module.new(position=position)
        new_user.properties['username'] = test_username
        new_user.properties['password'] = 'univention'
        new_user.properties['lastname'] = 'foo'
        new_user.save()

        user = next(user_module.search(f'uid={test_username}', opened=True))
        assert user
        user.delete()
    else:
        with pytest.raises(Forbidden):
            new_user = user_module.new(position=position)
            new_user.properties['username'] = test_username
            new_user.properties['password'] = 'univention'
            new_user.properties['lastname'] = 'foo'
            new_user.save()


@pytest.mark.parametrize('username, position', [
    ('Administrator', 'cn=users,dc=ucs,dc=test'),
    ('Administrator', 'cn=users,ou=ou1,dc=ucs,dc=test'),
    ('Administrator', 'ou=ou1,dc=ucs,dc=test'),
    ('Administrator', 'dc=ucs,dc=test'),
    ('ou1admin', 'cn=users,ou=ou1,dc=ucs,dc=test'),
    ('ou1admin', 'ou=ou1,dc=ucs,dc=test'),
])
def test_delete(username, position, random_username):
    udm_rest = create_udm_rest_client(username)
    user_module = udm_rest.get('users/user')
    test_username = random_username()
    generate_user(user_module, position, test_username)
    user = next(user_module.search(f'uid={test_username}', opened=True))
    assert user

    user.delete()
    users = list(user_module.search(f'uid={test_username}', opened=True))
    assert users == []


@pytest.mark.parametrize('username', [
    ("Administrator"),
    ("ou1admin"),
])
def test_search(username, udm):
    udm_rest = create_udm_rest_client(username)
    user_module = udm_rest.get('users/user')
    user_list = list(user_module.search('uid=*'))

    if username == "Administrator":
        assert len(user_list) == len(udm.list_objects('users/user', properties=['DN']))
    if username == "ou1admin":
        assert len(user_list) < len(udm.list_objects('users/user', properties=['DN']))
        assert len(user_list) == len(udm.list_objects('users/user', properties=['DN'], position="ou=ou1"))


@pytest.mark.parametrize('username, target_position, expected', [
    ("Administrator", "cn=users,dc=ucs,dc=test", True),
    ("ou1admin", "cn=users,dc=ucs,dc=test", False),
    ("Administrator", "cn=users,ou=ou1,dc=ucs,dc=test", True),
    ("ou1admin", "cn=users,ou=ou1,dc=ucs,dc=test", True),
])
def test_move(username, target_position, expected, random_username):
    test_username = random_username()
    udm_rest = create_udm_rest_client(username)
    user_module = udm_rest.get('users/user')

    if expected:
        user = generate_user(user_module, "ou=ou1,dc=ucs,dc=test", test_username)
        user.move(target_position)
        user.delete()
    else:
        with pytest.raises(BadRequest):
            user = next(user_module.search('uid=*', opened=True))
            user.move(target_position)


@pytest.mark.parametrize('username', [
    ('Administrator'),
    ('ou1admin'),
])
def test_modify_attr(username, random_username):
    udm_rest = create_udm_rest_client(username)
    user_module = udm_rest.get('users/user')
    test_username = random_username()

    user = generate_user(user_module, position='cn=users,ou=ou1,dc=ucs,dc=test', username=test_username)

    user.properties['lastname'] = 'bar'
    user.save()

    user = next(user_module.search(f'uid={test_username}', opened=True))
    assert user.properties['lastname'] == 'bar'

    user.delete()


@pytest.mark.parametrize('username', [
    ('Administrator'),
    ('ou1admin'),
])
def test_mail_domain_create(username, random_string):
    udm_rest = create_udm_rest_client(username)
    mail_module = udm_rest.get('mail/domain')
    name = random_string()

    if username == 'ou1admin':
        with pytest.raises(Forbidden):
            mail_domain = mail_module.new()
            mail_domain.properties['name'] = name
            mail_domain.save()
    else:
        mail_domain = mail_module.new()
        mail_domain.properties['name'] = name
        mail_domain.save()

        domain = next(mail_module.search(f'name={name}', opened=True))
        assert domain
        domain.delete()


@pytest.mark.parametrize('username', [
    ('Administrator'),
    ('ou1admin'),
])
def test_mail_domain_delete(username, random_string, udm, ldap_base):
    name = random_string()
    dn = udm.create_object('mail/domain', name=name, position=f'cn=domain,cn=mail,{ldap_base}')
    udm_rest = create_udm_rest_client(username)
    mail_module = udm_rest.get('mail/domain')
    mail_domain = mail_module.get(dn)
    if username == 'ou1admin':
        with pytest.raises(BadRequest):
            mail_domain.delete()
    else:
        mail_domain.delete()


@pytest.mark.parametrize('username', [
    ('Administrator'),
    ('ou1admin'),
])
def test_write_to_user_guardian_roles(username, dummy_username):
    udm_rest = create_udm_rest_client(username)
    user_module = udm_rest.get('users/user')
    user = next(user_module.search(f'uid={dummy_username}', opened=True))
    user.properties['guardianRoles'].append('umc:udm:dummyrole')

    if username == 'Administrator':
        user.save()
        user.reload()
        assert user.properties['guardianRoles'] == ['umc:udm:dummyrole']
    if username == 'ou1admin':
        with pytest.raises(Forbidden):
            user.save()


@pytest.mark.parametrize('username', [
    ('Administrator'),
    ('ou1admin'),
])
def test_write_to_group_guardian_member_roles(username, dummy_groupname):
    udm_rest = create_udm_rest_client(username)
    group_module = udm_rest.get('groups/group')
    group = next(group_module.search(f'name={dummy_groupname}', opened=True))
    group.properties['guardianMemberRoles'].append('umc:udm:dummyrole')

    if username == 'Administrator':
        group.save()
        group.reload()
        assert group.properties['guardianMemberRoles'] == ['umc:udm:dummyrole']
    if username == 'ou1admin':
        with pytest.raises(Forbidden):
            group.save()
