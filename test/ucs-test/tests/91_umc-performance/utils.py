# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import json
import logging
import os
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup


log = logging.getLogger(__name__)


USE_KEYCLOAK = os.environ.get('USE_KEYCLOAK', '1') == '1'
current_user = 0
start_user = 0
final_user = 5000
TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', '60'))

entry = '/univention/saml/'
session_cookie_name = 'UMCSessionId'
session_info = '/univention/get/session-info'
logout_entry = '/univention/logout'


def get_credentials() -> tuple[str, str]:
    global current_user
    current_user += 1
    if current_user > final_user:
        current_user = start_user
    return 'testuser%d' % current_user, 'univention'


def login_via_saml(client, username: str | None = None, password: str | None = None, prefix: str = ''):
    with client.get(entry, allow_redirects=True, timeout=TIMEOUT, catch_response=True, name=f'{prefix} login 1 {entry}') as req1:
        if req1.status_code != 401 and not (200 <= req1.status_code <= 399):
            req1.failure(f'Expected status code 401 or a status code between 200 and 399: {req1.status_code}')
            return None

        req1.success()
        if req1.text is None or len(req1.text) == 0:
            req1.failure('UCS: got no data')
            return None

        kerberos_redirect_url = get_kerberos_redirect(req1.text)
        idp_login_site = req1

    if kerberos_redirect_url:
        with client.get(kerberos_redirect_url, timeout=TIMEOUT, catch_response=True, name=f'{prefix} kerberos redirect page') as krb_redir:
            idp_login_site = krb_redir

    login_link, login_params = get_login_params(idp_login_site)
    if username is None or password is None:
        username, password = get_credentials()
    login_params.update(
        {
            'username': username,
            'password': password,
        }
    )

    with client.post(login_link, data=login_params, name=f'{prefix} login 2 POST credentials', catch_response=True, timeout=TIMEOUT) as req3:
        if not (200 <= req3.status_code <= 399):
            return None
        if req3.text is None or len(req3.text) == 0:
            req3.failure('UCS: got no data')
            return None
        error_responses = ['Nutzername oder Passwort falsch', 'Invalid username or password', 'Incorrect username or password']
        if any(msg in req3.text for msg in error_responses):
            req3.failure('UCS: wrong username or password')
            return None

        return do_saml_login_at_umc(client, req3, name=f'{prefix} login 3 {entry} POST saml response')


def do_saml_iframe_session_refresh(client, prefix: str = ''):
    with client.get('/univention/saml/iframe', allow_redirects=False, timeout=TIMEOUT, catch_response=True, name=f'{prefix} iframe 1 /univention/saml/iframe') as req1:
        if req1.status_code != 302:
            req1.failure(f'Expected 302: {req1.status_code}')
            return None
        if 'Location' not in req1.headers:
            req1.failure('UCS: got no location')
            return None
        location = req1.headers['Location']
    with client.get(location, allow_redirects=True, timeout=TIMEOUT, catch_response=True, name=f'{prefix} iframe 2 {urlparse(location).path}') as req2:
        if req2.status_code != 200:
            req2.failure(f'Expected 200: {req2.status_code}')
            return None

        return do_saml_login_at_umc(client, req2, name=f'{prefix} iframe 3 {entry} POST SAML response')


def do_saml_login_at_umc(client, req, **kwargs):
    saml_response, relay_state = get_SAML_response(req.text)
    if not saml_response:
        log.warning('Got no RelayState/SAMLResponse: %s %s', req.url, req.status_code)
        log.warning('%r', req.text)
        req.failure('UCS: Got no RelayState/SAMLResponse')
        return None

    with client.post(entry, data={'SAMLResponse': saml_response, 'RelayState': relay_state}, timeout=TIMEOUT, allow_redirects=True, catch_response=True, **kwargs) as req3:
        if req3.status_code != 200:
            req3.failure(f'Expected 200: {req3.status_code}')
            return None

        cookie = next((cookie.value for cookie in client.cookiejar if cookie.name == session_cookie_name), None)
        if not cookie:
            req3.failure(f'UCS: got no cookie for {session_cookie_name}')
        return cookie


def get_login_params(req):
    soup = BeautifulSoup(req.text, features='lxml')
    login_params = {}
    try:
        if USE_KEYCLOAK:
            login_link = soup.select_one('form[id="kc-form-login"]')['action']
            return login_link, login_params
        else:
            auth_state = soup.select_one('input[name="AuthState"]')['value']
            login_params['AuthState'] = auth_state
            # login_params["submit"] = "Anmelden"
            login_link = req.url  # SimpleSAMLphp has "?" as url, so the URL is the same
    except TypeError:
        log.warning('Got no AuthState or kc-form-login form: %s', req.url)
        log.warning('%r', req.text)
        req.failure('UCS: Got no AuthState or kc-form-login form')
        return None, None
    return login_link, login_params


def get_SAML_response(text: str) -> tuple:
    try:
        soup = BeautifulSoup(text, features='lxml')
        saml_response = soup.select_one('input[name="SAMLResponse"]')['value']
        relay_state = soup.select_one('input[name="RelayState"]')['value']
        return saml_response, relay_state
    except (AttributeError, KeyError, TypeError):
        return None, None


def get_kerberos_redirect(text: str) -> str | None:
    try:
        soup = BeautifulSoup(text, 'lxml')
        title = soup.find('title')
        if title and 'Kerberos' in title.text:
            return soup.find('body').findChild('form').attrs.get('action')
    except AttributeError:
        return None


def replay_har(har_file, client, host: str, verify, session_id: str | None = None) -> None:
    def to_dict(obj):
        return {entry['name']: entry['value'] for entry in obj}

    with open(har_file) as fd:
        har = json.load(fd)
    for entry in har['log']['entries']:
        request = entry['request']
        url = request['url']
        method = request['method']
        response_code = entry['response']['status']
        url_parts = urlparse(url)
        if entry['time'] == 0:
            # was cached
            continue
        if url_parts.netloc == 'www.piwik.univention.de':
            continue
        _host = host
        if url_parts.path.startswith('/simplesamlphp/'):  # TODO: do the same for Keycloak
            continue
        # if url contain /univention/{saml,auth,command,upload,set,get}.* then skip
        if not any(url_parts.path.startswith('/univention/' + x) for x in ['saml', 'auth', 'command', 'upload', 'set', 'get']):
            continue
        url = urlunparse(url_parts._replace(netloc=_host))
        if response_code == 0:
            continue
        headers = to_dict(request['headers'])
        headers.pop('Cookie', None)
        headers.pop('Host', None)
        headers.pop('Referer', None)
        kwargs = {}
        if method == 'POST' and request.get('postData') and request['postData']['mimeType'] == 'application/x-www-form-urlencoded':
            kwargs['data'] = to_dict(request['postData']['params'])
        if method == 'POST' and request.get('postData') and request['postData']['mimeType'] == 'application/json':
            kwargs['json'] = json.loads(request['postData']['text'])
        if 'X-XSRF-Protection' in headers:
            headers['X-XSRF-Protection'] = session_id
        with client.request(method, url, headers=headers, allow_redirects=False, verify=verify, catch_response=True, **kwargs) as resp:
            if resp.status_code == response_code:
                resp.success()
