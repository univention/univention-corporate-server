#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker UserDeleteSequentiell
## desc: "UDM REST API performance test for sequentiell user delete operations"
## exposure: dangerous
## env:
##   LOCUST_SPAWN_RATE: "1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "1"
##   LOCUST_LOGLEVEL: "INFO"
##   TIMEOUT: "300"


from locust import HttpUser, between, task
from locustfile import check_results  # noqa: F401
from locustfile import jmeter_summary  # noqa: F401
from rest_utils import UDMRestClient, UDMTestDataGenerator, get_ldap_containers, setup_logging


log = setup_logging()


class UserDeleteSequentiell(HttpUser):
    wait_time = between(0, 0)

    def on_start(self):
        log.info('User deletion test started')
        self.udm_client = UDMRestClient(self.client)
        self.data_generator = UDMTestDataGenerator(prefix='userdelete')
        self.containers = get_ldap_containers()

    @task
    def create_and_delete_user(self):
        user_data = self.data_generator.next_user_data(password='Univention.123')
        success, user_dn = self.udm_client.create_user(
            username=user_data['username'],
            lastname=user_data['lastname'],
            password=user_data['password'],
            description=user_data['description'],
        )
        if not success:
            return

        if not self.udm_client.delete_object('users/user', user_dn):
            log.warning(f'Failed to delete user: {user_dn}')
        else:
            if ('users/user', user_dn) in self.udm_client.created_objects:
                self.udm_client.created_objects.remove(('users/user', user_dn))
