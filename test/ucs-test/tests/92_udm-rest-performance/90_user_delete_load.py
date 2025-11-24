#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker UserDeleteLoad
## desc: "UDM REST API performance test for sequentiell user delete operations"
## exposure: dangerous
## env:
##   LOCUST_SPAWN_RATE: "0.1"
##   LOCUST_RUN_TIME: "2m"
##   LOCUST_USERS: "20"
##   LOCUST_LOGLEVEL: "INFO"
##   TIMEOUT: "300"


from locust import HttpUser, events, task
from locust.runners import MasterRunner, WorkerRunner
from locustfile import check_results  # noqa: F401
from locustfile import jmeter_summary  # noqa: F401
from rest_utils import UDMRestClient, get_config, setup_logging


log = setup_logging()


def on_get_user(environment, msg, **kwargs):
    # Fired when the master receives a message of type 'get_users'
    user = environment.users.pop()
    environment.runner.send_message('acknowledge_user', user, client_id=msg.node_id)


def on_acknowledge_user(environment, msg, **kwargs):
    # Fired when the worker receives a message of type 'acknowledge_user'
    environment.user_dn = msg.data


@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    if isinstance(environment.runner, MasterRunner):
        environment.runner.register_message('get_user', on_get_user)
    if isinstance(environment.runner, WorkerRunner):
        environment.runner.register_message('acknowledge_user', on_acknowledge_user)


@events.test_start.add_listener
def on_test_start(environment, **_kwargs):
    start = 0
    end = 10000
    name = 'testuser'
    if isinstance(environment.runner, MasterRunner):
        users = [f'uid={name}{x},cn=users,{get_config("LDAP_BASE")}' for x in range(start, end)]
        environment.users = users
    else:
        environment.user_dn = None


class UserDeleteLoad(HttpUser):

    def on_start(self):
        log.info('User deletion test started')
        self.udm_client = UDMRestClient(self.client)

    @task
    def task(self):
        user_dn = None
        self.environment.runner.send_message('get_user')
        if self.environment.user_dn:
            user_dn = self.environment.user_dn
            self.environment.user_dn = None
        if user_dn:
            if not self.udm_client.delete_object('users/user', user_dn):
                log.warning(f'Failed to delete user (may not exist): {user_dn}')
