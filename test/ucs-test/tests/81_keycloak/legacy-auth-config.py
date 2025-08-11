#!/usr/bin/python3
# SPDX-FileCopyrightText: 2013-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""
Create or remove legay authz config in keycloak (ldap group-mapper,
client roles and group role mappings

Just a helper to manually create a test env.
"""

from argparse import ArgumentParser, FileType

from keycloak import KeycloakAdmin
from utils import legacy_auth_config_create, legacy_auth_config_remove, run_command

from univention.config_registry import ucr


def main() -> None:
    keycloak_url = run_command(['univention-keycloak', 'get-keycloak-base-url']).strip()
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('action', help='action', choices=['create', 'remove'])
    parser.add_argument('--group-clients', help='group client mapping', action='append', metavar='GROUPNAME CLIENT_ID', nargs=2, required=True)
    parser.add_argument('--keycloak-url', help='keycloak url', default=keycloak_url)
    parser.add_argument('--keycloak-admin', help='keycloak admin', default='admin')
    parser.add_argument('--keycloak-password-file', help='keycloak password file', default='/etc/keycloak.secret', metavar='FILE', type=FileType('r', encoding='UTF-8'))
    opt = parser.parse_args()
    opt.group_clients = {x[0]: x[1] for x in opt.group_clients}
    opt.keycloak_secret = opt.keycloak_password_file.read().strip()
    session = KeycloakAdmin(
        server_url=opt.keycloak_url,
        username=opt.keycloak_admin,
        password=opt.keycloak_secret,
        realm_name='ucs',
        user_realm_name='master',
        verify=True,
    )
    if opt.action == 'create':
        legacy_auth_config_create(session, ucr['ldap/base'], opt.group_clients)
    elif opt.action == 'remove':
        legacy_auth_config_remove(session, opt.group_clients)
    else:
        raise NotImplementedError()


if __name__ == '__main__':
    main()
