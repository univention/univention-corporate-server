#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Create user/group/ou/client objects for test environments based on sizing scenarios."""

import base64
import logging
import random
import sys
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, replace
from functools import lru_cache
from io import BytesIO

from ldap.dn import escape_dn_chars
from ldap.filter import filter_format
from PIL import Image

from univention.admin import modules, uexceptions, uldap
from univention.config_registry import ucr


logger = logging.getLogger(__name__)


# allow idempotent re-creation of the same structure and distribution of members!
random.seed(42)


@dataclass
class Scenario:
    name: str
    users: int
    groups: int
    clients: int
    ous: int
    ou_size_min: int
    ou_size_max: int
    avg_group_memberships: int
    avg_members_per_group: int
    nested_groups_count: int
    avg_nested_groups_per_group: int
    profile_picture_percentage: float
    profile_picture_size: int

    ou_prefix: str = 'testou'
    username_prefix: str = 'testuser'
    groupname_prefix: str = 'testgroup'
    client_prefix: str = 'testclient'


# Scenario definitions from https://git.knut.univention.de/univention/product-management/requirements-management/-/blob/main/sizing-scenarios.md
# OU numbers: "in average 500 users per OU" which is the size of a typical school
SCENARIOS: dict[str, Scenario] = {
    'default': Scenario(
        name='Default',
        users=200_000,
        groups=20_000,
        clients=0,
        ous=400,
        ou_size_min=100,
        ou_size_max=5000,
        avg_group_memberships=10,
        avg_members_per_group=100,
        nested_groups_count=100,
        avg_nested_groups_per_group=3,
        profile_picture_percentage=0,
        profile_picture_size=0,
    ),
    'XS': Scenario(
        name='Minimal',
        users=100,
        groups=100,
        clients=100,
        ous=0,
        ou_size_min=100,
        ou_size_max=5000,
        avg_group_memberships=5,
        avg_members_per_group=10,
        nested_groups_count=0,
        avg_nested_groups_per_group=0,
        profile_picture_percentage=0.25,
        profile_picture_size=500 * 1024,
    ),
    'S': Scenario(
        name='Small',
        users=1_000,
        groups=1_000,
        clients=1_000,
        ous=0,
        ou_size_min=100,
        ou_size_max=5000,
        avg_group_memberships=5,
        avg_members_per_group=10,
        nested_groups_count=20,
        avg_nested_groups_per_group=5,
        profile_picture_percentage=0.25,
        profile_picture_size=500 * 1024,
    ),
    'M': Scenario(
        name='Medium',
        users=5_000,
        groups=5_000,
        clients=5_000,
        ous=10,
        ou_size_min=100,
        ou_size_max=5000,
        avg_group_memberships=10,
        avg_members_per_group=10,
        nested_groups_count=50,
        avg_nested_groups_per_group=10,
        profile_picture_percentage=0.25,
        profile_picture_size=500 * 1024,
    ),
    'L': Scenario(
        name='Large',
        users=20_000,
        groups=20_000,
        clients=20_000,
        ous=40,
        ou_size_min=100,
        ou_size_max=5000,
        avg_group_memberships=10,
        avg_members_per_group=20,
        nested_groups_count=250,
        avg_nested_groups_per_group=15,
        profile_picture_percentage=0.25,
        profile_picture_size=500 * 1024,
    ),
    'XL': Scenario(
        name='Extra Large',
        users=50_000,
        groups=50_000,
        clients=5_000,
        ous=100,
        ou_size_min=100,
        ou_size_max=5000,
        avg_group_memberships=15,
        avg_members_per_group=30,
        nested_groups_count=500,
        avg_nested_groups_per_group=20,
        profile_picture_percentage=0.25,
        profile_picture_size=500 * 1024,
    ),
    '2XL': Scenario(
        name='2 Extra Large',
        users=150_000,
        groups=150_000,
        clients=15_000,
        ous=300,
        ou_size_min=100,
        ou_size_max=5000,
        avg_group_memberships=20,
        avg_members_per_group=40,
        nested_groups_count=1000,
        avg_nested_groups_per_group=50,
        profile_picture_percentage=0.25,
        profile_picture_size=500 * 1024,
    ),
    '3XL': Scenario(
        name='3 Extra Large',
        users=500_000,
        groups=500_000,
        clients=0,
        ous=1000,
        ou_size_min=100,
        ou_size_max=5000,
        avg_group_memberships=30,
        avg_members_per_group=80,
        nested_groups_count=2500,
        avg_nested_groups_per_group=50,
        profile_picture_percentage=0.25,
        profile_picture_size=500 * 1024,
    ),
}


@lru_cache(maxsize=8)
def generate_profile_picture(size_bytes: int) -> bytes:
    """Generate a minimal valid JPEG image. Cached since all images with the same size are identical."""
    img = Image.new('RGB', (10, 10), color=(73, 109, 137))

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=10)
    jpeg_data = buffer.getvalue()

    if len(jpeg_data) < size_bytes:
        footer = b'\xff\xd9'
        if jpeg_data.endswith(footer):
            body = jpeg_data[:-2]
            padding_size = size_bytes - len(jpeg_data)
            jpeg_data = body + (b'\x00' * padding_size) + footer

    return jpeg_data


def calculate_ou_sizes(num_ous: int, total_objects: int, min_size: int = 100, max_size: int = 5000) -> list[int]:
    """
    Calculate varying OU sizes with configurable range, average ~500.
    Returns list of object counts per OU.
    """
    if num_ous == 0:
        return []

    ou_sizes = []
    avg_size = (min_size + max_size) / 2

    for _ in range(num_ous):
        size = int(random.triangular(min_size, max_size, avg_size))
        ou_sizes.append(size)

    current_total = sum(ou_sizes)
    ou_sizes = [int(size * total_objects / current_total) for size in ou_sizes]

    diff = total_objects - sum(ou_sizes)
    if diff > 0:
        for _ in range(diff):
            ou_sizes[random.randint(0, num_ous - 1)] += 1
    elif diff < 0:
        for _ in range(abs(diff)):
            idx = random.randint(0, num_ous - 1)
            if ou_sizes[idx] > min_size:
                ou_sizes[idx] -= 1

    return ou_sizes


class Environment:
    """Test environment creation."""

    def __init__(self, lo, position, base: str, scenario_config: dict):
        self.lo = lo
        self.position = position
        self.base = base
        self.scenario = scenario_config
        self.ou_dns: list[str] = []
        self.ou_name = None

    def create_all(self):
        modules.init(self.lo, self.position, modules.get('container/ou'))
        modules.init(self.lo, self.position, modules.get('container/cn'))
        modules.init(self.lo, self.position, modules.get('users/user'))
        modules.init(self.lo, self.position, modules.get('groups/group'))
        modules.init(self.lo, self.position, modules.get('computers/linux'))

        if self.scenario.ous > 0:
            self._create_ou_structure()
        else:
            user_to_groups = self._calculate_user_to_group_memberships()
            all_users = self._create_users(self.base, 0, self.scenario.users)
            self._create_groups(self.base, 0, self.scenario.groups, all_users, user_to_groups)
            self._create_clients(self.base, 0, self.scenario.clients)

    def _create_ou_structure(self):
        """Create OUs one by one, with all their content (users, groups, clients) before moving to next OU."""
        num_ous = self.scenario.ous
        ou_prefix = self.scenario.ou_prefix

        logger.info('Starting creation of %d OUs with content', num_ous)
        logger.info('Total objects to create: %d users, %d groups, %d clients', self.scenario.users, self.scenario.groups, self.scenario.clients)

        user_ou_sizes = calculate_ou_sizes(num_ous, self.scenario.users, self.scenario.ou_size_min, self.scenario.ou_size_max)
        group_ou_sizes = calculate_ou_sizes(num_ous, self.scenario.groups, self.scenario.ou_size_min, self.scenario.ou_size_max)
        client_ou_sizes = calculate_ou_sizes(num_ous, self.scenario.clients, self.scenario.ou_size_min, self.scenario.ou_size_max)

        logger.debug('Pre-calculating user to group memberships')
        user_to_groups = self._calculate_user_to_group_memberships()

        all_users = []
        all_groups = []
        user_offset = 0
        group_offset = 0
        client_offset = 0

        for ou_idx, num_users_in_ou, num_groups_in_ou, num_clients_in_ou in zip(range(1, num_ous + 1), user_ou_sizes, group_ou_sizes, client_ou_sizes):
            progress_pct = ((ou_idx - 1) / num_ous) * 100
            logger.info('Progress: %.1f%% - Creating OU %d/%d: %s%d', progress_pct, ou_idx, num_ous, ou_prefix, ou_idx)

            ou_dn = self._create_ou(ou_idx, ou_prefix)
            self.ou_dns.append(ou_dn)

            self.create_default_containers(ou_dn)
            self.create_primary_groups(ou_dn, f'{ou_prefix}{ou_idx}')

            all_users.extend(self._create_users(ou_dn, user_offset, num_users_in_ou))
            all_groups.extend(self._create_groups(ou_dn, group_offset, num_groups_in_ou, all_users, user_to_groups))
            self._create_clients(ou_dn, client_offset, num_clients_in_ou)

            user_offset += num_users_in_ou
            group_offset += num_groups_in_ou
            client_offset += num_clients_in_ou

        logger.info('Progress: 100.0%% - Completed creation of all %d OUs', num_ous)
        logger.info('Total created: %d users, %d groups', len(all_users), len(all_groups))

    def _create_ou(self, ou_idx: int, ou_prefix: str) -> str:
        """Create a single OU and return its DN."""
        ous_module = modules.get('container/ou')

        self.position.setDn(self.base)
        self.ou_name = ou_name = f'{ou_prefix}{ou_idx}'
        existing_ou = ous_module.lookup(None, self.lo, filter_format('ou=%s', [ou_name]), base=self.base, scope='one')

        if existing_ou:
            return existing_ou[0].dn

        logger.debug('Creating OU: %s', ou_name)
        ou = ous_module.object(None, self.lo, self.position)
        ou.open()
        ou['name'] = ou_name
        ou['description'] = f'Organizational Unit {ou_idx}'
        return ou.create()

    def create_default_containers(self, dn):
        containers_module = modules.get('container/cn')
        logger.debug('Creating default containers for %s', dn)
        for container_name in ['users', 'groups', 'computers']:
            self.position.setDn(dn)
            existing_container = containers_module.lookup(None, self.lo, filter_format('cn=%s', [container_name]), base=dn, scope='one')
            if not existing_container:
                try:
                    container = containers_module.object(None, self.lo, self.position)
                    container.open()
                    container['name'] = container_name
                    container['description'] = f'Primary container for {container_name} objects'
                    container[{'users': 'userPath', 'groups': 'groupPath', 'computers': 'computerPath'}[container_name]] = '1'
                    if container_name == 'computers':
                        container['domaincontrollerPath'] = '1'
                    container.create()
                except uexceptions.objectExists:
                    pass

    def create_primary_groups(self, dn, ou_name):
        logger.debug('Creating primary groups for %s', dn)
        groups_module = modules.get('groups/group')
        ous_module = modules.get('container/ou')

        groups_container_dn = f'cn=groups,{dn}'
        self.position.setDn(groups_container_dn)

        domain_users_group_name = f'Domain Users {ou_name}'
        existing_users_group = groups_module.lookup(None, self.lo, filter_format('cn=%s', [domain_users_group_name]), base=groups_container_dn, scope='one')
        if existing_users_group:
            domain_users_dn = existing_users_group[0].dn
        else:
            users_group = groups_module.object(None, self.lo, self.position)
            users_group.open()
            users_group['name'] = domain_users_group_name
            users_group['description'] = f'Default group for users in {ou_name}'
            domain_users_dn = users_group.create()

        domain_computers_group_name = f'Domain Computers {ou_name}'
        existing_computers_group = groups_module.lookup(None, self.lo, filter_format('cn=%s', [domain_computers_group_name]), base=groups_container_dn, scope='one')
        if existing_computers_group:
            domain_computers_dn = existing_computers_group[0].dn
        else:
            computers_group = groups_module.object(None, self.lo, self.position)
            computers_group.open()
            computers_group['name'] = domain_computers_group_name
            computers_group['description'] = f'Default group for computers in {ou_name}'
            domain_computers_dn = computers_group.create()

        ou_obj = ous_module.object(None, self.lo, self.position, dn)
        ou_obj.open()
        ou_obj.options.append('group-settings')
        ou_obj['defaultGroup'] = domain_users_dn
        ou_obj['defaultComputerGroup'] = domain_computers_dn
        ou_obj['defaultDomainControllerMBGroup'] = domain_computers_dn
        ou_obj['defaultDomainControllerGroup'] = domain_computers_dn
        ou_obj['defaultMemberServerGroup'] = domain_computers_dn
        ou_obj['defaultClientGroup'] = domain_computers_dn
        ou_obj.modify()

    def _calculate_user_to_group_memberships(self) -> dict[int, list[int]]:
        """Pre-calculate which groups each user should belong to."""
        number_of_groups = self.scenario.groups
        avg_group_memberships = self.scenario.avg_group_memberships

        return {
            user_idx: random.sample(range(1, number_of_groups + 1), min(avg_group_memberships, number_of_groups))
            for user_idx in range(1, self.scenario.users + 1)
        }

    def _create_users(self, base: str, start_idx: int, count: int) -> list[str]:
        """Create users in a specific container."""
        users_module = modules.get('users/user')

        user_base = f'cn=users,{base}'
        self.position.setDn(user_base)

        created_users = []
        profile_picture_percentage = self.scenario.profile_picture_percentage
        profile_picture_size = self.scenario.profile_picture_size
        username_prefix = self.scenario.username_prefix

        existing_users = {attr['uid'][0].decode('utf-8'): dn for dn, attr in self.lo.search(filter_format('uid=%s*', [username_prefix]), base=user_base, scope='one', attr=['uid'])}

        if count:
            logger.info('  Creating %d users in %s', count, user_base)
        for i in range(count):
            user_number = start_idx + i + 1
            name = f'{username_prefix}{user_number}'

            dn = existing_users.get(name)
            if not dn:
                user = users_module.object(None, self.lo, self.position)
                user.open()
                user['username'] = name
                user['firstname'] = f'First{user_number}'
                user['lastname'] = name
                user['description'] = f'Test user {name}'
                user['password'] = 'univention'
                if self.ou_name:
                    user['primaryGroup'] = f'cn=Domain Users {escape_dn_chars(self.ou_name)},cn=groups,{base}'

                if random.random() < profile_picture_percentage:
                    picture_data = generate_profile_picture(profile_picture_size)
                    if picture_data:
                        user['jpegPhoto'] = base64.b64encode(picture_data).decode('ascii')

                dn = user.create()

            created_users.append(dn)

        return created_users

    def _create_groups(self, base: str, start_idx: int, count: int, all_users: list[str], user_to_groups: dict[int, list[int]]) -> list[str]:
        """Create groups in a specific container."""
        groups_module = modules.get('groups/group')

        base = f'cn=groups,{base}'
        self.position.setDn(base)

        created_groups = []
        groupname_prefix = self.scenario.groupname_prefix

        existing_groups = {attr['cn'][0].decode('utf-8'): dn for dn, attr in self.lo.search(filter_format('cn=%s*', [groupname_prefix]), base=base, scope='one', attr=['cn'])}

        if count:
            logger.info('  Creating %d groups in %s', count, base)
        for i in range(count):
            group_number = start_idx + i + 1
            name = f'{groupname_prefix}{group_number}'

            group_members_dns = []
            for user_idx, group_indices in user_to_groups.items():
                if group_number in group_indices and user_idx <= len(all_users):
                    group_members_dns.append(all_users[user_idx - 1])

            dn = existing_groups.get(name)
            if not dn:
                group = groups_module.object(None, self.lo, self.position)
                group.open()
                group['name'] = name
                group['description'] = f'Test group {name}'
                role_name = name.replace(' ', '_').lower()
                group['guardianMemberRoles'] = [f'app:ns:{role_name}_role{j}' for j in range(3)]
                if group_members_dns:
                    group['users'] = group_members_dns
                group.create()
                dn = group.dn

            created_groups.append(dn)

        return created_groups

    def _create_clients(self, base: str, start_idx: int, count: int) -> list[str]:
        """Create clients in a specific container."""
        computers_module = modules.get('computers/linux')
        base = f'cn=computers,{base}'
        self.position.setDn(base)

        client_dns = []
        client_prefix = self.scenario.client_prefix

        existing_clients = {attr['cn'][0].decode('utf-8'): dn for dn, attr in self.lo.search(filter_format('cn=%s*', [client_prefix]), base=base, scope='one', attr=['cn'])}

        if count:
            logger.info('  Creating %d clients in %s', count, base)
        for i in range(count):
            client_number = start_idx + i + 1
            client_name = f'{client_prefix}{client_number}'
            dn = existing_clients.get(client_name)
            if not dn:
                client = computers_module.object(None, self.lo, self.position)
                client.open()
                client['name'] = client_name
                dn = client.create()

            client_dns.append(dn)

        return client_dns


def main(args: Namespace) -> None:
    setup_logging(verbosity=args.verbose, log_level=args.log_level)

    logger.info('Starting user creation with scenario: %s', args.scenario or 'default')

    lo, position = uldap.getAdminConnection()
    base = ucr['ldap/base']
    modules.update()

    base_scenario = SCENARIOS.get(args.scenario, SCENARIOS['default'])
    scenario = replace(base_scenario, **{key: getattr(args, key) for key in Scenario.__dataclass_fields__ if getattr(args, key, None) is not None})

    logger.info('Scenario: %s', scenario.name)
    logger.debug('Configuration: %s', scenario)

    Environment(lo, position, base, scenario).create_all()

    logger.info('User creation completed successfully!')


def setup_logging(verbosity: int = 0, log_level: str | None = None) -> None:
    """Configure logging based on verbosity level or explicit log level."""
    if not log_level:
        level_map = {
            0: logging.WARNING,  # Default: only warnings and errors
            1: logging.INFO,  # -v: info messages
            2: logging.DEBUG,  # -vv: debug messages
            3: logging.DEBUG,  # -vvv: debug with more details
        }
        level = level_map.get(verbosity, logging.DEBUG)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout,
    )
    logger.setLevel(level)


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('-s', '--scenario', help='Scenario name', choices=SCENARIOS)
    parser.add_argument('-u', '--users', help='How many users to create', type=int)
    parser.add_argument('-g', '--groups', help='How many groups to create', type=int)
    parser.add_argument('-c', '--clients', help='How many groups to create', type=int)
    parser.add_argument('--username-prefix', help='Prefix for usernames (default: %(default)s)', default=Scenario.username_prefix)
    parser.add_argument('--groupname-prefix', help='Prefix for group names (default: %(default)s)', default=Scenario.groupname_prefix)
    parser.add_argument('--ou-prefix', help='Prefix for OU names (default: %(default)s)', default=Scenario.ou_prefix)
    parser.add_argument('--client-prefix', help='Prefix for client names (default: %(default)s)', default=Scenario.client_prefix)
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity (can be repeated: -v, -vv, -vvv)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Set explicit log level (overrides -v)')
    args = parser.parse_args()

    main(args)
