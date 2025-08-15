#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker ObjectRetrievalTest
# /usr/share/ucs-test/runner /usr/share/ucs-test/locust --spawn-rate 20 -u 20 -t 2m --csv ObjectRetrieval --html ObjectRetrieval.html ObjectRetrievalTest
## desc: "UDM REST API performance test for object retrieval operations"
## exposure: safe
## tags: [producttest, SKIP]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## env:
##   LOCUST_SPAWN_RATE: "0.1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "20"
##   LOCUST_USER_CLASSES: ObjectRetrievalTest
##   WAIT_MIN: "0"
##   WAIT_MAX: "0"
##   TIMEOUT: "300"

import random

from locust import FastHttpUser, between, events, task
from rest_utils import (
    UDMRestClient, UDMTestDataGenerator, get_config, get_ldap_containers, get_random_created_group,
    get_random_created_user, setup_logging,
)


# Configuration
WAIT_MIN = get_config('WAIT_MIN', 0)
WAIT_MAX = get_config('WAIT_MAX', 0)

# Setup logging
log = setup_logging()


class ObjectRetrievalTest(FastHttpUser):
    wait_time = between(WAIT_MIN, WAIT_MAX)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.udm_client = None
        self.data_generator = None
        self.containers = None

    def on_start(self):
        """Initialize session with UDM client and data generator."""
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='objretrieval')
        self.containers = get_ldap_containers()
        log.info('Object retrieval test started')

    def on_stop(self):
        """Clean up created objects."""
        if self.udm_client:
            self.udm_client.cleanup_created_objects()
        log.info('Object retrieval test stopped')

    @task(10)
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

    @task(10)
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

    @task(6)
    def get_user_full_details(self):
        """Get a user with all available details."""
        user_dn = get_random_created_user()
        if user_dn:
            success, _user_data = self.udm_client.get_object(
                object_type='users/user',
                object_dn=user_dn,
                name='get_user_full_details',
            )

            if not success:
                raise Exception('Failed to retrieve user')

    @task(6)
    def get_group_full_details(self):
        """Get a group with all available details."""
        group_dn = get_random_created_group()
        if group_dn:
            success, _group_data = self.udm_client.get_object(
                object_type='groups/group',
                object_dn=group_dn,
                name='get_group_full_details',
            )

            if not success:
                raise Exception('Failed to retrieve group')

    @task(4)
    def get_multiple_users_sequential(self):
        """Get multiple users in sequence."""
        for i in range(3):
            user_dn = get_random_created_user()
            if user_dn:
                success, _user_data = self.udm_client.get_object(
                    object_type='users/user',
                    object_dn=user_dn,
                    name='get_multiple_users',
                )

                if not success:
                    raise Exception('Failed to retrieve user')

    @task(4)
    def get_multiple_groups_sequential(self):
        """Get multiple groups in sequence."""
        for i in range(3):
            group_dn = get_random_created_group()
            if group_dn:
                success, _group_data = self.udm_client.get_object(
                    object_type='groups/group',
                    object_dn=group_dn,
                    name='get_multiple_groups',
                )

                if not success:
                    raise Exception('Failed to retrieve group')

    @task(2)
    def get_user_by_username(self):
        """Get a user by searching for username first, then retrieving."""
        # First search for a user
        success, results = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr='(uid=objretrieval*)',
            name='search_for_retrieval',
        )
        if not success:
            raise Exception('Failed to search for user')

        if success and results and len(results) > 0:
            # Get the first result's DN and retrieve full object
            user_dn = results[0].get('dn')
            if user_dn:
                success, _user_data = self.udm_client.get_object(
                    object_type='users/user',
                    object_dn=user_dn,
                    name='get_user_by_username',
                )

                if not success:
                    raise Exception('Failed to retrieve user')

    @task(2)
    def get_group_by_name(self):
        """Get a group by searching for name first, then retrieving."""
        # First search for a group
        success, results = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr='(cn=objretrieval*)',
            name='search_group_for_retrieval',
        )

        if not success:
            raise Exception('Failed to search for group')

        if success and results and len(results) > 0:
            # Get the first result's DN and retrieve full object
            group_dn = results[0].get('dn')
            if group_dn:
                success, _group_data = self.udm_client.get_object(
                    object_type='groups/group',
                    object_dn=group_dn,
                    name='get_group_by_name',
                )

                if not success:
                    raise Exception('Failed to retrieve group')

    @task(1)
    def get_nonexistent_object(self):
        """Try to get a non-existent object (error handling test)."""
        fake_dn = f'uid=nonexistent-{random.randint(1000, 9999)},cn=users,dc=test'

        success, _user_data = self.udm_client.get_object(
            object_type='users/user',
            object_dn=fake_dn,
            name='get_nonexistent_object',
        )

        # This should fail gracefully
        if not success:
            log.debug(f'Correctly handled non-existent object: {fake_dn}')


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    # Check if the request is the first one using context
    if context.get("is_first_request", True):
        context["is_first_request"] = False
        return  # Returning None prevents the request from being logged


if __name__ == '__main__':
    print('This script should be run with the Locust command:')
    print('locust -f 92_udm-rest-performance/05_object_retrieval.py --host https://master.ucs.test')
    print('\nOr for a quick test:')
    print('locust -f 92_udm-rest-performance/05_object_retrieval.py --host https://master.ucs.test -u 1 -t 30s --headless')
