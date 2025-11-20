#!/usr/bin/env python3
"""
Common utilities for UDM REST API performance tests.

This module provides shared functionality for authentication, request handling,
data generation, and cleanup operations used across multiple UDM REST API performance tests.
"""

import base64
import json
import logging
import os
import random
import string

import urllib3


# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Default configuration
DEFAULT_CONFIG = {
    'WAIT_MIN': 1,
    'WAIT_MAX': 5,
    'TIMEOUT': 30,
    'BASE_URL': 'master.ucs.test',
    'LDAP_BASE': 'dc=ucs,dc=test',
    'USERNAME': 'Administrator',
    'PASSWORD': 'univention',
}

# UDM REST API paths
UDM_BASE_PATH = '/univention/udm'


# LDAP containers
def get_ldap_containers(ldap_base: str | None = None) -> dict[str, str]:
    """Get LDAP container DNs."""
    if not ldap_base:
        ldap_base = str(get_config('LDAP_BASE'))

    return {
        'users': f'cn=users,{ldap_base}',
        'groups': f'cn=groups,{ldap_base}',
        'base': ldap_base,
    }


def get_config(key: str, default: str | int | None = None) -> str | int | None:
    """Get configuration value from environment or defaults."""
    env_value = os.environ.get(key)
    if env_value is not None:
        # Try to convert to int if default is int
        if isinstance(DEFAULT_CONFIG.get(key), int):
            try:
                return int(env_value)
            except ValueError:
                pass
        return env_value

    if default is not None:
        return default

    return DEFAULT_CONFIG.get(key)


def generate_random_string(length: int = 8) -> str:
    """Generate a random string for test data."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_test_username(counter: int, prefix: str = 'testuser') -> str:
    """Generate a test username with counter and random suffix."""
    return f'{prefix}{counter}_{generate_random_string(6)}'


def generate_test_groupname(counter: int, prefix: str = 'testgroup') -> str:
    """Generate a test group name with counter and random suffix."""
    return f'{prefix}{counter}_{generate_random_string(6)}'


def get_test_credentials() -> tuple[str, str]:
    """Get test credentials from environment or defaults."""
    username = get_config('USERNAME')
    password = get_config('PASSWORD')
    return str(username), str(password)


class UDMRestAuthenticator:
    """Handles authentication for UDM REST API requests."""

    def __init__(self, username: str | None = None, password: str | None = None):
        """Initialize authenticator with credentials."""
        if username is None or password is None:
            username, password = get_test_credentials()

        self.username = username
        self.password = password
        self.auth_header = None
        self.setup_basic_auth()

    def setup_basic_auth(self) -> None:
        """Setup basic authentication header."""
        credentials = base64.b64encode(f'{self.username}:{self.password}'.encode('ISO8859-1')).decode('ASCII')
        self.auth_header = f'Basic {credentials}'

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for requests."""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        if self.auth_header:
            headers['Authorization'] = self.auth_header

        return headers


class UDMRestClient:
    """Enhanced HTTP client for UDM REST API operations."""

    def __init__(self, client, authenticator: UDMRestAuthenticator | None = None):
        """Initialize with Locust HTTP client and authenticator."""
        self.client = client
        self.authenticator = authenticator or UDMRestAuthenticator()
        self.timeout = get_config('TIMEOUT')
        self.created_objects = []

    def make_request(self, method: str, url: str, catch_response: bool = True, name: str | None = None, **kwargs) -> object:
        """Make an authenticated request with proper error handling."""
        headers = kwargs.get('headers', {})
        headers.update(self.authenticator.get_auth_headers())

        kwargs.update(
            {
                'headers': headers,
                'verify': False,
                'timeout': self.timeout,
            },
        )

        if catch_response:
            kwargs['catch_response'] = True

        if name:
            kwargs['name'] = name

        return getattr(self.client, method.lower())(url, **kwargs)

    def create_user(self, username: str, lastname: str, password: str = 'univention', description: str | None = None, position: str | None = None) -> tuple[bool, str]:
        """Create a user and return success status and DN."""
        if position is None:
            position = get_ldap_containers()['users']

        user_data = {
            'position': position,
            'properties': {
                'username': username,
                'lastname': lastname,
                'password': password,
            },
        }

        if description:
            user_data['properties']['description'] = description

        with self.make_request('POST', f'{UDM_BASE_PATH}/users/user/', json=user_data, name='create_user') as response:
            if response.status_code == 201:
                location = response.headers.get('Location', '')
                if location:
                    user_dn = location.rsplit('/', 1)[-1]  # TODO: url-undecode
                    self.created_objects.append(('users/user', user_dn))
                    response.success()
                    return True, user_dn
                else:
                    response.failure('No Location header in create response')
                    return False, ''
            else:
                response.failure(f'Failed to create user: {response.status_code} - {response.text}')
                return False, ''

    def create_group(self, groupname: str, description: str | None = None, position: str | None = None) -> tuple[bool, str]:
        """Create a group and return success status and DN."""
        if position is None:
            position = get_ldap_containers()['groups']

        group_data = {
            'position': position,
            'properties': {
                'name': groupname,
            },
        }

        if description:
            group_data['properties']['description'] = description

        with self.make_request('POST', f'{UDM_BASE_PATH}/groups/group/', json=group_data, name='create_group') as response:
            if response.status_code == 201:
                location = response.headers.get('Location', '')
                if location:
                    group_dn = location.rsplit('/', 1)[-1]  # TODO: url-undecode
                    self.created_objects.append(('groups/group', group_dn))
                    response.success()
                    return True, group_dn
                else:
                    response.failure('No Location header in create response')
                    return False, ''
            else:
                response.failure(f'Failed to create group: {response.status_code} - {response.text}')
                return False, ''

    def search_objects(
        self, object_type: str, position: str | None = None, scope: str = 'sub', filter_expr: str | None = None, name: str | None = None,
    ) -> tuple[bool, int]:
        """Search for objects and return success status and count."""
        params = {}

        if position:
            params['position'] = position
        if scope:
            params['scope'] = scope
        if filter_expr:
            params['filter'] = filter_expr

        search_name = name or f'search_{object_type}'

        with self.make_request('GET', f'{UDM_BASE_PATH}/{object_type}/', params=params, name=search_name) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    count = data.get('results', 0)
                    response.success()
                    return True, count
                except json.JSONDecodeError:
                    response.failure('Invalid JSON response')
                    return False, 0
            else:
                response.failure(f'Search failed: {response.status_code}')
                raise Exception(response.text, response.status_code)

    def get_object(self, object_type: str, object_dn: str, name: str | None = None) -> tuple[bool, dict]:
        """Get a single object by DN."""
        get_name = name or f'get_{object_type.rsplit("/", maxsplit=1)[-1]}'

        with self.make_request('GET', f'{UDM_BASE_PATH}/{object_type}/{object_dn}', name=get_name) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    response.success()
                    return True, data
                except json.JSONDecodeError:
                    response.failure('Invalid JSON response')
                    return False, {}
            else:
                response.failure(f'Get object failed: {response.status_code}')
                return False, {}

    def modify_object(self, object_type: str, object_dn: str, modifications: dict, name: str | None = None) -> bool:
        """Modify an object with the given modifications."""
        success, obj_data = self.get_object(object_type, object_dn, name=f'get_{object_type.rsplit("/", maxsplit=1)[-1]}_for_modify')
        if not success:
            return False

        if 'properties' not in obj_data:
            obj_data['properties'] = {}

        obj_data['properties'].update(modifications)

        if 'uuid' in obj_data:
            del obj_data['uuid']
        if 'uri' in obj_data:
            del obj_data['uri']
        if 'id' in obj_data:
            del obj_data['id']
        if '_links' in obj_data:
            del obj_data['_links']
        if '_embedded' in obj_data:
            del obj_data['_embedded']

        modify_name = name or f'modify_{object_type.rsplit("/", maxsplit=1)[-1]}'

        with self.make_request('PUT', f'{UDM_BASE_PATH}/{object_type}/{object_dn}', json=obj_data, name=modify_name) as response:
            if response.status_code in [200, 204]:
                response.success()
                return True
            else:
                response.failure(f'Modify failed: {response.status_code}')
                return False

    def delete_object(self, object_type: str, object_dn: str) -> bool:
        """Delete an given object"""
        with self.make_request('DELETE', f'{UDM_BASE_PATH}/{object_type}/{object_dn}', name='delete_object') as response:
            if response.status_code in [200, 204]:
                response.success()
                return True
            else:
                response.failure(f'Delete failed: {response.status_code}')
                return False

    def move_object(self, object_type: str, object_dn: str, new_position: str, name: str | None = None) -> tuple[bool, str]:
        """Move an object to a new position."""
        success, obj_data = self.get_object(object_type, object_dn, name=f'get_{object_type.rsplit("/", maxsplit=1)[-1]}_for_move')
        if not success:
            return False, ''

        rdn = object_dn.split(',', 1)[0]
        new_dn = f'{rdn},{new_position}'

        obj_data['position'] = new_position

        if 'uuid' in obj_data:
            del obj_data['uuid']
        if 'uri' in obj_data:
            del obj_data['uri']
        if 'id' in obj_data:
            del obj_data['id']
        if '_links' in obj_data:
            del obj_data['_links']
        if '_embedded' in obj_data:
            del obj_data['_embedded']

        move_name = name or f'move_{object_type.rsplit("/", maxsplit=1)[-1]}'

        with self.make_request('PUT', f'{UDM_BASE_PATH}/{object_type}/{object_dn}', json=obj_data, name=move_name) as response:
            if response.status_code in [200, 204]:
                response.success()
                return True, new_dn
            else:
                response.failure(f'Move failed: {response.status_code} - {response.text}')
                return False, ''

    def modify_group_membership(
        self, group_dn: str, users_to_add: list[str] | None = None, users_to_remove: list[str] | None = None, name: str | None = None,
    ) -> bool:
        """Modify group membership by adding or removing users."""
        patch_operations = []

        if users_to_add:
            for user_dn in users_to_add:
                patch_operations.append({
                    'op': 'add',
                    'path': '/properties/users/-',
                    'value': user_dn,
                })

        if users_to_remove:
            success, group_data = self.get_object('groups/group', group_dn, name='get_group_for_membership')
            if not success:
                return False
            current_members = group_data.get('properties', {}).get('users', [])
            for user_dn in users_to_remove:
                if user_dn in current_members:
                    index = current_members.index(user_dn)
                    patch_operations.append({
                        'op': 'remove',
                        'path': f'/properties/users/{index}',
                    })

        if not patch_operations:
            return True

        modify_name = name or 'modify_group_membership'
        headers = {'Content-Type': 'application/json-patch+json'}

        with self.make_request('PATCH', f'{UDM_BASE_PATH}/groups/group/{group_dn}', json=patch_operations, headers=headers, name=modify_name) as response:
            if response.status_code in [200, 204]:
                response.success()
                return True
            else:
                response.failure(f'Modify group membership failed: {response.status_code}')
                return False

    def cleanup_created_objects(self) -> None:
        """Clean up all objects created by this client."""
        for obj_type, obj_dn in self.created_objects:
            try:
                with self.make_request('DELETE', f'{UDM_BASE_PATH}/{obj_type}/{obj_dn}', name='cleanup_object') as response:
                    if response.status_code in [200, 204, 404]:
                        logging.debug(f'Cleaned up {obj_type}: {obj_dn}')
                    else:
                        logging.warning(f'Failed to cleanup {obj_type} {obj_dn}: {response.status_code}')
            except Exception as e:
                logging.warning(f'Exception during cleanup of {obj_type} {obj_dn}: {e}')


class UDMTestDataGenerator:
    """Generates test data for UDM objects."""

    def __init__(self, prefix: str = 'perftest'):
        """Initialize with naming prefix."""
        self.prefix = prefix
        self.counters = {'user': 0, 'group': 0}

    def next_user_data(self, password: str = 'Univention.123') -> dict:
        """Generate data for next test user."""
        self.counters['user'] += 1
        counter = self.counters['user']

        username = f'{self.prefix}_user_{counter}_{generate_random_string(4)}'
        lastname = f'TestUser{counter}'

        return {
            'username': username,
            'lastname': lastname,
            'password': password,
            'description': f'Performance test user {counter}',
        }

    def next_group_data(self) -> dict:
        """Generate data for next test group."""
        self.counters['group'] += 1
        counter = self.counters['group']

        groupname = f'{self.prefix}_group_{counter}_{generate_random_string(4)}'

        return {
            'name': groupname,
            'description': f'Performance test group {counter}',
        }


# Global collections for tracking created objects across users
created_users = []
created_groups = []


def add_created_user(user_dn: str) -> None:
    """Add user DN to global tracking."""
    if user_dn not in created_users:
        created_users.append(user_dn)


def add_created_group(group_dn: str) -> None:
    """Add group DN to global tracking."""
    if group_dn not in created_groups:
        created_groups.append(group_dn)


def get_random_created_user() -> str | None:
    """Get a random user DN from created users."""
    return random.choice(created_users) if created_users else None


def get_random_created_group() -> str | None:
    """Get a random group DN from created groups."""
    return random.choice(created_groups) if created_groups else None


# Common LDAP filters
LDAP_FILTERS = {
    'all_users': '(objectClass=posixAccount)',
    'all_groups': '(objectClass=univentionGroup)',
    'test_users': '(&(objectClass=posixAccount)(uid=*test*))',
    'test_groups': '(&(objectClass=univentionGroup)(cn=*test*))',
    'perftest_users': '(&(objectClass=posixAccount)(uid=perftest*))',
    'perftest_groups': '(&(objectClass=univentionGroup)(cn=perftest*))',
}


def get_ldap_filter(filter_name: str) -> str:
    """Get a predefined LDAP filter."""
    return LDAP_FILTERS.get(filter_name, filter_name)


# Logging setup
def setup_logging(level: str = 'INFO') -> logging.Logger:
    """Setup logging for UDM tests."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    return logging.getLogger(__name__)


# Common task weight configurations
TASK_WEIGHTS = {
    'search_heavy': {
        'search_users': 8,
        'search_groups': 8,
        'create_user': 5,
        'create_group': 5,
        'get_single_user': 4,
        'get_single_group': 4,
        'modify_user': 3,
        'modify_group': 3,
        'search_filtered': 2,
        'bulk_operations': 1,
    },
    'crud_balanced': {
        'create_user': 3,
        'create_group': 3,
        'search_users': 4,
        'search_groups': 4,
        'get_single_user': 2,
        'get_single_group': 2,
        'modify_user': 2,
        'modify_group': 2,
    },
    'simple': {
        'create_user': 3,
        'create_group': 3,
        'search_users': 5,
        'search_groups': 5,
        'get_single_user': 2,
        'get_single_group': 2,
    },
}


def get_task_weights(profile: str = 'search_heavy') -> dict:
    """Get task weight configuration by profile name."""
    return TASK_WEIGHTS.get(profile, TASK_WEIGHTS['search_heavy'])
