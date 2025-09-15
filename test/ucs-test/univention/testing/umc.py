#!/usr/bin/python3
#
# UCS test connections to remote UMC Servers
#
# SPDX-FileCopyrightText: 2016-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import pprint
import sys
from collections.abc import Iterable
from html.parser import HTMLParser
from typing import Any, Self
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from univention.config_registry import ConfigRegistry
from univention.lib.umc import Client as _Client


class Client(_Client):

    print_response = True
    print_request_data = True

    @classmethod
    def get_test_connection(cls, hostname: str | None = None, *args: Any, **kwargs: Any) -> Self:
        ucr = ConfigRegistry()
        ucr.load()
        username = ucr.get('tests/domainadmin/account')
        username = username.split(',')[0][len('uid='):]
        password = ucr.get('tests/domainadmin/pwd')
        return cls(hostname, username, password, *args, **kwargs)

    def umc_command(self, *args: Any, **kwargs: Any) -> Self:
        self.print_request_data = kwargs.pop('print_request_data', True)
        self.print_response = kwargs.pop('print_response', True)
        try:
            return super().umc_command(*args, **kwargs)
        finally:
            self.print_request_data = True
            self.print_response = True

    def request(self, method: str, path: str, data: Any = None, headers: Any = None) -> Any:
        print('')
        print('*** UMC request: "%s %s" %s' % (method, path, '(%s)' % (data.get('flavor'),) if isinstance(data, dict) else ''))
        if self.print_request_data:
            print(f'UMC request payload: \n{pprint.pformat(data)}')
        try:
            response = super().request(method, path, data, headers)
        except Exception:
            print(f'UMC request failed: {sys.exc_info()[1]}')
            print('')
            raise
        if self.print_response:
            print(f'*** UMC response: \n{pprint.pformat(response.data)}\n***')
        else:
            print('*** UMC response received')
        print('')
        return response


class SamlLoginError(Exception):
    pass


class GetHtmlTagValue(HTMLParser):
    def __init__(self, tag: str, condition: tuple[str, str], value_name: str) -> None:
        self.tag = tag
        self.condition = condition
        self.value_name = value_name
        self.value: str | None = None
        super().__init__()

    def handle_starttag(self, tag: str, attrs: Iterable[tuple[str, str | None]]) -> None:
        if tag == self.tag and self.condition in attrs:
            for attr in attrs:
                if attr[0] == self.value_name:
                    self.value = attr[1]


def get_html_tag_value(page: str, tag: str, condition: tuple[str, str], value_name: str) -> str:
    htmlParser = GetHtmlTagValue(tag, condition, value_name)
    htmlParser.feed(page)
    htmlParser.close()
    assert htmlParser.value is not None
    return htmlParser.value


class ClientSaml(Client):

    def authenticate(self, *args: Any) -> None:
        self.authenticate_saml(*args)

    def authenticate_saml(self, *args: Any) -> None:
        self.__samlSession = requests.Session()

        saml_login_url = "https://%s/univention/saml/" % self.hostname
        print('GET SAML login form at: %s' % saml_login_url)
        saml_login_page = self.__samlSession.get(saml_login_url)
        keycloak_no_kerberos_redirect = get_html_tag_value(saml_login_page.text, 'form', ('method', 'POST'), 'action')
        saml_login_page = self.__samlSession.get(keycloak_no_kerberos_redirect)
        saml_login_page.raise_for_status()
        saml_idp_login_ans = self._login_at_idp_with_credentials(saml_login_page)

        print('SAML message received from %s' % saml_idp_login_ans.url)
        self._send_saml_response_to_sp(saml_idp_login_ans)
        self.cookies.update(self.__samlSession.cookies.items())

    def _login_at_idp_with_credentials(self, saml_login_page: Any) -> Any:
        """Send login form to IdP"""
        data = {'username': self.username, 'password': self.password}
        saml_login_url = get_html_tag_value(saml_login_page.text, 'form', ('method', 'post'), 'action')
        print('Post SAML login form to: %s' % saml_login_url)
        saml_idp_login_ans = self.__samlSession.post(saml_login_url, data=data)
        saml_idp_login_ans.raise_for_status()
        if 'umcLoginWarning' in saml_idp_login_ans.text:
            raise SamlLoginError(f'Login failed?:\n{saml_idp_login_ans.text}')
        return saml_idp_login_ans

    def _send_saml_response_to_sp(self, saml_idp_login_ans: Any) -> None:
        sp_login_url = get_html_tag_value(saml_idp_login_ans.text, 'form', ('method', 'post'), 'action')
        saml_msg = get_html_tag_value(saml_idp_login_ans.text, 'input', ('name', 'SAMLResponse'), 'value')
        relay_state = get_html_tag_value(saml_idp_login_ans.text, 'input', ('name', 'RelayState'), 'value')
        print('Post SAML msg to: %s' % sp_login_url)
        self.__samlSession.post(sp_login_url, data={'SAMLResponse': saml_msg, 'RelayState': relay_state}).raise_for_status()


class ClientOIDC(Client):

    def authenticate(
        self,
        username: str,
        password: str,
        portal_fqdn: str | None = None,
        kc_idp_hint: str | None = None,
    ) -> None:
        self.session = requests.Session()
        server = portal_fqdn or self.hostname
        url = f'https://{server}/univention/oidc/'
        # kerberos redirect
        res = self.session.get(url)
        kerberos_redirect_url = self.get_kerberos_redirect(res.text)
        assert kerberos_redirect_url, res.text
        # external idp
        if kc_idp_hint:
            res = self.session.get(kerberos_redirect_url, params={'kc_idp_hint': kc_idp_hint})
            # kerberos redirect
            kerberos_redirect_url = self.get_kerberos_redirect(res.text)
            assert kerberos_redirect_url, res.text
        res = self.session.get(kerberos_redirect_url)
        login_link = self.get_login_link(res)
        self.auth_server = urlparse(login_link).netloc
        # login
        params = {'username': username, 'password': password}
        res = self.session.post(login_link, data=params)
        assert res.status_code == 200, res.text
        assert 'authentication has failed' not in res.text, res.text
        self.cookies.update(self.session.cookies.items())

    def logout(self) -> None:
        url = f'https://{self.auth_server}/realms/ucs/protocol/openid-connect/logout'
        res = self.session.get(url, verify=False)
        assert res.status_code == 200, res.text
        session_code, url = self.get_session_code(res.text)
        res = self.session.post(f'https://{self.auth_server}{url}', data={'session_code': session_code}, verify=False)
        assert res.status_code == 200, res.text

    def get_session_code(self, text):
        try:
            soup = BeautifulSoup(text, 'lxml')
            url = soup.find('form', {'method': 'POST'}).attrs['action']
            session_code = soup.find('input', {'name': 'session_code'}).attrs['value']
            return session_code, url
        except AttributeError:
            return None, None

    def get_kerberos_redirect(self, text):
        try:
            soup = BeautifulSoup(text, 'lxml')
            title = soup.find('title')
            if title and 'Kerberos' in title.text:
                return soup.find('body').findChild('form').attrs.get('action')
        except AttributeError:
            return None

    def get_login_link(self, req):
        soup = BeautifulSoup(req.text, features='lxml')
        login_link = soup.select_one('form[id="kc-form-login"]')['action']
        return login_link
