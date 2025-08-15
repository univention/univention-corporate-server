#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker GroupSearchTest
# /usr/share/ucs-test/runner /usr/share/ucs-test/locust --spawn-rate 20 -u 20 -t 2m --csv GroupSearch --html GroupSearch.html GroupSearchTest
## desc: "UDM REST API performance test for group search operations"
## exposure: safe
## tags: [producttest, SKIP]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## env:
##   LOCUST_SPAWN_RATE: "0.1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "20"
##   LOCUST_USER_CLASSES: GroupSearchTest
##   WAIT_MIN: "0"
##   WAIT_MAX: "0"
##   TIMEOUT: "300"

import random

from locust import FastHttpUser, between, events, task
from rest_utils import (
    UDMRestClient, UDMTestDataGenerator, get_config, get_ldap_containers, get_ldap_filter, setup_logging,
)


# Configuration
WAIT_MIN = get_config('WAIT_MIN', 1)
WAIT_MAX = get_config('WAIT_MAX', 3)

# Setup logging
log = setup_logging()


class GroupSearchTest(FastHttpUser):
    wait_time = between(WAIT_MIN, WAIT_MAX)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.udm_client = None
        self.data_generator = None
        self.containers = None

    def on_start(self):
        """Initialize session with UDM client and data generator."""
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='groupsearch')
        self.containers = get_ldap_containers()
        log.info('Group search test started')

    def on_stop(self):
        """Clean up created objects."""
        if self.udm_client:
            self.udm_client.cleanup_created_objects()
        log.info('Group search test stopped')

    @task(15)
    def search_all_groups(self):
        """Search for all groups."""
        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr=get_ldap_filter('all_groups'),
            name='search_all_groups',
        )

        if not success:
            raise Exception('Failed to search all groups')

    @task(8)
    def search_groups_filtered(self):
        """Search for groups with filter."""
        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr=get_ldap_filter('perftest_groups'),
            name='search_groups_filtered',
        )

        if not success:
            raise Exception('Failed to search filtered groups')

    @task(6)
    def search_groups_by_name_pattern(self):
        """Search for groups by name pattern."""
        patterns = ['admin*', '*users*', 'test*', '*service*']
        pattern = random.choice(patterns)

        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr=f'(cn={pattern})',
            name='search_groups_by_pattern',
        )

        if not success:
            raise Exception('Failed to search groups by pattern')

    @task(5)
    def bulk_search_groups(self):
        """Search for many groups with pagination."""
        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr=get_ldap_filter('all_groups'),
            name='bulk_search_groups',
        )

        if not success:
            raise Exception('Failed to bulk search groups')

    @task(4)
    def search_security_groups(self):
        """Search for security groups."""
        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr='(sambaGroupType=2)',
            name='search_security_groups',
        )

        if not success:
            raise Exception('Failed to search security groups')

    @task(3)
    def search_groups_with_members(self):
        """Search for groups that have members."""
        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr='(member=*)',
            name='search_groups_with_members',
        )

        if not success:
            raise Exception('Failed to search groups with members')

    @task(2)
    def search_recently_created_groups(self):
        """Search for recently created groups."""
        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr='(&(cn=groupsearch*)(createTimestamp>=20240101000000Z))',
            name='search_recent_groups',
        )

        if not success:
            raise Exception('Failed to search recently created groups')

    @task(1)
    def search_distribution_groups(self):
        """Search for distribution groups."""
        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            filter_expr='(sambaGroupType=8)',
            name='search_distribution_groups',
        )

        if not success:
            raise Exception('Failed to search distribution groups')


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    # Check if the request is the first one using context
    if context.get("is_first_request", True):
        context["is_first_request"] = False
        return  # Returning None prevents the request from being logged+


if __name__ == '__main__':
    print('This script should be run with the Locust command:')
    print('locust -f 92_udm-rest-performance/04_group_search.py --host https://master.ucs.test')
    print('\nOr for a quick test:')
    print('locust -f 92_udm-rest-performance/04_group_search.py --host https://master.ucs.test -u 1 -t 30s --headless')
