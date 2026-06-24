#!/usr/bin/python3
#
# Univention Directory Manager
#  REST API client
#
# SPDX-FileCopyrightText: 2019-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
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

from __future__ import annotations

import copy
import http.client
import time
import warnings
from typing import TYPE_CHECKING, Any, Self

import requests
import uritemplate


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

_ResponseType = requests.Response
http.client._MAXHEADERS = 1000


class HTTPError(Exception):
    """Generic HTTP Error."""

    __slots__ = ('code', 'error_details', 'response')

    errors = {}

    def __init__(self, code: int, message: str, response: _ResponseType | None, error_details: dict | None = None) -> None:
        self.code = code
        self.response = response
        self.error_details = error_details
        super().__init__(message)

    def __init_subclass__(cls, code=None, **kwargs):
        if code:
            HTTPError.errors[code] = cls
        super().__init_subclass__(**kwargs)


class BadRequest(HTTPError, code=400):
    """A 400 Bad Request error."""


class Unauthorized(HTTPError, code=401):
    """A 401 Unauthorized error."""


class Forbidden(HTTPError, code=403):
    """A 403 Forbidden error."""


class NotFound(HTTPError, code=404):
    """A 404 Not Found error."""


class PreconditionFailed(HTTPError, code=412):
    """A 412 Precondition Failed error."""


class UnprocessableEntity(HTTPError, code=422):
    """A 422 Unprocessable Entity error."""


class TooManyRequests(HTTPError, code=429):
    """A 429 Too Many Requests error."""


class ServerError(HTTPError, code=500):
    """A 500 Internal Server error."""


class ServiceUnavailable(HTTPError, code=503):
    """A 503 Service Unavailable error."""


class ConnectionError(Exception):
    """A HTTP Connection error."""


class UnexpectedResponse(ConnectionError):
    """A unexpected response payload error (e.g. not JSON)."""


class _NoRelation(Exception):
    pass


class Response:  # noqa: B903
    """Response wrapper."""

    __slots__ = ('data', 'response', 'uri')

    def __init__(self, response: _ResponseType, data: Any, uri: str) -> None:
        self.response = response
        self.data = data
        self.uri = uri


class Session:
    """A session holding credentials and language settings for a client."""

    __slots__ = ('credentials', 'default_headers', 'enable_caching', 'language', 'reconnect', 'session', 'user_agent')

    def __init__(self, credentials: UDM, language: str = 'en-US', reconnect: bool = True, user_agent: str = 'univention.lib/1.0', enable_caching: bool = False) -> None:
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

    def create_session(self) -> requests.Session:
        sess = requests.session()
        if self.credentials.bearer_token:
            sess.headers['Authorization'] = 'Bearer %s' % (self.credentials.bearer_token,)
        else:
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

    def get_method(self, method: str) -> Callable[..., _ResponseType]:
        sess = self.session
        return {
            'GET': sess.get,
            'POST': sess.post,
            'PUT': sess.put,
            'DELETE': sess.delete,
            'PATCH': sess.patch,
            'OPTIONS': sess.options,
        }.get(method.upper(), sess.get)

    def request(self, method: str, uri: str, data: dict | None = None, expect_json: bool = False, **headers: str) -> Any:
        return self.make_request(method, uri, data, expect_json=expect_json, **headers).data  # type: ignore # <https://github.com/python/mypy/issues/10008>

    def make_request(self, method: str, uri: str, data: dict | None = None, expect_json: bool = False, allow_redirects: bool = True, custom_redirect_handling: bool = False, **headers: str) -> Response:
        if method in ('GET', 'HEAD'):
            params = data
            json = None
        else:
            params = None
            json = data

        def doit() -> Response:
            try:
                response = self.get_method(method)(uri, params=params, json=json, headers=dict(self.default_headers, **headers), allow_redirects=allow_redirects)
            except requests.exceptions.ConnectionError as exc:
                raise ConnectionError(exc)
            if custom_redirect_handling:
                response = self._follow_redirection(response)
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

    def _follow_redirection(self, response: Response) -> Response:
        location = response.headers.get('Location')
        # python-requests doesn't follow redirects for 202
        if location and response.status_code in (201, 202):
            response = self.make_request('GET', location, allow_redirects=False).response

        # prevent allow_redirects because it does not wait Retry-After time causing a break up after 30 fast redirections
        while 300 <= response.status_code <= 399 and 'Location' in response.headers:
            location = response.headers['Location']
            if response.headers.get('Retry-After', '').isdigit():
                time.sleep(min(30, max(0, int(response.headers['Retry-After']))))
            response = self.make_request(self._select_method(response), location, allow_redirects=False).response

        return response

    def _select_method(self, response: Response) -> str:
        if response.status_code in (300, 301, 303) and response.request.method != 'HEAD':
            return 'GET'
        return response.request.method

    def eval_response(self, response: _ResponseType, expect_json: bool = False) -> Any:
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
            cls = HTTPError.errors.get(response.status_code, HTTPError)
            raise cls(response.status_code, msg, response, error_details=error_details)
        if response.headers.get('Content-Type') in ('application/json', 'application/hal+json'):
            return response.json()
        elif expect_json:
            raise UnexpectedResponse(response.text)
        if response.status_code == 204:
            return {}
        return response.text

    def get_relations(self, entry: dict, relation: str, name: str | None = None, template: dict[str, Any] | None = None) -> Iterator[dict[str, str]]:
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

    def has_relation(self, entry: dict, relation: str, name: str | None = None, template: dict[str, Any] | None = None) -> bool:
        rel = next(self.get_relations(entry, relation, name, template), None)
        return rel is not None

    def get_relation(self, entry: dict, relation: str, name: str | None = None, template: dict[str, Any] | None = None) -> dict[str, str]:
        rel = next(self.get_relations(entry, relation, name, template), None)
        if rel is None:
            raise _NoRelation(relation)
        return rel

    def resolve_relations(self, entry: dict, relation: str, name: str | None = None, template: dict[str, Any] | None = None) -> Iterator[Any]:
        embedded = entry.get('_embedded', {})
        if isinstance(embedded, dict) and relation in embedded:
            yield from embedded[relation]
            return

        for rel in self.get_relations(entry, relation, name, template):
            yield self.make_request('GET', rel['href']).data

    def resolve_relation(self, entry: dict, relation: str, name: str | None = None, template: dict[str, Any] | None = None) -> Any:
        rel = next(self.resolve_relations(entry, relation, name, template), None)
        if rel is None:
            raise _NoRelation(relation)
        return rel


class Client:  # noqa: B903
    """Abstract client base class."""

    __slots__ = ('client',)

    def __init__(self, client: Session) -> None:
        self.client = client


class UDM(Client):
    """Univention Directory Manager client."""

    __slots__ = ('_api_version', 'bearer_token', 'entry', 'password', 'uri', 'username')

    @classmethod
    def http(cls, uri: str, username: str, password: str) -> Self:
        return cls(uri, username, password)

    @classmethod
    def bearer(cls, uri: str, bearer_token: str) -> Self:
        return cls(uri, None, None, bearer_token=bearer_token)

    def __init__(self, uri: str, username: str, password: str, *args: Any, **kwargs: Any) -> None:
        self.uri = uri
        self.username = username
        self.password = password
        self.bearer_token = kwargs.pop('bearer_token', None)
        self._api_version: str | None = None
        self.entry: Any = None
        super().__init__(Session(self, *args, **kwargs))

    def load(self) -> None:
        # FIXME: use HTTP caching instead of memory caching
        if self.entry is None:
            self.reload()

    def reload(self) -> None:
        self.entry = self.client.request('GET', self.uri, expect_json=True)

    def get_ldap_base(self) -> str | None:
        self.load()
        return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:ldap-base')).dn

    def modules(self, name: str | None = None) -> Iterator[Module]:
        self.load()
        for module in self.client.resolve_relations(self.entry, 'udm:object-modules'):
            for module_info in self.client.get_relations(module, 'udm:object-types', name):
                yield Module(self, module_info['href'], module_info['name'], module_info['title'])

    def obj_by_dn(self, dn: str) -> Object:
        self.load()
        return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:object/get-by-dn', template={'dn': dn}))

    def obj_by_uuid(self, uuid: str) -> Object:
        self.load()
        return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:object/get-by-uuid', template={'uuid': uuid}))

    def get(self, name: str) -> Module | None:
        for module in self.modules(name):
            return module

        return None

    def get_object(self, object_type: str, dn: str) -> Object | None:
        mod = self.get(object_type)
        assert mod
        obj = mod.get(dn)
        return obj

    def version(self, api_version: str) -> Self:
        self._api_version = api_version
        return self

    def __repr__(self) -> str:
        return f'UDM(uri={self.uri!r}, username={self.username!r}, password=***)'


class Module(Client):
    """A UDM module representation."""

    __slots__ = ('name', 'password', 'relations', 'title', 'udm', 'uri', 'username')

    def __init__(self, udm: UDM, uri: str, name: str, title: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(udm.client, *args, **kwargs)
        self.udm = udm
        self.uri = uri
        self.username = udm.username
        self.password = udm.password
        self.name = name
        self.title = title
        self.relations: dict = {}

    def load_relations(self) -> None:
        if self.relations:
            return
        self.relations = self.client.request('GET', self.uri)

    def __repr__(self) -> str:
        return f'Module(uri={self.uri!r}, name={self.name!r})'

    def new(self, position: str | None = None, superordinate: str | None = None, template: dict[str, Any] | None = None) -> Object:
        self.load_relations()
        data = {'position': position, 'superordinate': superordinate, 'template': template}
        resp = self.client.resolve_relation(self.relations, 'create-form', template=data)
        return Object.from_data(self.udm, resp)

    def get(self, dn: str, properties: list[str] | None = None) -> Object | None:
        # TODO: use a link relation instead of a search
        for obj in self._search_closed(position=dn, scope='base', properties=properties):
            return obj.open()
        raise NotFound(404, 'Wrong object type!?', None)  # FIXME: object exists but is of different module. should be fixed on the server.

    def get_by_entry_uuid(self, uuid: str, properties: list[str] | None = None) -> Object | None:
        # TODO: use a link relation instead of a search
        # return self.udm.get_by_uuid(uuid)
        for obj in self._search_closed(filter={'entryUUID': uuid}, scope='base', properties=properties):
            return obj.open()
        raise NotFound(404, 'Wrong object type!?', None)  # FIXME: object exists but is of different module. should be fixed on the server.

    def get_by_id(self, dn: str, properties: list[str] | None = None) -> Object | None:
        # TODO: Needed?
        raise NotImplementedError()

    def search(
        self,
        filter: dict[str, str] | str | None = None,
        position: str | None = None,
        scope: str | None = 'sub',
        hidden: bool = False,
        superordinate: str | None = None,
        opened: bool = False,
        properties: list[str] | None = None,
    ) -> Iterator[Any]:
        """Search objects."""
        if opened:
            return self._search_opened(filter, position, scope, hidden, superordinate, properties)
        return self._search_closed(filter, position, scope, hidden, superordinate, properties)

    def _search_opened(self, filter: dict[str, str] | str | None = None, position: str | None = None, scope: str | None = 'sub', hidden: bool = False, superordinate: str | None = None, properties: list[str] | None = None) -> Iterator[Object]:
        for obj in self._search(filter, position, scope, hidden, superordinate, True, properties):
            yield Object.from_data(self.udm, obj)  # NOTE: this is missing last-modified, therefore no conditional request is done on modification!

    def _search_closed(self, filter: dict[str, str] | str | None = None, position: str | None = None, scope: str | None = 'sub', hidden: bool = False, superordinate: str | None = None, properties: list[str] | None = None) -> Iterator[ShallowObject]:
        for obj in self._search(filter, position, scope, hidden, superordinate, False, properties):
            yield self._shallow_object_from_entry(obj)

    def _search(self, filter: dict[str, str] | str | None = None, position: str | None = None, scope: str | None = 'sub', hidden: bool = False, superordinate: str | None = None, opened: bool = False, properties: list[str] | None = None) -> Iterator[Any]:
        entries = self._search_response(filter, position, scope, hidden, superordinate, opened, properties)
        yield from self.client.resolve_relations(entries, 'udm:object')

    def _search_response(
        self,
        filter: dict[str, str] | str | None = None,
        position: str | None = None,
        scope: str | None = 'sub',
        hidden: bool = False,
        superordinate: str | None = None,
        opened: bool = False,
        properties: list[str] | None = None,
        page_size: int | None = None,
        page: int | None = None,
        sort_by: str | list[str] | None = None,
        reverse: bool = False,
        pagination: bool = False,
    ) -> dict:
        data = self._search_template(filter, position, scope, hidden, superordinate, opened, properties, page_size, page, sort_by, reverse, pagination)
        self.load_relations()
        return self.client.resolve_relation(self.relations, 'search', template=data)

    def _search_template(
        self,
        filter: dict[str, str] | str | None = None,
        position: str | None = None,
        scope: str | None = 'sub',
        hidden: bool = False,
        superordinate: str | None = None,
        opened: bool = False,
        properties: list[str] | None = None,
        page_size: int | None = None,
        page: int | None = None,
        sort_by: str | list[str] | None = None,
        reverse: bool = False,
        pagination: bool = False,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
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
            data['opened'] = '0'
            data['properties'] = ['dn']
        if properties:
            data['properties'] = properties
        if page_size is not None:
            if page_size < 0:
                raise ValueError('page_size must not be negative')
            data['page_size'] = str(page_size)
        if page is not None:
            if page < 1:
                raise ValueError('page must be greater than zero')
            data['page'] = str(page)
        if sort_by:
            data['sort'] = sort_by
        if page_size is not None or page is not None or sort_by:
            data['dir'] = 'DESC' if reverse else 'ASC'
        if pagination:
            data['pagination'] = '1'
        return data

    def search_paginated(
        self,
        filter: dict[str, str] | str | None = None,
        position: str | None = None,
        scope: str | None = 'sub',
        hidden: bool = False,
        superordinate: str | None = None,
        opened: bool = False,
        properties: list[str] | None = None,
        page_size: int = 50,
        sort_by: str | list[str] | None = None,
        reverse: bool = False,
        pagination: bool = False,
    ) -> Iterator[Any]:
        """Yield all search results by following server-provided page links."""
        page = self.search_page(filter, position, scope, hidden, superordinate, opened, properties, page_size, 1, sort_by, reverse, pagination)
        while True:
            yield from page.items
            next_page = page.next()
            if next_page is None:
                break
            page = next_page

    def search_page(
        self,
        filter: dict[str, str] | str | None = None,
        position: str | None = None,
        scope: str | None = 'sub',
        hidden: bool = False,
        superordinate: str | None = None,
        opened: bool = False,
        properties: list[str] | None = None,
        page_size: int | None = 50,
        page: int = 1,
        sort_by: str | list[str] | None = None,
        reverse: bool = False,
        pagination: bool = False,
    ) -> _SearchPage:
        """Return one paginated search result page including navigation metadata."""
        warnings.warn('UDM REST API Pagination is unsupported, broken, experimental and the methods may change in the future. ', DeprecationWarning, stacklevel=3)
        entry = self._search_response(filter, position, scope, hidden, superordinate, opened, properties, page_size, page, sort_by, reverse, pagination)
        return self._page_from_entry(entry, opened, page_size, pagination)

    def _page_from_entry(self, entry: dict, opened: bool = False, page_size: int | None = None, pagination: bool = False) -> _SearchPage:
        if opened:
            items = [Object.from_data(self.udm, obj) for obj in self.client.resolve_relations(entry, 'udm:object')]
        else:
            items = [self._shallow_object_from_entry(obj) for obj in self.client.resolve_relations(entry, 'udm:object')]
        if pagination:
            return _SearchPage(self, entry, items, opened, page_size)
        return _SimpleSearchPage(self, entry, items, opened, page_size)

    def _shallow_object_from_entry(self, entry: dict) -> ShallowObject:
        objself = self.client.get_relation(entry, 'self')
        uri = objself['href']
        dn = objself['name']
        return ShallowObject(self.udm, dn, uri)

    def get_layout(self) -> Any | None:
        self.load_relations()
        return self.udm.client.resolve_relation(self.relations, 'udm:layout').get('layout')

    def get_properties(self) -> Any | None:
        self.load_relations()
        return self.udm.client.resolve_relation(self.relations, 'udm:properties').get('properties')

    def get_property_choices(self, property: str) -> Any | None:
        self.load_relations()
        relations = self.udm.client.resolve_relation(self.relations, 'udm:properties')
        return self.udm.client.resolve_relation(relations, 'udm:property-choices', name=property).get('choices')

    def policy_result(self, policy_module: str, position: str, policy: str | None = None) -> dict:
        self.load_relations()
        policy_result = self.udm.client.resolve_relation(self.relations, 'udm:policy-result', name=policy_module, template={'position': position, 'policy': policy})
        policy_result.pop('_links', None)
        policy_result.pop('_embedded', None)
        return policy_result

    def get_report_types(self) -> list[str]:
        self.load_relations()
        return [x['name'] for x in self.udm.client.get_relations(self.relations, 'udm:report', template={'dn': ''}) if x.get('name')]

    def create_report(self, report_type: str, object_dns: list[str]) -> Any:
        self.load_relations()
        return self.udm.client.resolve_relation(self.relations, 'udm:report', name=report_type, template={'dn': object_dns})


class ShallowObject(Client):
    """A reference to an UDM object, which is not recevied from server yet."""

    __slots__ = ('dn', 'udm', 'uri')

    def __init__(self, udm: UDM, dn: str | None, uri: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(udm.client, *args, **kwargs)
        self.dn = dn
        self.udm = udm
        self.uri = uri

    def open(self) -> Object:
        return Object.from_response(self.udm, self.client.make_request('GET', self.uri))

    def __repr__(self) -> str:
        return f'ShallowObject(dn={self.dn!r})'


class References:
    # """Descriptor that provides access to related UDM objects."""

    __slots__ = ('obj', 'udm')

    def __init__(self, obj: Object | None = None) -> None:
        self.obj = obj
        self.udm = self.obj.udm if self.obj is not None else None

    def __getitem__(self, item: str) -> list[ShallowObject]:
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

    def __get__(self, obj: Any, cls: type | None = None) -> References:
        """Return a new References bound to the given object."""
        return type(self)(obj)


class Object(Client):
    """A UDM object with related references."""

    objects = References()
    """Descriptor that provides access to related UDM objects."""

    @property
    def module(self):
        # FIXME: use "type" relation link
        # object_type = self.udm.get_relation(self.hal, 'type')['href']
        return self.udm.get(self.object_type)

    @property
    def object_type(self) -> str:
        return self.representation['objectType']

    @property
    def dn(self) -> str | None:
        return self.representation.get('dn')

    @property
    def properties(self):
        return self.representation['properties']

    @property
    def options(self) -> dict:
        return self.representation.get('options', {})

    @property
    def policies(self) -> dict:
        return self.representation.get('policies', {})

    @property
    def superordinate(self) -> str | None:
        return self.representation.get('superordinate')

    @superordinate.setter
    def superordinate(self, superordinate: str) -> None:
        self.representation['superordinate'] = superordinate

    @property
    def position(self) -> str | None:
        return self.representation.get('position')

    @position.setter
    def position(self, position: str) -> None:
        self.representation['position'] = position

    @property
    def uri(self) -> str | None:
        try:
            uri = self.client.get_relation(self.hal, 'self')
        except _NoRelation:
            uri = None
        if uri:
            return uri['href']
        return self.representation.get('uri')

    @classmethod
    def from_response(cls, udm: UDM, response: Response) -> Object:
        return cls.from_data(udm, response.data, response.response.headers)

    @classmethod
    def from_data(cls, udm: UDM, entry: dict, headers: Mapping[str, str] | None = None) -> Object:
        headers = headers or {}
        return cls(udm, entry, etag=headers.get('Etag'), last_modified=headers.get('Last-Modified'))

    __slots__ = ('etag', 'hal', 'last_modified', 'representation', 'udm')

    def __init__(self, udm: UDM, representation: dict, etag: str | None = None, last_modified: str | None = None, *args: Any, **kwargs: Any) -> None:
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
        return f'Object(module={self.object_type!r}, dn={self.dn!r}, uri={self.uri!r})'

    def reload(self) -> None:
        try:
            uri = self.client.get_relation(self.hal, 'self')
        except _NoRelation:
            uri = None
        if uri:
            obj = ShallowObject(self.udm, self.dn, uri['href']).open()
        else:
            obj = self.module.get(self.dn)
        self._copy_from_obj(obj)

    def save(self, reload: bool = True) -> Response:
        if self.dn:
            return self._modify(reload)
        else:
            return self._create(reload)

    def json_patch(self, patch: dict, reload: bool = True) -> Response:
        if self.dn:
            return self._patch(patch, reload=reload)
        else:
            uri = self.client.get_relation(self.hal, 'create')
            return self._request('POST', uri['href'], patch, {'Content-Type': 'application/json-patch+json'})

    def delete(self, remove_referring: bool = False) -> bytes:
        assert self.uri
        headers = {key: value for key, value in {
            'If-Unmodified-Since': self.last_modified,
            'If-Match': self.etag,
        }.items() if value}
        return self.client.request('DELETE', self.uri, **headers)  # type: ignore # <https://github.com/python/mypy/issues/10008>

    def restore(self, reload: bool = True) -> Response:
        """Restore an object from the Recycle Bin."""
        uri = self.client.get_relation(self.hal, 'udm:restore')['href']
        return self._request('POST', uri, {}, {}, reload=reload)

    def move(self, position: str, reload: bool = True) -> None:
        self.position = position
        self.save(reload=reload)

    def _modify(self, reload: bool = True) -> Response:
        assert self.uri
        headers = {key: value for key, value in {
            'If-Unmodified-Since': self.last_modified,
            'If-Match': self.etag,
        }.items() if value}
        return self._request('PUT', self.uri, self.representation, headers, reload=reload)

    def _patch(self, data: dict, reload: bool = True) -> Response:
        assert self.uri
        headers = {key: value for key, value in {
            'If-Unmodified-Since': self.last_modified,
            'If-Match': self.etag,
            'Content-Type': 'application/json-patch+json',
        }.items() if value}
        return self._request('PATCH', self.uri, data, headers, reload=reload)

    def _create(self, reload: bool = True) -> Response:
        uri = self.client.get_relation(self.hal, 'create')
        return self._request('POST', uri['href'], self.representation, {}, reload=reload)

    def _request(self, method: str, uri: str, data: dict, headers: dict, reload: bool = True) -> Response:
        response = self.client.make_request(method, uri, data=data, allow_redirects=False, custom_redirect_handling=True, **headers)  # type: ignore # <https://github.com/python/mypy/issues/10008>
        self._reload_from_response(response, reload)
        return response

    def _reload_from_response(self, response: Response, reload: bool) -> None:
        if reload and 200 <= response.response.status_code <= 299 and 'Location' in response.response.headers:
            uri = response.response.headers['Location']
            obj = ShallowObject(self.udm, None, uri)
            self._copy_from_obj(obj.open())
            return

        if response.response.status_code == 200:
            # the response already contains a new representation
            self._copy_from_obj(Object.from_response(self.udm, response))
            return

        if reload:
            self.reload()

    def _copy_from_obj(self, obj: Object) -> None:
        self.udm = obj.udm
        self.representation = copy.deepcopy(obj.representation)
        self.hal = copy.deepcopy(obj.hal)
        self.etag = obj.etag
        self.last_modified = obj.last_modified

    def generate_service_specific_password(self, service: str) -> Any | None:
        uri = self.client.get_relation(self.hal, 'udm:service-specific-password')['href']
        response = self.client.make_request('POST', uri, data={"service": service})
        return response.data.get('password', None)

    def get_layout(self) -> Any | None:
        return self.udm.client.resolve_relation(self.hal, 'udm:layout').get('layout')

    def get_properties(self) -> Any | None:
        return self.udm.client.resolve_relation(self.hal, 'udm:properties').get('properties')

    def get_property_choices(self, property: str) -> Any | None:
        hal = self.udm.client.resolve_relation(self.hal, 'udm:properties')
        return self.udm.client.resolve_relation(hal, 'udm:property-choices', name=property).get('choices')

    def policy_result(self, policy_module: str, policy: str | None = None) -> dict:
        policy_result = self.udm.client.resolve_relation(self.hal, 'udm:policy-result', name=policy_module, template={'policy': policy})
        policy_result.pop('_links', None)
        policy_result.pop('_embedded', None)
        return policy_result


class _SimpleSearchPage:
    """A single paged UDM search result page."""

    __slots__ = ('entry', 'items', 'module', 'opened', 'page_size', 'pagination')

    def __init__(
        self,
        module: Module,
        entry: dict,
        items: list[Any],
        opened: bool = False,
        page_size: int | None = None,
    ) -> None:
        self.module = module
        self.entry = entry
        self.items = items
        self.opened = opened
        self.page_size = page_size
        self.pagination = False

    def __repr__(self) -> str:
        return f'SimpleSearchPage(page_size={self.page_size}, items={len(self.items)}, has_next={self.has_next})'

    def __iter__(self) -> Iterator[Any]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def _follow(self, relation: str) -> Self | None:
        try:
            entry = self.module.client.resolve_relation(self.entry, relation)
        except _NoRelation:
            return None
        return self.module._page_from_entry(entry, opened=self.opened, page_size=self.page_size, pagination=self.pagination)

    @property
    def has_next(self) -> bool:
        return self.module.client.has_relation(self.entry, 'next')

    def next(self) -> Self | None:
        return self._follow('next')


class _SearchPage(_SimpleSearchPage):
    """A single paginated UDM search result page."""

    __slots__ = ('page', 'total')

    def __init__(
        self,
        module: Module,
        entry: dict,
        items: list[Any],
        opened: bool = False,
        page_size: int | None = None,
    ) -> None:
        super().__init__(module, entry, items, opened, page_size)
        try:
            self.page = int(self.module.client.get_relation(entry, 'current')['page'])
        except _NoRelation:  # module doesn't provide pagination
            self.page = 0
        self.total = entry.get('results')
        self.pagination = True

    def __repr__(self) -> str:
        return f'SearchPage(page={self.page}, page_size={self.page_size}, items={len(self.items)}, total={self.total}, has_prev={self.has_prev}, has_next={self.has_next}, last_page={self.last_page})'

    @property
    def last_page(self) -> int | None:
        try:
            last = self.module.client.get_relation(self.entry, 'last')
        except _NoRelation:
            return None
        return int(last['page'])

    @property
    def has_prev(self) -> bool:
        return self.module.client.has_relation(self.entry, 'prev')

    def first(self) -> Self:
        return self._follow('first') or self

    def prev(self) -> Self | None:
        return self._follow('prev')

    def last(self) -> Self | None:
        return self._follow('last')


class PatchDocument:
    """application/json-patch+json representation"""

    __slots__ = ('patch',)

    def __init__(self):
        self.patch = []

    def add(self, path_segments, value):
        self.patch.append({
            'op': 'add',
            'path': self.expand_path(path_segments),
            'value': value,
        })

    def replace(self, path_segments, value):
        self.patch.append({
            'op': 'replace',
            'path': self.expand_path(path_segments),
            'value': value,
        })

    def remove(self, path_segments, value):
        self.patch.append({
            'op': 'remove',
            'path': self.expand_path(path_segments),
            'value': value,  # TODO: not official
        })

    def move(self, path_segments, from_segments):
        self.patch.append({
            'op': 'move',
            'path': self.expand_path(path_segments),
            'from': self.expand_path(from_segments),
        })

    def copy(self, path_segments, from_segments):
        self.patch.append({
            'op': 'copy',
            'path': self.expand_path(path_segments),
            'from': self.expand_path(from_segments),
        })

    def test(self, path_segments, value):
        self.patch.append({
            'op': 'test',
            'path': self.expand_path(path_segments),
            'value': value,
        })

    def expand_path(self, path_segments):
        return '/'.join(path.replace('~', '~0').replace('/', '~1') for path in ['', *path_segments])
