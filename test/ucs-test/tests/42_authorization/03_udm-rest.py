#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous
import pytest

from univention.admin.rest.client import UDM as UDM_REST, HTTPError
from univention.config_registry import ConfigRegistry
from univention.testing import utils


def create_udm_rest_client(username):
    ucr = ConfigRegistry()
    ucr.load()
    return UDM_REST('https://%(hostname)s.%(domainname)s/univention/udm/' % ucr, username=username, password=utils.UCSTestDomainAdminCredentials().bindpw)


def generate_user(user_module, position, username):
    new_user = user_module.new(position=position)
    new_user.properties['username'] = username
    new_user.properties['password'] = 'univention'
    new_user.properties['lastname'] = 'foo'
    new_user.save()
    return new_user


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
        with pytest.raises(HTTPError):
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
        user_list_ou1 = list(user_module.search('uid=*ou1*'))
        assert len(user_list) == len(user_list_ou1)


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
        with pytest.raises(HTTPError):
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
def test_mail_domain_create(username):
    udm_rest = create_udm_rest_client(username)
    mail_module = udm_rest.get('mail/domain')

    if username == 'ou1admin':
        with pytest.raises(HTTPError):
            mail_domain = mail_module.new()
            mail_domain.properties['name'] = 'test_mail_domain'
            mail_domain.save()
    else:
        mail_domain = mail_module.new()
        mail_domain.properties['name'] = 'test_mail_domain'
        mail_domain.save()

        domain = next(mail_module.search('name=test_mail_domain', opened=True))
        assert domain
        domain.delete()


@pytest.mark.parametrize('username', [
    ('Administrator'),
    ('ou1admin'),
])
def test_mail_domain_delete(username):

    #  Create domain to be deleted and admin udm_rest client for
    #  test cleanup
    admin_udm_rest = create_udm_rest_client('Administrator')
    admin_mail_module = admin_udm_rest.get('mail/domain')
    mail_domain = admin_mail_module.new()
    mail_domain.properties['name'] = 'test_mail_domain'
    mail_domain.save()

    udm_rest = create_udm_rest_client(username)
    mail_module = udm_rest.get('mail/domain')

    if username == 'ou1admin':
        with pytest.raises(HTTPError):
            mail_domain = next(mail_module.search('name=test_mail_domain', opened=True))
            mail_domain.delete()
    else:
        mail_domain = next(mail_module.search('name=test_mail_domain', opened=True))
        mail_domain.delete()
    if domains := list(admin_mail_module.search('name=test_mail_domain', opened=True)):
        domains[0].delete()
