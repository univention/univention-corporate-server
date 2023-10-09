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


def get_login_link(content):
    if content is None or len(content) == 0:
        return None
    soup = BeautifulSoup(content, features="lxml")
    login_link = soup.find("form", {"id": "kc-form-login"})
    if not login_link:
        return None
    return html.unescape(login_link.get("action"))


def get_SAML_response(content):
    try:
        soup = BeautifulSoup(content, features="lxml")
        saml_response = soup.find("input", {"name": "SAMLResponse"}).attrs["value"]
        relay_state = soup.find("input", {"name": "RelayState"}).attrs["value"]
        return saml_response, relay_state
    except (AttributeError, KeyError, TypeError):
        return None, None


def get_keberos_redirect(content):
    try:
        soup = BeautifulSoup(content.decode("utf8"), "html.parser")
        title = soup.find("title")
        if title and "Kerberos" in title.text:
            return soup.find("body").findChild("form").attrs.get("action")
    except AttributeError:
        return None


# locust test for the login with all request
def loginEveryRequest(client, host, user, timeout=30, umc_login=False):
    uri = f"{host}/univention/saml/"
    try:
        # umc
        with client.get(uri, name=f"{uri}-INIT", allow_redirects=True, timeout=timeout, catch_response=True) as res1:
            # another redirect because of the kerberos configuration in keycloak
            if res1.status_code == 401:
                redirect = get_keberos_redirect(res1.content)
                if not redirect:
                    res1.failure("No kerberos redirect")
                    return
                name = redirect.split("?")[0]
                with client.post(redirect, name=f"{name}-KRB5", allow_redirects=True, timeout=timeout) as res2:
                    login_link = get_login_link(res2.content)
                    res1.success()
            else:
                login_link = get_login_link(res1.content)
            if not login_link:
                res1.failure("No login link from keycloak")
                return

        # keycloak login
        name = login_link.split("?")[0]
        data = {'username': user.username, 'password': user.password}
        with client.post(login_link, name=f"{name}-LOGIN", allow_redirects=True, catch_response=True, timeout=timeout, data=data) as res3:
            saml_response, relay_state = get_SAML_response(res3.content)
            if not saml_response or not relay_state:
                res3.failure("no SAMLResponse/RelayState in keycloak response")
                return

        if umc_login:
            # back to umc
            data = {'SAMLResponse': saml_response, 'RelayState': relay_state}
            with client.post(uri, name=f"{uri}-LOGIN", allow_redirects=True, timeout=timeout, catch_response=True, data=data) as res4:
                umc_user = client.cookies.get("UMCUsername")
                if not umc_user or umc_user != user.username:
                    res4.failure("Could not find UMCUsername")
                    return

    finally:
        client.cookies.clear()


# locust test for login, but only include the one UMC request for the stats
def loginOneRequest(client, host, user, timeout=30):
    uri = f"{host}/univention/saml/"
    try:
        # we only want to cound this one request to umc, everything else will be done silently
        with client.get(uri, name=uri, allow_redirects=True, timeout=timeout, catch_response=True) as res1:
            # keycloak wants kerberos by default, we have to handle this
            # here manually by making another request to keycloak
            if res1.status_code == 401:
                redirect = get_keberos_redirect(res1.content)
                if not redirect:
                    res1.failure("No kerberos redirect")
                    return
                res2 = client.post(redirect, allow_redirects=True, catch_response=True, timeout=timeout)
                login_link = get_login_link(res2.content)
                res1.success()
            else:
                login_link = get_login_link(res1.content)
            # check the we got a proper response
            if not login_link:
                res1.failure("No login link from keycloak")
                return

            # keycloak login
            data = {'username': user.username, 'password': user.password}
            res3 = client.post(login_link, allow_redirects=True, catch_response=True, timeout=timeout, data=data)
            saml_response, relay_state = get_SAML_response(res3.content)
            if not saml_response or not relay_state:
                res1.failure("no SAMLResponse/RelayState in keycloak response")
                return

            # back to umc
            data = {'SAMLResponse': saml_response, 'RelayState': relay_state}
            client.post(uri, allow_redirects=True, catch_response=True, timeout=timeout, data=data)
            umc_user = client.cookies.get("UMCUsername")
            if not umc_user or umc_user != user.username:
                res1.failure("Could not find UMCUsername")
                return
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
        loginEveryRequest(self.client, host, user)


class PrimaryOnly(HttpUser):
    wait_time = constant_throughput(0.1)
    td = TestData()

    @task
    def get_samlSession(self):
        user = self.td.walk_users()
        host = "https://primary.ucs.test"
        loginEveryRequest(self.client, host, user)


class PrimaryOnlyWithUMCLogin(HttpUser):
    wait_time = constant_throughput(0.1)
    td = TestData()

    @task
    def get_samlSession(self):
        user = self.td.walk_users()
        host = "https://primary.ucs.test"
        loginEveryRequest(self.client, host, user, umc_login=True)
