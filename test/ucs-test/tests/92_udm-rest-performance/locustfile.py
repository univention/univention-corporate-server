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
    if context.get("is_first_request", True):
        context["is_first_request"] = False
        return


class UserCRUDTest(FastHttpUser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.udm_client = None
        self.data_generator = None
        self.containers = None

    def on_start(self):
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='usercrud')
        self.containers = get_ldap_containers()
        log.info('User CRUD test started')

    def on_stop(self):
        if self.udm_client:
            self.udm_client.cleanup_created_objects()
        log.info('User CRUD test stopped')

    @task(5)
    def create_user(self):
        user_data = self.data_generator.next_user_data(password='Univention.123')
        success, _user_dn = self.udm_client.create_user(
            username=user_data['username'],
            lastname=user_data['lastname'],
            password=user_data['password'],
            description=user_data['description'],
        )
        if not success:
            raise AssertionError(f'Failed to create user: {user_data["username"]}')

    @task(8)
    def read_user(self):
        user_dn = random.choice(self.udm_client.created_objects) if self.udm_client.created_objects else None
        if not user_dn or user_dn[0] != 'users/user':
            return
        success, _user_data = self.udm_client.get_object('users/user', user_dn[1], name='read_user')
        if not success:
            raise AssertionError(f'Failed to read user: {user_dn[1]}')

    @task(4)
    def modify_user_description(self):
        user_dn = random.choice([dn for obj_type, dn in self.udm_client.created_objects if obj_type == 'users/user']) if self.udm_client.created_objects else None
        if not user_dn:
            return
        new_description = f'Modified at {random.randint(1000, 9999)}'
        success = self.udm_client.modify_object('users/user', user_dn, {'description': new_description}, name='modify_user_description')
        if not success:
            raise AssertionError(f'Failed to modify user: {user_dn}')

    @task(2)
    def delete_user(self):
        user_objs = [(obj_type, dn) for obj_type, dn in self.udm_client.created_objects if obj_type == 'users/user']
        if not user_objs:
            return
        obj_type, user_dn = random.choice(user_objs)
        success = self.udm_client.delete_object(obj_type, user_dn)
        if success and (obj_type, user_dn) in self.udm_client.created_objects:
            self.udm_client.created_objects.remove((obj_type, user_dn))


class GroupCRUDTest(FastHttpUser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.udm_client = None
        self.data_generator = None
        self.containers = None

    def on_start(self):
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='groupcrud')
        self.containers = get_ldap_containers()
        log.info('Group CRUD test started')

    def on_stop(self):
        if self.udm_client:
            self.udm_client.cleanup_created_objects()
        log.info('Group CRUD test stopped')

    @task(5)
    def create_group(self):
        group_data = self.data_generator.next_group_data()
        success, _group_dn = self.udm_client.create_group(
            groupname=group_data['name'],
            description=group_data['description'],
        )
        if not success:
            raise AssertionError(f'Failed to create group: {group_data["name"]}')

    @task(8)
    def read_group(self):
        group_dn = random.choice([dn for obj_type, dn in self.udm_client.created_objects if obj_type == 'groups/group']) if self.udm_client.created_objects else None
        if not group_dn:
            return
        success, _group_data = self.udm_client.get_object('groups/group', group_dn, name='read_group')
        if not success:
            raise AssertionError(f'Failed to read group: {group_dn}')

    @task(4)
    def modify_group_description(self):
        group_dn = random.choice([dn for obj_type, dn in self.udm_client.created_objects if obj_type == 'groups/group']) if self.udm_client.created_objects else None
        if not group_dn:
            return
        new_description = f'Modified group at {random.randint(1000, 9999)}'
        success = self.udm_client.modify_object('groups/group', group_dn, {'description': new_description}, name='modify_group_description')
        if not success:
            raise AssertionError(f'Failed to modify group: {group_dn}')

    @task(6)
    def search_groups(self):
        success, _count = self.udm_client.search_objects(
            object_type='groups/group',
            position=self.containers['groups'],
            scope='sub',
            name='search_groups',
        )
        if not success:
            raise AssertionError('Failed to search groups')


class GroupMembershipTest(FastHttpUser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.udm_client = None
        self.data_generator = None
        self.containers = None

    def on_start(self):
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='groupmember')
        self.containers = get_ldap_containers()
        log.info('Group membership test started')
        for i in range(3):
            user_data = self.data_generator.next_user_data(password='Univention.123')
            self.udm_client.create_user(
                username=user_data['username'],
                lastname=user_data['lastname'],
                password=user_data['password'],
                description=user_data['description'],
            )
            group_data = self.data_generator.next_group_data()
            self.udm_client.create_group(groupname=group_data['name'], description=group_data['description'])

    def on_stop(self):
        if self.udm_client:
            self.udm_client.cleanup_created_objects()
        log.info('Group membership test stopped')

    @task(8)
    def add_user_to_group(self):
        group_dn = random.choice([dn for obj_type, dn in self.udm_client.created_objects if obj_type == 'groups/group']) if self.udm_client.created_objects else None
        user_dn = random.choice([dn for obj_type, dn in self.udm_client.created_objects if obj_type == 'users/user']) if self.udm_client.created_objects else None
        if not group_dn or not user_dn:
            return
        success = self.udm_client.modify_group_membership(group_dn=group_dn, users_to_add=[user_dn], name='add_user_to_group')
        if not success:
            raise AssertionError('Failed to add user to group')

    @task(5)
    def remove_user_from_group(self):
        group_dn = random.choice([dn for obj_type, dn in self.udm_client.created_objects if obj_type == 'groups/group']) if self.udm_client.created_objects else None
        user_dn = random.choice([dn for obj_type, dn in self.udm_client.created_objects if obj_type == 'users/user']) if self.udm_client.created_objects else None
        if not group_dn or not user_dn:
            return
        success = self.udm_client.modify_group_membership(group_dn=group_dn, users_to_remove=[user_dn], name='remove_user_from_group')
        if not success:
            raise AssertionError('Failed to remove user from group')


class MoveOperationsTest(FastHttpUser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.udm_client = None
        self.data_generator = None
        self.containers = None

    def on_start(self):
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='movetest')
        self.containers = get_ldap_containers()
        log.info('Move operations test started')
        for i in range(5):
            user_data = self.data_generator.next_user_data(password='Univention.123')
            self.udm_client.create_user(
                username=user_data['username'],
                lastname=user_data['lastname'],
                password=user_data['password'],
                description=user_data['description'],
            )
            group_data = self.data_generator.next_group_data()
            self.udm_client.create_group(groupname=group_data['name'], description=group_data['description'])

    def on_stop(self):
        if self.udm_client:
            self.udm_client.cleanup_created_objects()
        log.info('Move operations test stopped')

    @task(10)
    def move_user_back_and_forth(self):
        user_objs = [(obj_type, dn) for obj_type, dn in self.udm_client.created_objects if obj_type == 'users/user']
        if not user_objs:
            return
        obj_type, user_dn = random.choice(user_objs)
        current_position = user_dn.split(',', 1)[1]
        target_position = self.containers['users'] if current_position != self.containers['users'] else self.containers['base']
        success, new_dn = self.udm_client.move_object(object_type=obj_type, object_dn=user_dn, new_position=target_position, name='move_user')
        if success and (obj_type, user_dn) in self.udm_client.created_objects:
            self.udm_client.created_objects.remove((obj_type, user_dn))
            self.udm_client.created_objects.append((obj_type, new_dn))

    @task(8)
    def move_group_back_and_forth(self):
        group_objs = [(obj_type, dn) for obj_type, dn in self.udm_client.created_objects if obj_type == 'groups/group']
        if not group_objs:
            return
        obj_type, group_dn = random.choice(group_objs)
        current_position = group_dn.split(',', 1)[1]
        target_position = self.containers['groups'] if current_position != self.containers['groups'] else self.containers['base']
        success, new_dn = self.udm_client.move_object(object_type=obj_type, object_dn=group_dn, new_position=target_position, name='move_group')
        if success and (obj_type, group_dn) in self.udm_client.created_objects:
            self.udm_client.created_objects.remove((obj_type, group_dn))
            self.udm_client.created_objects.append((obj_type, new_dn))
