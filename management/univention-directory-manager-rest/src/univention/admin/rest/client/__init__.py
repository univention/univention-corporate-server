#!/usr/bin/python3
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2019-2023 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.
"""
Sample Client for the UDM REST API.

>>> from univention.admin.rest.client import UDM
>>> uri = 'http://localhost/univention/udm/'
>>> udm = UDM.http(uri, 'Administrator', 'univention')
>>> module = udm.get('users/user')
>>> print('Found {}'.format(module))
>>> obj = next(module.search())
>>> if obj:
>>>     obj = obj.open()
>>> print('Object {}'.format(obj))
"""


import copy
import sys
import time
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Type, Union  # noqa: F401

import requests
import uritemplate


if sys.version_info.major > 2:
    import http.client
    http.client._MAXHEADERS = 1000  # type: ignore
else:
    import httplib
    httplib._MAXHEADERS = 1000


class HTTPError(Exception):

    def __init__(self, code: int, message: str, response: "Optional[requests.Response]", error_details: "Optional[dict]"=None) -> None:
        self.code = code
        self.response = response
        self.error_details = error_details
        super().__init__(message)


class BadRequest(HTTPError):
    pass


class Unauthorized(HTTPError):
    pass


class Forbidden(HTTPError):
    pass


class NotFound(HTTPError):
    pass


class PreconditionFailed(HTTPError):
    pass


class UnprocessableEntity(HTTPError):
    pass


class ServerError(HTTPError):
    pass


class ServiceUnavailable(HTTPError):
    pass


class ConnectionError(Exception):
    pass


class UnexpectedResponse(ConnectionError):
    pass


class _NoRelation(Exception):
    pass


class Response:

    def __init__(self, response: "requests.Response", data: "Any", uri: str) -> None:
        self.response = response
        self.data = data
        self.uri = uri


class Session:

    def __init__(self, credentials: "UDM", language: str='en-US', reconnect: bool=True, user_agent: str='univention.lib/1.0', enable_caching: bool=False) -> None:
        self.language = language
        self.credentials = credentials
        self.reconnect = reconnect
        self.user_agent = user_agent
        self.enable_caching = enable_caching
        self.default_headers = {
            'Accept': 'application/hal+json; q=1, application/json; q=0.9; text/html; q=0.2, */*; q=0.1',
            'Accept-Language': self.language,
            'User-Agent': self.user_agent,
        }
        self.session = self.create_session()

    def create_session(self) -> "requests.Session":
        sess = requests.session()
        sess.auth = (self.credentials.username, self.credentials.password)
        if not self.enable_caching:
            return sess
        try:
            from cachecontrol import CacheControl
        except ImportError:
            pass
        else:
            sess = CacheControl(sess)
        return sess

    def get_method(self, method: str) -> "Callable[..., requests.Response]":
        sess = self.session
        return {
            'GET': sess.get,
            'POST': sess.post,
            'PUT': sess.put,
            'DELETE': sess.delete,
            'PATCH': sess.patch,
            'OPTIONS': sess.options,
        }.get(method.upper(), sess.get)

    def request(self, method: str, uri: str, data: "Dict"=None, expect_json: bool=False, **headers: str) -> "Any":
        return self.make_request(method, uri, data, expect_json=expect_json, **headers).data  # type: ignore # <https://github.com/python/mypy/issues/10008>

    def make_request(self, method: str, uri: str, data: "Dict"=None, expect_json: bool=False, allow_redirects: bool=True, **headers: str) -> "Response":
        if method in ('GET', 'HEAD'):
            params = data
            json = None
        else:
            params = None
            json = data

        def doit() -> "Response":
            try:
                response = self.get_method(method)(uri, params=params, json=json, headers=dict(self.default_headers, **headers), allow_redirects=allow_redirects)
            except requests.exceptions.ConnectionError as exc:
                raise ConnectionError(exc)
            data = self.eval_response(response, expect_json=expect_json)
            return Response(response, data, uri)

        for _i in range(5):
            try:
                return doit()
            except ServiceUnavailable as exc:  # TODO: same for ConnectionError? python-request does it itself.
                if not self.reconnect:
                    raise
                try:
                    assert exc.response is not None
                    retry_after = min(5, int(exc.response.headers.get('Retry-After', 1)))
                except ValueError:
                    retry_after = 1
                time.sleep(retry_after)

        return doit()

    def eval_response(self, response: "requests.Response", expect_json: bool=False) -> "Any":
        if response.status_code >= 399:
            msg = f'{response.request.method} {response.url}: {response.status_code}'
            error_details = None
            try:
                json = response.json()
            except ValueError:
                pass
            else:
                if isinstance(json, dict):
                    error_details = json.get('error', {})
                    try:
                        error_details['error'] = list(self.resolve_relations(json, 'udm:error'))
                    except _NoRelation:
                        pass
                    if error_details:
                        server_message = error_details.get('message')
                        # traceback = error_details.get('traceback')
                        if server_message:
                            msg += f'\n{server_message}'
            errors = {400: BadRequest, 404: NotFound, 403: Forbidden, 401: Unauthorized, 412: PreconditionFailed, 422: UnprocessableEntity, 500: ServerError, 503: ServiceUnavailable}
            cls = HTTPError
            cls = errors.get(response.status_code, cls)
            raise cls(response.status_code, msg, response, error_details=error_details)
        if response.headers.get('Content-Type') in ('application/json', 'application/hal+json'):
            return response.json()
        elif expect_json:
            raise UnexpectedResponse(response.text)
        return response.text

    def get_relations(self, entry: "Dict", relation: str, name: "Optional[str]"=None, template: "Optional[Dict[str, Any]]"=None) -> "Iterator[Dict[str, str]]":
        links = copy.deepcopy(entry.get('_links', {}))
        links = links.get(relation, [None])
        links = links if links and isinstance(links, list) else [links]
        links = [link for link in links if isinstance(link, dict) and (not name or link.get('name') == name)]
        for link in sorted(links, key=lambda x: not x.get('templated', False) if template else x.get('templated', False)):
            if link.get('deprecation'):
                pass  # TODO: log warning
            if link.get('templated'):
                link['href'] = uritemplate.expand(link['href'], template)
            yield link

    def get_relation(self, entry: "Dict", relation: str, name: "Optional[str]"=None, template: "Optional[Dict[str, Any]]"=None) -> "Dict[str, str]":
        try:
            return next(self.get_relations(entry, relation, name, template))
        except StopIteration:
            raise _NoRelation(relation)

    def resolve_relations(self, entry: "Dict", relation: str, name: "Optional[str]"=None, template: "Optional[Dict[str, Any]]"=None) -> "Iterator[Any]":
        embedded = entry.get('_embedded', {})
        if isinstance(embedded, dict) and relation in embedded:
            yield from embedded[relation]
            return

        for rel in self.get_relations(entry, relation, name, template):
            yield self.make_request('GET', rel['href']).data

    def resolve_relation(self, entry: "Dict", relation: str, name: "Optional[str]"=None, template: "Optional[Dict[str, Any]]"=None) -> "Any":
        try:
            return next(self.resolve_relations(entry, relation, name, template))
        except StopIteration:
            raise _NoRelation(relation)


class Client:

    def __init__(self, client: "Session") -> None:
        self.client = client


class UDM(Client):

    @classmethod
    def http(cls, uri: str, username: str, password: str) -> "UDM":
        return cls(uri, username, password)

    def __init__(self, uri: str, username: str, password: str, *args: "Any", **kwargs: "Any") -> None:
        self.uri = uri
        self.username = username
        self.password = password
        self._api_version: "Optional[str]" = None
        self.entry: "Any" = None  # Optional[Dict]
        super().__init__(Session(self, *args, **kwargs))

    def load(self) -> None:
        # FIXME: use HTTP caching instead of memory caching
        if self.entry is None:
            self.reload()

    def reload(self) -> None:
        self.entry = self.client.request('GET', self.uri, expect_json=True)

    def get_ldap_base(self) -> "Optional[str]":
        self.load()
        return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:ldap-base')).dn

    def modules(self, name: "Optional[str]"=None) -> "Iterator[Module]":
        self.load()
        for module in self.client.resolve_relations(self.entry, 'udm:object-modules'):
            for module_info in self.client.get_relations(module, 'udm:object-types', name):
                yield Module(self, module_info['href'], module_info['name'], module_info['title'])

    def version(self, api_version: str) -> "UDM":
        self._api_version = api_version
        return self

    def obj_by_dn(self, dn: str) -> "Object":
        self.load()
        return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:object/get-by-dn', template={'dn': dn}))

    def obj_by_uuid(self, uuid: str) -> "Object":
        self.load()
        return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:object/get-by-uuid', template={'uuid': uuid}))

    def get(self, name: str) -> "Optional[Module]":
        for module in self.modules(name):
            return module

        return None

    def get_object(self, object_type: str, dn: str) -> "Optional[Object]":
        mod = self.get(object_type)
        assert mod
        obj = mod.get(dn)
        return obj

    def __repr__(self) -> str:
        return f'UDM(uri={self.uri}, username={self.username}, password=****, version={self._api_version})'


class Module(Client):

    def __init__(self, udm: "UDM", uri: str, name: str, title: str, *args: "Any", **kwargs: "Any") -> None:
        super().__init__(udm.client, *args, **kwargs)
        self.udm = udm
        self.uri = uri
        self.username = udm.username
        self.password = udm.password
        self.name = name
        self.title = title
        self.relations: "Dict" = {}

    def load_relations(self) -> None:
        if self.relations:
            return
        self.relations = self.client.request('GET', self.uri)

    def __repr__(self) -> str:
        return f'Module(uri={self.uri}, name={self.name})'

    def new(self, position: "Optional[str]"=None, superordinate: "Optional[str]"=None, template: "Optional[Dict[str, Any]]"=None) -> "Object":
        self.load_relations()
        data = {'position': position, 'superordinate': superordinate, 'template': template}
        resp = self.client.resolve_relation(self.relations, 'create-form', template=data)
        return Object.from_data(self.udm, resp)

    def get(self, dn: str) -> "Optional[Object]":
        # TODO: use a link relation instead of a search
        for obj in self._search_closed(position=dn, scope='base'):
            return obj.open()
        raise NotFound(404, 'Wrong object type!?', None)  # FIXME: object exists but is of different module. should be fixed on the server.

    def get_by_entry_uuid(self, uuid: str) -> "Optional[Object]":
        # TODO: use a link relation instead of a search
        # return self.udm.get_by_uuid(uuid)
        for obj in self._search_closed(filter={'entryUUID': uuid}, scope='base'):
            return obj.open()
        raise NotFound(404, 'Wrong object type!?', None)  # FIXME: object exists but is of different module. should be fixed on the server.

    def get_by_id(self, dn: str) -> "Optional[Object]":
        # TODO: Needed?
        raise NotImplementedError()

    def search(self, filter: "Union[Dict[str, str], str, bytes, None]"=None, position: "Optional[str]"=None, scope: "Optional[str]"='sub', hidden: bool=False, superordinate: "Optional[str]"=None, opened: bool=False) -> "Iterator[Any]":
        if opened:
            return self._search_opened(filter, position, scope, hidden, superordinate)
        else:
            return self._search_closed(filter, position, scope, hidden, superordinate)

    def _search_opened(self, filter: "Union[Dict[str, str], str, bytes, None]"=None, position: "Optional[str]"=None, scope: "Optional[str]"='sub', hidden: bool=False, superordinate: "Optional[str]"=None) -> "Iterator[Object]":
        for obj in self._search(filter, position, scope, hidden, superordinate, True):
            yield Object.from_data(self.udm, obj)  # NOTE: this is missing last-modified, therefore no conditional request is done on modification!

    def _search_closed(self, filter: "Union[Dict[str, str], str, bytes, None]"=None, position: "Optional[str]"=None, scope: "Optional[str]"='sub', hidden: bool=False, superordinate: "Optional[str]"=None) -> "Iterator[ShallowObject]":
        for obj in self._search(filter, position, scope, hidden, superordinate, False):
            objself = self.client.get_relation(obj, 'self')
            uri = objself['href']
            dn = objself['name']
            yield ShallowObject(self.udm, dn, uri)

    def _search(self, filter: "Union[Dict[str, str], str, bytes, None]"=None, position: "Optional[str]"=None, scope: "Optional[str]"='sub', hidden: bool=False, superordinate: "Optional[str]"=None, opened: bool=False) -> "Iterator[Any]":
        data = {
            'position': position,
            'scope': scope,
            'hidden': '1' if hidden else '0',
        }
        if isinstance(filter, dict):
            for prop, val in filter.items():
                data.setdefault('query', {})[f'query[{prop}]'] = val
        elif isinstance(filter, str):
            data['filter'] = filter
        if superordinate:
            data['superordinate'] = superordinate
        if not opened:
            data['properties'] = 'dn'
        self.load_relations()
        entries = self.client.resolve_relation(self.relations, 'search', template=data)
        yield from self.client.resolve_relations(entries, 'udm:object')

    def get_layout(self) -> "Optional[Any]":
        self.load_relations()
        return self.udm.client.resolve_relation(self.relations, 'udm:layout').get('layout')

    def get_properties(self) -> "Optional[Any]":
        self.load_relations()
        return self.udm.client.resolve_relation(self.relations, 'udm:properties').get('properties')

    def get_property_choices(self, property: str) -> "Optional[Any]":
        self.load_relations()
        relations = self.udm.client.resolve_relation(self.relations, 'udm:properties')
        return self.udm.client.resolve_relation(relations, 'udm:property-choices', name=property).get('choices')

    def policy_result(self, policy_module: str, position: str, policy: "Optional[str]"=None) -> "Dict":
        self.load_relations()
        policy_result = self.udm.client.resolve_relation(self.relations, 'udm:policy-result', name=policy_module, template={'position': position, 'policy': policy})
        policy_result.pop('_links', None)
        policy_result.pop('_embedded', None)
        return policy_result

    def get_report_types(self) -> "List[str]":
        self.load_relations()
        return [x['name'] for x in self.udm.client.get_relations(self.relations, 'udm:report', template={'dn': ''}) if x.get('name')]

    def create_report(self, report_type: str, object_dns: "List[str]") -> "Any":
        self.load_relations()
        return self.udm.client.resolve_relation(self.relations, 'udm:report', name=report_type, template={'dn': object_dns})


class ShallowObject(Client):

    def __init__(self, udm: "UDM", dn: "Optional[str]", uri: str, *args: "Any", **kwargs: "Any") -> None:
        super().__init__(udm.client, *args, **kwargs)
        self.dn = dn
        self.udm = udm
        self.uri = uri

    def open(self) -> "Object":
        return Object.from_response(self.udm, self.client.make_request('GET', self.uri))

    def __repr__(self) -> str:
        return f'ShallowObject(dn={self.dn})'


class References:

    def __init__(self, obj: "Optional[Object]"=None) -> None:
        self.obj = obj
        self.udm = self.obj.udm if self.obj is not None else None

    def __getitem__(self, item: str) -> "List[ShallowObject]":
        assert self.obj
        assert self.udm
        return [
            ShallowObject(self.obj.udm, x['name'], x['href'])
            for x in self.udm.client.get_relations(self.obj.hal, f'udm:object/property/reference/{item}')
        ]

    def __getattribute__(self, key):
        try:
            return super().__getattribute__(key)
        except AttributeError:
            return self[key]

    def __get__(self, obj: "Any", cls: "Type"=None) -> "References":
        return type(self)(obj)


class Object(Client):

    objects = References()

    @property
    def module(self):
        # FIXME: use "type" relation link
        # object_type = self.udm.get_relation(self.hal, 'type')['href']
        return self.udm.get(self.object_type)

    @property
    def object_type(self) -> str:
        return self.representation['objectType']

    @property
    def dn(self) -> "Optional[str]":
        return self.representation.get('dn')

    @property
    def properties(self):
        return self.representation['properties']

    @property
    def options(self) -> "Dict":
        return self.representation.get('options', {})

    @property
    def policies(self) -> "Dict":
        return self.representation.get('policies', {})

    @property
    def superordinate(self) -> "Optional[str]":
        return self.representation.get('superordinate')

    @superordinate.setter
    def superordinate(self, superordinate):
        # type. (str) -> None
        self.representation['superordinate'] = superordinate

    @property
    def position(self) -> "Optional[str]":
        return self.representation.get('position')

    @position.setter
    def position(self, position):
        # type. (str) -> None
        self.representation['position'] = position

    @property
    def uri(self) -> "Optional[str]":
        try:
            uri = self.client.get_relation(self.hal, 'self')
        except _NoRelation:
            uri = None
        if uri:
            return uri['href']
        return self.representation.get('uri')

    @classmethod
    def from_response(cls, udm: "UDM", response: "Response") -> "Object":
        return cls.from_data(udm, response.data, response.response.headers)

    @classmethod
    def from_data(cls, udm: "UDM", entry: "Dict", headers: "Optional[Mapping[str, str]]"=None) -> "Object":
        headers = headers or {}
        return cls(udm, entry, etag=headers.get('Etag'), last_modified=headers.get('Last-Modified'))

    def __init__(self, udm: "UDM", representation: "Dict", etag: "Optional[str]"=None, last_modified: "Optional[str]"=None, *args: "Any", **kwargs: "Any") -> None:
        super().__init__(udm.client, *args, **kwargs)
        self.udm = udm
        self.representation = representation
        self.hal = {
            '_links': representation.pop('_links', {}),
            '_embedded': representation.pop('_embedded', {}),
        }
        self.etag = etag
        self.last_modified = last_modified

    def __repr__(self) -> str:
        return f'Object(module={self.object_type}, dn={self.dn}, uri={self.uri})'

    def reload(self) -> None:
        uri = self.client.get_relation(self.hal, 'self')
        if uri:
            obj = ShallowObject(self.udm, self.dn, uri['href']).open()
        else:
            obj = self.module.get(self.dn)
        self._copy_from_obj(obj)

    def save(self, reload: bool=True) -> "Response":
        if self.dn:
            return self._modify(reload)
        else:
            return self._create(reload)

    def delete(self, remove_referring: bool=False) -> bytes:
        assert self.uri
        return self.client.request('DELETE', self.uri)

    def move(self, position: str) -> None:
        self.position = position
        self.save()

    def _modify(self, reload: bool=True) -> "Response":
        assert self.uri
        headers = {key: value for key, value in {
            'If-Unmodified-Since': self.last_modified,
            'If-Match': self.etag,
        }.items() if value}

        response = self.client.make_request('PUT', self.uri, data=self.representation, allow_redirects=False, **headers)  # type: ignore # <https://github.com/python/mypy/issues/10008>
        response = self._follow_redirection(response, reload)  # move() causes multiple redirections!
        return response

    def _create(self, reload: bool=True) -> "Response":
        uri = self.client.get_relation(self.hal, 'create')
        response = self.client.make_request('POST', uri['href'], data=self.representation, allow_redirects=False)
        response = self._follow_redirection(response, reload)
        return response

    def _reload_from_response(self, response: "Response", reload: bool) -> None:
        if 200 <= response.response.status_code <= 299 and 'Location' in response.response.headers:
            uri = response.response.headers['Location']
            obj = ShallowObject(self.udm, None, uri)
            if reload:
                self._copy_from_obj(obj.open())
        elif reload:
            self.reload()

    def _follow_redirection(self, response: "Response", reload: bool=True) -> "Response":
        location = None
        # python-requests doesn't follow redirects for 202
        if response.response.status_code in (201, 202) and 'Location' in response.response.headers:
            location = response.response.headers['Location']
            response = self.client.make_request('GET', location, allow_redirects=False)

        # prevent allow_redirects because it does not wait Retry-After time causing a break up after 30 fast redirections
        while 300 <= response.response.status_code <= 399 and 'Location' in response.response.headers:
            location = response.response.headers['Location']
            if response.response.headers.get('Retry-After', '').isdigit():
                time.sleep(min(30, max(0, int(response.response.headers['Retry-After']))))
            response = self.client.make_request('GET', location, allow_redirects=False)

        if location and response.response.status_code == 200:
            # the response already contains a new representation
            self._copy_from_obj(Object.from_response(self.udm, response))
        elif reload:
            self._reload_from_response(response, reload)
        return response

    def _copy_from_obj(self, obj: "Object") -> None:
        self.udm = obj.udm
        self.representation = copy.deepcopy(obj.representation)
        self.hal = copy.deepcopy(obj.hal)
        self.etag = obj.etag
        self.last_modified = obj.last_modified

    def generate_service_specific_password(self, service: str) -> "Optional[Any]":
        uri = self.client.get_relation(self.hal, 'udm:service-specific-password')['href']
        response = self.client.make_request('POST', uri, data={"service": service})
        return response.data.get('password', None)

    def get_layout(self) -> "Optional[Any]":
        return self.udm.client.resolve_relation(self.hal, 'udm:layout').get('layout')

    def get_properties(self) -> "Optional[Any]":
        return self.udm.client.resolve_relation(self.hal, 'udm:properties').get('properties')

    def get_property_choices(self, property: str) -> "Optional[Any]":
        hal = self.udm.client.resolve_relation(self.hal, 'udm:properties')
        return self.udm.client.resolve_relation(hal, 'udm:property-choices', name=property).get('choices')

    def policy_result(self, policy_module: str, policy: "Optional[str]"=None) -> "Dict":
        policy_result = self.udm.client.resolve_relation(self.hal, 'udm:policy-result', name=policy_module, template={'policy': policy})
        policy_result.pop('_links', None)
        policy_result.pop('_embedded', None)
        return policy_result
