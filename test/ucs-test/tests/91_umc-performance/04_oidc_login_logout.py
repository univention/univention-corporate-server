#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker OIDCLogin
## desc: "make 5000 SAML logins and refresh sessions after a while via iframe / passive SAML login"
## exposure: safe
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## tags: [producttest]
## env:
##   LOCUST_SPAWN_RATE: "10"
##   LOCUST_RUN_TIME: "20m"
##   LOCUST_USERS: "5000"
##   LOCUST_USER_CLASSES: OIDCLogin
##   USE_KEYCLOAK: "1"
##   WAIT_MAX: "180"
##   REQUEST_TIMEOUT: "120"
from __future__ import annotations

import logging
import os
import time
from urllib.parse import urlparse

from locust import FastHttpUser, constant, events, run_single_user, task
from locust_jmeter_listener import JmeterListener
from utils import TIMEOUT, get_credentials, login_via_oidc


WAIT_MAX = int(os.environ.get('WAIT_MAX', '120'))


class OIDCLogin(FastHttpUser):
    wait_time = constant(WAIT_MAX)
    network_timeout = TIMEOUT
    connection_timeout = TIMEOUT
    insecure = True

    @events.init.add_listener
    def on_init(environment, **_kwargs):
        environment.stats.use_response_times_cache = True
        try:
            JmeterListener(environment, results_filename='/mnt/locust/jmeter_results_SAMLSessionRefresh.csv')
        except PermissionError:
            print("JmeterListener disabled")

    @task
    def task1(self):
        self.username, self.password = get_credentials()

        next_path = ''
        self.client.cookiejar.clear()
        # 1. GET /
        with self.client.get('/', allow_redirects=False, timeout=TIMEOUT, catch_response=True, name='01 /') as resp:
            if resp.status_code != 302:
                resp.failure(f'Expected 302: {resp.status_code}')
                return

            next_path = urlparse(resp.headers['Location']).path

        # 2. GET /univention/
        with self.client.get(next_path, allow_redirects=False, timeout=TIMEOUT, catch_response=True, name='02 /univention') as resp:
            if resp.status_code != 302:
                resp.failure(f'Expected 302: {resp.status_code}')
                return

            next_path = urlparse(resp.headers['Location']).path

        # 3. GET /univention/portal/
        with self.client.get(next_path, allow_redirects=False, timeout=TIMEOUT, catch_response=True, name='03 /univention/portal') as resp:
            if resp.status_code != 200:
                resp.failure(f'Expected 200: {resp.status_code}')
                return

        # 4. GET /univention/get/session-info
        with self.client.get('/univention/get/session-info', allow_redirects=False, timeout=TIMEOUT, catch_response=True, name='04 /univention/get/session-info') as resp:
            if resp.status_code != 401:
                resp.failure(f'Expected 401: {resp.status_code}')
                return
            else:
                resp.success()

        # 5-10. login
        umc_session_id = login_via_oidc(self.client, self.username, self.password, prefix='05')
        if umc_session_id is None:
            logging.info('Login failed')
            return

        # 12. GET /univention/get/session-info
        with self.client.get('/univention/get/session-info', allow_redirects=False, timeout=TIMEOUT, catch_response=True, name='07 /univention/get/session-info') as resp:
            if resp.status_code != 200:
                resp.failure(f'Expected 200: {resp.status_code}')
                return

        with self.client.get('/univention/portal/portal.json', timeout=TIMEOUT, catch_response=True, name='fetch portal.json') as resp:
            if resp.status_code != 200:
                resp.failure(f'Expected 200: {resp.status_code}')

        print(f'sleeping for {WAIT_MAX}')
        time.sleep(WAIT_MAX)

        # 14. GET /univention/get/session-info
        with self.client.get('/univention/get/session-info', allow_redirects=False, timeout=TIMEOUT, catch_response=True, name='09 /univention/get/session-info') as resp:
            if resp.status_code != 200:
                resp.failure(f'Expected 200: {resp.status_code}')
                return

        time.sleep(999999999999)


if __name__ == '__main__':
    run_single_user(OIDCLogin)
