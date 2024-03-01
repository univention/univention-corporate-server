#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test univention-keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import json
import os
from subprocess import CalledProcessError

import pytest
from keycloak.exceptions import KeycloakGetError
from utils import run_command

from univention.testing.strings import random_int, random_string
from univention.testing.utils import wait_for_listener_replication
from univention.udm.binary_props import Base64Bzip2BinaryProperty


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_create_oidc_client(keycloak_administrator_connection):
    """Creates and delete OIDC client in Keycloak"""
    client_id = 'foo-cli'
    args = ['univention-keycloak', 'oidc/rp', 'create', '--app-url=', client_id]
    run_command(args)
    keycloak_client_id = keycloak_administrator_connection.get_client_id(client_id)
    if not keycloak_client_id:
        raise RuntimeError(f'Failed to create {client_id} OIDC client')
    keycloak_administrator_connection.delete_client(keycloak_client_id)
    assert not keycloak_administrator_connection.get_client_id(client_id)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_upgrade_config_status(keycloak_app_version):
    """no upgrade needed after installation"""
    upgrades = run_command(['univention-keycloak', 'upgrade-config', '--json', '--get-upgrade-steps'])
    upgrades = json.loads(upgrades)
    assert not upgrades
    # no pending upgrades
    upgrades = run_command(['univention-keycloak', 'domain-config', '--json', '--get'])
    upgrades = json.loads(upgrades)
    assert upgrades.get('domain_config_version')
    assert upgrades.get('domain_config_init')


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_upgrade_config_pending_upgrades(upgrade_status_obj):
    """
    remove domain config version and checks for updates
    there should be at least one update
    """
    data = json.loads(upgrade_status_obj.props.data.raw)
    del data['domain_config_version']
    raw_value = json.dumps(data).encode('ascii')
    upgrade_status_obj.props.data = Base64Bzip2BinaryProperty('data', raw_value=raw_value)
    upgrade_status_obj.save()
    wait_for_listener_replication()
    pending_upgrades = run_command(['univention-keycloak', 'upgrade-config', '--json', '--get-upgrade-steps'])
    pending_upgrades = json.loads(pending_upgrades)
    assert len(pending_upgrades) > 0


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_user_attribute_ldap_mapper(keycloak_administrator_connection):
    # create
    name = random_string()
    parent_id = keycloak_administrator_connection.get_components(query={'name': 'ldap-provider', 'type': 'org.keycloak.storage.UserStorageProvider'})[0]['id']
    run_command(['univention-keycloak', 'user-attribute-ldap-mapper', 'create', name])
    query = {'parent': parent_id, 'type': 'org.keycloak.storage.ldap.mappers.LDAPStorageMapper', 'name': name}
    mapper = keycloak_administrator_connection.get_components(query=query)
    assert len(mapper) == 1
    mapper = mapper[0]
    assert mapper['providerId'] == 'user-attribute-ldap-mapper'
    assert mapper['config']['ldap.attribute'] == [name]
    assert mapper['config']['user.model.attribute'] == [name]
    # get
    out = run_command(['univention-keycloak', 'user-attribute-ldap-mapper', 'get', '--json'])
    out = json.loads(out)
    assert name in out
    # delete
    run_command(['univention-keycloak', 'user-attribute-ldap-mapper', 'delete', name])
    mapper = keycloak_administrator_connection.get_components(query=query)
    assert len(mapper) == 0


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_saml_client_user_attribute_mapper(keycloak_administrator_connection):
    # create
    name = random_string()
    clients = json.loads(run_command(['univention-keycloak', 'saml/sp', 'get', '--json']))
    assert len(clients) > 0, 'could find a saml cient, at least one for UMC should always be there'
    client = clients[0]
    # create
    run_command(
        [
            'univention-keycloak',
            'saml-client-user-attribute-mapper',
            'create',
            client,
            name,
            '--attribute-name',
            'xyz',
            '--user-attribute',
            'xyz',
        ]
    )
    # get
    mappers = json.loads(
        run_command(
            [
                'univention-keycloak',
                'saml-client-user-attribute-mapper',
                'get',
                client,
                '--all',
                '--json',
            ]
        )
    )
    mapper = next(x for x in mappers if x['name'] == name)
    assert mapper['protocol'] == 'saml'
    assert mapper['protocolMapper'] == 'saml-user-attribute-mapper'
    assert mapper['config']['user.attribute'] == 'xyz'
    assert mapper['config']['attribute.name'] == 'xyz'
    # delete
    run_command(['univention-keycloak', 'saml-client-user-attribute-mapper', 'delete', client, name])
    client_id = keycloak_administrator_connection.get_client_id(client)
    mappers = [x['name'] for x in keycloak_administrator_connection.get_client(client_id)['protocolMappers']]
    assert name not in mappers


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_messages():
    languages = json.loads(run_command(['univention-keycloak', 'messages', 'get-locales', '--json']))
    for lang in languages:
        key = random_string()
        value = random_string()
        # create
        run_command(['univention-keycloak', 'messages', 'set', lang, key, value])
        # get and check
        messages = json.loads(run_command(['univention-keycloak', 'messages', 'get', lang, '--json']))
        assert key in messages
        assert messages[key] == value
        # delete and check
        run_command(['univention-keycloak', 'messages', 'delete', lang, key])
        messages = json.loads(run_command(['univention-keycloak', 'messages', 'get', lang, '--json']))
        assert key not in messages


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_login_links():
    languages = json.loads(run_command(['univention-keycloak', 'messages', 'get-locales', '--json']))
    for lang in languages:
        existing_links = json.loads(run_command(['univention-keycloak', 'login-links', 'get', lang, '--json']))
        try:
            # create
            number = str(random_int(1, 12))
            desc = random_string()
            href = random_string()
            run_command(['univention-keycloak', 'login-links', 'set', lang, number, desc, href])
            # get and check
            links = json.loads(run_command(['univention-keycloak', 'login-links', 'get', lang, '--json']))
            assert number in links
            assert links[number]['description'] == desc
            assert links[number]['reference'] == href
            # delete and check
            run_command(['univention-keycloak', 'login-links', 'delete', lang, number])
            links = json.loads(run_command(['univention-keycloak', 'login-links', 'get', lang, '--json']))
            assert number not in links
        finally:
            # at least create everything that was there before
            for number in existing_links:
                run_command(
                    [
                        'univention-keycloak',
                        'login-links',
                        'set',
                        lang,
                        number,
                        existing_links[number]['description'],
                        existing_links[number]['reference'],
                    ],
                )


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_init_with_parameters(random_string, keycloak_admin_connection):
    realm_name = random_string()
    try:
        cmd = ['univention-keycloak', '--realm', realm_name, 'init', '--no-kerberos', '--no-starttls', '--frontchannel-logout-off']
        run_command(cmd)
        cmd = ['univention-keycloak', 'realms', 'get', '--all', '--json']
        realms = json.loads(run_command(cmd))
        realm = next(x for x in realms if x['id'] == realm_name)
        assert realm['realm'] == realm_name
        keycloak_admin_connection.realm_name = realm_name
        provider = keycloak_admin_connection.get_components(query={'type': 'org.keycloak.storage.UserStorageProvider', 'name': 'ldap-provider'})[0]
        assert provider['config']['startTls'] == ['false']
        assert provider['config']['allowKerberosAuthentication'] == ['false']
    finally:
        try:
            keycloak_admin_connection.delete_realm(realm_name=realm_name)
        except KeycloakGetError:
            pass


def test_bindpwd(admin_account):
    cmd = ['univention-keycloak', '--binduser', admin_account.username, '--bindpwd', admin_account.bindpw, 'realms', 'get']
    run_command(cmd)
    cmd = ['univention-keycloak', '--binduser', admin_account.username, '--bindpwd', "bindpw", 'realms', 'get']
    with pytest.raises(CalledProcessError):
        run_command(cmd)


@pytest.fixture()
def without_keycloak_secret():
    secret = '/etc/keycloak.secret'
    secret_tmp = f'{secret}.tmp'
    moved = False

    if os.path.isfile(secret):
        os.rename(secret, secret_tmp)
        moved = True

    yield

    if moved and os.path.isfile(secret_tmp):
        os.rename(secret_tmp, secret)


@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup')
def test_machine_account(without_keycloak_secret):
    cmd = ['univention-keycloak', 'realms', 'get']
    run_command(cmd)


@pytest.mark.roles('domaincontroller_slave', 'memberserver')
def test_machine_account_fails(without_keycloak_secret):
    cmd = ['univention-keycloak', 'realms', 'get']
    with pytest.raises(CalledProcessError):
        run_command(cmd)
