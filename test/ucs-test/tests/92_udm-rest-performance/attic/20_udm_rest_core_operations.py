#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker UDMRestCoreOperations
# /usr/share/ucs-test/runner /usr/share/ucs-test/locust --spawn-rate 20 -u 20 -t 5m --csv UDMRestCore --html UDMRestCore.html UDMRestCoreOperations
## desc: "Core UDM REST API performance test for users and groups"
## exposure: safe
## tags: [producttest, SKIP]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## env:
##   LOCUST_SPAWN_RATE: "0.1"
##   LOCUST_RUN_TIME: "10m"
##   LOCUST_USERS: "100"
##   LOCUST_USER_CLASSES: UDMRestCoreOperations
##   WAIT_MIN: "0"
##   WAIT_MAX: "0"
##   TIMEOUT: "300"

import time

from locust import FastHttpUser, between, events, task
from rest_utils import (
    UDMRestClient, UDMTestDataGenerator, get_config, get_ldap_containers, get_ldap_filter, get_random_created_group,
    get_random_created_user, setup_logging,
)


# Configuration
WAIT_MIN = get_config('WAIT_MIN', 1)
WAIT_MAX = get_config('WAIT_MAX', 3)

# Setup logging
log = setup_logging()


class UDMRestCoreOperations(FastHttpUser):
    wait_time = between(WAIT_MIN, WAIT_MAX)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.udm_client = None
        self.data_generator = None
        self.containers = None

    def on_start(self):
        """Initialize session with UDM client and data generator."""
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='perftest')
        self.containers = get_ldap_containers()
        log.info('Core operations test user started')

    def on_stop(self):
        """Clean up created objects."""
        if self.udm_client:
            self.udm_client.cleanup_created_objects()
        log.info('Core operations test user stopped')

    @task(5)
    def create_user(self):
        """Create a new user."""
        user_data = self.data_generator.next_user_data(password='Univention.123')

        success, _user_dn = self.udm_client.create_user(
            username=user_data['username'],
            lastname=user_data['lastname'],
            password=user_data['password'],
            description=user_data['description'],
        )

        if not success:
            raise Exception(f'Failed to create user: {user_data["username"]}')

    @task(5)
    def create_group(self):
        """Create a new group."""
        group_data = self.data_generator.next_group_data()

        success, _group_dn = self.udm_client.create_group(
            groupname=group_data['name'],
            description=group_data['description'],
        )

        if not success:
            raise Exception(f'Failed to create group: {group_data["name"]}')

    @task(8)
    def search_users(self):
        """Search for users."""
        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr=get_ldap_filter('all_users'),
            name='search_users',
        )

        if not success:
            raise Exception('Failed to search users')

    @task(8)
    def search_groups(self):
        """Search for groups."""
        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr=get_ldap_filter('all_groups'),
            name='search_groups',
        )

        if not success:
            raise Exception('Failed to search groups')

    @task(4)
    def get_single_user(self):
        """Get a specific user by DN."""
        user_dn = get_random_created_user()
        if user_dn:
            success, _user_data = self.udm_client.get_object(
                object_type='users/user',
                object_dn=user_dn,
                name='get_single_user',
            )

            if not success:
                raise Exception('Failed to retrieve user')

    @task(4)
    def get_single_group(self):
        """Get a specific group by DN."""
        group_dn = get_random_created_group()
        if group_dn:
            success, _group_data = self.udm_client.get_object(
                object_type='groups/group',
                object_dn=group_dn,
                name='get_single_group',
            )

            if not success:
                raise Exception('Failed to retrieve group')

    @task(3)
    def modify_user(self):
        """Modify an existing user."""
        user_dn = get_random_created_user()
        if user_dn:
            modifications = {
                'description': f'Modified at {int(time.time())}',
            }

            success = self.udm_client.modify_object(
                object_type='users/user',
                object_dn=user_dn,
                modifications=modifications,
                name='modify_user',
            )

            if not success:
                raise Exception('Failed to modify user')

    @task(3)
    def modify_group(self):
        """Modify an existing group."""
        group_dn = get_random_created_group()
        if group_dn:
            modifications = {
                'description': f'Modified at {int(time.time())}',
            }

            success = self.udm_client.modify_object(
                object_type='groups/group',
                object_dn=group_dn,
                modifications=modifications,
                name='modify_group',
            )

            if not success:
                raise Exception('Failed to modify group')

    @task(2)
    def search_users_filtered(self):
        """Search for users with filter."""
        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr=get_ldap_filter('perftest_users'),
            name='search_users_filtered',
        )

        if not success:
            raise Exception('Failed to search users')

    @task(2)
    def search_groups_filtered(self):
        """Search for groups with filter."""
        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr=get_ldap_filter('perftest_groups'),
            name='search_groups_filtered',
        )

        if not success:
            raise Exception('Failed to search groups')

    @task(1)
    def bulk_search_users(self):
        """Search for many users with pagination."""
        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr=get_ldap_filter('all_users'),
            name='bulk_search_users',
        )

        if not success:
            raise Exception('Failed to search users')

    @task(1)
    def bulk_search_groups(self):
        """Search for many groups with pagination."""
        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr=get_ldap_filter('all_groups'),
            name='bulk_search_groups',
        )

        if not success:
            raise Exception('Failed to search groups')

    @task(2)
    def get_specific_user(self):
        """Get a specific user."""
        user_dn = get_random_created_user()
        if user_dn:
            success, _user_data = self.udm_client.get_object(
                object_type='users/user',
                object_dn=user_dn,
                name='get_user',
            )

            if not success:
                raise Exception(f'Failed to get user: {user_dn}')

    @task(2)
    def get_specific_group(self):
        """Get a specific group."""
        group_dn = get_random_created_group()
        if group_dn:
            success, _group_data = self.udm_client.get_object(
                object_type='groups/group',
                object_dn=group_dn,
                name='get_group',
            )

            if not success:
                raise Exception(f'Failed to get group: {group_dn}')


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    # Check if the request is the first one using context
    if context.get("is_first_request", True):
        context["is_first_request"] = False
        return  # Returning None prevents the request from being logged


if __name__ == '__main__':
    # This script should be run with Locust command, not directly
    print('This script should be run with the Locust command:')
    print('locust -f 92_udm-rest-performance/01_udm_rest_core_operations.py --host https://master.ucs.test')
    print('\nOr for a quick test:')
    print('locust -f 92_udm-rest-performance/01_udm_rest_core_operations.py --host https://master.ucs.test -u 1 -t 30s --headless')
