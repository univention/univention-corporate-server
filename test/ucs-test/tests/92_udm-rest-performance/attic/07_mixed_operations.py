#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker MixedOperationsTest
# /usr/share/ucs-test/runner /usr/share/ucs-test/locust --spawn-rate 20 -u 20 -t 2m --csv MixedOperations --html MixedOperations.html MixedOperationsTest
## desc: "UDM REST API performance test for mixed operations"
## exposure: safe
## tags: [producttest, SKIP]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## env:
##   LOCUST_SPAWN_RATE: "0.1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "20"
##   LOCUST_USER_CLASSES: MixedOperationsTest
##   WAIT_MIN: "0"
##   WAIT_MAX: "0"
##   TIMEOUT: "300"

import random
import time

from locust import FastHttpUser, between, events, task
from rest_utils import (
    UDMRestClient, UDMTestDataGenerator, add_created_group, get_config, get_ldap_containers, get_ldap_filter,
    get_random_created_group, get_random_created_user, setup_logging,
)


# Configuration
WAIT_MIN = get_config('WAIT_MIN', 0)
WAIT_MAX = get_config('WAIT_MAX', 0)

# Setup logging
log = setup_logging()


class MixedOperationsTest(FastHttpUser):
    wait_time = between(WAIT_MIN, WAIT_MAX)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.udm_client = None
        self.data_generator = None
        self.containers = None

    def on_start(self):
        """Initialize session with UDM client and data generator."""
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='mixed')
        self.containers = get_ldap_containers()
        log.info('Mixed operations test started')

    def on_stop(self):
        """Clean up created objects."""
        if self.udm_client:
            self.udm_client.cleanup_created_objects()
        log.info('Mixed operations test stopped')

    @task(8)
    def create_search_modify_user(self):
        """Create a user, search for it, then modify it."""
        # Create user
        user_data = self.data_generator.next_user_data(password='Univention.123')
        success, user_dn = self.udm_client.create_user(
            username=user_data['username'],
            lastname=user_data['lastname'],
            password=user_data['password'],
            description=user_data['description'],
        )

        if not success:
            raise Exception(f'Failed to create user: {user_data["username"]}')

        if success and user_dn:

            # Search for the created user
            success, _count = self.udm_client.search_objects(
                object_type='users/user',
                position=self.containers['users'],
                filter_expr=f'(uid={user_data["username"]})',
                name='mixed_search_created_user',
            )

            if not success:
                raise Exception(f'Failed to search for created user: {user_data["username"]}')

            # Modify the user
            modifications = {
                'description': f'Modified in mixed ops at {int(time.time())}',
            }

            success = self.udm_client.modify_object(
                object_type='users/user',
                object_dn=user_dn,
                modifications=modifications,
                name='mixed_modify_user',
            )

            if not success:
                raise Exception(f'Failed to modify created user: {user_data["username"]}')

    @task(8)
    def create_search_modify_group(self):
        """Create a group, search for it, then modify it."""
        # Create group
        group_data = self.data_generator.next_group_data()
        success, group_dn = self.udm_client.create_group(
            groupname=group_data['name'],
            description=group_data['description'],
        )
        if not success:
            raise Exception(f'Failed to create group: {group_data["name"]}')

        if success and group_dn:
            add_created_group(group_dn)
            log.debug(f'Created group for mixed ops: {group_data["name"]}')

            # Search for the created group
            success, _count = self.udm_client.search_objects(
                object_type='groups/group',
                position=self.containers['groups'],
                filter_expr=f'(cn={group_data["name"]})',
                name='mixed_search_created_group',
            )

            if not success:
                raise Exception(f'Failed to search for created group: {group_data["name"]}')

            # Modify the group
            modifications = {
                'description': f'Modified in mixed ops at {int(time.time())}',
            }

            success = self.udm_client.modify_object(
                object_type='groups/group',
                object_dn=group_dn,
                modifications=modifications,
                name='mixed_modify_group',
            )

            if not success:
                raise Exception(f'Failed to modify group: {group_dn}')

    @task(6)
    def search_and_retrieve_users(self):
        """Search for users then retrieve specific ones."""
        # Search for users
        success, results = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr=get_ldap_filter('mixed_users'),
            name='mixed_search_users',
        )
        if not success:
            raise Exception('Failed to search for users')

        if success and results:
            # Pick a random user from results and retrieve full details
            user_result = random.choice(results)
            user_dn = user_result.get('dn')

            if user_dn:
                success, _user_data = self.udm_client.get_object(
                    object_type='users/user',
                    object_dn=user_dn,
                    name='mixed_retrieve_user',
                )

                if not success:
                    raise Exception(f'Failed to retrieve user: {user_dn}')

    @task(6)
    def search_and_retrieve_groups(self):
        """Search for groups then retrieve specific ones."""
        # Search for groups
        success, results = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr=get_ldap_filter('mixed_groups'),
            name='mixed_search_groups',
        )
        if not success:
            raise Exception('Failed to search for groups')

        if success and results:
            # Pick a random group from results and retrieve full details
            group_result = random.choice(results)
            group_dn = group_result.get('dn')

            if group_dn:
                success, _group_data = self.udm_client.get_object(
                    object_type='groups/group',
                    object_dn=group_dn,
                    name='mixed_retrieve_group',
                )

                if not success:
                    raise Exception(f'Failed to retrieve group: {group_dn}')

    @task(3)
    def modify_and_retrieve_workflow(self):
        """Modify an object then immediately retrieve it."""
        user_dn = get_random_created_user()
        if user_dn:
            # Modify user
            timestamp = int(time.time())
            modifications = {
                'description': f'Modified then retrieved at {timestamp}',
            }

            success = self.udm_client.modify_object(
                object_type='users/user',
                object_dn=user_dn,
                modifications=modifications,
                name='mixed_modify_before_retrieve',
            )
            if not success:
                raise Exception(f'Failed to modify user: {user_dn}')

            if success:
                # Immediately retrieve to verify modification
                success, _user_data = self.udm_client.get_object(
                    object_type='users/user',
                    object_dn=user_dn,
                    name='mixed_retrieve_after_modify',
                )

                if not success:
                    raise Exception(f'Failed to retrieve user: {user_dn}')

    @task(2)
    def cross_reference_operations(self):
        """Perform operations that cross-reference users and groups."""
        user_dn = get_random_created_user()
        group_dn = get_random_created_group()

        if user_dn and group_dn:
            # Get user details
            success, _user_data = self.udm_client.get_object(
                object_type='users/user',
                object_dn=user_dn,
                name='mixed_get_user_for_xref',
            )
            if not success:
                raise Exception(f'Failed to retrieve user: {user_dn}')

            # Get group details
            success, _group_data = self.udm_client.get_object(
                object_type='groups/group',
                object_dn=group_dn,
                name='mixed_get_group_for_xref',
            )

            if not success:
                raise Exception('Failed to retrieve user or group')

    @task(1)
    def error_handling_workflow(self):
        """Test error handling in mixed operations."""
        fake_dn = f'uid=nonexistent-{random.randint(1000, 9999)},cn=users,dc=test'

        # Try to get non-existent object
        _success, _user_data = self.udm_client.get_object(
            object_type='users/user',
            object_dn=fake_dn,
            name='mixed_error_get',
        )

        # Try to modify non-existent object
        self.udm_client.modify_object(
            object_type='users/user',
            object_dn=fake_dn,
            modifications={'description': 'Should fail'},
            name='mixed_error_modify',
        )

        log.debug('Completed error handling workflow')


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    # Check if the request is the first one using context
    if context.get("is_first_request", True):
        context["is_first_request"] = False
        return  # Returning None prevents the request from being logged


if __name__ == '__main__':
    print('This script should be run with the Locust command:')
    print('locust -f 92_udm-rest-performance/07_mixed_operations.py --host https://master.ucs.test')
    print('\nOr for a quick test:')
    print('locust -f 92_udm-rest-performance/07_mixed_operations.py --host https://master.ucs.test -u 1 -t 30s --headless')
