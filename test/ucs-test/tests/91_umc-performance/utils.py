#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
import logging
import os
from contextlib import contextmanager
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup

from univention.config_registry import ucr


USE_KEYCLOAK = os.environ.get("USE_KEYCLOAK", "0") == "1"
KEYCLOAK_FQDN = ucr.get('keycloak/server/sso/fqdn', 'ucs-sso-ng.%s' % ucr['domainname'])
SSP_FQDN = ucr.get('ucs/server/sso/fqdn', 'ucs-sso.%s' % ucr.get('domainname'))
current_user = 0
start_user = 0
final_user = 5000
TIMEOUT = 60

entry = "/univention/saml/"
session_name = "UMCSessionId"
session_info = "/univention/get/session-info"
logout_entry = "/univention/logout"


@contextmanager
def ucs_sso(client):
    old_base_url = client.base_url
    client.base_url = KEYCLOAK_FQDN if USE_KEYCLOAK else SSP_FQDN
    for c in client.cookies:
        c.domain = urlparse(client.base_url).netloc

    yield client

    client.base_url = old_base_url
    for c in client.cookies:
        c.domain = urlparse(client.base_url).netloc


def get_credentials():
    global current_user
    current_user += 1
    if current_user > final_user:
        current_user = start_user
    return 'testuser%d' % current_user, 'univention'


def login_via_saml(client, username=None, password=None, prefix=""):
    with client.get(entry, allow_redirects=True, timeout=TIMEOUT, catch_response=True, name=f"{prefix} login 1 {entry}") as req1:
        if not (200 <= req1.status_code <= 399):
            # logging.warning(f"UCS: got no data: status={req1.status_code} url={req1.url}")
            return None
        if req1.content is None or len(req1.content) == 0:
            req1.failure("UCS: got no data")
            return None

        login_link, login_params = get_login_params(req1)
        if username is None or password is None:
            username, password = get_credentials()
        login_params.update({
            "username": username,
            "password": password,
        })

        with ucs_sso(client) as client:
            with client.post(
                login_link,
                data=login_params,
                cookies=req1.history[1].cookies,
                name=f"{prefix} login 2 /simplesamlphp/module.php/core/loginuserpass.php",
                catch_response=True,
                timeout=TIMEOUT
            ) as req2:
                if not (200 <= req2.status_code <= 399):
                    return None
                if req2.content is None or len(req2.content) == 0:
                    req2.failure("UCS: got no data")
                    return None
                if b'Nutzername oder Passwort falsch' in req2.content or b"Incorrect username or password." in req2.content:
                    req2.failure("UCS: wrong username or password")
                    return None

                return do_saml_login_at_umc(client, req2, None, name=f"{prefix} login 3 {entry}")
        return None


def do_saml_iframe_session_refresh(client, umc_session_id, prefix=""):
    cookies = {session_name: umc_session_id}

    with client.get("/univention/saml/iframe", cookies=cookies, allow_redirects=False, timeout=TIMEOUT, catch_response=True, name=f"{prefix} iframe 1 /univention/saml/iframe") as req1:
        if req1.status_code != 302:
            req1.failure(f"Expected 302: {req1.status_code}")
            return None
        if "Location" not in req1.headers:
            req1.failure("UCS: got no location")
            return None
        location = req1.headers["Location"]
        with ucs_sso(client) as client:
            with client.get(location, cookies=cookies, allow_redirects=True, timeout=TIMEOUT, catch_response=True, name=f"{prefix} iframe 2/simplesamlphp/saml2/idp/SSOService.php") as req2:
                if req2.status_code != 200:
                    req2.failure(f"Expected 200: {req2.status_code}")
                    return None

                return do_saml_login_at_umc(client, req2, cookies, name=f"{prefix} iframe 3 {entry}")
        return None


def do_saml_login_at_umc(client, req, cookies, **kwargs):
    saml_response, relay_state = get_SAML_response(req.content)
    if not saml_response:
        logging.warning(f"Got no RelayState/SAMLResponse: {req.url} {req.status_code}")
        logging.warning(req.content.decode("utf8"))
        req.failure("UCS: Got no RelayState/SAMLResponse")
        return None
    # url = urlparse(soup.select_one("form")["action"]).path
    with client.post(entry, data={"SAMLResponse": saml_response, "RelayState": relay_state}, timeout=TIMEOUT, allow_redirects=True, cookies=cookies, catch_response=True, **kwargs) as req3:
        if req3.status_code != 200:
            req3.failure(f"Expected 200: {req3.status_code}")
            return None
        try:  # iframe
            return req3.cookies[session_name]
        except IndexError:  # no iframe
            try:
                return req3.history[0].cookies[session_name]
            except IndexError:
                req3.failure('UCS: got no cookie for umc_session_id')


def get_login_params(req):
    soup = BeautifulSoup(req.content, features="lxml")

    login_params = {}
    if USE_KEYCLOAK:
        login_link = urlparse(soup.select_one('form[id="kc-form-login"]')["action"]).path
    else:
        try:
            auth_state = soup.select_one('input[name="AuthState"]')['value']
        except TypeError:
            logging.warning(f"Got no AuthState: {req.url}")
            logging.warning(req.content.decode("utf8"))
            req.failure("UCS: Got no AuthState")
            return None
        login_params['AuthState'] = auth_state
        # login_params["submit"] = "Anmelden"
        login_link = req.url  # SimpleSAMLphp has "?" as url, so the URL is the same
    return login_link, login_params


def get_SAML_response(content):
    try:
        soup = BeautifulSoup(content, features="lxml")
        saml_response = soup.select_one('input[name="SAMLResponse"]')['value']
        relay_state = soup.select_one('input[name="RelayState"]')['value']
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


def replay_har(har_file, client, host, verify, session_id=None):
    def to_dict(obj):
        return {entry["name"]: entry["value"] for entry in obj}

    with open(har_file) as fd:
        har = json.load(fd)
    for entry in har["log"]["entries"]:
        request = entry["request"]
        url = request["url"]
        method = request["method"]
        response_code = entry["response"]["status"]
        url_parts = urlparse(url)
        if entry["time"] == 0:
            # was cached
            continue
        if url_parts.netloc == "www.piwik.univention.de":
            continue
        _host = host
        if url_parts.path.startswith("/simplesamlphp/"):
            continue
        # if url contain /univention/{saml,auth,command,upload,set,get}.* then skip
        if not any(url_parts.path.startswith("/univention/" + x) for x in ["saml", "auth", "command", "upload", "set", "get"]):
            continue
        url = urlunparse(url_parts._replace(netloc=_host))
        if response_code == 0:
            continue
        headers = to_dict(request["headers"])
        headers.pop("Cookie", None)
        headers.pop("Host", None)
        headers.pop("Referer", None)
        kwargs = {}
        if method == "POST" and request.get("postData") and request["postData"]["mimeType"] == "application/x-www-form-urlencoded":
            kwargs["data"] = to_dict(request["postData"]["params"])
        if method == "POST" and request.get("postData") and request["postData"]["mimeType"] == "application/json":
            kwargs["json"] = json.loads(request["postData"]["text"])
        if "X-XSRF-Protection" in headers:
            headers["X-XSRF-Protection"] = session_id
            # print(headers["X-XSRF-Protection"])
        with client.request(method, url, headers=headers, allow_redirects=False, verify=verify, catch_response=True, **kwargs) as resp:
            if resp.status_code == response_code:
                resp.success()
