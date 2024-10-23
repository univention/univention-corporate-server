#!/usr/share/ucs-test/runner /usr/share/ucs-test/locust-docker SAMLSessionRefresh
## desc: "make 5000 SAML logins and refresh sessions after a while via iframe / passive SAML login"
## exposure: safe
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## tags: [producttest]
## env:
##   LOCUST_SPAWN_RATE: "12"
##   LOCUST_RUN_TIME: "20m"
##   LOCUST_USERS: "1400"
##   LOCUST_THROUGHPUT: "100"
##   LOCUST_USER_CLASSES: SAMLSessionRefresh
##   USE_KEYCLOAK: "1"
##   WAIT_MAX: "180"
##   REQUEST_TIMEOUT: "120"
from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

import gevent
from locust import FastHttpUser, events, run_single_user, task
from locust_plugins import constant_total_ips
from locust_plugins.listeners.jmeter import JmeterListener
from utils import TIMEOUT, do_saml_iframe_session_refresh, get_credentials, login_via_saml


WAIT_MAX = int(os.environ.get('WAIT_MAX', '120'))


class SAMLSessionRefresh(FastHttpUser):
    throughput = int(os.environ.get('LOCUST_THROUGHPUT', '100'))
    print(f'Running with a target throughput of {throughput}')
    wait_time = constant_total_ips(throughput)
    network_timeout = TIMEOUT
    connection_timeout = TIMEOUT
    insecure = True

    @events.init.add_listener
    def on_init(environment, **_kwargs):
        environment.stats.use_response_times_cache = True
        JmeterListener(env=environment, results_filename='/mnt/locust/jmeter_results_SAMLSessionRefresh.csv', timestamp_format='%Y/%m/%d %H:%M:%S')

    @task
    def login_refresh_logout(self):
        self.username, self.password = get_credentials()

        self.client.cookiejar.clear()
        next_path = ''

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
        umc_session_id = login_via_saml(self.client, self.username, self.password, prefix='05')

        if umc_session_id is None:
            logging.info('Login failed')
            return

        # 11. GET /univention/portal/
        with self.client.get('/univention/portal/', allow_redirects=False, timeout=TIMEOUT, catch_response=True, name='06 /univention/portal/') as resp:
            if resp.status_code != 200:
                resp.failure(f'Expected 200: {resp.status_code}')
                return

        # 12. GET /univention/get/session-info
        with self.client.get('/univention/get/session-info', allow_redirects=False, timeout=TIMEOUT, catch_response=True, name='07 /univention/get/session-info') as resp:
            if resp.status_code != 200:
                resp.failure(f'Expected 200: {resp.status_code}')
                return

        # 13. GET /univention/get/modules
        with self.client.get('/univention/get/modules', allow_redirects=False, timeout=TIMEOUT, catch_response=True, name='08 /univention/get/modules') as resp:
            if resp.status_code != 200:
                resp.failure(f'Expected 200: {resp.status_code}')
                return

        # sleep before re-freshing session via iframe
        gevent.sleep(WAIT_MAX, ref=False)

        # 14. GET /univention/get/session-info
        with self.client.get('/univention/get/session-info', allow_redirects=False, timeout=TIMEOUT, catch_response=True, name='09 /univention/get/session-info') as resp:
            if resp.status_code != 200:
                resp.failure(f'Expected 200: {resp.status_code}')
                return

        # 15. GET /univention/saml/iframe
        umc_session_id = do_saml_iframe_session_refresh(self.client, prefix='10')
        if umc_session_id is None:
            logging.info('Session refresh failed')
            return

        # 16. GET /univention/get/session-info
        with self.client.get('/univention/get/session-info', allow_redirects=False, timeout=TIMEOUT, catch_response=True, name='11 /univention/get/session-info') as resp:
            if resp.status_code != 200:
                resp.failure(f'Expected 200: {resp.status_code}')
                return


if __name__ == '__main__':
    run_single_user(SAMLSessionRefresh)
