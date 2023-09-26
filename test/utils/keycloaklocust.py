#!/usr/bin/env python3

import random
from html.parser import HTMLParser
from types import SimpleNamespace
from typing import List

from bs4 import BeautifulSoup
from diskcache import Index
from locust import HttpUser, constant_throughput, events, task
from locust_jmeter_listener import JmeterListener


USER_CACHE_PATH = "/var/lib/test-data/users"
GROUP_CACHE_PATH = "/var/lib/test-data/groups"
html = HTMLParser()
WAIT_MIN = 1
WAIT_MAX = 1


@events.init.add_listener
def on_init(environment, **kwargs):
    JmeterListener(environment)


def get_login_link(content, res):
    if content is None or len(content) == 0:
        res.failure("no content in response")
        return None
    soup = BeautifulSoup(content, features="lxml")
    login_link = soup.find("form", {"id": "kc-form-login"})
    if not login_link:
        res.failure(f"no login link in response: {content}")
        return None
    return html.unescape(login_link.get("action"))


# locust test for the login with all request
def loginEveryRequest(client, host, user, timeout=30):
    uri = f"{host}/univention/saml/"
    try:
        kerberos_redirect = None
        login_link = None
        with client.get(uri, name=uri, allow_redirects=True, timeout=timeout, catch_response=True) as res:

            if res.status_code == 401:
                soup = BeautifulSoup(res.content.decode("utf8"), "html.parser")
                title = soup.find("title")
                if title and "Kerberos" in title.text:
                    res.success()
                    kerberos_redirect = soup.find("body").findChild("form").attrs.get("action")
            else:
                login_link = get_login_link(res.content, res)

        if kerberos_redirect:
            name = kerberos_redirect.split("?")[0]
            with client.post(kerberos_redirect, name=f"{name}-KRB5", allow_redirects=True, timeout=timeout, catch_response=True) as res:
                login_link = get_login_link(res.content, res)

        if login_link:
            name = login_link.split("?")[0]
            data = {'username': user.username, 'password': user.password}
            with client.post(login_link, name=name, allow_redirects=True, timeout=timeout, catch_response=True, data=data) as res:
                soup = BeautifulSoup(res.content, features="lxml")
                saml_response = soup.find("input", {"name": "SAMLResponse"})
                if not saml_response:
                    res.failure(f"no saml response in: {res.text}")
                    return
    finally:
        client.cookies.clear()


# locust test for login, but only include the one UMC request for the stats
def loginOneRequest(client, host, user, timeout=30):
    uri = f"{host}/univention/saml/"
    try:
        # we only want to cound this one request to umc, everything else will be done silently
        with client.get(uri, name=uri, allow_redirects=True, timeout=timeout, catch_response=True) as res:
            # keycloak want kerberos by default, we have to handle this
            # here manually by making another request to keycloak
            if res.status_code == 401:
                soup = BeautifulSoup(res.content.decode("utf8"), "html.parser")
                title = soup.find("title")
                if title and "Kerberos" in title.text:
                    res.success()
                    kerberos_redirect = soup.find("body").findChild("form").attrs.get("action")
                    name = kerberos_redirect.split("?")[0]
                    res1 = client.post(kerberos_redirect, name=name, allow_redirects=True, catch_response=True, timeout=timeout)
                    content = res1.content
            else:
                content = res.content
            # check the we got a proper response
            login_link = get_login_link(content, res)
            if login_link:
                name = login_link.split("?")[0]
                data = {'username': user.username, 'password': user.password}
                res2 = client.post(login_link, name=name, allow_redirects=True, catch_response=True, timeout=timeout, data=data)
                soup = BeautifulSoup(res2.content, features="lxml")
                saml_response = soup.find("input", {"name": "SAMLResponse"})
                if not saml_response:
                    res.failure(f"no saml response in: {res.text}")
    finally:
        client.cookies.clear()


class TestData(object):

    def __init__(self):
        self.user_cache = Index(USER_CACHE_PATH)
        self.group_cache = Index(GROUP_CACHE_PATH)
        self.user_list = list(self.user_cache.keys())
        self.group_list = list(self.group_cache.keys())
        self.user_index = 0
        self.group_index = 0
        # check that the database is not empty
        assert self.user_list
        assert self.group_list

    @property
    def users(self) -> List[str]:
        return self.user_list

    @property
    def groups(self) -> List[str]:
        return self.group_list

    def user(self, username: str) -> SimpleNamespace:
        return SimpleNamespace(**self.user_cache[username])

    def random_user(self) -> SimpleNamespace:
        return SimpleNamespace(**self.user_cache[random.choice(self.user_list)])

    def random_users(self, k: int = 10) -> List[SimpleNamespace]:
        return [
            SimpleNamespace(**self.user_cache[user])
            for user in random.sample(self.user_list, k=k)
        ]

    def walk_users(self) -> SimpleNamespace:
        try:
            self.user_list[self.user_index]
        except IndexError:
            self.user_index = 0
        user = self.user_cache[self.user_list[self.user_index]]
        self.user_index += 1
        return SimpleNamespace(**user)

    def group(self, name: str) -> SimpleNamespace:
        return SimpleNamespace(**self.db["groups"][name])

    def random_group(self) -> SimpleNamespace:
        return SimpleNamespace(**self.group_cache[random.choice(self.group_list)])

    def random_groups(self, k: int = 10) -> List[SimpleNamespace]:
        return [
            SimpleNamespace(**self.group_cache[group])
            for group in random.sample(self.group_list, k=k)
        ]

    def walk_groups(self) -> SimpleNamespace:
        try:
            self.group_list[self.group_index]
        except IndexError:
            self.group_index = 0
        group = self.group_cache[self.group_list[self.group_index]]
        self.group_index += 1
        return SimpleNamespace(**group)


class PrimaryAndBackup(HttpUser):
    wait_time = constant_throughput(0.1)
    td = TestData()
    hosts = ["https://primary.ucs.test", "https://backup1.ucs.test"]

    @task
    def get_samlSession(self):
        user = self.td.walk_users()
        host = random.choice(self.hosts)
        loginOneRequest(self.client, host, user)


class PrimaryOnly(HttpUser):
    wait_time = constant_throughput(0.1)
    td = TestData()

    @task
    def get_samlSession(self):
        user = self.td.walk_users()
        host = "https://primary.ucs.test"
        loginOneRequest(self.client, host, user)
        #loginEveryRequest(self.client, host, user)
