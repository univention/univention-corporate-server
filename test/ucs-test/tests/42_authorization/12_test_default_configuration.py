from pprint import pprint

import pytest

from univention.authorization.authorization import GuardianAuthorizationClient
from univention.testing import ucr


@pytest.fixture(scope='module')
def auth_client(ucr_session: ucr):
    fqdn = ucr_session.get('directory/manager/delegative-administration/guardian/host', f'{ucr_session["hostname"]}.{ucr_session["domainname"]}')
    keycloak_fqdn = ucr_session.get('directory/manager/delegative-administration/guardian/keycloak', ucr_session.get("keycloak/server/sso/fqdn", ''))
    assert keycloak_fqdn
    username = ucr_session.get('directory/manager/delegative-administration/guardian/user', 'Administrator')
    password = ucr_session.get('directory/manager/delegative-administration/guardian/password', 'univention')
    with GuardianAuthorizationClient(fqdn, keycloak_fqdn, username=username, password=password) as guardian_auth_client:
        yield guardian_auth_client


test_permissions_testdata = [
    pytest.param(
        {
            'actor': {
                'id': 'uid=Administrator,cn=users,dc=ucs,dc=test',
                'attributes': {
                    'dn': 'uid=Administrator,cn=users,dc=ucs,dc=test',
                },
                'roles': [
                    'udm:default-roles:domain-administrator',
                    'guardian:builtin:super-admin',
                ],
            },
            'targets': [
                {
                    'old_target': {
                        'id': 'uid=my_test_user,cn=users,dc=ucs,dc=test',
                        'attributes': {
                            'dn': 'uid=my_test_user,cn=users,dc=ucs,dc=test',
                            'objecttype': 'users/user',
                        },
                        'roles': [],
                    },
                    'new_target': None,
                },
            ],
            'contexts': [],
            'namespaces': [],
            'targeted_permissions_to_check': [
                'udm:users-user:create',
                'udm:users-user:modify',
                'udm:users-user:move',
                'udm:users-user:read',
                'udm:users-user:read-property-all',
                'udm:users-user:remove',
                'udm:users-user:rename',
                'udm:users-user:report-create',
                'udm:users-user:search',
                'udm:users-user:search-property-all',
                'udm:users-user:write-property-all',
            ],
            'extra_request_data': {},
            'expected_result': True,
        },
        id='udm:default-roles:domain-administrator_users/user_true',
    ),
    pytest.param(
        {
            'actor': {
                'id': 'uid=OuAdmin,cn=users,dc=ucs,dc=test',
                'attributes': {
                    'dn': 'uid=OuAdmin,cn=users,dc=ucs,dc=test',
                },
                'roles': [
                    'udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=bremen,dc=ucs,dc=test',
                ],
            },
            'targets': [
                {
                    'old_target': {
                        'id': 'ou=bremen,dc=ucs,dc=test',
                        'attributes': {
                            'dn': 'ou=bremen,dc=ucs,dc=test',
                            'objecttype': 'container/ou',
                        },
                        'roles': [],
                    },
                    'new_target': None,
                },
            ],
            'contexts': [
                'udm:position:contexts',
            ],
            'namespaces': [],
            'targeted_permissions_to_check': [
                'udm:container-ou:read',
                'udm:container-ou:read-property-all',
                'udm:container-ou:search',
                'udm:container-ou:search-property-all',
            ],
            'extra_request_data': {},
            'expected_result': True,
        },
        id='udm:default-roles:organizational-unit-admin_container/ou_true',
    ),
    pytest.param(
        {
            'actor': {
                'id': 'uid=OuAdmin,cn=users,dc=ucs,dc=test',
                'attributes': {
                    'dn': 'uid=OuAdmin,cn=users,dc=ucs,dc=test',
                },
                'roles': [
                    'udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=bremen,dc=ucs,dc=test',
                ],
            },
            'targets': [
                {
                    'old_target': {
                        'id': 'ou=berlin,dc=ucs,dc=test',
                        'attributes': {
                            'dn': 'ou=berlin,dc=ucs,dc=test',
                            'objecttype': 'container/ou',
                        },
                        'roles': [],
                    },
                    'new_target': None,
                },
            ],
            'contexts': [
                'udm:position:contexts',
            ],
            'namespaces': [],
            'targeted_permissions_to_check': [
                'udm:container-ou:read',
                'udm:container-ou:read-property-all',
                'udm:container-ou:search',
                'udm:container-ou:search-property-all',
            ],
            'extra_request_data': {},
            'expected_result': False,
        },
        id='udm:default-roles:organizational-unit-admin_container/ou_true',
    ),
]


@pytest.mark.parametrize('testdata', test_permissions_testdata)
def test_permissions(auth_client: GuardianAuthorizationClient, testdata: dict):
    pprint(testdata)

    response = auth_client.get_permissions(
        actor=testdata['actor'],
        targets=testdata['targets'],
        contexts=testdata['contexts'],
        namespaces=testdata['namespaces'],
        extra_request_data=testdata['extra_request_data'],
    )
    pprint(response)
    assert (
        set(testdata['targeted_permissions_to_check']).issubset(
            response['target_permissions'][0]['permissions'],
        )
        == testdata['expected_result']
    )

    response = auth_client.check_permissions(
        actor=testdata['actor'],
        targets=testdata['targets'],
        contexts=testdata['contexts'],
        namespaces=testdata['namespaces'],
        targeted_permissions_to_check=testdata['targeted_permissions_to_check'],
        extra_request_data=testdata['extra_request_data'],
    )
    pprint(response)

    assert response.get('actor_has_all_targeted_permissions') == testdata['expected_result']
