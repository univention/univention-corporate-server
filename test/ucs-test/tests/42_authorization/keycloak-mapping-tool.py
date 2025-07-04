#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Tool for Keycloak IDP mapppings

- list and show groups and IDP mappers
- create IDP mapper. If the group did not exists the group will be created.
...
"""

import argparse
import json
import sys
from pprint import pprint
from textwrap import dedent
from typing import Any

import yaml
from keycloak import KeycloakAdmin

from univention.config_registry import ucr


class KeycloakMappingToolSettings:
    username: str
    password: str
    server_url: str
    realm_name: str
    user_realm: str | None
    idp_alias: str

    def __init__(self, config_file: str):
        with open(config_file) as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)

        self.username = data.get('username')
        self.password = data.get('password')
        self.server_url = data.get('server_url') or ucr['ucs/server/sso/uri'].strip('/')
        self.realm_name = data.get('realm_name')
        self.user_realm = data.get('user_realm')
        self.idp_alias = data.get('idp_alias')


def _get_keycloak_session(settings: KeycloakMappingToolSettings) -> KeycloakAdmin:
    return KeycloakAdmin(
        server_url=settings.server_url,
        username=settings.username,
        password=settings.password,
        realm_name=settings.realm_name,
        user_realm_name=settings.user_realm,
        verify=True,
    )


def _create_group(
    session: KeycloakAdmin,
    name: str,
    nubus_roles: list[str] | str | None = None,
    skip_exists: bool = False,
) -> str:
    group_payload = {
        'name': name,
        'path': f'/{name}',
    }
    if nubus_roles:
        group_payload['attributes'] = {}
        if isinstance(nubus_roles, list):
            group_payload['attributes']['nubus_roles'] = nubus_roles
        elif isinstance(nubus_roles, str):
            group_payload['attributes']['nubus_roles'] = [nubus_roles]
        else:
            raise TypeError('Role type must be str or list[str]')

    group_id = session.create_group(payload=group_payload, skip_exists=skip_exists)

    return group_id


def _get_group_by_name(session: KeycloakAdmin, name: str) -> dict:
    group = session.get_group_by_path(f'/{name}')
    return group


def _get_groups(session: KeycloakAdmin) -> list[dict]:
    groups = session.get_groups(query={'briefRepresentation': False})
    return groups


def _create_idp_group_mapper(
    session: KeycloakAdmin,
    idp_alias: str,
    name: str,
    claim_key: str,
    claim_value: str,
    group_name: str,
    value_is_regex: bool = False,
):
    idp_mapper_payload = {
        'name': name,
        'identityProviderAlias': idp_alias,
        'identityProviderMapper': 'oidc-advanced-group-idp-mapper',
        'config': {
            'syncMode': 'FORCE',
            'claims': f'[{{"key":"{claim_key}","value":"{claim_value}"}}]',
            'are.claim.values.regex': 'true' if value_is_regex else 'false',
            'group': group_name,
        },
    }

    resp = session.connection.raw_post(
        f'admin/realms/{session.connection.realm_name}/identity-provider/instances/{idp_alias}/mappers',
        data=json.dumps(idp_mapper_payload),
    )

    # To have the same handling as it is via the Keycloak API
    # the functions returns None when the mapper already exists.
    if resp.status_code == 400:
        mapper = _get_idp_mapper_by_name(session=session, idp_alias=idp_alias, name=name)
        if mapper:
            return None

    assert resp.status_code == 201, resp.text
    mapper = _get_idp_mapper_by_name(session=session, idp_alias=idp_alias, name=name)
    return mapper['id']


def _get_idp_mappers(session: KeycloakAdmin, idp_alias: str) -> Any:
    uri = f'admin/realms/{session.connection.realm_name}/identity-provider/instances/{idp_alias}/mappers'
    resp = session.connection.raw_get(uri)
    assert resp.status_code == 200, resp.text

    mappers = json.loads(resp.text)

    return mappers


def _get_idp_mapper_by_name(session: KeycloakAdmin, idp_alias: str, name: str) -> dict:
    mappers = _get_idp_mappers(session, idp_alias)
    for mapper in mappers:
        if mapper['name'] == name:
            return mapper
    return None


def _get_idp_mapper(session: KeycloakAdmin, idp_alias: str, mapper_id: str):
    uri = f'admin/realms/{session.connection.realm_name}/identity-provider/instances/{idp_alias}/mappers/{mapper_id}'
    resp = session.connection.raw_get(uri)
    assert resp.status_code == 200, resp.text

    mapper = json.loads(resp.text)

    return mapper


def list_mappers(session: KeycloakAdmin, idp_alias: str):
    mappers = _get_idp_mappers(session, idp_alias)
    max_name_len = len(max([d['name'] for d in mappers], key=len))
    for mapper in sorted(mappers, key=lambda d: d['name']):
        print(f'{mapper["name"].ljust(max_name_len, " ")}  {mapper["id"]}')


def list_groups(session: KeycloakAdmin):
    groups = _get_groups(session)
    max_name_len = len(max([d['name'] for d in groups], key=len))
    for group in sorted(groups, key=lambda d: d['name']):
        print(f'{group["name"].ljust(max_name_len, " ")}  {group["id"]}')


def show_mapper(session: KeycloakAdmin, idp_alias: str, mapper_id: str):
    mapper = _get_idp_mapper(session=session, idp_alias=idp_alias, mapper_id=mapper_id)
    pprint(mapper)


def show_group(session: KeycloakAdmin, group_id: str):
    group = session.get_group(group_id)
    pprint(group)


def create_from_config(session: KeycloakAdmin, idp_alias: str, config: list[dict]):
    # Validate config
    is_dirty = False
    for mapper in config:
        if not mapper.get('external-group-name') or not mapper.get('internal-group-name'):
            if not is_dirty:
                print(
                    dedent("""
                Error: The mapper config must contain at least external and internal group names!
                {
                    "external-group-name": "external_group_1",
                    "internal-group-name": ""
                }
                Given:
                ------
                """),
                )
            print(json.dumps(mapper, indent=4))
            is_dirty = True

    if is_dirty:
        print('Please fix the errors and start the script again!')
        return

    for mapper in config:
        create_from_args(
            session=session,
            idp_alias=idp_alias,
            external_group_name=mapper.get('external-group-name'),
            internal_group_name=mapper.get('internal-group-name'),
            internal_group_nubus_roles=mapper.get('internal-group-nubus-roles'),
        )


def create_from_args(
    session: KeycloakAdmin,
    idp_alias: str,
    external_group_name: str,
    internal_group_name: str,
    internal_group_nubus_roles: str | None = None,
):
    group_id = _create_group(
        session, name=internal_group_name, nubus_roles=internal_group_nubus_roles, skip_exists=True,
    )

    if not group_id:
        group_id = _get_group_by_name(session=session, name=internal_group_name)['id']
        print(f'Use existing group {internal_group_name} with ID {group_id}')
    else:
        print(f'Group {internal_group_name} with ID {group_id} created!')

    mapper_name = f'group_{external_group_name}'

    mapper_id = _create_idp_group_mapper(
        session=session,
        idp_alias=idp_alias,
        name=mapper_name,
        claim_key='groups',
        claim_value=external_group_name,
        group_name=internal_group_name,
    )

    if not mapper_id:
        print(f'IDP mapper with the name {mapper_name} still exists in {session.connection.realm_name}/{idp_alias}!')
    else:
        print(f'IDP mapper {mapper_name} with ID {mapper_id} created!')


def _parse_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
    parser.add_argument(
        '--config',
        type=str,
        default='keycloak_mapping_tool_config.yaml',
        help='Name of the group to map from.',
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    create_parser = subparsers.add_parser(name='create', help='Command to add an object.')
    list_parser = subparsers.add_parser(name='list', help='Command to list all objects.')
    show_parser = subparsers.add_parser(name='show', help='Command to show object details.')

    _parse_create_command_args(create_parser=create_parser)
    _parse_list_command_args(list_parser=list_parser)
    _parse_show_command_args(show_parser=show_parser)

    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    return args


def _parse_create_command_args(create_parser: argparse.ArgumentParser):
    create_subparsers = create_parser.add_subparsers(
        dest='object_type',
        required=True,
        help='Type of the object that should be created.',
    )

    create_mapper_parser = create_subparsers.add_parser(name='mapper', help='IDP mapper')
    create_subparsers.add_parser(name='group', help='Keycloak group.')

    create_mapper_parser.add_argument(
        '--external-group-name',
        type=str,
        help='Name of the group to map from.',
        required='--internal-group_name' in sys.argv
        or ('--internal-group-name' not in sys.argv and '--mapping-config' not in sys.argv),
    )
    create_mapper_parser.add_argument(
        '--internal-group-name',
        type=str,
        help='Name of the group to map to.',
        required='--external-group_name' in sys.argv
        or ('--external-group-name' not in sys.argv and '--mapping-config' not in sys.argv),
    )
    create_mapper_parser.add_argument(
        '--internal-group-nubus-roles',
        type=str,
        help='The Nubus roles that should be mapped to UMC.',
    )
    create_mapper_parser.add_argument(
        '--mapping-config',
        type=str,
        help='Mapping config file.',
        required='--external-group-name' not in sys.argv and '--internal-group_name' not in sys.argv,
    )


def _parse_list_command_args(list_parser: argparse.ArgumentParser):
    list_subparsers = list_parser.add_subparsers(dest='object_type', required=True)

    list_subparsers.add_parser('mapper', help='IDP mappers')
    list_subparsers.add_parser('group', help='Keycloak groups')


def _parse_show_command_args(show_parser: argparse.ArgumentParser):
    show_subparsers = show_parser.add_subparsers(dest='object_type', required=True)

    show_mapper_parser = show_subparsers.add_parser('mapper', help='IDP mapper')
    show_group_parser = show_subparsers.add_parser('group', help='Keycloak group')

    show_mapper_parser.add_argument(
        'id',
        type=str,
        help='UUID of the mapper',
    )

    show_group_parser.add_argument(
        'id',
        type=str,
        help='UUID of the group',
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    args = _parse_args(parser)

    try:
        settings = KeycloakMappingToolSettings(config_file=args.config)
    except FileNotFoundError:
        print(f'Error: Configuration file {args.config} not found!')
        return

    session = _get_keycloak_session(settings=settings)

    if args.command == 'show':
        if args.object_type == 'group':
            show_group(session=session, group_id=args.id)
        elif args.object_type == 'mapper':
            show_mapper(session=session, idp_alias=settings.idp_alias, mapper_id=args.id)

    elif args.command == 'list':
        if args.object_type == 'group':
            list_groups(session=session)
        elif args.object_type == 'mapper':
            list_mappers(session=session, idp_alias=settings.idp_alias)

    elif args.command == 'create':
        if args.object_type == 'group':
            print('Not implemented!')
        elif args.object_type == 'mapper':
            if args.internal_group_name and args.external_group_name and not args.mapping_config:
                create_from_args(
                    session=session,
                    idp_alias=settings.idp_alias,
                    external_group_name=args.external_group_name,
                    internal_group_name=args.internal_group_name,
                    internal_group_nubus_roles=args.internal_group_nubus_roles,
                )
            elif not args.internal_group_name and not args.external_group_name and args.mapping_config:
                try:
                    with open(args.mapping_config) as fp:
                        file_content = json.load(fp)
                except FileNotFoundError:
                    print(f'File {args.mapping_config} not found!')
                    return

                create_from_config(session=session, idp_alias=settings.idp_alias, config=file_content)


if __name__ == '__main__':
    main()
