#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test various functions in the UDM REST API
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-rest

import subprocess
import time
from operator import itemgetter

import pytest
import requests

from univention.admin.rest.client import (
    UDM as UDMClient, Forbidden, PreconditionFailed, Unauthorized, UnprocessableEntity,
)
from univention.config_registry import ucr
from univention.lib.misc import custom_groupname
from univention.testing.conftest import locale_available
from univention.testing.udm import UDM, UCSTestUDM_CreateUDMObjectFailed
from univention.testing.utils import UCSTestDomainAdminCredentials


if ucr.is_true('ad/member'):
    # REST server needs to reload UCR variables for "Domain Adminis" group name
    subprocess.call(['service', 'univention-directory-manager-rest', 'restart'])


class UDMClient(UDMClient):

    @classmethod
    def master_connection(cls, username, password):
        return cls.http('https://%s/univention/udm/' % (ucr['ldap/master'],), username, password)

    @classmethod
    def test_connection(cls):
        account = UCSTestDomainAdminCredentials(ucr)
        return cls.master_connection(account.username, account.bindpw)


@pytest.fixture()
def udm_client():
    return UDMClient.test_connection()


@pytest.fixture()
def udm_rest():
    with UDM() as udm:
        yield udm


def test_authentication(udm):
    userdn, user = udm.create_user()

    print('1. invalid password must be detected')
    with pytest.raises(Unauthorized):
        udm_client = UDMClient.master_connection(user, 'foobar')
        udm_client.get('users/user')

    print('2. regular domain user must not access the API')
    with pytest.raises(Forbidden):
        udm_client = UDMClient.master_connection(user, 'univention')
        udm_client.get('users/user')

    udm.modify_object('users/user', dn=userdn, groups='cn=%s,cn=groups,%s' % (custom_groupname('Domain Admins', ucr), ucr['ldap/base']))
    print('3. domain admin must be able to access the API')
    udm_client = UDMClient.master_connection(user, 'univention')
    udm_client.get('users/user')


def test_etag_after_create_via_post(udm, udm_client, random_string):
    """make sure POST a new user creates a etag"""
    User = udm_client.get('users/user')
    auth = (udm_client.username, udm_client.password)
    headers = {'Accept-Encoding': 'identity', 'Accept': 'application/json'}

    user = User.new()
    user.properties['username'] = random_string()
    user.properties['lastname'] = random_string()
    user.properties['password'] = 'univention'

    response = requests.post(User.uri, auth=auth, headers=dict(headers, **{'Content-Type': 'application/json'}), json=user.representation)
    assert response.status_code == 201
    uri = response.headers['Location']
    etag = response.headers.get('Etag')
    assert etag
    time.sleep(1)

    # ensure Etag is equal after creation
    assert requests.get(uri, auth=auth, headers=dict(headers, **{'If-None-Match': '"foobar"'})).status_code == 200
    response = requests.get(uri, auth=auth, headers=dict(headers, **{'If-None-Match': etag}))
    assert response.status_code == 304
    # ensure a 304 Not Modified also ships the same Etag
    assert response.headers['Etag'] == etag


def test_etag_after_modify_via_put(udm, udm_client):
    """make sure that changes to an object via PUT change the Etag and respect If-Match"""
    userdn, _username = udm.create_user()
    User = udm_client.get('users/user')
    user = User.get(userdn)
    uri = user.uri
    auth = (udm_client.username, udm_client.password)
    headers = {'Accept-Encoding': 'identity', 'Accept': 'application/json'}
    etag = user.etag

    data = requests.get(uri, auth=auth, headers=headers).json()
    data['properties']['description'] = 'asdf'
    assert requests.put(uri, auth=auth, headers=dict(headers, **{'Content-Type': 'application/json', 'If-Match': '"foobar"'}), json=data).status_code == 412
    response = requests.put(uri, auth=auth, headers=dict(headers, **{'Content-Type': 'application/json', 'If-Match': etag}), json=data)
    assert response.status_code == 204
    assert response.headers['Etag'] != etag
    assert requests.get(uri, auth=auth, headers=dict(headers, **{'If-None-Match': response.headers['Etag']})).status_code == 304


def test_etag_after_modify_via_patch(udm, udm_client):
    """make sure that changes to an object via PATCH change the Etag and respect If-Match"""
    userdn, _username = udm.create_user()
    User = udm_client.get('users/user')
    user = User.get(userdn)
    uri = user.uri
    auth = (udm_client.username, udm_client.password)
    headers = {'Accept-Encoding': 'identity', 'Accept': 'application/json'}
    etag = user.etag

    # make sure PATCH respects If-Match
    data = {'properties': {'description': 'foo'}}
    assert requests.patch(uri, auth=auth, headers=dict(headers, **{'Content-Type': 'application/json', 'If-Match': '"foobar"'}), json=data).status_code == 412
    response = requests.patch(uri, auth=auth, headers=dict(headers, **{'Content-Type': 'application/json', 'If-Match': etag}), json=data)
    assert response.status_code == 204
    assert response.headers['Etag'] != etag
    assert requests.get(uri, auth=auth, headers=dict(headers, **{'If-None-Match': response.headers['Etag']})).status_code == 304


def test_etag_last_modified_via_client(udm, udm_client):
    userdn, user = udm.create_user()
    time.sleep(1)
    user = udm_client.get('users/user').get(userdn)
    assert user.etag
    assert user.last_modified
    last_modified = user.last_modified
    user.last_modified = None
    udm.modify_object('users/user', dn=userdn, description='foo')
    time.sleep(1)
    user.properties['lastname'] = 'foobar'
    with pytest.raises(PreconditionFailed) as exc:
        user.save()
    assert 'If-Match' in str(exc.value)

    user.last_modified = last_modified
    user.etag = None
    with pytest.raises(PreconditionFailed) as exc:
        user.save()
    assert 'If-Unmodified-Since' in str(exc.value)


def test_etag_via_delete(udm, udm_client):
    userdn, _username = udm.create_user()
    User = udm_client.get('users/user')
    user = User.get(userdn)
    uri = user.uri
    auth = (udm_client.username, udm_client.password)
    headers = {'Accept-Encoding': 'identity', 'Accept': 'application/json'}
    etag = user.etag

    assert requests.delete(uri, auth=auth, headers=dict(headers, **{'If-Match': '"something"'})).status_code == 412
    assert requests.delete(uri, auth=auth, headers=dict(headers, **{'If-Match': etag})).status_code == 204


@pytest.mark.xfail(reason='Not working')
def test_etag_after_modification_of_external_referenced_object(udm, udm_client):
    group_dn, _group = udm.create_group()
    userdn, _username = udm.create_user(groups=[group_dn])
    User = udm_client.get('users/user')
    user = User.get(userdn)
    uri = user.uri
    auth = (udm_client.username, udm_client.password)
    headers = {'Accept-Encoding': 'identity', 'Accept': 'application/json'}
    etag = user.etag

    # make sure that changes to external references of an object (e.g. group memberships of users) also change the Etag
    udm.modify_object('groups/group', dn=group_dn, remove={'users': [user.dn]})
    response = requests.get(uri, auth=auth, headers=dict(headers, **{'If-None-Match': etag}))
    assert response.status_code == 200
    etag = response.headers['Etag']


@pytest.mark.parametrize('suffix', ['', 'ä'])
def test_create_modify_move_remove(random_string, suffix, ucr, udm_rest):
    if suffix:
        ucr.handler_set(['directory/manager/web/modules/users/user/properties/username/syntax=string'])
        subprocess.call(['systemctl', 'restart', 'univention-directory-manager-rest'])
        time.sleep(1)

    username = random_string() + suffix
    userdn, _user = udm_rest.create_user(username=username)
    udm_rest.verify_ldap_object(userdn)
    org_dn = userdn

    username = random_string() + suffix

    description = random_string()
    userdn = udm_rest.modify_object('users/user', dn=userdn, description=description)
    udm_rest.verify_ldap_object(userdn)
    assert userdn == org_dn

    userdn = udm_rest.modify_object('users/user', dn=userdn, username=username)
    udm_rest.verify_ldap_object(userdn)
    assert userdn != org_dn
    org_dn = userdn

    userdn = udm_rest.move_object('users/user', dn=userdn, position=ucr['ldap/base'])
    udm_rest.verify_ldap_object(userdn)
    assert userdn != org_dn

    udm_rest.remove_object('users/user', dn=userdn)
    udm_rest.verify_ldap_object(userdn, should_exist=False)


@pytest.mark.parametrize('name', [
    '''a !"#$%&'"()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~z''',
    'foo//bar',
    'foobär',
])
def test_special_characters_in_dn(name, udm_client, udm_rest):
    container = udm_rest.create_object('container/cn', name=name)
    obj = udm_client.get('container/cn').get(container)
    print(obj)
    assert obj


@locale_available()
@pytest.mark.parametrize('language,error_message', [
    ('en-US', 'The property gecos has an invalid value: GECOS: Field must only contain ASCII characters!'),
    ('de-DE', 'Die Eigenschaft gecos hat einen ungültigen Wert: GECOS: Der Wert darf nur ASCII Buchstaben enthalten!'),
])
def test_translation(language, error_message):
    with UDM(language=language) as udm:
        with pytest.raises(UCSTestUDM_CreateUDMObjectFailed) as exc:
            _userdn, _user = udm.create_user(gecos='foobär')

        assert error_message in str(exc.value)


def test_error_handling(udm, ldap_base, udm_client):
    users_user = udm_client.get('users/user')

    # missing required properties
    user = users_user.new()
    with pytest.raises(UnprocessableEntity) as exc:
        user.save()
    assert sorted(exc.value.error_details['error'], key=itemgetter('location')) == sorted([
        {'location': ['body', 'properties', 'username'], 'message': 'The property "username" is required.', 'type': 'value_error'},  # should be value_error.required
        {'location': ['body', 'properties', 'lastname'], 'message': 'The property "lastname" is required.', 'type': 'value_error'},  # should be value_error.required
        {'location': ['body', 'properties', 'password'], 'message': 'The property "password" is required.', 'type': 'value_error'},  # should be value_error.required
    ], key=itemgetter('location'))

    # invalid query parameter
    with pytest.raises(UnprocessableEntity) as exc:
        list(users_user.search(position='cn=does,dc=not,dc=exists', scope='blah', filter='invalidone'))

    assert sorted(exc.value.error_details['error'], key=itemgetter('location')) == sorted([
        {'location': ['query', 'scope'], 'message': "Value has to be one of ['sub', 'one', 'base', 'base+one']", 'type': 'value_error'},
        {'location': ['query', 'filter'], 'message': 'Not a valid LDAP search filter.', 'type': 'value_error'},
        {'location': ['query', 'position'], 'message': f'The ldap base is invalid. Use {ldap_base.lower()}.', 'type': 'value_error'},
    ], key=itemgetter('location'))

    # not existing search base underneath of the real LDAP base
    with pytest.raises(UnprocessableEntity) as exc:
        list(users_user.search(position=f'cn=does,cn=not,cn=exists,{ldap_base}'))
    assert exc.value.error_details['error'] == [{'location': ['query', 'position'], 'message': f'LDAP object cn=does,cn=not,cn=exists,{ldap_base} could not be found.\nIt possibly has been deleted or moved. Please update your search results and open the object again.', 'type': 'value_error'}]

    userdn, _username = udm.create_user(wait_for=False)
    user = users_user.get(userdn)

    # prohibited usernames
    udm.create_object('settings/prohibited_username', name='udm-rest-test', usernames=['root2'])
    user.properties['username'] = 'root2'
    with pytest.raises(UnprocessableEntity) as exc:
        user.save()
    assert sorted(exc.value.error_details['error'], key=itemgetter('location')) == sorted([{'location': ['body', 'properties', 'username'], 'message': 'Prohibited username: root2.', 'type': 'value_error'}], key=itemgetter('location'))

    # two different layers of errors are combined (UDM syntax and UDM REST API type errors)
    user.properties['description'] = ['foo']  # singlevalue
    user.properties['e-mail'] = 'foo@example.com'  # multivalue
    user.properties['gecos'] = 'foobär'  # invalid value
    with pytest.raises(UnprocessableEntity) as exc:
        user.save()
    assert sorted(exc.value.error_details['error'], key=itemgetter('location')) == sorted([
        {'location': ['body', 'properties', 'gecos'], 'message': 'The property gecos has an invalid value: Field must only contain ASCII characters!', 'type': 'value_error'},
        {'location': ['body', 'properties', 'description'], 'message': 'The property description has an invalid value: Value must be of type string not list.', 'type': 'value_error'},  # should be type_error
        {'location': ['body', 'properties', 'e-mail'], 'message': 'The property e-mail has an invalid value: Value must be of type array not str.', 'type': 'value_error'},  # should be type_error
    ], key=itemgetter('location'))

    # broken / incomplete representation
    user.representation.update({'properties': {}, 'policies': []})
    user.representation.pop('position')
    with pytest.raises(UnprocessableEntity) as exc:
        user.save()
    assert sorted(exc.value.error_details['error'], key=itemgetter('location')) == sorted([
        {'location': ['body', 'position'], 'message': 'Argument required', 'type': 'value_error'},  # should be value_error.required
        {'location': ['body', 'policies'], 'message': 'Not a "dict"', 'type': 'value_error'},  # should be type_error
    ], key=itemgetter('location'))
