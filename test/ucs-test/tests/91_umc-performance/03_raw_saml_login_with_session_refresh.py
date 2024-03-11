#!/usr/share/ucs-test/runner locust --spawn-rate 10 -u 5000 -t 15m --csv SAMLSessionRefresh --html SAMLSessionRefresh.html SAMLSessionRefresh
## desc: "Replay a captured HAR of the login flow and use UMC afterwards"
## exposure: safe

import logging
import os
from urllib.parse import urlparse

import gevent
from locust import HttpUser, constant, task
from utils import TIMEOUT, do_saml_iframe_session_refresh, get_credentials, login_via_saml


USE_TASK = os.environ.get("USE_TASK", "0") == "1"
WAIT_MIN = int(os.environ.get("WAIT_MIN", "180"))
WAIT_MAX = int(os.environ.get("WAIT_MAX", "300"))


# TODO: use FastHttpUser instead of HttpUser
# https://docs.locust.io/en/stable/increase-performance.html
class SAMLSessionRefresh(HttpUser):
    wait_time = constant(WAIT_MAX)

    # @task
    def on_start(self):
        self.username, self.password = get_credentials()
        if USE_TASK:
            return

        # 1. GET /
        with self.client.get("/", allow_redirects=False, timeout=TIMEOUT, catch_response=True, name="01 /") as resp:
            if resp.status_code != 302:
                resp.failure(f"Expected 302: {resp.status_code}")
                return

            # 2. GET /univention/
            next_path = urlparse(resp.headers["Location"]).path
            with self.client.get(next_path, allow_redirects=False, timeout=TIMEOUT, catch_response=True, name="02 /univention") as resp:
                if resp.status_code != 302:
                    resp.failure(f"Expected 302: {resp.status_code}")
                    return

                # 3. GET /univention/portal/
                next_path = urlparse(resp.headers["Location"]).path
                with self.client.get(next_path, allow_redirects=False, timeout=TIMEOUT, catch_response=True, name="03 /univention/portal") as resp:
                    if resp.status_code != 200:
                        resp.failure(f"Expected 200: {resp.status_code}")
                        return

        # 4. GET /univention/get/session-info
        with self.client.get("/univention/get/session-info", allow_redirects=False, timeout=TIMEOUT, catch_response=True, name="04 /univention/get/session-info") as resp:
            if resp.status_code != 401:
                resp.failure(f"Expected 401: {resp.status_code}")
                return
            else:
                resp.success()

        # 5-10. login
        umc_session_id = login_via_saml(self.client, self.username, self.password, prefix="05")

        if umc_session_id is None:
            logging.info("Login failed")
            return

        # 11. GET /univention/portal/
        with self.client.get("/univention/portal/", allow_redirects=False, timeout=TIMEOUT, catch_response=True, name="06 /univention/portal/") as resp:
            if resp.status_code != 200:
                resp.failure(f"Expected 200: {resp.status_code}")
                return

        # 12. GET /univention/get/session-info
        with self.client.get("/univention/get/session-info", allow_redirects=False, timeout=TIMEOUT, catch_response=True, name="07 /univention/get/session-info") as resp:
            if resp.status_code != 200:
                resp.failure(f"Expected 200: {resp.status_code}")
                return

        # 13. GET /univention/get/modules
        with self.client.get("/univention/get/modules", allow_redirects=False, timeout=TIMEOUT, catch_response=True, name="08 /univention/get/modules") as resp:
            if resp.status_code != 200:
                resp.failure(f"Expected 200: {resp.status_code}")
                return

        # sleep before re-freshing session via iframe
        gevent.sleep(WAIT_MAX, ref=False)

        # 14. GET /univention/get/session-info
        with self.client.get("/univention/get/session-info", allow_redirects=False, timeout=TIMEOUT, catch_response=True, name="09 /univention/get/session-info") as resp:
            if resp.status_code != 200:
                resp.failure(f"Expected 200: {resp.status_code}")
                return

        # 15. GET /univention/saml/iframe
        umc_session_id = do_saml_iframe_session_refresh(self.client, umc_session_id, prefix="10")
        if umc_session_id is None:
            logging.info("Login failed")
            return

        # 16. GET /univention/get/session-info
        with self.client.get("/univention/get/session-info", allow_redirects=False, timeout=TIMEOUT, catch_response=True, name="11 /univention/get/session-info") as resp:
            if resp.status_code != 200:
                resp.failure(f"Expected 200: {resp.status_code}")
                return

    @task
    def login(self):
        pass

    def on_stop(self):
        self.client.close()
