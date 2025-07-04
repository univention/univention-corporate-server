#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check external management domain with delegated administration
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

from collections.abc import Generator
from pprint import pprint
from types import SimpleNamespace

import pytest
from keycloak import KeycloakAdmin

from univention.config_registry import ucr
from univention.testing.umc import ClientOIDC


pytestmark = pytest.mark.skipif(not ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='authz not activated')


#
# Helper
#
def get_user_nubus_id(username: str, kc_session: KeycloakAdmin) -> str:
    user_id = kc_session.get_user_id(username)
    user = kc_session.get_user(user_id=user_id)
    # WTF? Check if it is an error that array is returned!
    nubus_id = user['attributes'].get('nubus_id')[0]

    print(f'get_user_nubus_id -> Nubus ID for user {username} ({user_id}): {nubus_id}')

    return nubus_id


def delete_umc_user(kc_ucs_session: KeycloakAdmin, kc_master_session: KeycloakAdmin, master_username: str):
    master_user_id = kc_master_session.get_user_id(master_username)
    master_user = kc_master_session.get_user(user_id=master_user_id)

    print('delete_umc_user -> master_user:')
    pprint(master_user)

    nubus_id = master_user['attributes'].get('nubus_id')[0]
    umc_user_id = kc_ucs_session.get_user_id(f'oidc.{nubus_id}')

    print(f'delete_umc_user - Nubus ID for user {master_username} ({master_user_id}/{umc_user_id}): {nubus_id}')

    kc_ucs_session.delete_user(umc_user_id)


def get_kc_session(realm: str) -> KeycloakAdmin:
    return KeycloakAdmin(
        server_url=ucr['ucs/server/sso/uri'].strip('/'),
        username='Administrator',
        password='univention',
        realm_name=realm,
        user_realm_name='master',
        verify=True,
    )


#
# Fixtures
#
@pytest.fixture
def kc_ucs_session() -> KeycloakAdmin:
    return get_kc_session('ucs')


@pytest.fixture
def kc_master_session() -> KeycloakAdmin:
    return get_kc_session('master')


@pytest.fixture
def kc_master_with_preferred_username_mapper(kc_master_session: KeycloakAdmin) -> Generator[KeycloakAdmin, None, None]:
    client_id = kc_master_session.get_client_id('idp-client')
    mapper = {
        'name': 'username',
        'protocol': 'openid-connect',
        'protocolMapper': 'oidc-usermodel-property-mapper',
        'consentRequired': False,
        'config': {
            'userinfo.token.claim': 'true',
            'user.attribute': 'username',
            'id.token.claim': 'true',
            'access.token.claim': 'true',
            'claim.name': 'preferred_username',
            'jsonType.label': 'String',
        },
    }
    kc_master_session.add_mapper_to_client(client_id, mapper)

    yield kc_master_session

    mappers = kc_master_session.get_mappers_from_client(client_id)
    mapper_id = next(iter([x['id'] for x in mappers if x['name'] == 'username']))
    kc_master_session.remove_client_mapper(client_id, mapper_id)


@pytest.fixture
def kc_ucs_with_preferred_username_mapper(kc_ucs_session: KeycloakAdmin) -> Generator[KeycloakAdmin, None, None]:
    idp_alias = 'oidc'
    client_id = kc_ucs_session.get_client_id('https://master.ucs.test/univention/oidc/')
    idp_mapper = {
        'name': 'nubus_external_username',
        'identityProviderAlias': idp_alias,
        'identityProviderMapper': 'oidc-user-attribute-idp-mapper',
        'config': {'syncMode': 'FORCE', 'claim': 'preferred_username', 'user.attribute': 'nubus_external_username'},
    }
    client_mapper = {
        'name': 'nubus_external_username',
        'protocol': 'openid-connect',
        'protocolMapper': 'oidc-usermodel-attribute-mapper',
        'consentRequired': False,
        'config': {
            'introspection.token.claim': 'true',
            'userinfo.token.claim': 'true',
            'user.attribute': 'nubus_external_username',
            'id.token.claim': 'false',
            'lightweight.claim': 'false',
            'access.token.claim': 'false',
            'claim.name': 'nubus_external_username',
            'jsonType.label': 'String',
        },
    }
    kc_ucs_session.add_mapper_to_idp(idp_alias, idp_mapper)
    kc_ucs_session.add_mapper_to_client(client_id, client_mapper)

    yield kc_ucs_session

    idp_mappers = kc_ucs_session.get_idp_mappers(idp_alias)
    idp_mapper_id = next(iter([x['id'] for x in idp_mappers if x['name'] == 'nubus_external_username']))
    kc_ucs_session.raw_delete(f'admin/realms/ucs/identity-provider/instances/oidc/mappers/{idp_mapper_id}')
    mappers = kc_ucs_session.get_mappers_from_client(client_id)
    mapper_id = next(iter([x['id'] for x in mappers if x['name'] == 'nubus_external_username']))
    kc_ucs_session.remove_client_mapper(client_id, mapper_id)


@pytest.fixture
def kc_master_without_username_mapper(kc_master_session: KeycloakAdmin) -> Generator[KeycloakAdmin, None, None]:
    client_id = kc_master_session.get_client_id('idp-client')
    mappers = kc_master_session.get_mappers_from_client(client_id)

    username_mapper = None
    for mapper in mappers:
        if mapper['name'] == 'username':
            username_mapper = mapper
            kc_master_session.remove_client_mapper(client_id, username_mapper['id'])
            break

    # if not username_mapper:
    #     raise Exception('No username mapper found!')

    yield kc_master_session

    if username_mapper:
        kc_master_session.add_mapper_to_client(client_id, username_mapper)


@pytest.fixture
def manager_ou1_umc(
    kc_ucs_session: KeycloakAdmin,
    kc_master_session: KeycloakAdmin,
) -> Generator[ClientOIDC, None, None]:
    client = ClientOIDC()
    client.authenticate('manager-ou1', 'univention', kc_idp_hint='oidc')

    yield client

    delete_umc_user(kc_ucs_session=kc_ucs_session, kc_master_session=kc_master_session, master_username='manager-ou1')


@pytest.fixture
def manager_ou2_umc(
    kc_ucs_session: KeycloakAdmin,
    kc_master_session: KeycloakAdmin,
) -> Generator[ClientOIDC, None, None]:
    client = ClientOIDC()
    client.authenticate('manager-ou2', 'univention', kc_idp_hint='oidc')

    yield client

    delete_umc_user(kc_ucs_session=kc_ucs_session, kc_master_session=kc_master_session, master_username='manager-ou2')


@pytest.fixture
def manager_all_umc(
    kc_ucs_session: KeycloakAdmin,
    kc_master_session: KeycloakAdmin,
) -> Generator[ClientOIDC, None, None]:
    client = ClientOIDC()
    client.authenticate('manager-all', 'univention', kc_idp_hint='oidc')

    yield client

    delete_umc_user(kc_ucs_session=kc_ucs_session, kc_master_session=kc_master_session, master_username='manager-all')


#
# Tests
#
def test_manager_ou1_oidc_umc_login(manager_ou1_umc: ClientOIDC, kc_master_session: KeycloakAdmin):
    # umc user name per default is oidc.nubus_id
    nubus_id = get_user_nubus_id('manager-ou1', kc_master_session)
    assert manager_ou1_umc.cookies['UMCUsername'] == nubus_id
    res = manager_ou1_umc.umc_get('modules')
    assert res.data.get('modules')


def test_manager_ou1_default_container_umc(manager_ou1_umc, ou):
    res = manager_ou1_umc.umc_command('udm/containers', {'objectType': 'users/user'}, 'users/user').result
    assert {x['id'] for x in res} == {ou.user_default_container}
    res = manager_ou1_umc.umc_command('udm/containers', {'objectType': 'groups/group'}, 'groups/group').result
    assert {x['id'] for x in res} == {ou.group_default_container}


def test_manager_all_default_container_umc(manager_all_umc: ClientOIDC, ou: SimpleNamespace):
    assert ou
    res = manager_all_umc.umc_command('udm/containers', {'objectType': 'users/user'}, 'users/user').result
    assert len(res) == 15, res


def test_username_mapper(kc_ucs_session: KeycloakAdmin, kc_master_session: KeycloakAdmin, manager_ou1_umc: ClientOIDC):
    """
    Test the mapping of the username from manager-ou1 to oidc.<NUBUS_ID> on federated login.

    It is configured in setup-external-mapping-domain.py -> create_idp_in_ucs_keycloak()except KeyError
    """
    assert manager_ou1_umc

    master_nubus_id = get_user_nubus_id('manager-ou1', kc_master_session)
    ucs_nubus_id = get_user_nubus_id(f'oidc.{master_nubus_id}', kc_ucs_session)

    assert master_nubus_id == ucs_nubus_id


def test_missing_username_mapper(
    kc_master_without_username_mapper: KeycloakAdmin,
    kc_ucs_session: KeycloakAdmin,
    manager_ou1_umc: ClientOIDC,
):
    """
    Test the login without username protocol mapper.

    The default mapper could be found in setup-external-mapping-domain.py -> create_oidc_client_external_keycloak()
    """
    assert manager_ou1_umc

    master_nubus_id = get_user_nubus_id('manager-ou1', kc_master_without_username_mapper)
    umc_nubus_id = get_user_nubus_id(f'oidc.{master_nubus_id}', kc_ucs_session)
    assert master_nubus_id == umc_nubus_id

    umc_user_id = kc_ucs_session.get_user_id(f'oidc.{master_nubus_id}')
    umc_user = kc_ucs_session.get_user(umc_user_id)

    print('test_missing_username_mapper -> umc_user')
    pprint(umc_user)

    assert not umc_user['attributes'].get('nubus_external_username')


def test_optional_preferred_username(
    kc_master_with_preferred_username_mapper: KeycloakAdmin,
    kc_ucs_with_preferred_username_mapper: KeycloakAdmin,
    manager_ou1_umc: ClientOIDC,
):
    """Test login and UMC username if preferred_username is configured"""
    assert manager_ou1_umc.cookies['UMCUsername'] == 'manager-ou1'


@pytest.mark.skip(reason='Senseless since Nubus roles came over Keycloak group attribute!')
def test_roles_over_kc(manager_ou2_umc: ClientOIDC, kc_master_session: KeycloakAdmin, kc_ucs_session: KeycloakAdmin):
    assert manager_ou2_umc

    master_nubus_id = get_user_nubus_id('manager-ou2', kc_master_session)
    umc_nubus_id = get_user_nubus_id(f'oidc.{master_nubus_id}', kc_ucs_session)
    assert master_nubus_id == umc_nubus_id

    umc_user_id = kc_ucs_session.get_user_id(f'oidc.{master_nubus_id}')
    umc_user = kc_ucs_session.get_user(umc_user_id)

    print('test_roles_over_kc -> umc_user:')
    pprint(umc_user)

    umc_user_groups = kc_ucs_session.get_user_groups(user_id=umc_user_id, brief_representation=False)

    print('test_roles_over_kc -> umc_user_groups:')
    pprint(umc_user_groups)

    pytest.fail('...')
