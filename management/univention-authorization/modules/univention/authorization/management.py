#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Guardian Management Client"""

import json
import logging
import os
import shutil
from functools import lru_cache
from time import sleep
from urllib.parse import quote

import requests


log = logging.getLogger('ACL').getChild(__name__)
ALREADY_EXISTS = object()
TIMEOUT = 10


class TokenInvalidError(Exception):
    pass


class GuardianManagementClient:

    def __init__(self, management_url, username, password, oidc_token_endpoint_url, oidc_client_id):
        self.management_url = management_url
        self.username = username
        self.password = password
        self.oidc_token_endpoint_url = oidc_token_endpoint_url
        self.oidc_client_id = oidc_client_id

    @staticmethod
    @lru_cache(maxsize=1)
    def get_token(token_endpoint_url, client_id, username, password):
        log.info("Getting token")
        data = {
            "client_id": client_id,
            "username": username,
            "password": password,
            "grant_type": "password",
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        attempt = 0
        while True:
            attempt += 1
            try:
                response = requests.post(token_endpoint_url, data=data, headers=headers, timeout=TIMEOUT)
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                if attempt > 5:
                    raise
                else:
                    sleep(2)
                    continue
            break
        token = response.json()["access_token"]
        log.info("Token received")
        return token

    def handle_status_code(self, response):
        if response.status_code == 400 and response.json().get('detail') == {
            "message": "An object with the given identifiers already exists.",
        }:
            return ALREADY_EXISTS

        if response.status_code == 401:
            raise TokenInvalidError(response.json())

        if not response.ok:
            log.debug('response=%r', response.__dict__)
        response.raise_for_status()
        return response

    def generate_headers(self):
        token = self.get_token(self.oidc_token_endpoint_url, self.oidc_client_id, self.username, self.password)
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        return headers

    def post(self, path, data):
        return self.request('POST', path, data)

    def put(self, path, data):
        return self.request('PUT', path, data)

    def patch(self, path, data):
        return self.request('PATCH', path, data)

    def request(self, method, path, data):
        response = requests.request(method, f"{self.management_url}{path}", headers=self.generate_headers(), json=data, timeout=TIMEOUT)
        try:
            return self.handle_status_code(response)
        except TokenInvalidError:
            self.get_token.cache_clear()
            response = requests.request(method, f"{self.management_url}{path}", headers=self.generate_headers(), json=data, timeout=TIMEOUT)
            return self.handle_status_code(response)

    def create_app(self, app_name, display_name):
        data = {"name": app_name, "display_name": display_name}
        response = self.post("/apps/register", data)
        if response is ALREADY_EXISTS:
            self.modify_app(app_name, display_name)
        else:
            log.info("App %r created: %s", app_name, response.json())

    def modify_app(self, app_name, display_name):
        data = {"display_name": display_name}
        response = self.patch(f"/apps/{quote(app_name)}", data)
        log.info("App %r modified: %s", app_name, response.json())

    def create_namespace(self, app_name, namespace_name, display_name=None):
        data = {"name": namespace_name, "display_name": display_name}
        response = self.post(f"/namespaces/{quote(app_name)}", data)

        if response is ALREADY_EXISTS:
            self.modify_namespace(app_name, namespace_name, display_name)
        else:
            log.info("Namespace %r created: %s", namespace_name, response.json())

    def modify_namespace(self, app_name, namespace_name, display_name):
        data = {"display_name": display_name}
        response = self.patch(f"/namespaces/{quote(app_name)}/{quote(namespace_name)}", data)

        log.info("Namespace %r modified: %s", namespace_name, response.json())

    def create_role(self, app_name, namespace_name, role_name, display_name):
        data = {"name": role_name, "display_name": display_name}
        response = self.post(f"/roles/{quote(app_name)}/{quote(namespace_name)}", data)

        if response is ALREADY_EXISTS:
            self.modify_role(app_name, namespace_name, role_name, display_name)
        else:
            log.info("Role %r created: %s", role_name, response.json())

    def modify_role(self, app_name, namespace_name, role_name, display_name):
        data = {"display_name": display_name}
        response = self.patch(f"/roles/{quote(app_name)}/{quote(namespace_name)}/{quote(role_name)}", data)

        log.info("Role %r created: %s", role_name, response.json())

    def create_permission(self, app_name, namespace_name, permission_name, display_name):
        log.info("Create Permission %r", permission_name)
        data = {"name": permission_name, "display_name": display_name}
        response = self.post(f"/permissions/{quote(app_name)}/{quote(namespace_name)}", data)

        if response is ALREADY_EXISTS:
            self.modify_permission(app_name, namespace_name, permission_name, display_name)
        else:
            log.info("Permission %r created: %s", permission_name, response.json())

    def modify_permission(self, app_name, namespace_name, permission_name, display_name):
        data = {"display_name": display_name}
        response = self.patch(f"/permissions/{quote(app_name)}/{quote(namespace_name)}/{quote(permission_name)}", data)

        log.info("Permission %r modified: %s", permission_name, response.json())

    def create_context(self, app_name, namespace_name, context_name, display_name):
        data = {"name": context_name, "display_name": display_name}
        response = self.post(f"/contexts/{quote(app_name)}/{quote(namespace_name)}", data)

        if response is ALREADY_EXISTS:
            self.modify_context(app_name, namespace_name, context_name, display_name)
        else:
            log.info("Context %r created: %s", context_name, response.json())

    def modify_context(self, app_name, namespace_name, context_name, display_name):
        data = {"display_name": display_name}
        response = self.patch(f"/contexts/{quote(app_name)}/{quote(namespace_name)}/{quote(context_name)}", data)

        log.info("Context %r modified: %s", context_name, response.json())

    def create_condition(
        self, app_name, namespace_name, condition_name, display_name, documentation, code, parameters=None,
    ):
        if parameters is None:
            parameters = []
        data = {
            "name": condition_name,
            "display_name": display_name,
            "documentation": documentation,
            "parameters": parameters,
            "code": code,
        }
        response = self.post(f"/conditions/{quote(app_name)}/{quote(namespace_name)}", data)

        if response is ALREADY_EXISTS:
            self.modify_condition(app_name, namespace_name, condition_name, display_name, documentation, code, parameters)
        else:
            log.info("Condition %r created: %s", condition_name, response.json())

    def modify_condition(
        self, app_name, namespace_name, condition_name, display_name, documentation, code, parameters=None,
    ):
        if parameters is None:
            parameters = []
        data = {
            "display_name": display_name,
            "documentation": documentation,
            "parameters": parameters,
            "code": code,
        }
        try:
            response = self.patch(f"/conditions/{quote(app_name)}/{quote(namespace_name)}/{quote(condition_name)}", data)
        except requests.HTTPError as exc:
            log.exception('Impossible to modify condition: %s', exc)
            return

        log.info("Condition %r modified: %s", condition_name, response.json())

    def create_role_capability_mapping(
        self, app_name, namespace_name, name, display_name, role, permissions, conditions=None, relation="AND",
    ):
        if conditions is None:
            conditions = []
        data = {
            "name": name,
            "display_name": display_name,
            "role": role,
            "conditions": conditions,
            "relation": relation,
            "permissions": [
                permission if isinstance(permission, dict) else {"app_name": app_name, "namespace_name": namespace_name, "name": permission}
                for permission in permissions
            ],
        }
        response = self.post(f"/capabilities/{quote(app_name)}/{quote(namespace_name)}", data)

        if response is ALREADY_EXISTS:
            self.modify_role_capability_mapping(app_name, namespace_name, name, display_name, role, permissions, conditions=None, relation="AND")
        else:
            log.info("Role-Capability-Mapping %r created: %s", name, response.json())

    def modify_role_capability_mapping(
        self, app_name, namespace_name, name, display_name, role, permissions, conditions=None, relation="AND",
    ):
        if conditions is None:
            conditions = []
        data = {
            "display_name": display_name,
            "role": role,
            "conditions": conditions,
            "relation": relation,
            "permissions": [
                permission if isinstance(permission, dict) else {"app_name": app_name, "namespace_name": namespace_name, "name": permission}
                for permission in permissions
            ],
        }
        response = self.put(f"/capabilities/{quote(app_name)}/{quote(namespace_name)}/{quote(name)}", data)

        log.info("Role-Capability-Mapping %r modified: %s", name, response.json())

    def prune(self, apps, contexts, namespaces, roles, capabilities):
        pass  # not possible, Guardian supports no removal


def expand_role(app_name, namespace_name, name):
    return {
        "app_name": app_name,
        "namespace_name": namespace_name,
        "name": name,
    }


def expand_permission(app_name, namespace_name, name):
    return expand_role(app_name, namespace_name, name)


def expand_string(string):
    return string.split(':', 2)


def implode_string(app_name, namespace_name, name):
    return f'{app_name}:{namespace_name}:{name}'


def expand_condition(condition, parameters=None):
    app_name, namespace_name, name = expand_string(condition)
    return {
        **expand_role(app_name, namespace_name, name),
        "parameters": parameters or [],
    }


class GuardianManagementClientLocal(GuardianManagementClient):

    def __init__(self, local_path, management_url, username, password, oidc_token_endpoint_url, oidc_client_id):
        self.local_path = local_path
        super().__init__(management_url, username, password, oidc_token_endpoint_url, oidc_client_id)

    def request(self, method, path, data):
        if method == 'POST':
            path = f'{path}/{data["name"]}'
        filepath = f'{self.local_path}/{path}.json'
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as fd:
            json.dump(data, fd)

        r = requests.Response()
        r.status_code = 200
        r._content = b'{}'
        r.headers['Content-Type'] = 'application/json'
        return r

    def prune(self, apps, contexts, namespaces, roles, capabilities):
        if not any((apps, contexts, namespaces, roles, capabilities)):
            kw = {'': True}
        else:
            kw = {'apps': apps, 'contexts': contexts, 'namespaces': namespaces, 'roles': roles, 'capabilities': capabilities}
        for name, remove in kw.items():
            if not remove:
                continue
            path = os.path.join(self.local_path, name)
            if os.path.exists(path):
                shutil.rmtree(path)
