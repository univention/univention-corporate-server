#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Test Guardian conditions in management/univention-directory-manager-modules/conditions


import base64
import json
from pathlib import Path
from pprint import pprint
from time import sleep
from typing import Any

import pytest

from univention.authorization.authorization import GuardianAuthorizationClient
from univention.authorization.management import GuardianManagementClient
from univention.testing import ucr
from univention.testing.strings import random_string


# Guardian needs some time to prozess the creation
# of the needed objects. (async calls ...)
# So we wait a little bit ...
GUARDIAN_WAIT_TIME = 30


@pytest.fixture(scope='module')
def auth_client(ucr_session: ucr):
    fqdn = ucr_session.get('directory/manager/delegative-administration/guardian/host', f'{ucr_session["hostname"]}.{ucr_session["domainname"]}')
    keycloak_fqdn = ucr_session.get('directory/manager/delegative-administration/guardian/keycloak', ucr_session.get("keycloak/server/sso/fqdn", ''))
    assert keycloak_fqdn
    username = ucr_session.get('directory/manager/delegative-administration/guardian/user', 'Administrator')
    password = ucr_session.get('directory/manager/delegative-administration/guardian/password', 'univention')
    with GuardianAuthorizationClient(fqdn, keycloak_fqdn, username=username, password=password) as guardian_auth_client:
        yield guardian_auth_client


@pytest.fixture(scope='module')
def mgmt_client(ucr_session: ucr):
    management_url = f'https://{ucr_session["hostname"]}.{ucr_session["domainname"]}/guardian/management'
    username = 'Administrator'
    password = 'univention'
    keycloak_url = f'https://{ucr_session["keycloak/server/sso/fqdn"]}/realms/ucs/protocol/openid-connect/token'
    keycloak_client = 'guardian-scripts'

    with GuardianManagementClient(
        management_url,
        username,
        password,
        keycloak_url,
        keycloak_client,
    ) as guardian_mgmt_client:
        yield guardian_mgmt_client


@pytest.fixture(scope='module')
def guardian_config(mgmt_client: GuardianManagementClient):
    rnd_string = random_string(5)
    app_name = f'test-app-{rnd_string}'
    mgmt_client.create_app(app_name=app_name, display_name=app_name)

    namespace_name = f'test-ns-{rnd_string}'
    mgmt_client.create_namespace(app_name=app_name, namespace_name=namespace_name, display_name=namespace_name)

    context_name = f'test-context-{rnd_string}'
    mgmt_client.create_context(
        app_name=app_name,
        namespace_name=namespace_name,
        context_name=context_name,
        display_name=context_name,
    )

    permission_name = f'test-perm-{rnd_string}'
    mgmt_client.create_permission(
        app_name=app_name,
        namespace_name=namespace_name,
        permission_name=permission_name,
        display_name=permission_name,
    )

    role_name = f'test-role-{rnd_string}'
    mgmt_client.create_role(
        app_name=app_name,
        namespace_name=namespace_name,
        role_name=role_name,
        display_name=role_name,
    )

    condition_dir = '/usr/share/univention-directory-manager-modules/conditions'
    path_list = Path(condition_dir).glob('*.json')
    conditions = []
    for json_file_name in path_list:
        condition_name_orig = json_file_name.stem
        condition_name = f'test_cond_{rnd_string}_{condition_name_orig}'
        condition_spec = None
        with open(json_file_name) as json_file:
            content = json_file.read()
            condition_spec = json.loads(content)

        condition_code = None
        with open(f'{condition_dir}/{condition_name_orig}.rego') as rego_file:
            content = rego_file.read()
            content = content.replace(
                f'udm:conditions:{condition_name_orig}', f'{app_name}:{namespace_name}:{condition_name}',
            )
            condition_code = base64.b64encode(content.encode()).decode()

        if condition_spec and condition_code:
            mgmt_client.create_condition(
                app_name=app_name,
                namespace_name=namespace_name,
                condition_name=condition_name,
                display_name=condition_spec['display_name'],
                documentation=condition_spec['documentation'],
                code=condition_code,
                parameters=condition_spec['parameters'],
            )
            conditions.append(
                {
                    'name_orig': condition_name_orig,
                    'name': condition_name,
                    'app_name': app_name,
                    'namespace_name': namespace_name,
                    'parameters': condition_spec['parameters'],
                },
            )

    guardian_config = {
        'rnd_string': rnd_string,
        'app_name': app_name,
        'namespace_name': namespace_name,
        'context_name': context_name,
        'permission_name': permission_name,
        'role_name': role_name,
        'conditions': conditions,
    }

    return guardian_config


@pytest.fixture
def condition(mgmt_client: GuardianManagementClient, guardian_config: dict, request: Any):
    # TODO: Fix evil hack!
    if request.param[0] == 'target_position_from_context':
        for i in range(len(request.param[1])):
            if request.param[1][i]['name'] == 'position':
                request.param[1][i]['value'] = f"{guardian_config['app_name']}:{guardian_config['namespace_name']}:{guardian_config['context_name']}"

    condition: dict = next((x for x in guardian_config['conditions'] if x['name_orig'] == request.param[0]), None)
    capability_name = f'test_capability_{condition["name"]}'
    mgmt_client.create_role_capability_mapping(
        app_name=guardian_config['app_name'],
        namespace_name=guardian_config['namespace_name'],
        name=capability_name,
        display_name=capability_name,
        role=guardian_config['role_name'],
        permissions=[guardian_config['permission_name']],
        conditions=[
            {
                'app_name': guardian_config['app_name'],
                'namespace_name': guardian_config['namespace_name'],
                'name': condition['name'],
                'parameters': request.param[1],
            },
        ],
        relation='AND',
    )

    yield condition['name_orig']

    mgmt_client.delete_role_capability_mapping(
        guardian_config['app_name'],
        guardian_config['namespace_name'],
        capability_name,
    )


@pytest.fixture
def request_data(guardian_config: dict, request: Any):
    if isinstance(request.param, tuple):
        target_attributes = request.param[0]
        actor_role_context_value = request.param[1]
    elif isinstance(request.param, dict):
        target_attributes = request.param
        actor_role_context_value = None
    else:
        raise ValueError()

    data = {
        'namespaces': [
            {
                'app_name': guardian_config['app_name'],
                'name': guardian_config['namespace_name'],
            },
        ],
        'actor': {
            'id': 'uid=Administrator,cn=users,dc=ucs,dc=test',
            'roles': [
                {
                    'app_name': guardian_config['app_name'],
                    'namespace_name': guardian_config['namespace_name'],
                    'name': guardian_config['role_name'],
                    'context': {
                        'app_name': guardian_config['app_name'],
                        'namespace_name': guardian_config['namespace_name'],
                        'name': guardian_config['context_name'],
                    },
                },
            ],
            'attributes': {
                'id': 'uid=Administrator,cn=users,dc=ucs,dc=test',
            },
        },
        'targets': [
            {
                'old_target': {
                    'id': 'my_test_target',
                    'attributes': target_attributes,
                    'roles': [],
                },
                'new_target': {
                    'id': 'my_test_target',
                    'attributes': target_attributes,
                    'roles': [],
                },
            },
        ],
        'targeted_permissions_to_check': [
            {
                'app_name': guardian_config['app_name'],
                'namespace_name': guardian_config['namespace_name'],
                'name': guardian_config['permission_name'],
            },
        ],
        'general_permissions_to_check': [],
        'contexts': [
            {
                'app_name': guardian_config['app_name'],
                'namespace_name': guardian_config['namespace_name'],
                'name': guardian_config['context_name'],
            },
        ],
        'extra_request_data': {
            'actor_roles': [
                {
                    'app_name': guardian_config['app_name'],
                    'namespace_name': guardian_config['namespace_name'],
                    'name': guardian_config['role_name'],
                    'context': {
                        'app_name': guardian_config['app_name'],
                        'namespace_name': guardian_config['namespace_name'],
                        'name': guardian_config['context_name'],
                        'value': actor_role_context_value,
                    },
                },
            ],
        } if actor_role_context_value else {},
    }
    pprint(data)
    return data


@pytest.fixture
def expected_result(request: Any) -> bool:
    return request.param


target_property_value_compares_testdata = [
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': '=='}, {'name': 'value', 'value': 'testvalue'}]),
            {'properties': {'testproperty': 'testvalue'}},
            True,
            id='==_true',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': '=='}, {'name': 'value', 'value': 'testvalue'}]),
            {'properties': {'testproperty': 'wrongtestvalue'}},
            False,
            id='==_false',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': '!='}, {'name': 'value', 'value': 'testvalue'}]),
            {'properties': {'testproperty': 'wrongtestvalue'}},
            True,
            id='!=_true',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': '!='}, {'name': 'value', 'value': 'testvalue'}]),
            {'properties': {'testproperty': 'testvalue'}},
            False,
            id='!=_false',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': '==-i'}, {'name': 'value', 'value': 'testvalue'}]),
            {'properties': {'testproperty': 'TESTVALUE'}},
            True,
            id='==-i_true',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': '==-i'}, {'name': 'value', 'value': 'testvalue'}]),
            {'properties': {'testproperty': 'WRONGTESTVALUE'}},
            False,
            id='==-i_false',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': '!=-i'}, {'name': 'value', 'value': 'testvalue'}]),
            {'properties': {'testproperty': 'WRONGTESTVALUE'}},
            True,
            id='!=-i_true',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': '!=-i'}, {'name': 'value', 'value': 'testvalue'}]),
            {'properties': {'testproperty': 'TESTVALUE'}},
            False,
            id='!=-i_false',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': 'regex-match'}, {'name': 'value', 'value': r'^[^@]+@[^@]+\.[^@]+$'}]),
            {'properties': {'testproperty': 'foo@bar.org'}},
            True,
            id='regex-match_true',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': 'regex-match'}, {'name': 'value', 'value': r'^[^@]+@[^@]+\.[^@]+$'}]),
            {'properties': {'testproperty': 'foo [at] bar.org'}},
            False,
            id='regex-match_false',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': 'regex-nomatch'}, {'name': 'value', 'value': r'^[^@]+@[^@]+\.[^@]+$'}]),
            {'properties': {'testproperty': 'foo [at] bar.org'}},
            True,
            id='regex-nomatch_true',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': 'regex-nomatch'}, {'name': 'value', 'value': r'^[^@]+@[^@]+\.[^@]+$'}]),
            {'properties': {'testproperty': 'foo@bar.org'}},
            False,
            id='regex-nomatch_false',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': 'regex-match-i'}, {'name': 'value', 'value': r'^[a-z]+$'}]),
            {'properties': {'testproperty': 'TESTVALUE'}},
            True,
            id='regex-match-i_true',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': 'regex-match-i'}, {'name': 'value', 'value': r'^[a-z]+$'}]),
            {'properties': {'testproperty': 'WRONG-TESTVALUE'}},
            False,
            id='regex-match-i_false',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': 'regex-nomatch-i'}, {'name': 'value', 'value': r'^[a-z]+$'}]),
            {'properties': {'testproperty': 'WRONG-TESTVALUE'}},
            True,
            id='regex-nomatch-i_true',
        )
    ),
    (
        pytest.param(
            ('target_property_value_compares', [{'name': 'property', 'value': 'testproperty'}, {'name': 'operator', 'value': 'regex-nomatch-i'}, {'name': 'value', 'value': r'^[a-z]+$'}]),
            {'properties': {'testproperty': 'TESTVALUE'}},
            False,
            id='regex-nomatch-i_false',
        )
    ),
]


@pytest.mark.parametrize(
    'condition,request_data,expected_result',
    target_property_value_compares_testdata,
    indirect=True,
)
def test_target_property_value_compares(
    condition: str, request_data: dict, expected_result: bool, auth_client: GuardianAuthorizationClient,
):
    assert condition
    sleep(GUARDIAN_WAIT_TIME)  # Give Guardian some time to process the condition. Is not the fastest ...
    response = auth_client.post('/permissions/check', request_data).json()
    assert response.get('actor_has_all_targeted_permissions') == expected_result


target_object_type_equals_testdata = [
    (
        pytest.param(
            ('target_object_type_equals', [{'name': 'objecttype', 'value': 'users/user'}]),
            {'objecttype': 'users/user'},
            True,
            id='true',
        )
    ),
    (
        pytest.param(
            ('target_object_type_equals', [{'name': 'objecttype', 'value': 'users/user'}]),
            {'objecttype': 'groups/group'},
            False,
            id='false',
        )
    ),
]


@pytest.mark.parametrize(
    'condition,request_data,expected_result',
    target_object_type_equals_testdata,
    indirect=True,
)
def test_target_object_type_equals(
    condition: str, request_data: dict, expected_result: bool, auth_client: GuardianAuthorizationClient,
):
    assert condition
    sleep(GUARDIAN_WAIT_TIME)  # Give Guardian some time to process the condition. Is not the fastest ...
    response = auth_client.post('/permissions/check', request_data).json()
    pprint(response)
    assert response.get('actor_has_all_targeted_permissions') == expected_result


target_position_in_testdata = [
    (
        pytest.param(
            ('target_position_in', [{'name': 'scope', 'value': 'base'}, {'name': 'position', 'value': 'cn=users,dc=ucs,dc=test'}]),
            {'dn': 'uid=testuser,cn=users,dc=ucs,dc=test'},
            True,
            id='base_true',
        )
    ),
    (
        pytest.param(
            ('target_position_in', [{'name': 'scope', 'value': 'base'}, {'name': 'position', 'value': 'cn=users,dc=ucs,dc=test'}]),
            {'dn': 'uid=testuser,cn=ou1,cn=users,dc=ucs,dc=test'},
            False,
            id='base_false',
        )
    ),
    (
        pytest.param(
            ('target_position_in', [{'name': 'scope', 'value': 'subtree'}, {'name': 'position', 'value': 'dc=ucs,dc=test'}]),
            {'dn': 'uid=testuser,cn=users,dc=ucs,dc=test'},
            True,
            id='subtree_true',
        )
    ),
    (
        pytest.param(
            ('target_position_in', [{'name': 'scope', 'value': 'subtree'}, {'name': 'position', 'value': 'cn=users,dc=ucs,dc=test'}]),
            {'dn': 'uid=testuser,cn=ou1,cn=users,dc=ucs,dc=anothertest'},
            False,
            id='subtree_false',
        )
    ),

]


@pytest.mark.parametrize(
    'condition,request_data,expected_result',
    target_position_in_testdata,
    indirect=True,
)
def test_target_position_in(
    condition: str, request_data: dict, expected_result: bool, auth_client: GuardianAuthorizationClient,
):
    assert condition
    sleep(GUARDIAN_WAIT_TIME)  # Give Guardian some time to process the condition. Is not the fastest ...
    response = auth_client.post('/permissions/check', request_data).json()
    pprint(response)
    assert response.get('actor_has_all_targeted_permissions') == expected_result


target_position_from_context_testdata = [
    (
        pytest.param(
            ('target_position_from_context', [{'name': 'scope', 'value': 'base'}, {'name': 'position', 'value': 'FIXME'}]),
            ({'dn': 'uid=testuser,ou=bremen,cn=users,dc=ucs,dc=test'}, 'ou=bremen,cn=users,dc=ucs,dc=test'),
            True,
            id='base_true',
        )
    ),
    (
        pytest.param(
            ('target_position_from_context', [{'name': 'scope', 'value': 'base'}, {'name': 'position', 'value': 'FIXME'}]),
            ({'dn': 'uid=testuser,ou=berlin,cn=users,dc=ucs,dc=test'}, 'ou=bremen,cn=users,dc=ucs,dc=test'),
            False,
            id='base_false',
        )
    ),
    (
        pytest.param(
            ('target_position_from_context', [{'name': 'scope', 'value': 'subtree'}, {'name': 'position', 'value': 'FIXME'}]),
            ({'dn': 'uid=testuser,ou=teacher,ou=bremen,cn=users,dc=ucs,dc=test'}, 'ou=bremen,cn=users,dc=ucs,dc=test'),
            True,
            id='subtree_true',
        )
    ),
    (
        pytest.param(
            ('target_position_from_context', [{'name': 'scope', 'value': 'subtree'}, {'name': 'position', 'value': 'FIXME'}]),
            ({'dn': 'uid=testuser,ou=teacher,ou=berlin,cn=users,dc=ucs,dc=test'}, 'ou=bremen,cn=users,dc=ucs,dc=test'),
            False,
            id='subtree_false',
        )
    ),
]


@pytest.mark.parametrize(
    'condition,request_data,expected_result',
    target_position_from_context_testdata,
    indirect=True,
)
def test_target_position_from_context(
    condition: str, request_data: dict, expected_result: bool, auth_client: GuardianAuthorizationClient,
):
    assert condition
    sleep(GUARDIAN_WAIT_TIME)  # Give Guardian some time to process the condition. Is not the fastest ...
    response = auth_client.post('/permissions/check', request_data).json()
    pprint(response)
    assert response.get('actor_has_all_targeted_permissions') == expected_result
