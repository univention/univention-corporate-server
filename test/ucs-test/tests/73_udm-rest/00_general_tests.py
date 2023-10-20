#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test various functions in the UDM REST API
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-directory-manager-rest

import subprocess
import time
from operator import itemgetter

import pytest

from univention.admin.rest.client import (
    UDM as UDMClient, Forbidden, PreconditionFailed, Unauthorized, UnprocessableEntity,
)
from univention.config_registry import ConfigRegistry, handler_set
from univention.lib.misc import custom_groupname
from univention.testing.udm import UDM, UCSTestUDM_CreateUDMObjectFailed
from univention.testing.utils import UCSTestDomainAdminCredentials


ucr = ConfigRegistry()
ucr.load()


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


def test_etag_last_modified(udm):
    userdn, user = udm.create_user()
    time.sleep(1)
    udm_client = UDMClient.test_connection()
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
    # assert 'If-Match' in str(exc)

    user.last_modified = last_modified
    user.etag = None
    with pytest.raises(PreconditionFailed) as exc:
        user.save()
    exc  # noqa: B018
    # assert 'If-Unmodified-Since' in str(exc)


@pytest.mark.parametrize('suffix', ['', 'ä'])
def test_create_modify_move_remove(random_string, suffix, ucr):
    if suffix:
        handler_set(['directory/manager/web/modules/users/user/properties/username/syntax=string'])
        subprocess.call(['systemctl', 'restart', 'univention-directory-manager-rest'])
        time.sleep(1)

    with UDM() as udm:
        username = random_string() + suffix
        userdn, user = udm.create_user(username=username)
        udm.verify_ldap_object(userdn)
        org_dn = userdn

        username = random_string() + suffix

        description = random_string()
        userdn = udm.modify_object('users/user', dn=userdn, description=description)
        udm.verify_ldap_object(userdn)
        assert userdn == org_dn

        userdn = udm.modify_object('users/user', dn=userdn, username=username)
        udm.verify_ldap_object(userdn)
        assert userdn != org_dn
        org_dn = userdn

        userdn = udm.move_object('users/user', dn=userdn, position=ucr['ldap/base'])
        udm.verify_ldap_object(userdn)
        assert userdn != org_dn

        udm.remove_object('users/user', dn=userdn)
        udm.verify_ldap_object(userdn, should_exist=False)


@pytest.mark.parametrize('name', [
    '''a !"#$%&'"()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~z''',
    'foo//bar',
    'foobär',
])
def test_special_characters_in_dn(name):
    with UDM() as udm:
        container = udm.create_object('container/cn', name=name)

        udm_client = UDMClient.test_connection()
        obj = udm_client.get('container/cn').get(container)
        print(obj)
        assert obj


@pytest.mark.parametrize('language,error_message', [
    ('en-US', 'The property gecos has an invalid value: Field must only contain ASCII characters!'),
    ('de-DE', 'Die Eigenschaft gecos hat einen ungültigen Wert: Der Wert darf nur ASCII Buchstaben enthalten!'),
])
def test_translation(language, error_message):
    with UDM(language=language) as udm:
        with pytest.raises(UCSTestUDM_CreateUDMObjectFailed) as exc:
            userdn, user = udm.create_user(gecos='foobär')

        assert error_message in str(exc.value)


def test_error_handling(udm, ldap_base):
    udm_client = UDMClient.test_connection()
    users_user = udm_client.get('users/user')

    # invalid query parameter
    with pytest.raises(UnprocessableEntity) as exc:
        list(users_user.search(position='cn=does,dc=not,dc=exists', scope='blah', filter='invalidone'))

    assert sorted(exc.value.error_details['error'], key=itemgetter('location')) == sorted([
        {'location': ['query', 'scope'], 'message': "Value has to be one of ['sub', 'one', 'base', 'base+one']", 'type': 'value_error'},
        {'location': ['query', 'filter'], 'message': 'Not a valid LDAP search filter.', 'type': 'value_error'},
        {'location': ['query', 'position'], 'message': f'The ldap base is invalid. Use {ldap_base.lower()}.', 'type': 'value_error'},
    ], key=itemgetter('location'))

    # not existing search base underneath of the real LDAP base
    users_user = udm_client.get('users/user')  # FIXME: weird stuff is going on, the new search uses the old params
    with pytest.raises(UnprocessableEntity) as exc:
        list(users_user.search(position=f'cn=does,cn=not,cn=exists,{ldap_base}'))
    assert exc.value.error_details['error'] == [{'location': ['query', 'position'], 'message': f'LDAP object cn=does,cn=not,cn=exists,{ldap_base} could not be found.\nIt possibly has been deleted or moved. Please update your search results and open the object again.', 'type': 'value_error'}]

    users_user = udm_client.get('users/user')  # FIXME: weird stuff is going on, the new search uses the old params
    userdn, username = udm.create_user(wait_for=False)
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
