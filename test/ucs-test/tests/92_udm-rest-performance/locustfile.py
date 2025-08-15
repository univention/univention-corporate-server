#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import random
import time

from locust import FastHttpUser, events, task
from locust.runners import LocalRunner, MasterRunner
from rest_utils import UDMRestClient, UDMTestDataGenerator, get_ldap_containers, setup_logging


# Setup logging
log = setup_logging()


class CheckStats:
    min_num_requests = None


class UserCreationTest(FastHttpUser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.udm_client = None
        self.data_generator = None
        self.containers = None

    def on_start(self):
        """Initialize session with UDM client and data generator."""
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='usercreation')
        self.containers = get_ldap_containers()
        log.info('User creation test started')

    def on_stop(self):
        """Clean up created objects."""
        if self.udm_client:
            self.udm_client.cleanup_created_objects()
        log.info('User creation test stopped')

    @task(10)
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

    @task(2)
    def create_bulk_users(self):
        """Create multiple users in quick succession."""
        for i in range(3):
            user_data = self.data_generator.next_user_data(password='Univention.123')
            success, _user_dn = self.udm_client.create_user(
                username=user_data['username'],
                lastname=user_data['lastname'],
                password=user_data['password'],
                description=f'Bulk user {i + 1} - {user_data["description"]}',
            )
            if not success:
                raise Exception(f'Failed to create user: {user_data["username"]}')


class UserSearchTest(FastHttpUser):

    filters_expected_results = []
    connection_timeout = 120.0

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

    @task(8)
    def search_users(self):
        """Search for users with filter."""
        search_filter, expected_results = random.choice(UserSearchTest.filters_expected_results)
        success, _count = self.udm_client.search_objects(
            object_type='users/user',
            position=self.containers['users'],
            filter_expr=search_filter,
            name='search_users',
        )
        log.debug(f'search_users result count: {_count}')
        if not success:
            raise Exception('Failed to search filtered users')
        assert _count >= expected_results, f'{_count} >= {expected_results}'


@events.quitting.add_listener
def check_results(environment, **kwargs):
    if isinstance(environment.runner, MasterRunner):
        stats = environment.stats.serialize_stats()
        if stats:
            log.debug('checking results')
            if CheckStats.min_num_requests:
                num_requests = stats[0]['num_requests']
                assert num_requests >= CheckStats.min_num_requests, f'{num_requests} >= {CheckStats.min_num_requests}'


@events.quitting.add_listener
def jmeter_summary(environment, **kwargs):
    if isinstance(environment.runner, (MasterRunner, LocalRunner)):
        stats = environment.stats.serialize_stats()
        log_file = f'{environment.parsed_options.csv_prefix}_jmeter_summary.log'
        log_dir = os.path.join(os.path.dirname(environment.parsed_options.csv_prefix), 'jmeter')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'{os.path.basename(environment.parsed_options.csv_prefix)}.log')
        if stats:
            name = stats[0]['name']
            requests = stats[0]['num_requests']
            total_time = stats[0]['last_request_timestamp'] - stats[0]['start_time']
            rps = requests / total_time
            avg_rt = stats[0]['total_response_time'] / requests
            min_rt = stats[0]['min_response_time']
            max_rt = stats[0]['max_response_time']
            err = stats[0]['num_failures']
            err_perc = err * 100 / requests
            with open(log_file, 'w') as fh:
                # 2025-08-25 10:15:42,719 INFO o.a.j.r.Summariser: summary =   60000 in 3s =   1.0/s Avg: 3225 Min: 150 Max: 350 Err:   2 (0.67%)
                fh.write('jmeter.reporters.Summariser: Generate Summary Results\n')
                fh.write(time.strftime('%Y-%m-%d %H:%M:%S,000'))
                fh.write(f' INFO o.a.j.r.Summariser: {name} = {requests} in {round(total_time, 2)}s = {round(rps, 4)}/s')
                fh.write(f' Avg: {int(avg_rt)} Min: {int(min_rt)} Max: {int(max_rt)} Err: {err} ({round(err_perc, 2)}%)')
                fh.write('\n')


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    # Check if the request is the first one using context
    if context.get("is_first_request", True):
        context["is_first_request"] = False
        return  # Returning None prevents the request from being logged
