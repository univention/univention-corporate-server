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
def on_init(environment,**kwargs):
    JmeterListener(environment)


def logout_at_idp(client, host,):
    logout = "/univention/logout"
    uri = host + logout
    with client.get(uri, name="/univention/logout/", allow_redirects=True, timeout=30, catch_response=True,) as req3:
        if not (200 <= req3.status_code <= 399):
            return


def login_at_idp_with_credentials(client, login_link, user,):
    data = {'username': user.username, 'password': user.password}
    name = login_link.split("?")[0]
    with client.post(login_link, name=name, allow_redirects=True, timeout=30, catch_response=True, data=data,) as res:
        if res.status_code != 200:
            return
        soup = BeautifulSoup(res.content, features="lxml",)
        saml_response = soup.find("input", {"name": "SAMLResponse"},)
        if not saml_response:
            res.failure(f"no saml response in: {res.text}")
            return


def entry(client, host, user,):
    entry = "/univention/saml/"
    uri = host + entry
    try:
        with client.get(uri, name=uri, allow_redirects=True, timeout=30, catch_response=True,) as res:
            if res.status_code == 401:
                soup = BeautifulSoup(res.content.decode("utf8"), "html.parser",)
                title = soup.find("title")
                if title and "Kerberos" in title.text:
                    res.success()
                    action = soup.find("body").findChild("form").attrs.get("action")
                    res = client.post(action, name=action, allow_redirects=True, timeout=30, catch_response=True,)

            if res.status_code != 200:
                return
            if res.content is None or len(res.content) == 0:
                return
            soup = BeautifulSoup(res.content, features="lxml",)
            login_link = soup.find("form", {"id": "kc-form-login"},)
            if not login_link:
                return
            login_link = html.unescape(login_link.get("action"))
        login_at_idp_with_credentials(client, login_link, user,)
    finally:
        pass
        #logout_at_idp(client, host)
        # client.cookiejar.clear()


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

    def user(self, username: str,) -> SimpleNamespace:
        return SimpleNamespace(**self.user_cache[username])

    def random_user(self) -> SimpleNamespace:
        return SimpleNamespace(**self.user_cache[random.choice(self.user_list)])

    def random_users(self, k: int = 10,) -> List[SimpleNamespace]:
        return [
            SimpleNamespace(**self.user_cache[user])
            for user in random.sample(self.user_list, k=k,)
        ]

    def walk_users(self) -> SimpleNamespace:
        try:
            self.user_list[self.user_index]
        except IndexError:
            self.user_index = 0
        user = self.user_cache[self.user_list[self.user_index]]
        self.user_index += 1
        return SimpleNamespace(**user)

    def group(self, name: str,) -> SimpleNamespace:
        return SimpleNamespace(**self.db["groups"][name])

    def random_group(self) -> SimpleNamespace:
        return SimpleNamespace(**self.group_cache[random.choice(self.group_list)])

    def random_groups(self, k: int = 10,) -> List[SimpleNamespace]:
        return [
            SimpleNamespace(**self.group_cache[group])
            for group in random.sample(self.group_list, k=k,)
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
        entry(self.client, host, user,)


class PrimaryOnly(HttpUser):
    wait_time = constant_throughput(0.1)
    td = TestData()
    host = "https://primary.ucs.test"

    @task
    def get_samlSession(self):
        user = self.td.walk_users()
        entry(self.client, self.host, user,)
