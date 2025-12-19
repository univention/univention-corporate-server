#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Interface to Guardian"""

import functools
import json
import pathlib
import re
from time import sleep

import requests

from univention.admin.log import log
from univention.dn import DN  # type: ignore


TIMEOUT = 30

log = log.getChild(__name__)


class LocalGuardianAuthorizationClient:

    def __init__(self, base_path):
        self.base_path = base_path

    def reload(self):
        self._get_capabilities.cache_clear()
        self.load_local_roles.cache_clear()

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def load_local_roles(base_path):
        capabilities = (pathlib.Path(base_path) / 'capabilities').glob('**/*.json')
        permissions = (pathlib.Path(base_path) / 'permissions').glob('**/*.json')
        roles = (pathlib.Path(base_path) / 'roles').glob('**/*.json')

        def _cap(x, d):
            return {
                'name': d['name'],
                'fullname': _rol(x, d),
                'conditions': [(f'{c["app_name"]}:{c["namespace_name"]}:{c["name"]}', {item['name']: item['value'] for item in c['parameters']}) for c in d['conditions']],
                'permissions': [f'{p["app_name"]}:{p["namespace_name"]}:{p["name"]}' for p in d['permissions']],
                'relation': {'AND': all, 'OR': any}[d['relation']],
                'role': f'{d["role"]["app_name"]}:{d["role"]["namespace_name"]}:{d["role"]["name"]}',
            }

        def _rol(x, d):
            return f'{x.parent.parent.name}:{x.parent.name}:{d["name"]}'
        return [
            [_cap(p, json.loads(p.read_bytes())) for p in capabilities],
            [_rol(p, json.loads(p.read_bytes())) for p in permissions],
            [_rol(p, json.loads(p.read_bytes())) for p in roles],
        ]

    @staticmethod
    @functools.lru_cache(maxsize=20)
    def _get_capabilities(base_path, actor_roles: tuple[str], namespaces):
        all_capabilities = LocalGuardianAuthorizationClient.load_local_roles(base_path)[0]
        return [
            cap
            for cap in all_capabilities
            if cap['role'] in actor_roles and (not namespaces or any(cap['fullname'].startswith(ns + ':') for ns in namespaces))
        ]

    def check_permissions(self, actor, targets, contexts, namespaces, extra_request_data=None, targeted_permissions_to_check=None, general_permissions_to_check=None):
        return self.get_and_check_permissions(actor, targets, contexts, namespaces, extra_request_data, targeted_permissions_to_check, general_permissions_to_check)

    def get_and_check_permissions(self, actor, targets, contexts, namespaces, extra_request_data=None, targeted_permissions_to_check=None, general_permissions_to_check=None):
        general_permissions, target_permissions = self.get_permissions(actor, targets, contexts, namespaces, extra_request_data, include_general_permissions=bool(general_permissions_to_check))
        actor_has_all_targeted_permissions = False
        actor_has_all_general_permissions = False
        permissions_check_results = []

        if targeted_permissions_to_check:
            actor_has_all_targeted_permissions = True
            for i, target in enumerate(targets):
                target_perms = target_permissions[i]
                assert target_perms['target_id'] in (target['old_target']['id'], target['new_target']['id']), (target['old_target']['id'], target['new_target']['id'], target_perms['target_id'])
                target_check_result = {
                    'target_id': target_perms['target_id'],
                    'actor_has_permissions': set(targeted_permissions_to_check).issubset(target_perms['permissions']),
                }
                if not target_check_result['actor_has_permissions']:
                    actor_has_all_targeted_permissions = False
                permissions_check_results.append(target_check_result)

        if general_permissions_to_check:
            actor_has_all_general_permissions = set(general_permissions_to_check).issubset(general_permissions)

        return {
            'actor_id': actor['id'],
            'permissions_check_results': permissions_check_results,
            'actor_has_all_general_permissions': actor_has_all_general_permissions,
            'actor_has_all_targeted_permissions': actor_has_all_targeted_permissions,
            'general_permissions': general_permissions,
            'target_permissions': target_permissions,
        }

    def get_permissions(self, actor, targets, contexts, namespaces, extra_request_data=None, include_general_permissions=False):
        caps = self._get_capabilities(self.base_path, self._extract_roles(actor['roles']), tuple(namespaces))
        general_permissions = set()
        if include_general_permissions:
            general_permissions = self._get_permissions(actor, [{'old_target': None, 'new_target': None}], contexts, namespaces, extra_request_data, caps)[0]['permissions']
        target_permissions = self._get_permissions(actor, targets, contexts, namespaces, extra_request_data, caps)
        return general_permissions, target_permissions

    def _get_permissions(self, actor, targets, contexts, namespaces, extra_request_data, caps):
        EMPTY_TARGET = {'new_target': {'id': '', 'attributes': {}, 'roles': []}, 'old_target': {'id': '', 'attributes': {}, 'roles': []}}
        target_permissions = []
        for target in targets:
            permissions = set()
            if not target.get('new_target') and not target.get('old_target'):
                target = EMPTY_TARGET
            for cap in caps:
                if not cap['conditions'] or cap['relation'](self._evaluate_condition(cond, actor, [r.split('&', 1) for r in actor['roles']], target, contexts, namespaces, extra_request_data) for cond in cap['conditions']):
                    permissions |= set(cap['permissions'])
            # TODO: Fix!!!
            target_permissions.append({'target_id': target['old_target']['id'], 'permissions': permissions})
            # target_permissions.append({'target_id': target['new_target']['id'] or target['old_target']['id'], 'permissions': permissions})
        return target_permissions

    def _extract_roles(self, roles):
        return tuple(role.split('&', 1)[0] for role in roles)

    def _evaluate_condition(self, condition, actor, roles, target, contexts, namespaces, extra_request_data):
        cond, params = condition
        func = {
            'udm:conditions:target_position_from_context': self.udm_conditions_target_position_from_context,
            'udm:conditions:target_position_in': self.udm_conditions_target_position_in,
            'udm:conditions:target_object_type_equals': self.udm_conditions_target_object_type_equals,
            'guardian:builtin:target_is_self': self.target_is_self,
        }[cond]
        return func(params, {'actor': actor, 'actor_role': roles, 'target': target, 'contexts': contexts, 'namespaces': namespaces, 'extra_args': extra_request_data})

    def udm_conditions_target_position_from_context(self, params, condition_data):
        context_name = params['context']
        positions = [
            c[1].split(context_name + '=', 1)[-1]
            for c in condition_data['actor_role']
            if len(c) > 1 and c[1].startswith(context_name)
        ]
        params = {
            'position': positions,
            'scope': params['scope'],
        }
        return self.udm_conditions_target_position_in(params, condition_data)

    def udm_conditions_target_position_in(self, params, condition_data):
        """Checks if the position matches the condition."""
        result = []
        for target in (condition_data['target']['new_target']['attributes'], condition_data['target']['old_target']['attributes']):
            target_dn = target.get('dn')
            if target_dn is None:
                result.append(False)
                continue

            scope = params.get('scope', 'base')
            pos = params['position']
            try:
                func = {
                    "subtree": _check_scope_subtree,
                    "base": _check_scope_base,
                    "one": _check_scope_one,
                }[scope]
            except KeyError:
                pass
            else:
                if not func(target_dn, pos if isinstance(pos, list) else [pos]):
                    return False
                result.append(True)
                continue

            raise NotImplementedError(f"Scope {scope} not implemented")
        return any(result)

    def udm_conditions_target_object_type_equals(self, params, condition_data):
        """Checks the object type of the target object"""
        oc = (condition_data['target']['new_target']['attributes'] or condition_data['target']['old_target']['attributes']).get('objectType')
        return oc == params.get('objectType')

    def udm_conditions_target_property_values_compares(self, params, condition_data):
        """Checks a property matches any certain value in the target object properties"""
        def check(operator, value, data):
            if operator in ('==-i', '!=-i'):
                data, value = data.lower(), value.lower()
                operator = operator[:-2]

            if operator == '==':
                return value == data
            if operator == '!=':
                return value != data
            if operator.startswith('regex'):
                operator, flags = (operator[:-2], re.I) if operator.endswith('-i') else (operator, 0)
                matched = re.match(value, data, flags) is not None
                return matched if operator == 'regex-match' else not matched
            if operator.startswith('dn'):
                _, _, scope = operator.partition('-')
                func = {
                    "": _check_scope_base,
                    "subtree": _check_scope_subtree,
                    "base": _check_scope_base,
                    "one": _check_scope_one,
                }[scope]
                return func(value, [data])

        prop = params['property']
        operator = params['operator']
        values = params['values']

        for target in (condition_data['target']['new_target']['attributes'], condition_data['target']['old_target']['attributes']):
            if not target.get('properties', {}).get(prop):
                continue
            propval = target['properties'][prop]  # FIXME: multivalue
            if any(check(operator, values, propval) for value in values):
                return True
        return False

    def target_is_self(self, params, condition_data):
        field = params.get('field')
        if field:
            target_attributes = (condition_data['target']['new_target']['attributes'] or condition_data['target']['old_target']['attributes'])
            try:
                return condition_data['actor']['attributes'][field] == target_attributes[field]
            except KeyError:
                return False
        target_id = (condition_data['target']['new_target']['id'] or condition_data['target']['old_target']['id'])
        try:
            return condition_data['actor']['id'] and condition_data['actor']['id'] == target_id
        except KeyError:
            return False


def _check_scope_subtree(position: str, condition_positions: list[str]) -> bool:
    """
    Checks if the position is in the subtree of the condition.

    >>> _check_scope_subtree('cn=users,dc=base', ['cn=users,dc=base'])
    True
    >>> _check_scope_subtree('uid=fbest,cn=users,dc=base', ['cn=users,dc=base'])
    True
    >>> _check_scope_subtree('uid=fbest,cn=foo,cn=users,dc=base', ['cn=users,dc=base'])
    True
    >>> _check_scope_subtree('dc=base', ['cn=users,dc=base'])
    False
    >>> _check_scope_subtree('uid=fbest,cn=userz,dc=base', ['cn=users,dc=base'])
    False
    """
    position = DN(position)
    condition_positions = [DN(condition_position) for condition_position in condition_positions]
    return any(
        position.endswith(condition_position)
        for condition_position in condition_positions
    )


def _check_scope_base(position: str, condition_positions: list[str]) -> bool:
    """
    Checks if the position is in the base of the condition.
    >>> _check_scope_base('cn=users,dc=base', ['dc=base'])
    False
    >>> _check_scope_base('cn=users,dc=base', ['cn=userz,dc=base'])
    False
    >>> _check_scope_base('cn=users,dc=base', ['cn = users,dc=base'])
    True
    """
    position = DN(position)
    condition_positions = [DN(condition_position) for condition_position in condition_positions]
    return position in condition_positions


def _check_scope_one(position: str, condition_positions: list[str]) -> bool:
    """
    Checks if the position is in the scope onelevel of the condition.
    >>> _check_scope_one('uid=foo,cn=users,dc=base', ['dc=base'])
    False
    >>> _check_scope_one('uid=foo,cn=users,dc=base', ['cn=userz,dc=base'])
    False
    >>> _check_scope_one('uid=foo,cn=users,dc=base', ['cn = users,dc=base'])
    True
    """
    position = DN(position)
    condition_positions = [DN(condition_position) for condition_position in condition_positions]
    return position.parent in condition_positions


class TokenInvalidError(Exception):
    pass


class UnprocessableEntity(Exception):
    pass


class BadGateway(Exception):
    pass


class GuardianAuthorizationClient:

    def __init__(self, fqdn, keycloak_fqdn, username='Administrator', password='univention', realm='ucs'):
        self._base_url = f'https://{fqdn}/guardian/authorization/'.rstrip('/')
        self.username = username
        self.password = password
        self.oidc_token_endpoint_url = f'https://{keycloak_fqdn}/realms/{realm}/protocol/openid-connect/token'
        self.oidc_client_id = 'guardian-scripts'

    def __enter__(self):
        return self

    def __exit__(self, etype, exc, etraceback):
        pass

    def check_permissions(self, actor, targets, contexts, namespaces, extra_request_data=None, targeted_permissions_to_check=None, general_permissions_to_check=None):
        if not targets:
            raise ValueError('Targets must be set!')
        if not targets[0]['old_target']:
            raise ValueError('At least old target must be set!')

        # Workaround for missing Guardian dynamic contexts.
        # See: https://git.knut.univention.de/univention/dev/ucs/-/blob/5.2-4/management/univention-directory-manager-modules/README-authorization.md#no-dynamic-contexts-allowed
        extra_actor_roles = {'actor_roles': [self._prepare_role(r, with_context_value=True) for r in actor['roles']]}

        data = {
            # "namespaces": [expand_role_string(f'{n}:') for n in namespaces],
            "actor": {
                "id": actor['id'],
                "roles": [self._prepare_role(r) for r in actor['roles']],
                "attributes": actor['attributes'],
            },
            "targets": [
                {
                    "old_target": self._prepare_target(target['old_target']),
                    "new_target": self._prepare_target(target['new_target'] or target['old_target']),
                } for target in targets or {}
            ],
            "contexts": [expand_role_string(c) for c in contexts],
            "targeted_permissions_to_check": [expand_role_string(t) for t in targeted_permissions_to_check] if targeted_permissions_to_check else [],
            "general_permissions_to_check": [expand_role_string(g) for g in general_permissions_to_check] if general_permissions_to_check else [],
            "extra_request_data": extra_request_data | extra_actor_roles or {},
        }
        log.trace('request to /permissions/check: %s', data)

        response = self.post('/permissions/check', data)
        if response:
            response = response.json()
        log.trace('response: %s', response)

        return response

    def get_and_check_permissions(self, actor, targets, contexts, namespaces, extra_request_data=None, targeted_permissions_to_check=None, general_permissions_to_check=None):
        permissions = self.get_permissions(actor, targets, contexts, namespaces, extra_request_data)
        check = self.check_permissions(actor, targets, contexts, namespaces, extra_request_data=extra_request_data, targeted_permissions_to_check=targeted_permissions_to_check, general_permissions_to_check=general_permissions_to_check)
        permissions.update(check)
        return permissions

    def get_permissions(self, actor, targets, contexts, namespaces, extra_request_data=None, include_general_permissions=False):
        if not targets:
            raise ValueError('Targets must be set!')
        if not targets[0]['old_target']:
            raise ValueError('At least old target must be set!')

        # Workaround for missing Guardian dynamic contexts.
        # See: https://git.knut.univention.de/univention/dev/ucs/-/blob/5.2-4/management/univention-directory-manager-modules/README-authorization.md#no-dynamic-contexts-allowed
        extra_actor_roles = {'actor_roles': self._prepare_roles(actor['roles'], with_context_value=True)}

        data = {
            # "namespaces": [expand_role_string(f'{n}:') for n in namespaces],
            "actor": {
                "id": actor['id'],
                "roles": self._prepare_roles(actor['roles']),
                "attributes": actor['attributes'],
            },
            "targets": [
                {
                    "old_target": self._prepare_target(target['old_target']),
                    "new_target": self._prepare_target(target['new_target'] or target['old_target']),
                } for target in targets or {}
            ],
            "contexts": [expand_role_string(c) for c in contexts],
            "include_general_permissions": include_general_permissions,
            "include_target_permissions": True,
            "extra_request_data": extra_request_data | extra_actor_roles or {},
        }
        log.trace('request to /permissions: %s', data)

        response = self.post('/permissions', data)
        if response:
            response = response.json()
        log.trace('response: %s', response)

        return {
            'actor_id': response['actor_id'],
            'general_permissions': {implode_permission(p) for p in response['general_permissions']},
            'target_permissions': [
                {'target_id': tp['target_id'], 'permissions': {implode_permission(p) for p in tp['permissions']}}
                for tp in response['target_permissions']
            ],
        } if response else {}

    @staticmethod
    def _prepare_target(target: dict) -> dict:
        return {
            'id': target['id'],
            'attributes': target['attributes'],
            'roles': [expand_role_string(r) for r in target['roles']],
        }

    @staticmethod
    def _prepare_role(role_str: str, with_context_value: bool = False) -> dict:
        """
        Prepares the role dictionary for Guardian.

        :param role_str: UDM role e.g. udm:default-roles:my-role&udm:contexts:my-context=my-value
        :type role_str: str
        :param with_context_value:
            Flag if the context value should be added to the Guardian role.
            Not supported from Guardian. Only used in extra_request_data!
        :type with_context_value: bool
        :return: Guardian role as dict e.g.
            {
                'app_name': 'udm',
                'namespace_name': 'default-roles',
                'name': 'my-role',
                'context': {
                    'app_name': 'udm',
                    'namespace_name': 'contexts',
                    'name': 'my-context',
                    'value': 'my-value', <= Not supported from Guardian. Only used in extra_request_data!
                }
            }
        :rtype: dict
        """
        role, _, role_context = role_str.partition('&')
        role = _expand_role_string(role)
        if _ and role_context:
            context, _, context_value = role_context.partition('=')
            if context:
                role['context'] = _expand_role_string(context)
                if with_context_value and context_value:
                    role['context']['value'] = context_value
        return role

    def _prepare_roles(self, roles: list[str], with_context_value: bool = False) -> dict:
        return [
            self._prepare_role(role, with_context_value=with_context_value)
            for role in roles
        ]

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def get_token(token_endpoint_url, client_id, username, password):
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
        return token

    def handle_status_code(self, response: requests.Response) -> requests.Response:
        if response.status_code == 401:
            raise TokenInvalidError()
        elif response.status_code == 422:
            raise UnprocessableEntity(response.json())
        elif response.status_code == 502:
            # TODO: Check why so often 502 - Proxy error
            raise BadGateway()

        response.raise_for_status()
        return response

    def generate_headers(self):
        token = self.get_token(self.oidc_token_endpoint_url, self.oidc_client_id, self.username, self.password)
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        return headers

    def post(self, path, data):
        return self.request('POST', path, data)

    def request(self, method, path, data) -> requests.Response:
        max_retries = 5
        request_error = None
        for i in range(5):
            try:
                response = requests.request(method, f"{self._base_url}{path}", headers=self.generate_headers(), json=data, timeout=TIMEOUT)
                return self.handle_status_code(response)
            except TokenInvalidError as exc:
                request_error = exc
                self.get_token.cache_clear()
                log.warning('TokenInvalidError error. Retry with cleared cache (%s/%s)', i + 1, max_retries)
                continue
            except BadGateway as exc:
                request_error = exc
                log.warning('BadGateway error. Retry (%s/%s)', i + 1, max_retries)
                sleep(2)
                continue
        raise request_error


def expand_role(app_name, namespace_name, name):
    return {
        "app_name": app_name,
        "namespace_name": namespace_name,
        "name": name,
    }


def _expand_role_string(string):
    return expand_role(*string.split(':', 2))


def expand_role_string(string):
    role, _, context = string.partition('&')
    role = _expand_role_string(role)
    if _ and context:
        role['context'] = _expand_role_string(context)
    return role


def implode_permission(data):
    return f'{data["app_name"]}:{data["namespace_name"]}:{data["name"]}'
