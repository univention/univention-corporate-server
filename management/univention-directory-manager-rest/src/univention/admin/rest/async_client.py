#!/usr/bin/python3
#
# Univention Directory Manager
#  REST API async client
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2019-2024 Univention GmbH
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
Sample asynchronous client for the UDM REST API.

```python
import asyncio
from univention.admin.rest.async_client import UDM
uri = 'http://localhost/univention/udm/'

async def main():
    async with UDM.http(uri, 'Administrator', 'univention') as udm:
        module = await udm.get('users/user')
        print(f'Found {module}')
        objs = module.search()
        async for obj in objs:
            if not obj:
                continue
            obj = await obj.open()
            print(f'Object {obj}')
            for group in obj.objects.groups:
                grp = await group.open()
                print(f'Group {grp}')

asyncio.run(main())
```
"""

from __future__ import annotations

import asyncio
import copy
from types import TracebackType
from typing import (
    Any, AsyncIterator, Awaitable, Callable, Dict, Iterator, List, Mapping, Optional, Type, TypeVar, Union, cast,
)

import aiohttp
import uritemplate
from typing_extensions import Protocol

from .client import (
    BadRequest, ConnectionError, Forbidden, HTTPError, HttpRequestP, HttpResponse, NoRelation, NotFound,
    ObjectCopyProto, ObjectRepr, PreconditionFailed, References, Response, ServerError, ServiceUnavailable,
    Unauthorized, UnexpectedResponse, UnprocessableEntity,
)


T = TypeVar('T')
U = TypeVar('U')


try:
    aiter  # noqa: B018
except NameError:  # Python 3.7
    class _AsyncIterable:
        def __init__(self, iterable: AsyncIterator[T]) -> None:
            self.iterable = iterable

        def __aiter__(self) -> _AsyncIterable:
            return self

        async def __anext__(self) -> T:
            return await anext(self.iterable)

    def anext(iterable: AsyncIterator[U]) -> Awaitable[U]:
        return iterable.__anext__()

    def aiter(iterable: AsyncIterator[U]) -> _AsyncIterable:
        return _AsyncIterable(iterable)


class AsyncHttpResponse(HttpResponse, Protocol):
    request_info: HttpRequestP
    status: int

    async def text(self) -> str:  # type: ignore
        ...

    async def json(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:  # type: ignore
        ...


class AsyncResponse(Response[AsyncHttpResponse]):
    ...


class Session:

    __slots__ = ('credentials', 'default_headers', 'enable_caching', 'language', 'reconnect', 'session', 'user_agent')

    def __init__(self, credentials: UDM, language: str = 'en-US', reconnect: bool = True, user_agent: str = 'univention.lib/1.0', enable_caching: bool = False, concurrency_limit: int = 10) -> None:
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
        self.session = self.create_session(concurrency_limit)

    async def __aenter__(self) -> Session:
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]],
                        exc_value: Optional[BaseException],
                        traceback: Optional[TracebackType]) -> None:
        await self.session.__aexit__(exc_type, exc_value, traceback)

    def create_session(self, concurrency_limit: int = 10) -> aiohttp.ClientSession:
        connector = aiohttp.TCPConnector(limit=concurrency_limit)
        auth = aiohttp.BasicAuth(self.credentials.username, self.credentials.password)  # type: ignore
        return aiohttp.ClientSession(connector=connector, auth=auth)

    def get_method(self, method: str) -> Callable[..., Awaitable[AsyncHttpResponse]]:
        sess = self.session
        func_mapping: Dict[str, Callable[..., Awaitable[aiohttp.ClientResponse]]] = {
            'GET': sess.get,
            'POST': sess.post,
            'PUT': sess.put,
            'DELETE': sess.delete,
            'PATCH': sess.patch,
            'OPTIONS': sess.options,
        }
        return cast(Callable[..., Awaitable[AsyncHttpResponse]], func_mapping.get(method.upper(), sess.get))

    async def request(self, method: str, uri: str, data: Optional[Dict[str, Any]] = None, expect_json: bool = False, **headers: str) -> Any:
        return (await self.make_request(method, uri, data, expect_json=expect_json, **headers)).data  # type: ignore # <https://github.com/python/mypy/issues/10008>

    async def make_request(self, method: str, uri: str, data: Optional[Dict[str, Any]] = None, expect_json: bool = False, allow_redirects: bool = True, custom_redirect_handling: bool = False, **headers: str) -> AsyncResponse:
        if method in ('GET', 'HEAD'):
            params = data
            json = None
        else:
            params = None
            json = data

        async def doit() -> AsyncResponse:
            try:
                response: AsyncHttpResponse = await self.get_method(method)(uri, params=params, json=json, headers=dict(self.default_headers, **headers), allow_redirects=allow_redirects)
            except aiohttp.ClientConnectionError as exc:  # pragma: no cover
                raise ConnectionError(exc)
            if custom_redirect_handling:
                response = await self._follow_redirection(response)
            data = await self.eval_response(response, expect_json=expect_json)
            return AsyncResponse(response, data, uri)

        for _i in range(5):
            try:
                return await doit()
            except ServiceUnavailable as exc:  # TODO: same for ConnectionError? python-request does it itself.
                if not self.reconnect:  # pragma: no cover
                    raise
                try:
                    assert exc.response is not None
                    retry_after = min(5, int(exc.response.headers.get('Retry-After', 1)))
                except ValueError:  # pragma: no cover
                    retry_after = 1
                await asyncio.sleep(retry_after)

        return await doit()

    async def _follow_redirection(self, response: AsyncHttpResponse) -> AsyncHttpResponse:
        location = response.headers.get('Location')
        #  aiohttp doesn't follow redirects for 202?
        if location and response.status in (201, 202):
            response = (await self.make_request('GET', location, allow_redirects=False)).response

        # prevent allow_redirects because it does not wait Retry-After time causing a break up after 30 fast redirections
        while 300 <= response.status <= 399 and 'Location' in response.headers:
            location = response.headers['Location']
            if response.headers.get('Retry-After', '').isdigit():
                await asyncio.sleep(min(30, max(0, int(response.headers['Retry-After']))))
            response = (await self.make_request(self._select_method(response), location, allow_redirects=False)).response

        return response

    def _select_method(self, response: AsyncHttpResponse) -> str:
        if response.status in (300, 301, 303) and response.request_info.method != 'HEAD':
            return 'GET'
        return response.request_info.method  # pragma: no cover

    async def eval_response(self, response: AsyncHttpResponse, expect_json: bool = False) -> Any:
        if response.status >= 399:
            msg = f'{response.request_info.method} {response.url}: {response.status}'
            error_details = None
            try:
                json = await response.json()
            except (ValueError, aiohttp.client_exceptions.ContentTypeError):  # pragma: no cover
                pass
            else:
                if isinstance(json, dict):
                    error_details = json.get('error', {})
                    try:
                        error_details['error'] = [error async for error in self.resolve_relations(json, 'udm:error')]
                    except NoRelation:  # pragma: no cover
                        pass
                    if error_details:
                        server_message = error_details.get('message')
                        # traceback = error_details.get('traceback')
                        if server_message:
                            msg += f'\n{server_message}'
            errors: Dict[int, Type[HTTPError]] = {400: BadRequest, 404: NotFound, 403: Forbidden, 401: Unauthorized, 412: PreconditionFailed, 422: UnprocessableEntity, 500: ServerError, 503: ServiceUnavailable}
            cls = errors.get(response.status, HTTPError)
            raise cls(response.status, msg, response, error_details=error_details)
        if response.headers.get('Content-Type') in ('application/json', 'application/hal+json'):
            return await response.json()
        elif expect_json:  # pragma: no cover
            raise UnexpectedResponse(await response.text())
        return await response.text()

    def get_relations(self, entry: Dict[str, Any], relation: str, name: Optional[str] = None, template: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, str]]:
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

    def get_relation(self, entry: Dict[str, Any], relation: str, name: Optional[str] = None, template: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        try:
            return next(self.get_relations(entry, relation, name, template))
        except StopIteration:  # pragma: no cover
            raise NoRelation(relation)

    async def resolve_relations(self, entry: Dict[str, Any], relation: str, name: Optional[str] = None, template: Optional[Dict[str, Any]] = None) -> AsyncIterator[Dict[str, Any]]:
        embedded = entry.get('_embedded', {})
        if isinstance(embedded, dict) and relation in embedded:
            # yield from embedded[relation]
            for x in embedded[relation]:
                yield x
            return

        for rel in self.get_relations(entry, relation, name, template):
            yield (await self.make_request('GET', rel['href'])).data

    async def resolve_relation(self, entry: Dict[str, Any], relation: str, name: Optional[str] = None, template: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            return await anext(self.resolve_relations(entry, relation, name, template))
        except StopAsyncIteration:  # pragma: no cover
            raise NoRelation(relation)


class Client:

    __slots__ = ('client',)

    def __init__(self, client: Session) -> None:
        self.client = client


class UDM(Client):

    __slots__ = ('bearer_token', 'entry', 'password', 'uri', 'username')

    @classmethod
    def http(cls, uri: str, username: str, password: str) -> UDM:
        return cls(uri, username, password)

    @classmethod  # pragma: no cover
    def bearer(cls, uri: str, bearer_token: str) -> UDM:
        return cls(uri, None, None, bearer_token=bearer_token)

    def __init__(self, uri: str, username: Optional[str], password: Optional[str], *args: Any, **kwargs: Any) -> None:
        self.uri = uri
        self.username = username
        self.password = password
        self.bearer_token = kwargs.pop('bearer_token', None)
        self.entry: Union[Dict[str, Any], Any, None] = None
        super().__init__(Session(self, *args, **kwargs))

    async def __aenter__(self) -> UDM:
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]],
                        exc_value: Optional[BaseException],
                        traceback: Optional[TracebackType]) -> None:
        await self.client.__aexit__(exc_type, exc_value, traceback)

    async def load(self) -> None:
        # FIXME: use HTTP caching instead of memory caching
        if self.entry is None:
            await self.reload()

    async def reload(self) -> None:
        self.entry = await self.client.request('GET', self.uri, expect_json=True)

    async def get_ldap_base(self) -> Optional[str]:
        await self.load()
        assert self.entry is not None
        return Object.from_data(self, await self.client.resolve_relation(self.entry, 'udm:ldap-base')).dn

    async def modules(self, name: Optional[str] = None) -> AsyncIterator[Module]:
        await self.load()
        assert self.entry is not None
        async for module in self.client.resolve_relations(self.entry, 'udm:object-modules'):
            for module_info in self.client.get_relations(module, 'udm:object-types', name):
                yield Module(self, module_info['href'], module_info['name'], module_info['title'])

    async def obj_by_dn(self, dn: str) -> Object:
        await self.load()
        assert self.entry is not None
        return Object.from_data(self, await self.client.resolve_relation(self.entry, 'udm:object/get-by-dn', template={'dn': dn}))

    async def obj_by_uuid(self, uuid: str) -> Object:
        await self.load()
        assert self.entry is not None
        return Object.from_data(self, await self.client.resolve_relation(self.entry, 'udm:object/get-by-uuid', template={'uuid': uuid}))

    async def get(self, name: str) -> Optional[Module]:
        async for module in self.modules(name):
            return module

        return None

    async def get_object(self, object_type: str, dn: str) -> Optional[Object]:
        mod = await self.get(object_type)
        assert mod
        obj = await mod.get(dn)
        return obj

    def __repr__(self) -> str:
        return f'UDM(uri={self.uri!r}, username={self.username!r}, password=***)'


class Module(Client):

    __slots__ = ('name', 'password', 'relations', 'title', 'udm', 'uri', 'username')

    def __init__(self, udm: UDM, uri: str, name: str, title: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(udm.client, *args, **kwargs)
        self.udm = udm
        self.uri = uri
        self.username = udm.username
        self.password = udm.password
        self.name = name
        self.title = title
        self.relations: Dict[str, Any] = {}

    async def load_relations(self) -> None:
        if self.relations:
            return
        self.relations = await self.client.request('GET', self.uri)

    def __repr__(self) -> str:
        return f'Module(uri={self.uri!r}, name={self.name!r})'

    async def new(self, position: Optional[str] = None, superordinate: Optional[str] = None, template: Optional[Dict[str, Any]] = None) -> Object:
        await self.load_relations()
        data = {'position': position, 'superordinate': superordinate, 'template': template}
        resp = await self.client.resolve_relation(self.relations, 'create-form', template=data)
        return Object.from_data(self.udm, resp)

    async def get(self, dn: str, properties: Optional[List[str]] = None) -> Object:
        # TODO: use a link relation instead of a search
        async for obj in self._search_closed(position=dn, scope='base', properties=properties):
            return await obj.open()
        raise NotFound(404, 'Wrong object type!?', None)  # FIXME: object exists but is of different module. should be fixed on the server.

    async def get_by_entry_uuid(self, uuid: str, properties: Optional[List[str]] = None) -> Object:
        # TODO: use a link relation instead of a search
        # return self.udm.get_by_uuid(uuid)
        async for obj in self._search_closed(filter={'entryUUID': uuid}, scope='base', properties=properties):
            return await obj.open()
        raise NotFound(404, 'Wrong object type!?', None)  # FIXME: object exists but is of different module. should be fixed on the server.

    async def get_by_id(self, id_: str, properties: Optional[List[str]] = None) -> Object:  # pragma: no cover
        # TODO: Needed?
        raise NotImplementedError()

    async def search(self, filter: Union[Dict[str, str], str, bytes, None] = None, position: Optional[str] = None, scope: Optional[str] = 'sub', hidden: bool = False, superordinate: Optional[str] = None, opened: bool = False, properties: Optional[List[str]] = None) -> AsyncIterator[Union[Object, ShallowObject]]:
        if opened:
            async for obj in cast(AsyncIterator[Object], aiter(self._search_opened(filter, position, scope, hidden, superordinate, properties))):
                yield obj
        else:
            async for shallow_obj in cast(AsyncIterator[ShallowObject], aiter(self._search_closed(filter, position, scope, hidden, superordinate, properties))):
                yield shallow_obj

    async def _search_opened(self, filter: Union[Dict[str, str], str, bytes, None] = None, position: Optional[str] = None, scope: Optional[str] = 'sub', hidden: bool = False, superordinate: Optional[str] = None, properties: Optional[List[str]] = None) -> AsyncIterator[Object]:
        async for obj in self._search(filter, position, scope, hidden, superordinate, True, properties):
            yield Object.from_data(self.udm, obj)  # NOTE: this is missing last-modified, therefore no conditional request is done on modification!

    async def _search_closed(self, filter: Union[Dict[str, str], str, bytes, None] = None, position: Optional[str] = None, scope: Optional[str] = 'sub', hidden: bool = False, superordinate: Optional[str] = None, properties: Optional[List[str]] = None) -> AsyncIterator[ShallowObject]:
        async for obj in self._search(filter, position, scope, hidden, superordinate, False, properties):
            objself = self.client.get_relation(obj, 'self')
            uri = objself['href']
            dn = objself['name']
            yield ShallowObject(self.udm, dn, uri)

    async def _search(self, filter: Union[Dict[str, str], str, bytes, None] = None, position: Optional[str] = None, scope: Optional[str] = 'sub', hidden: bool = False, superordinate: Optional[str] = None, opened: bool = False, properties: Optional[List[str]] = None) -> AsyncIterator[Dict[str, Any]]:
        data: Dict[str, Union[str, List[str], Dict[str, Any], None]] = {
            'position': position,
            'scope': scope,
            'hidden': '1' if hidden else '0',
        }
        if isinstance(filter, dict):
            for prop, val in filter.items():
                data.setdefault('query', {})[f'query[{prop}]'] = val  # type: ignore
        elif isinstance(filter, str):
            data['filter'] = filter
        if superordinate:
            data['superordinate'] = superordinate
        if not opened:
            data['opened'] = '0'
            data['properties'] = ['dn']
        if properties:
            data['properties'] = properties
        await self.load_relations()
        entries = await self.client.resolve_relation(self.relations, 'search', template=data)
        async for entry in self.client.resolve_relations(entries, 'udm:object'):
            yield entry

    async def get_layout(self) -> Optional[Any]:
        await self.load_relations()
        relation = await self.udm.client.resolve_relation(self.relations, 'udm:layout')
        return relation.get('layout')

    async def get_properties(self) -> Optional[Any]:
        await self.load_relations()
        return (await self.udm.client.resolve_relation(self.relations, 'udm:properties')).get('properties')

    async def get_property_choices(self, property: str) -> Optional[Any]:
        await self.load_relations()
        relations = await self.udm.client.resolve_relation(self.relations, 'udm:properties')
        return (await self.udm.client.resolve_relation(relations, 'udm:property-choices', name=property)).get('choices')

    async def policy_result(self, policy_module: str, position: str, policy: Optional[str] = None) -> Dict[str, Any]:
        await self.load_relations()
        policy_result = await self.udm.client.resolve_relation(self.relations, 'udm:policy-result', name=policy_module, template={'position': position, 'policy': policy})
        policy_result.pop('_links', None)
        policy_result.pop('_embedded', None)
        return policy_result

    async def get_report_types(self) -> list[str]:
        await self.load_relations()
        return [x['name'] for x in self.udm.client.get_relations(self.relations, 'udm:report', template={'dn': ''}) if x.get('name')]

    async def create_report(self, report_type: str, object_dns: list[str]) -> Any:
        await self.load_relations()
        return await self.udm.client.resolve_relation(self.relations, 'udm:report', name=report_type, template={'dn': object_dns})


class ShallowObject(Client):

    __slots__ = ('dn', 'udm', 'uri')

    def __init__(self, udm: UDM, dn: Optional[str], uri: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(udm.client, *args, **kwargs)
        self.dn = dn
        self.udm = udm
        self.uri = uri

    async def open(self) -> Object:
        return Object.from_response(self.udm, await self.client.make_request('GET', self.uri))

    def __repr__(self) -> str:
        return f'ShallowObject(dn={self.dn!r})'


class Object(ObjectRepr, Client):

    __slots__ = tuple(['etag', 'hal', 'last_modified', 'representation'] + list(Client.__slots__))

    objects = References()

    def __init__(self, udm: UDM, representation: Dict[str, Any], etag: Optional[str] = None, last_modified: Optional[str] = None, *args: Any, **kwargs: Any) -> None:
        Client.__init__(self, udm.client, *args, **kwargs)
        ObjectRepr.__init__(self, representation, etag, last_modified)
        self.udm = udm

    def _copy_from_obj(self, obj: ObjectCopyProto) -> None:
        ObjectRepr._copy_from_obj(self, obj)
        self.udm = obj.udm

    @property
    def module(self) -> Awaitable[Optional[Module]]:
        # FIXME: use "type" relation link
        # object_type = self.udm.get_relation(self.hal, 'type')['href']
        return self.udm.get(self.object_type)

    @property
    def uri(self) -> Optional[str]:
        try:
            uri = self.client.get_relation(self.hal, 'self')
        except NoRelation:
            uri = None
        if uri:
            return uri['href']
        return self.representation.get('uri')

    @classmethod
    def from_response(cls, udm: UDM, response: AsyncResponse) -> Object:
        return cls.from_data(udm, response.data, response.response.headers)

    @classmethod
    def from_data(cls, udm: UDM, entry: Dict[str, Any], headers: Optional[Mapping[str, str]] = None) -> Object:
        headers = headers or {}
        return cls(udm, entry, etag=headers.get('Etag'), last_modified=headers.get('Last-Modified'))

    def __repr__(self) -> str:
        return f'Object(module={self.object_type!r}, dn={self.dn!r}, uri={self.uri!r})'

    async def reload(self) -> None:
        try:
            uri = self.client.get_relation(self.hal, 'self')
        except NoRelation:
            uri = None
        if uri:
            obj = await ShallowObject(self.udm, self.dn, uri['href']).open()
        else:
            module = await self.module
            assert module and self.dn
            obj = await module.get(self.dn)
        self._copy_from_obj(obj)

    async def save(self, reload: bool = True) -> AsyncResponse:
        if self.dn:
            return await self._modify(reload)
        else:
            return await self._create(reload)

    async def json_patch(self, patch: Dict[str, Any], reload: bool = True) -> AsyncResponse:
        if self.dn:
            return await self._patch(patch, reload=reload)
        else:
            uri = self.client.get_relation(self.hal, 'create')
            return await self._request('POST', uri['href'], patch, {'Content-Type': 'application/json-patch+json'})

    async def delete(self, remove_referring: bool = False) -> bytes:
        assert self.uri
        headers = {key: value for key, value in {
            'If-Unmodified-Since': self.last_modified,
            'If-Match': self.etag,
        }.items() if value}
        return await self.client.request('DELETE', self.uri, **headers)  # type: ignore # <https://github.com/python/mypy/issues/10008>

    async def move(self, position: str, reload: bool = True) -> None:
        self.position = position
        await self.save(reload=reload)

    async def _modify(self, reload: bool = True) -> AsyncResponse:
        assert self.uri
        headers = {key: value for key, value in {
            'If-Unmodified-Since': self.last_modified,
            'If-Match': self.etag,
        }.items() if value}
        return await self._request('PUT', self.uri, self.representation, headers, reload=reload)

    async def _patch(self, data: Dict[str, Any], reload: bool = True) -> AsyncResponse:
        assert self.uri
        headers = {key: value for key, value in {
            'If-Unmodified-Since': self.last_modified,
            'If-Match': self.etag,
            'Content-Type': 'application/json-patch+json',
        }.items() if value}
        return await self._request('PATCH', self.uri, data, headers, reload=reload)

    async def _create(self, reload: bool = True) -> AsyncResponse:
        uri = self.client.get_relation(self.hal, 'create')
        return await self._request('POST', uri['href'], self.representation, {}, reload=reload)

    async def _request(self, method: str, uri: str, data: Dict[str, Any], headers: Dict[str, Any], reload: bool = True) -> AsyncResponse:
        response = await self.client.make_request(method, uri, data=data, allow_redirects=False, custom_redirect_handling=True, **headers)
        await self._reload_from_response(response, reload)
        return response

    async def _reload_from_response(self, response: AsyncResponse, reload: bool) -> None:
        if reload and 200 <= response.response.status <= 299 and 'Location' in response.response.headers:
            uri = response.response.headers['Location']
            obj = ShallowObject(self.udm, None, uri)
            self._copy_from_obj(await obj.open())
            return

        if response.response.status == 200:
            # the response already contains a new representation
            self._copy_from_obj(Object.from_response(self.udm, response))
            return

        if reload:  # pragma: no cover
            await self.reload()

    async def generate_service_specific_password(self, service: str) -> Optional[Any]:
        uri = self.client.get_relation(self.hal, 'udm:service-specific-password')['href']
        response = await self.client.make_request('POST', uri, data={"service": service})
        return response.data.get('password', None)

    async def get_layout(self) -> Optional[Any]:
        return (await self.udm.client.resolve_relation(self.hal, 'udm:layout')).get('layout')

    async def get_properties(self) -> Optional[Any]:
        return (await self.udm.client.resolve_relation(self.hal, 'udm:properties')).get('properties')

    async def get_property_choices(self, property: str) -> Optional[Any]:
        hal = await self.udm.client.resolve_relation(self.hal, 'udm:properties')
        return (await self.udm.client.resolve_relation(hal, 'udm:property-choices', name=property)).get('choices')

    async def policy_result(self, policy_module: str, policy: Optional[str] = None) -> Dict[str, Any]:
        policy_result = await self.udm.client.resolve_relation(self.hal, 'udm:policy-result', name=policy_module, template={'policy': policy})
        policy_result.pop('_links', None)
        policy_result.pop('_embedded', None)
        return policy_result
