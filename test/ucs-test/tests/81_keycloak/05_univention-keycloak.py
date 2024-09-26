#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
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
        ],
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
            ],
        ),
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


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
@pytest.mark.parametrize("enable_user_events, expected", [
    (True, True),
    (False, False),
])
def test_init_with_user_events_flag(random_string, keycloak_admin_connection, enable_user_events, expected):
    """
    Test the initialization of a Keycloak realm with user events enabled or disabled.
    Verifies that the 'eventsEnabled' attribute is set correctly and 'jboss-logging' is in 'eventsListeners'.
    """
    realm_name = random_string()
    try:
        cmd = [
            'univention-keycloak',
            '--realm', realm_name,
            'init',
            '--enable-user-events' if enable_user_events else '',
        ]
        # Remove empty strings to avoid issues
        cmd = [arg for arg in cmd if arg]
        run_command(cmd)

        cmd = ['univention-keycloak', 'realms', 'get', '--all', '--json']
        realms = json.loads(run_command(cmd))

        realm = next((x for x in realms if x['id'] == realm_name), None)
        assert realm is not None, f"Realm {realm_name} was not found."

        assert realm['realm'] == realm_name, "Realm name does not match."

        # Verify that 'eventsEnabled' is set as expected
        assert realm.get('eventsEnabled') is expected, f"'eventsEnabled' should be {expected}."

        # Verify that 'jboss-logging' is in 'eventsListeners'
        assert "jboss-logging" in realm.get('eventsListeners', []), "'jboss-logging' should be in 'eventsListeners'."

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


def get_protocol_mappers(con, client_id):
    keycloak_id = con.get_client_id(client_id)
    client = con.get_client(keycloak_id)
    for pm in client['protocolMappers']:
        del pm['id']
    return keycloak_id, client['protocolMappers']


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_oidc_guardian_audience_mapper(random_string, keycloak_admin_connection):
    client_id = random_string()
    args = ['univention-keycloak', 'oidc/rp', 'create', '--add-guardian-audience-mapper', client_id]
    run_command(args)
    expected_mapper = {
        "name": "guardian-audience",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-audience-mapper",
        "consentRequired": False,
        "config": {
            "included.client.audience": "guardian",
            "id.token.claim": "false",
            "access.token.claim": "true",
            'userinfo.token.claim': 'false',
        },
    }
    try:
        keycloak_id, mappers = get_protocol_mappers(keycloak_admin_connection, client_id)
        assert expected_mapper in mappers
    finally:
        if keycloak_id:
            keycloak_admin_connection.delete_client(keycloak_id)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_oidc_dn_mapper(random_string, keycloak_admin_connection):
    client_id = random_string()
    args = ['univention-keycloak', 'oidc/rp', 'create', '--add-dn-mapper', client_id]
    run_command(args)
    expected_mapper = {
        "name": "dn",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-usermodel-attribute-mapper",
        "consentRequired": False,
        "config": {
            "access.token.claim": "true",
            "aggregate.attrs": 'false',
            "claim.name": "dn",
            "id.token.claim": "false",
            "jsonType.label": "String",
            "multivalued": 'false',
            "user.attribute": "LDAP_ENTRY_DN",
            "userinfo.token.claim": "false",
        },
    }
    try:
        keycloak_id, mappers = get_protocol_mappers(keycloak_admin_connection, client_id)
        assert expected_mapper in mappers
    finally:
        if keycloak_id:
            keycloak_admin_connection.delete_client(keycloak_id)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
@pytest.mark.parametrize('audience_to_map', [None, 'myaudience'])
def test_oidc_audience_mapper(random_string, keycloak_admin_connection, audience_to_map):
    client_id = random_string()
    args = ['univention-keycloak', 'oidc/rp', 'create', '--add-audience-mapper']
    if audience_to_map:
        args.append('--audience-to-map')
        args.append(audience_to_map)
    args.append(client_id)
    run_command(args)
    expected_mapper = {
        "name": "audiencemap",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-audience-mapper",
        "consentRequired": False,
        "config": {
            "included.client.audience": audience_to_map if audience_to_map else client_id,
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true",
        },
    }
    try:
        keycloak_id, mappers = get_protocol_mappers(keycloak_admin_connection, client_id)
        assert expected_mapper in mappers
    finally:
        if keycloak_id:
            keycloak_admin_connection.delete_client(keycloak_id)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_oidc_guardian_management_mappers(random_string, keycloak_admin_connection):
    client_id = random_string()
    args = ['univention-keycloak', 'oidc/rp', 'create', '--add-guardian-management-mappers', client_id]
    run_command(args)
    expected_mappers = [
        {
            "protocol": "openid-connect",
            "name": "Client IP Address",
            "protocolMapper": "oidc-usersessionmodel-note-mapper",
            "consentRequired": False,
            "config": {
                "user.session.note": "clientAddress",
                "userinfo.token.claim": "true",
                "id.token.claim": "true",
                "claim.name": "clientAddress",
                "jsonType.label": "String",
                "access.token.claim": "true",
                "access.tokenResponse.claim": 'false',
            },
        },
        {
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usersessionmodel-note-mapper",
            "name": "Client IP Address",
            "consentRequired": False,
            "config": {
                "user.session.note": "clientAddress",
                "claim.name": "clientAddress",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "userinfo.token.claim": "true",
                "access.tokenResponse.claim": 'false',
            },
        },
        {
            "protocol": "openid-connect",
            "protocolMapper": "oidc-audience-mapper",
            "name": "audiencemap",
            "consentRequired": False,
            "config": {
                "included.client.audience": "guardian-cli",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "userinfo.token.claim": "true",
            },
        },
        {
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usersessionmodel-note-mapper",
            "name": "Client Host",
            "consentRequired": False,
            "config": {
                "user.session.note": "clientHost",
                "claim.name": "clientHost",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "userinfo.token.claim": "true",
                "access.tokenResponse.claim": 'false',
            },
        },
        {
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "name": "dn",
            "consentRequired": False,
            "config": {
                "user.attribute": "LDAP_ENTRY_DN",
                "claim.name": "dn",
                "jsonType.label": "String",
                "id.token.claim": "false",
                "access.token.claim": "true",
                "userinfo.token.claim": "false",
                "multivalued": 'false',
                "aggregate.attrs": 'false',
            },
        },
        {
            "protocol": "openid-connect",
            "protocolMapper": "oidc-audience-mapper", "name": "guardian-audience", "consentRequired": False,
            "config": {
                "included.client.audience": "guardian",
                "id.token.claim": "false",
                "access.token.claim": "true",
                "userinfo.token.claim": "false",
            },
        },
    ]
    try:
        keycloak_id, mappers = get_protocol_mappers(keycloak_admin_connection, client_id)
        for mapper in expected_mappers:
            assert mapper in mappers
    finally:
        if keycloak_id:
            keycloak_admin_connection.delete_client(keycloak_id)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_oidc_ics_mappers(random_string, keycloak_admin_connection):
    client_id = random_string()
    args = ['univention-keycloak', 'oidc/rp', 'create', '--add-ics-mappers', client_id]
    run_command(args)
    expected_mappers = [
        {
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "name": "phoenixusername_temp",
            "consentRequired": False,
            "config": {
                "introspection.token.claim": "true",
                "userinfo.token.claim": "true",
                "user.attribute": "uid",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "phoenixusername",
                "jsonType.label": "String",
                "lightweight.claim": 'false',
                "multivalued": 'false',
                "aggregate.attrs": 'false',
            },
        },
        {
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "name": "entryuuid_temp",
            "consentRequired": False,
            "config": {
                "introspection.token.claim": "true",
                "userinfo.token.claim": "true",
                "user.attribute": "entryUUID",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "entryuuid",
                "jsonType.label": "String",
                "lightweight.claim": 'false',
                "multivalued": 'false',
                "aggregate.attrs": 'false',
            },
        },
        {
            "protocol": "openid-connect",
            "protocolMapper": "oidc-audience-mapper",
            "name": "intercom-audience",
            "consentRequired": False,
            "config": {
                "included.client.audience": "opendesk-intercom",
                "id.token.claim": "false",
                "access.token.claim": "true",
                "introspection.token.claim": "true",
                "lightweight.claim": 'false',
                "userinfo.token.claim": "false",
            },
        },
    ]
    try:
        keycloak_id, mappers = get_protocol_mappers(keycloak_admin_connection, client_id)
        assert len(mappers) == 3
        for mapper in expected_mappers:
            assert mapper in mappers
    finally:
        if keycloak_id:
            keycloak_admin_connection.delete_client(keycloak_id)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_oidc_client_defaults(random_string, keycloak_admin_connection):
    client_id = random_string()
    args = ['univention-keycloak', 'oidc/rp', 'create', client_id]
    run_command(args)
    try:
        keycloak_id = keycloak_admin_connection.get_client_id(client_id)
        client = keycloak_admin_connection.get_client(keycloak_id)
        assert client['adminUrl'] == ''
        assert not client.get('baseUrl')
        assert client['publicClient'] is False
        assert client['attributes']['backchannel.logout.revoke.offline.tokens'] == 'false'
        # TODO test more options
    finally:
        if keycloak_id:
            keycloak_admin_connection.delete_client(keycloak_id)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_oidc_client_options(random_string, keycloak_admin_connection):
    client_id = random_string()
    admin_url = random_string()
    app_url = f'https://{random_string()}'
    args = ['univention-keycloak', 'oidc/rp', 'create', client_id]
    args = [
        'univention-keycloak', 'oidc/rp', 'create',
        '--app-url', app_url,
        '--admin-url', admin_url,
        '--public-client',
        '--backchannel-logout-revoke-session',
        client_id,
    ]
    run_command(args)
    try:
        keycloak_id = keycloak_admin_connection.get_client_id(client_id)
        client = keycloak_admin_connection.get_client(keycloak_id)
        assert client['adminUrl'] == admin_url
        assert client['rootUrl'] == app_url
        assert client['baseUrl'] == app_url
        assert app_url in client['redirectUris']
        assert app_url in client['webOrigins']
        assert client['publicClient'] is True
        assert client['attributes']['backchannel.logout.revoke.offline.tokens'] == 'true'
        # TODO test more options
    finally:
        if keycloak_id:
            keycloak_admin_connection.delete_client(keycloak_id)
