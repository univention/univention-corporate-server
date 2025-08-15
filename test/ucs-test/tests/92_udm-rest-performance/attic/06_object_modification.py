#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker ObjectModificationTest
# /usr/share/ucs-test/runner /usr/share/ucs-test/locust --spawn-rate 20 -u 20 -t 2m --csv ObjectModification --html ObjectModification.html ObjectModificationTest
## desc: "UDM REST API performance test for object modification operations"
## exposure: safe
## tags: [producttest, SKIP]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## env:
##   LOCUST_SPAWN_RATE: "0.1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "20"
##   LOCUST_USER_CLASSES: ObjectModificationTest
##   WAIT_MIN: "0"
##   WAIT_MAX: "0"
##   TIMEOUT: "300"

import random
import time

from locust import FastHttpUser, between, events, task
from rest_utils import (
    UDMRestClient, UDMTestDataGenerator, get_config, get_ldap_containers, get_random_created_group,
    get_random_created_user, setup_logging,
)


# Configuration
WAIT_MIN = get_config('WAIT_MIN', 1)
WAIT_MAX = get_config('WAIT_MAX', 3)

# Setup logging
log = setup_logging()


class ObjectModificationTest(FastHttpUser):
    wait_time = between(WAIT_MIN, WAIT_MAX)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.udm_client = None
        self.data_generator = None
        self.containers = None

    def on_start(self):
        """Initialize session with UDM client and data generator."""
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='objmod')
        self.containers = get_ldap_containers()

        # Create some initial objects to modify
        self._create_initial_objects()
        log.info('Object modification test started')

    def on_stop(self):
        """Clean up created objects."""
        if self.udm_client:
            self.udm_client.cleanup_created_objects()
        log.info('Object modification test stopped')

    def _create_initial_objects(self):
        """Create some initial objects for modification tests."""
        # Create a few users
        for i in range(3):
            user_data = self.data_generator.next_user_data(password='Univention.123')
            success, _user_dn = self.udm_client.create_user(
                username=user_data['username'],
                lastname=user_data['lastname'],
                password=user_data['password'],
                description='Initial user for modification tests',
            )
            if not success:
                log.error(f'Failed to create user {user_data["username"]}')

        # Create a few groups
        for i in range(3):
            group_data = self.data_generator.next_group_data()
            success, _group_dn = self.udm_client.create_group(
                groupname=group_data['name'],
                description='Initial group for modification tests',
            )
            if not success:
                log.error(f'Failed to create group {group_data["name"]}')

    @task(15)
    def modify_user_description(self):
        """Modify a user's description."""
        user_dn = get_random_created_user()
        if user_dn:
            modifications = {
                'description': f'Modified at {int(time.time())}',
            }

            success = self.udm_client.modify_object(
                object_type='users/user',
                object_dn=user_dn,
                modifications=modifications,
                name='modify_user_description',
            )

            if not success:
                raise Exception(f'Failed to modify user description: {user_dn}')

    @task(15)
    def modify_group_description(self):
        """Modify a group's description."""
        group_dn = get_random_created_group()
        if group_dn:
            modifications = {
                'description': f'Modified at {int(time.time())}',
            }

            success = self.udm_client.modify_object(
                object_type='groups/group',
                object_dn=group_dn,
                modifications=modifications,
                name='modify_group_description',
            )

            if not success:
                raise Exception(f'Failed to modify group description: {group_dn}')

    @task(10)
    def modify_user_email(self):
        """Modify a user's email address."""
        user_dn = get_random_created_user()
        if user_dn:
            timestamp = int(time.time())
            modifications = {
                'email': f'modified-{timestamp}@example.com',
            }

            success = self.udm_client.modify_object(
                object_type='users/user',
                object_dn=user_dn,
                modifications=modifications,
                name='modify_user_email',
            )

            if not success:
                raise Exception(f'Failed to modify user email: {user_dn}')

    @task(8)
    def modify_user_firstname(self):
        """Modify a user's first name."""
        user_dn = get_random_created_user()
        if user_dn:
            firstnames = ['John', 'Jane', 'Bob', 'Alice', 'Mike', 'Sarah']
            modifications = {
                'firstname': random.choice(firstnames),
            }

            success = self.udm_client.modify_object(
                object_type='users/user',
                object_dn=user_dn,
                modifications=modifications,
                name='modify_user_firstname',
            )

            if not success:
                raise Exception(f'Failed to modify user firstname: {user_dn}')

    @task(6)
    def modify_user_multiple_fields(self):
        """Modify multiple user fields at once."""
        user_dn = get_random_created_user()
        if user_dn:
            timestamp = int(time.time())
            modifications = {
                'description': f'Multi-field update at {timestamp}',
                'firstname': f'Updated{timestamp % 1000}',
                'email': f'multi-{timestamp}@example.com',
            }

            success = self.udm_client.modify_object(
                object_type='users/user',
                object_dn=user_dn,
                modifications=modifications,
                name='modify_user_multiple_fields',
            )

            if not success:
                raise Exception(f'Failed to modify user multiple fields: {user_dn}')

    @task(5)
    def modify_group_multiple_fields(self):
        """Modify multiple group fields at once."""
        group_dn = get_random_created_group()
        if group_dn:
            timestamp = int(time.time())
            modifications = {
                'description': f'Multi-field group update at {timestamp}',
            }

            success = self.udm_client.modify_object(
                object_type='groups/group',
                object_dn=group_dn,
                modifications=modifications,
                name='modify_group_multiple_fields',
            )

            if not success:
                raise Exception(f'Failed to modify group multiple fields: {group_dn}')

    @task(4)
    def modify_user_phone(self):
        """Modify a user's phone number."""
        user_dn = get_random_created_user()
        if user_dn:
            phone_numbers = ['+1-555-0123', '+1-555-0456', '+1-555-0789']
            modifications = {
                'phone': random.choice(phone_numbers),
            }

            success = self.udm_client.modify_object(
                object_type='users/user',
                object_dn=user_dn,
                modifications=modifications,
                name='modify_user_phone',
            )

            if not success:
                raise Exception(f'Failed to modify user phone: {user_dn}')

    @task(3)
    def modify_user_lastname(self):
        """Modify a user's last name."""
        user_dn = get_random_created_user()
        if user_dn:
            lastnames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia']
            modifications = {
                'lastname': random.choice(lastnames),
            }

            success = self.udm_client.modify_object(
                object_type='users/user',
                object_dn=user_dn,
                modifications=modifications,
                name='modify_user_lastname',
            )

            if not success:
                raise Exception(f'Failed to modify user lastname: {user_dn}')

    @task(2)
    def modify_user_sequential(self):
        """Modify the same user multiple times sequentially."""
        user_dn = get_random_created_user()
        if user_dn:
            for i in range(3):
                modifications = {
                    'description': f'Sequential modification {i + 1} at {int(time.time())}',
                }

                success = self.udm_client.modify_object(
                    object_type='users/user',
                    object_dn=user_dn,
                    modifications=modifications,
                    name='modify_user_sequential',
                )

                if not success:
                    raise Exception(f'Failed to modify user sequentially: {user_dn}')

    @task(2)
    def modify_group_sequential(self):
        """Modify the same group multiple times sequentially."""
        group_dn = get_random_created_group()
        if group_dn:
            for i in range(3):
                modifications = {
                    'description': f'Sequential group modification {i + 1} at {int(time.time())}',
                }

                success = self.udm_client.modify_object(
                    object_type='groups/group',
                    object_dn=group_dn,
                    modifications=modifications,
                    name='modify_group_sequential',
                )

                if not success:
                    raise Exception(f'Failed to modify group sequentially: {group_dn}')

    @task(1)
    def modify_nonexistent_object(self):
        """Try to modify a non-existent object (error handling test)."""
        fake_dn = f'uid=nonexistent-{random.randint(1000, 9999)},cn=users,dc=test'
        modifications = {
            'description': 'This should fail',
        }

        success = self.udm_client.modify_object(
            object_type='users/user',
            object_dn=fake_dn,
            modifications=modifications,
            name='modify_nonexistent_object',
        )

        # This should fail gracefully
        if not success:
            log.debug(f'Correctly handled modification of non-existent object: {fake_dn}')


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    # Check if the request is the first one using context
    if context.get("is_first_request", True):
        context["is_first_request"] = False
        return  # Returning None prevents the request from being logged


if __name__ == '__main__':
    print('This script should be run with the Locust command:')
    print('locust -f 92_udm-rest-performance/06_object_modification.py --host https://master.ucs.test')
    print('\nOr for a quick test:')
    print('locust -f 92_udm-rest-performance/06_object_modification.py --host https://master.ucs.test -u 1 -t 30s --headless')
