#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test univention-keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os

import pytest
from DATA import GOOGLE_CLIENT, NC_CLIENT, O365CLIENT, OC_CLIENT, UMC_CLIENT, UMC_OIDC_CLIENT
from utils import run_command

from univention.config_registry import ucr


def get_client_by_id(connection, client_id):
    kc_id = connection.get_client_id(client_id)
    return kc_id, connection.get_client(kc_id)


def compare_client(old, new, substitutes, client_id):
    old_mappers = old.pop('protocolMappers', [])
    new_mappers = new.pop('protocolMappers', [])
    for mapp in old_mappers:
        for new_mapp in new_mappers:
            if mapp['name'] == new_mapp['name']:
                compare_client(mapp, new_mapp, substitutes, client_id)
                break
        else:
            pytest.fail("Old client contains more protocolMappers than the new one")

    for key in old.keys():
        print(f"assert {key} expected value: {old[key]}, given value {new.get(key)}")
        if key == 'id':
            continue
        if isinstance(old[key], dict):
            compare_client(old[key], new[key], substitutes, client_id)
        elif isinstance(old[key], list):
            assert old[key].sort() == new[key].sort()
        else:
            if new.get(key) != 'ignore':
                if isinstance(new.get(key), str):
                    assert old[key] == new.get(key).format(**substitutes), f'mismatch for {key} in {client_id}'
                else:
                    assert old[key] == new.get(key), f'mismatch for {key} in {client_id}'


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
@pytest.mark.parametrize("client,client_id,args", [
    (O365CLIENT, 'urn:federation:MicrosoftOnline', ['univention-keycloak', 'saml/sp', 'create', '--metadata-file=ms.xml', '--metadata-url=urn:federation:MicrosoftOnline', '--idp-initiated-sso-url-name=MicrosoftOnline', '--name-id-format=persistent']),
    (OC_CLIENT, 'owncloudclient', ['univention-keycloak', 'oidc/rp', 'create', '--client-secret=univention', '--app-url=https://backup.ucs.test/owncloud/apps/openidconnect/redirect', 'owncloudclient']),
    (NC_CLIENT, 'https://backup.ucs.test/nextcloud/apps/user_saml/saml/metadata', ['univention-keycloak', 'saml/sp', 'create', '--metadata-url=https://backup.ucs.test/nextcloud/apps/user_saml/saml/metadata', '--metadata-file=nc.xml', '--role-mapping-single-value']),
    (GOOGLE_CLIENT, 'google.com', ['univention-keycloak', 'saml/sp', 'create', '--client-id=google.com', '--assertion-consumer-url-post=https://www.google.com/a/testdomain.com/acs', '--single-logout-service-url-post=https://www.google.com/a/testdomain.com/acs', '--idp-initiated-sso-url-name=google.com', '--name-id-format=email', '--frontchannel-logout-off']),
    (UMC_CLIENT, 'https://whatever.ucs.test/univention/saml/metadata', ['univention-keycloak', 'saml/sp', 'create', '--metadata-url=https://whatever.ucs.test/univention/saml/metadata', '--metadata-file=umc.xml']),
    (UMC_OIDC_CLIENT, f'https://{ucr["hostname"]}.{ucr["domainname"]}/univention/oidc/', None),
])
def test_create_client(keycloak_administrator_connection, client, client_id, args):
    """Creates Google SAML client with univention-keycloak"""
    if args:
        run_command(args)
    try:
        kc_id, new_client = get_client_by_id(keycloak_administrator_connection, client_id)
        substitutes = {}
        if not args:
            substitutes['domainname'] = f'{ucr["domainname"]}'
            substitutes['fqdn'] = f'{ucr["hostname"]}.{ucr["domainname"]}'
            substitutes['fqdn_lower'] = f'{ucr["hostname"]}.{ucr["domainname"]}'.lower()
            substitutes['ip'] = f'{ucr["interfaces/eth0/address"]}'
        compare_client(new_client, client, substitutes, client_id)
    finally:
        if args:
            keycloak_administrator_connection.delete_client(kc_id)
