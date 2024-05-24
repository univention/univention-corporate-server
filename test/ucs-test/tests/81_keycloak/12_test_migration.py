#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test univention-keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os

import pytest
from DATA import GOOGLE_CLIENT, NC_CLIENT, O365CLIENT, OC_CLIENT
from utils import run_command


kc_id = 666


def get_client_by_id(connection, client_id):
    kc_id = connection.get_client_id(client_id)
    return kc_id, connection.get_client(kc_id)


def compare_client(old, new):
    for key in old.keys():
        print(f"assert {key} expected value: {old[key]}, given value {new[key]}")
        if key == 'id':
            continue
        if isinstance(old[key], dict):
            compare_client(old[key], new[key])
        elif isinstance(old[key], list):
            assert old[key].sort() == new[key].sort()
        else:
            assert old[key] == new[key]


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_create_o365_client(keycloak_administrator_connection):
    """Creates Microsoft 365 SAML client with univention-keycloak"""
    client_id = 'urn:federation:MicrosoftOnline'
    args = ['univention-keycloak', 'saml/sp', 'create', '--metadata-file=ms.xml', '--metadata-url=urn:federation:MicrosoftOnline', '--idp-initiated-sso-url-name=MicrosoftOnline', '--name-id-format=persistent']
    run_command(args)
    try:
        kc_id, client = get_client_by_id(keycloak_administrator_connection, client_id)
        run_command(args)
        O365CLIENT['id'] = kc_id
        compare_client(client, O365CLIENT)
    finally:
        keycloak_administrator_connection.delete_client(kc_id)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_create_google_client(keycloak_administrator_connection):
    """Creates Google SAML client with univention-keycloak"""
    client_id = "google.com"
    args = ['univention-keycloak', 'saml/sp', 'create', '--client-id=google.com', '--assertion-consumer-url-post=https://www.google.com/a/testdomain.com/acs', '--single-logout-service-url-post=https://www.google.com/a/testdomain.com/acs', '--idp-initiated-sso-url-name=google.com', '--name-id-format=email', '--frontchannel-logout-off']
    run_command(args)
    try:
        kc_id, client = get_client_by_id(keycloak_administrator_connection, client_id)
        GOOGLE_CLIENT['id'] = kc_id
        GOOGLE_CLIENT['protocolMappers'][0]['id'] = client['protocolMappers'][0]['id']
        compare_client(client, GOOGLE_CLIENT)
    finally:
        keycloak_administrator_connection.delete_client(kc_id)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_create_nextcloud_client(keycloak_administrator_connection, ucr):
    """Creates Nextcloud SAML client with univention-keycloak"""
    client_id = 'https://backup.ucs.test/nextcloud/apps/user_saml/saml/metadata'
    args = ['univention-keycloak', 'saml/sp', 'create', '--metadata-url=https://backup.ucs.test/nextcloud/apps/user_saml/saml/metadata', '--metadata-file=nc.xml', '--role-mapping-single-value']
    run_command(args)
    kc_id, client = get_client_by_id(keycloak_administrator_connection, client_id)
    try:
        compare_client(client, NC_CLIENT)
    finally:
        keycloak_administrator_connection.delete_client(kc_id)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_create_owncloud_client(keycloak_administrator_connection, ucr):
    """Creates Owncloud SAML client with univention-keycloak"""
    client_id = 'owncloudclient'
    args = ['univention-keycloak', 'oidc/rp', 'create', '--client-secret=univention', '--app-url=https://backup.ucs.test/owncloud/apps/openidconnect/redirect', 'owncloudclient']
    run_command(args)
    try:
        kc_id, client = get_client_by_id(keycloak_administrator_connection, client_id)
        kc_mappers = client.pop('protocolMappers')
        oc_mappers = OC_CLIENT.pop('protocolMappers')
        compare_client(client, OC_CLIENT)
        for m in range(len(kc_mappers)):
            kc_mappers[m].pop('id')
        OC_CLIENT['id'] = kc_id
        assert client == OC_CLIENT
        # list of dicts that are nested...
        for mapper in oc_mappers:
            assert mapper in kc_mappers
    finally:
        keycloak_administrator_connection.delete_client(kc_id)
