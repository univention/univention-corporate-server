#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker UserSearchTest
# /usr/share/ucs-test/runner /usr/share/ucs-test/locust --spawn-rate 20 -u 20 -t 2m --csv UserSearch --html UserSearch.html UserSearchTest
## desc: "UDM REST API performance test for user search operations"
## exposure: safe
## tags: [producttest, SKIP]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## env:
##   LOCUST_SPAWN_RATE: "0.1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "20"
##   LOCUST_USER_CLASSES: UserSearchTest
##   WAIT_MIN: "0"
##   WAIT_MAX: "0"
##   TIMEOUT: "300"

import random

from locust import FastHttpUser, between, events, task
from rest_utils import (
    UDMRestClient, UDMTestDataGenerator, get_config, get_ldap_containers, get_ldap_filter, setup_logging,
)


# Configuration
WAIT_MIN = get_config('WAIT_MIN', 0)
WAIT_MAX = get_config('WAIT_MAX', 0)

# Setup logging
log = setup_logging()


class UserSearchTest(FastHttpUser):
    wait_time = between(WAIT_MIN, WAIT_MAX)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.udm_client = None
        self.data_generator = None
        self.containers = None

    def on_start(self):
        """Initialize session with UDM client and data generator."""
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='usersearch')
        self.containers = get_ldap_containers()
        log.info('User search test started')

    def on_stop(self):
        """Clean up created objects."""
        if self.udm_client:
            self.udm_client.cleanup_created_objects()
        log.info('User search test stopped')

    @task(15)
    def search_all_users(self):
        """Search for all users."""
        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr=get_ldap_filter('all_users'),
            name='search_all_users',
        )

        if not success:
            raise Exception('Failed to search all users')

    @task(8)
    def search_users_filtered(self):
        """Search for users with filter."""
        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr=get_ldap_filter('perftest_users'),
            name='search_users_filtered',
        )

        if not success:
            raise Exception('Failed to search filtered users')

    @task(6)
    def search_users_by_username_pattern(self):
        """Search for users by username pattern."""
        patterns = ['test*', '*admin*', 'user*', '*service*']
        pattern = random.choice(patterns)

        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr=f'(uid={pattern})',
            name='search_users_by_pattern',
        )

        if not success:
            raise Exception('Failed to search users by pattern')

    @task(5)
    def bulk_search_users(self):
        """Search for many users with pagination."""
        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr=get_ldap_filter('all_users'),
            name='bulk_search_users',
        )

        if not success:
            raise Exception('Failed to bulk search users')

    @task(4)
    def search_users_by_lastname(self):
        """Search for users by lastname pattern."""
        lastnames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones']
        lastname = random.choice(lastnames)

        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr=f'(sn=*{lastname}*)',
            name='search_users_by_lastname',
        )

        if not success:
            raise Exception('Failed to search users by lastname')

    @task(3)
    def search_users_with_email(self):
        """Search for users with email addresses."""
        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr='(mail=*)',
            name='search_users_with_email',
        )

        if not success:
            raise Exception('Failed to search users with email addresses')

    @task(2)
    def search_recently_created_users(self):
        """Search for recently created users."""
        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr='(&(uid=usersearch*)(createTimestamp>=20240101000000Z))',
            name='search_recent_users',
        )

        if not success:
            raise Exception('Failed to search recently created users')

    @task(1)
    def search_disabled_users(self):
        """Search for disabled users."""
        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr='(userAccountControl:1.2.840.113556.1.4.803:=2)',
            name='search_disabled_users',
        )

        if not success:
            raise Exception('Failed to search disabled users')


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    # Check if the request is the first one using context
    if context.get("is_first_request", True):
        context["is_first_request"] = False
        return  # Returning None prevents the request from being logged


if __name__ == '__main__':
    print('This script should be run with the Locust command:')
    print('locust -f 92_udm-rest-performance/03_user_search.py --host https://master.ucs.test')
    print('\nOr for a quick test:')
    print('locust -f 92_udm-rest-performance/03_user_search.py --host https://master.ucs.test -u 1 -t 30s --headless')
