#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker UserCreationTest
# /usr/share/ucs-test/runner /usr/share/ucs-test/locust --spawn-rate 20 -u 20 -t 2m --csv UserCreation --html UserCreation.html UserCreationTest
## desc: "UDM REST API performance test for user creation operations"
## exposure: dangerous
## tags: [producttest, SKIP]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## env:
##   LOCUST_SPAWN_RATE: "0.1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "20"
##   LOCUST_USER_CLASSES: UserCreationTest
##   WAIT_MIN: "0"
##   WAIT_MAX: "0"
##   TIMEOUT: "300"

from locust import FastHttpUser, between, events, task
from rest_utils import UDMRestClient, UDMTestDataGenerator, get_config, get_ldap_containers, setup_logging


# Configuration
WAIT_MIN = get_config('WAIT_MIN', 0)
WAIT_MAX = get_config('WAIT_MAX', 0)

# Setup logging
log = setup_logging()


class UserCreationTest(FastHttpUser):
    wait_time = between(WAIT_MIN, WAIT_MAX)

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


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    # Check if the request is the first one using context
    if context.get("is_first_request", True):
        context["is_first_request"] = False
        return  # Returning None prevents the request from being logged


if __name__ == '__main__':
    print('This script should be run with the Locust command:')
    print('locust -f 92_udm-rest-performance/01_user_creation.py --host https://master.ucs.test')
    print('\nOr for a quick test:')
    print('locust -f 92_udm-rest-performance/01_user_creation.py --host https://master.ucs.test -u 1 -t 30s --headless')
