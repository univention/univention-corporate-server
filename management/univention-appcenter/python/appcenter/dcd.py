#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright 2022 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.


import json
from typing import Any, Iterator, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from requests.compat import json as requests_json

from univention.appcenter.ucr import ucr_get
from univention.appcenter.udm import get_machine_connection, search_objects


class DCDError(BaseException):
    pass


class ConnectionError(DCDError):
    pass


class ServerError(DCDError):
    pass


class AuthFailed(DCDError):
    pass


class SchemaConflict(DCDError):
    pass


class InvalidValue(DCDError):
    pass


class DCD:
    """
    Client to Univention Distributed Configuration Database
    Uses the Web API of Database.

    Example:
    dcd = DCD("user", "pass", "https://example.com/univention/dcd/", version=1)
    dcd.register("key", {"type": "number"})
    dcd.set("key", 100)
    """

    def __init__(self, username: str, password: str, url: str, version: int, ssl_verify: bool = True):
        if url.endswith("/"):
            url = url[:-1]
        url = f"{url}/v{version}"
        self.url = url
        self.ssl_verify = ssl_verify
        self.token = None
        self.token = self.auth(username, password)

    def _error_handler(self, data, code, request_id):
        if code == 502:
            raise ConnectionError(data)
        if code == 401:
            raise AuthFailed(data)
        if code == 409:
            raise SchemaConflict(data)
        if code == 422:
            raise InvalidValue(data)
        if code == 503:
            raise ConnectionError(data)
        if code == 500:
            raise ServerError(f"Your request caused an error in the Database. This should not have happened, please contact the administrator: {data}")
        return data, code, request_id

    def _req(self, method: str, path: str, data: Optional[dict] = None, json: Optional[dict] = None, params: Optional[dict] = None, request_id: Optional[str] = None) -> Any:
        headers = {}
        if request_id:
            headers["X-Request-Id"] = request_id
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            response = requests.request(method, f"{self.url}{path}", data=data or {}, json=json or {}, params=params, headers=headers, verify=self.ssl_verify)
            request_id = response.headers.get("X-Request-Id")
        except requests.RequestException as exc:
            raise ConnectionError(str(exc))
        return self._error_handler(response.json(), response.status_code, request_id)

    def auth(self, username: str, password: str, request_id: Optional[str] = None) -> str:
        """
        Authenticate against the API
        See the documentation of the API how to setup users.
        The login mechanism returns a token which will be saved for future requests.
        """
        try:
            data, _, _ = self._req("POST", "/login", data={"grant_type": "", "username": username, "password": password, "scope": "", "client_id": "", "client_secret": ""}, request_id=request_id)
        except requests_json.JSONDecodeError:
            raise AuthFailed("Response Error. Wrong URL or service not running?")
        try:
            return data["access_token"]
        except KeyError:
            raise AuthFailed("Wrong credentials?")

    def search(self, pattern: str, request_id: Optional[str] = None) -> Iterator[Tuple[str, Any]]:
        """
        Search keys in a glob like pattern.
        Returns an iterator over the keys and their values.
        Unset values will be found with their default values (or None)
        """
        data, _, request_id = self._req("GET", "/config/", params={"pattern": f"{pattern}"}, request_id=request_id)
        for key in data["keys"]:
            yield key, self.get(key, request_id=request_id)

    def get(self, key: str, request_id: Optional[str] = None) -> Any:
        """Get one specific key from the database"""
        data, _, _ = self._req("GET", f"/config/{key}", request_id=request_id)
        if "value" in data:
            return data["value"]
        return None

    def set(self, key: str, value: Any, request_id: Optional[str] = None) -> bool:
        """
        Sets one key to a value. Returns whether setting it was a success.
        A key needs to be registered first. And the value needs to be valid
        with respect to the JSON Schema.
        """
        _, code, _ = self._req("PUT", f"/config/{key}", json={"value": value}, request_id=request_id)
        return code < 400

    def unset(self, key: str, request_id: Optional[str] = None) -> bool:
        """Unset a key. Default values will still be returned."""
        _, code, _ = self._req("DELETE", f"/config/{key}", request_id=request_id)
        return code < 400

    def schema(self, key: str, request_id: Optional[str] = None) -> dict:
        """
        Get the currently registered schema for a key. Will raise a KeyError
        if the key is unknown
        """
        data, _, _ = self._req("GET", f"/schema/{key}", request_id=request_id)
        return data["json_schema"]

    def register(self, key: str, schema: dict, request_id: Optional[str] = None) -> bool:
        """
        Register a JSON schema for a key. If the key is already known and
        set, the new schema has to be valid for the set value. Otherwise, it
        will not be set. Returns the success
        """
        _, code, _ = self._req("PUT", f"/schema/{key}", json={"json_schema": schema}, request_id=request_id)
        return code < 400

    def unregister(self, key: str, request_id: Optional[str] = None) -> bool:
        """
        Unregisters the schema of a key. A potential value has to be unset
        before unregistering
        """
        _, code, _ = self._req("DELETE", f"/schema/{key}", request_id=request_id)
        return code < 400

    async def changes(self, keys: List[str], request_id: Optional[str] = None):
        """
        Listen to changes of a list of keys (via a websocket; async). Returns
        if the websocket is closed on server side (e.g. service is restarted)
        If a key is unset, the value will be None (or the default)
        Example:
        dcd = DCD("user", "pass", "https://example.com/univention/dcd/", version=1)
        async def main():
            async for key, value in dcd.changes(["key1", "key2"]):
                print(f"{key} was set to {value}")
        asyncio.run(main())
        """
        from websockets import ConnectionClosed, connect
        parsed = urlparse(self.url)
        if parsed.scheme == 'http':
            scheme = 'ws'
        else:
            scheme = 'wss'
        url = parsed._replace(scheme=scheme).geturl()
        keys = "&keys=".join([f"{key}" for key in keys])
        url = f"{url}/updates/?token={self.token}&keys={keys}"
        async with connect(url) as websocket:
            while True:
                try:
                    msg = await websocket.recv()
                except ConnectionClosed:
                    break
                msg = json.loads(msg)
                key = msg["key"]
                yield key, self.get(key, request_id=request_id)


def _get_dcd():
    username = '%s$' % ucr_get('hostname')
    password = open('/etc/machine.secret').read()
    lo, pos = get_machine_connection()
    for role in ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver']:
        servers = search_objects('computers/%s' % role, lo, pos, service='Distributed Configuration Database')
        if servers:
            server = servers[0]['fqdn']
            break
    else:
        return None
    print(username, password)
    return DCD(username, password, "https://%s/univention/dcd/" % server, version=1)


def get_from_app(app, setting):
    dcd = _get_dcd()
    key = 'apps/%s' % app.id
    return (dcd.get(key) or {}).get(setting)


def set_for_app(app, settings):
    dcd = _get_dcd()
    key = 'apps/%s' % app.id
    dcd.register(key, {'type': 'object'})
    old_value = dcd.get(key) or {}
    old_value.update(settings)
    dcd.set(key, old_value)
