#!/usr/bin/env python3

from html.parser import HTMLParser

import random
from bs4 import BeautifulSoup
import univention.testing.utils as utils
from locust import HttpUser, task, constant_throughput

html = HTMLParser()

account = utils.UCSTestDomainAdminCredentials()

WAIT_MIN = 1
WAIT_MAX = 1
hosts = ["https://master.ucs.test", "https://backup.ucs.test"]
#hosts = ["https://master.ucs.test"]
login_user = ["testuser" + str(i) for i in range(10000)]


def logout_at_idp(client, host):
    logout = "/univention/logout"
    uri = host + logout
    with client.get(uri, name="/univention/logout/", allow_redirects=True, timeout=30, catch_response=True) as req3:
        if not (200 <= req3.status_code <= 399):
            return


def login_at_idp_with_credentials(client, login_link):
    data = {'username': 'Administrator', 'password': "univention"}
    with client.post(login_link, name="/realms/ucs/login-actions/authenticate", allow_redirects=True, timeout=30, catch_response=True, data=data) as req2:
        soup = BeautifulSoup(req2.content, features="lxml")
        try:
            saml_response = soup.find("input", {"name": "SAMLResponse"}).get("value")
        except AttributeError:
            print(soup)
            return
        if not saml_response:
            return
        if not (200 <= req2.status_code <= 399):
            return


def entry(client, host):
    entry = "/univention/saml/"
    uri = host + entry
    try:
        with client.get(uri, name="/univention/saml/", allow_redirects=True, timeout=30, catch_response=True) as req1:
            if not (200 <= req1.status_code <= 399):
                return
            if req1.content is None or len(req1.content) == 0:
                return
        soup = BeautifulSoup(req1.content, features="lxml")
        login_link = soup.find("form", {"id": "kc-form-login"}).get("action")
        login_link = html.unescape(login_link)
        login_at_idp_with_credentials(client, login_link)
    finally:
        #logout_at_idp(client, host)
        client.cookies.clear()


class QuickstartUser(HttpUser):
    wait_time = constant_throughput(0.1)

    @task
    def get_samlSession(self):
        host = random.choice(hosts)
        entry(self.client, host)
