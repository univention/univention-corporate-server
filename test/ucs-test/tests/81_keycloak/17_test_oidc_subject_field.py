#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: Test subject field in the OIDC token contains the username (type sensitive), see pullcord univention/dev/internal/dev-issues/dev-incidents#186
## tags: [keycloak, skip_admember]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import base64
import json
import os
from types import SimpleNamespace

import pytest
import requests

from univention.testing.udm import UCSTestUDM


# Decode JWT (ID token)
def decode_jwt_section(section):
    """Decode a JWT base64url-encoded section."""
    section += "=" * (-len(section) % 4)  # fix padding
    return base64.urlsafe_b64decode(section.encode())


def get_client_secret(keycloak, keycloak_admin_username, keycloak_admin_password, client):
    token_url = f"{keycloak}realms/master/protocol/openid-connect/token"

    token_data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": keycloak_admin_username,
        "password": keycloak_admin_password,
    }
    token_resp = requests.post(token_url, data=token_data)
    token_resp.raise_for_status()
    admin_access_token = token_resp.json()["access_token"]

    # Get client info by clientId
    clients_url = f"{keycloak}admin/realms/ucs/clients"
    headers = {"Authorization": f"Bearer {admin_access_token}"}

    params = {"clientId": client}
    clients_resp = requests.get(clients_url, headers=headers, params=params)
    clients_resp.raise_for_status()

    client_info = clients_resp.json()[0]  # first match
    client_uuid = client_info["id"]

    secret_url = f"{keycloak}admin/realms/ucs/clients/{client_uuid}/client-secret"

    secret_resp = requests.get(secret_url, headers=headers)
    secret_resp.raise_for_status()

    client_secret = secret_resp.json()["value"]

    return client_secret


def get_oidc_claim_sub(username, password, keycloak_url, keycloak_admin_username, keycloak_admin_password, portal_url):
    token_url = f"{keycloak_url}realms/ucs/protocol/openid-connect/token"
    client_id = f"{portal_url}univention/oidc/"
    client_secret = get_client_secret(keycloak_url, keycloak_admin_username, keycloak_admin_password, client_id)

    data = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
        "scope": "openid",
    }

    response = requests.post(token_url, data=data)
    response.raise_for_status()
    tokens = response.json()

    id_token = tokens["id_token"]

    _, payload_b64, _ = id_token.split(".")
    payload = json.loads(decode_jwt_section(payload_b64))

    # Extract subject claim
    sub = payload.get("sub")
    return sub


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_oidc_claim_mixed_case(keycloak_admin: str, keycloak_secret: str, keycloak_config: SimpleNamespace, portal_config: SimpleNamespace, udm: UCSTestUDM):

    username = 'testUserMixedCase'

    _, user_name = udm.create_user(username='testUserMixedCase', password='univention')
    assert username == user_name

    sub_username = get_oidc_claim_sub(
        username,
        'univention',
        keycloak_config.url,
        keycloak_admin,
        keycloak_secret,
        portal_url=f'https://{portal_config.fqdn}/',
    )

    assert username in sub_username
