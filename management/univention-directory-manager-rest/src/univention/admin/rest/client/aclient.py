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

>>> from univention.admin.rest.client.aclient import UDM
>>> uri = 'http://localhost/univention/udm/'
>>> udm = UDM.http(uri, 'Administrator', 'univention')
>>> module = udm.get('users/user')
>>> print('Found {}'.format(module))
>>> obj = next(module.search())
>>> if obj:
>>>     obj = obj.open()
>>> print('Object {}'.format(obj))
"""

import asyncio
import copy
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Text, Type, Union  # noqa: F401

import aiohttp
import uritemplate


#import http.client
#http.client._MAXHEADERS = 1000  # type: ignore


class HTTPError(Exception):

    def __init__(self, code, message, response, error_details=None):
        # type: (int, str, Optional[aiohttp.ClientResponse], Optional[dict]) -> None
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

    def __init__(self, response, data, uri):
        # type: (aiohttp.ClientResponse, Any, str) -> None
        self.response = response
        self.data = data
        self.uri = uri


class Session:

    def __init__(self, credentials, language='en-US', reconnect=True, user_agent='univention.lib/1.0', enable_caching=False):
        # type: (UDM, str, bool, str, bool) -> None
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

    async def __aenter__(self):
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc, etype, etraceback):
        await self.session.__aexit__(exc, etype, etraceback)

    def create_session(self):
        # type: () -> aiohttp.ClientSession
        sess = aiohttp.ClientSession(auth=aiohttp.BasicAuth(self.credentials.username, self.credentials.password))
        if not self.enable_caching:
            return sess
        try:
            from cachecontrol import CacheControl
        except ImportError:
            pass
        else:
            sess = CacheControl(sess)
        return sess

    def get_method(self, method):
        # type: (str) -> Callable[..., aiohttp.ClientResponse]
        sess = self.session
        return {
            'GET': sess.get,
            'POST': sess.post,
            'PUT': sess.put,
            'DELETE': sess.delete,
            'PATCH': sess.patch,
            'OPTIONS': sess.options,
        }.get(method.upper(), sess.get)

    async def request(self, method, uri, data=None, expect_json=False, **headers):
        # type: (str, str, Dict, bool, **str) -> Any
        return (await self.make_request(method, uri, data, expect_json=expect_json, **headers)).data  # type: ignore # <https://github.com/python/mypy/issues/10008>

    async def make_request(self, method, uri, data=None, expect_json=False, allow_redirects=True, **headers):
        # type: (str, str, Dict, bool, bool, **str) -> Response
        if method in ('GET', 'HEAD'):
            params = data
            json = None
        else:
            params = None
            json = data

        async def doit():
            # type: () -> Response
            try:
                response = await self.get_method(method)(uri, params=params, json=json, headers=dict(self.default_headers, **headers), allow_redirects=allow_redirects)
            except aiohttp.ClientConnectionError as exc:
                raise ConnectionError(exc)
            data = await self.eval_response(response, expect_json=expect_json)
            return Response(response, data, uri)

        for _i in range(5):
            try:
                return await doit()
            except ServiceUnavailable as exc:  # TODO: same for ConnectionError? python-request does it itself.
                if not self.reconnect:
                    raise
                try:
                    assert exc.response is not None
                    retry_after = min(5, int(exc.response.headers.get('Retry-After', 1)))
                except ValueError:
                    retry_after = 1
                await asyncio.sleep(retry_after)

        return await doit()

    async def eval_response(self, response, expect_json=False):
        # type: (aiohttp.ClientResponse, bool) -> Any
        if response.status >= 399:
            msg = f'{response.request.method} {response.url}: {response.status}'
            error_details = None
            try:
                json = await response.json()
            except ValueError:
                pass
            else:
                if isinstance(json, dict):
                    error_details = json.get('error', {})
                    try:
                        error_details['error'] = list(await self.resolve_relations(json, 'udm:error'))
                    except _NoRelation:
                        pass
                    if error_details:
                        server_message = error_details.get('message')
                        # traceback = error_details.get('traceback')
                        if server_message:
                            msg += f'\n{server_message}'
            errors = {400: BadRequest, 404: NotFound, 403: Forbidden, 401: Unauthorized, 412: PreconditionFailed, 422: UnprocessableEntity, 500: ServerError, 503: ServiceUnavailable}
            cls = HTTPError
            cls = errors.get(response.status, cls)
            raise cls(response.status, msg, response, error_details=error_details)
        if response.headers.get('Content-Type') in ('application/json', 'application/hal+json'):
            return await response.json()
        elif expect_json:
            raise UnexpectedResponse(await response.text())
        return await response.text()

    def get_relations(self, entry, relation, name=None, template=None):
        # type: (Dict, str, Optional[str], Optional[Dict[str, Any]]) -> Iterator[Dict[str, str]]
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

    def get_relation(self, entry, relation, name=None, template=None):
        # type: (Dict, str, Optional[str], Optional[Dict[str, Any]]) -> Dict[str, str]
        try:
            return next(self.get_relations(entry, relation, name, template))
        except StopIteration:
            raise _NoRelation(relation)

    async def resolve_relations(self, entry, relation, name=None, template=None):
        # type: (Dict, str, Optional[str], Optional[Dict[str, Any]]) -> Iterator[Any]
        embedded = entry.get('_embedded', {})
        if isinstance(embedded, dict) and relation in embedded:
            #yield from embedded[relation]
            for x in embedded[relation]:
                yield x
            return

        for rel in self.get_relations(entry, relation, name, template):
            yield (await self.make_request('GET', rel['href'])).data

    async def resolve_relation(self, entry, relation, name=None, template=None):
        # type: (Dict, str, Optional[str], Optional[Dict[str, Any]]) -> Any
        try:
            return await anext(self.resolve_relations(entry, relation, name, template))
        except StopAsyncIteration:
            raise _NoRelation(relation)


class Client:

    def __init__(self, client):
        # type: (Session) -> None
        self.client = client


class UDM(Client):

    @classmethod
    def http(cls, uri, username, password):
        # type: (str, str, str) -> UDM
        return cls(uri, username, password)

    def __init__(self, uri, username, password, *args, **kwargs):
        # type: (str, str, str, *Any, **Any) -> None
        self.uri = uri
        self.username = username
        self.password = password
        self._api_version = None  # type: Optional[str]
        self.entry = None  # type: Any # Optional[Dict]
        super().__init__(Session(self, *args, **kwargs))

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc, etype, etraceback):
        await self.client.__aexit__(exc, etype, etraceback)

    async def load(self):
        # type: () -> None
        # FIXME: use HTTP caching instead of memory caching
        if self.entry is None:
            await self.reload()

    async def reload(self):
        # type: () -> None
        self.entry = await self.client.request('GET', self.uri, expect_json=True)

    async def get_ldap_base(self):
        # type: () -> Optional[str]
        await self.load()
        return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:ldap-base')).dn

    async def modules(self, name=None):
        # type: (Optional[str]) -> Iterator[Module]
        await self.load()
        async for module in self.client.resolve_relations(self.entry, 'udm:object-modules'):
            for module_info in self.client.get_relations(module, 'udm:object-types', name):
                yield Module(self, module_info['href'], module_info['name'], module_info['title'])

    def version(self, api_version):
        # type: (str) -> UDM
        self._api_version = api_version
        return self

    async def obj_by_dn(self, dn):
        # type: (str) -> Object
        self.load()
        return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:object/get-by-dn', template={'dn': dn}))

    async def obj_by_uuid(self, uuid):
        # type: (str) -> Object
        self.load()
        return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:object/get-by-uuid', template={'uuid': uuid}))

    async def get(self, name):
        # type: (str) -> Optional[Module]
        async for module in self.modules(name):
            return module

        return None

    async def get_object(self, object_type, dn):
        # type: (str, str) -> Optional[Object]
        mod = self.get(object_type)
        assert mod
        obj = await mod.get(dn)
        return obj

    def __repr__(self):
        # type: () -> str
        return f'UDM(uri={self.uri}, username={self.username}, password=****, version={self._api_version})'


class Module(Client):

    def __init__(self, udm, uri, name, title, *args, **kwargs):
        # type: (UDM, str, str, str, *Any, **Any) -> None
        super().__init__(udm.client, *args, **kwargs)
        self.udm = udm
        self.uri = uri
        self.username = udm.username
        self.password = udm.password
        self.name = name
        self.title = title
        self.relations = {}  # type: Dict

    async def load_relations(self):
        # type: () -> None
        if self.relations:
            return
        self.relations = await self.client.request('GET', self.uri)

    def __repr__(self):
        # type: () -> str
        return f'Module(uri={self.uri}, name={self.name})'

    async def new(self, position=None, superordinate=None, template=None):
        # type: (Optional[str], Optional[str], Optional[Dict[str, Any]]) -> Object
        self.load_relations()
        data = {'position': position, 'superordinate': superordinate, 'template': template}
        resp = self.client.resolve_relation(self.relations, 'create-form', template=data)
        return Object.from_data(self.udm, resp)

    async def get(self, dn):
        # type: (str) -> Optional[Object]
        # TODO: use a link relation instead of a search
        async for obj in self._search_closed(position=dn, scope='base'):
            return await obj.open()
        raise NotFound(404, 'Wrong object type!?', None)  # FIXME: object exists but is of different module. should be fixed on the server.

    async def get_by_entry_uuid(self, uuid):
        # type: (str) -> Optional[Object]
        # TODO: use a link relation instead of a search
        # return self.udm.get_by_uuid(uuid)
        async for obj in self._search_closed(filter={'entryUUID': uuid}, scope='base'):
            return await obj.open()
        raise NotFound(404, 'Wrong object type!?', None)  # FIXME: object exists but is of different module. should be fixed on the server.

    async def get_by_id(self, dn):
        # type: (str) -> Optional[Object]
        # TODO: Needed?
        raise NotImplementedError()

    async def search(self, filter=None, position=None, scope='sub', hidden=False, superordinate=None, opened=False):
        # type: (Union[Dict[str, str], Text, bytes, None], Optional[str], Optional[str], bool, Optional[str], bool) -> Iterator[Any]
        if opened:
            async for entry in aiter(self._search_opened(filter, position, scope, hidden, superordinate)):
                yield entry
        else:
            async for entry in aiter(self._search_closed(filter, position, scope, hidden, superordinate)):
                yield entry

    async def _search_opened(self, filter=None, position=None, scope='sub', hidden=False, superordinate=None):
        # type: (Union[Dict[str, str], Text, bytes, None], Optional[str], Optional[str], bool, Optional[str]) -> Iterator[Object]
        async for obj in self._search(filter, position, scope, hidden, superordinate, True):
            yield Object.from_data(self.udm, obj)  # NOTE: this is missing last-modified, therefore no conditional request is done on modification!

    async def _search_closed(self, filter=None, position=None, scope='sub', hidden=False, superordinate=None):
        # type: (Union[Dict[str, str], Text, bytes, None], Optional[str], Optional[str], bool, Optional[str]) -> Iterator[ShallowObject]
        async for obj in self._search(filter, position, scope, hidden, superordinate, False):
            objself = self.client.get_relation(obj, 'self')
            uri = objself['href']
            dn = objself['name']
            yield ShallowObject(self.udm, dn, uri)

    async def _search(self, filter=None, position=None, scope='sub', hidden=False, superordinate=None, opened=False):
        # type: (Union[Dict[str, str], Text, bytes, None], Optional[str], Optional[str], bool, Optional[str], bool) -> Iterator[Any]
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
        await self.load_relations()
        entries = await self.client.resolve_relation(self.relations, 'search', template=data)
        async for entry in self.client.resolve_relations(entries, 'udm:object'):
            yield entry

    async def get_layout(self):
        # type: () -> Optional[Any]
        await self.load_relations()
        return await self.udm.client.resolve_relation(self.relations, 'udm:layout').get('layout')

    async def get_properties(self):
        # type: () -> Optional[Any]
        await self.load_relations()
        return await self.udm.client.resolve_relation(self.relations, 'udm:properties').get('properties')

    async def get_property_choices(self, property):
        # type: (str) -> Optional[Any]
        await self.load_relations()
        relations = await self.udm.client.resolve_relation(self.relations, 'udm:properties')
        return await self.udm.client.resolve_relation(relations, 'udm:property-choices', name=property).get('choices')

    async def policy_result(self, policy_module, position, policy=None):
        # type: (str, str, Optional[str]) -> Dict
        await self.load_relations()
        policy_result = await self.udm.client.resolve_relation(self.relations, 'udm:policy-result', name=policy_module, template={'position': position, 'policy': policy})
        policy_result.pop('_links', None)
        policy_result.pop('_embedded', None)
        return policy_result

    async def get_report_types(self):
        # type: () -> List[str]
        await self.load_relations()
        return [x['name'] for x in self.udm.client.get_relations(self.relations, 'udm:report', template={'dn': ''}) if x.get('name')]

    async def create_report(self, report_type, object_dns):
        # type: (str, List[str]) -> Any
        await self.load_relations()
        return await self.udm.client.resolve_relation(self.relations, 'udm:report', name=report_type, template={'dn': object_dns})


class ShallowObject(Client):

    def __init__(self, udm, dn, uri, *args, **kwargs):
        # type: (UDM, Optional[str], str, *Any, **Any) -> None
        super().__init__(udm.client, *args, **kwargs)
        self.dn = dn
        self.udm = udm
        self.uri = uri

    async def open(self):
        # type: () -> Object
        return Object.from_response(self.udm, await self.client.make_request('GET', self.uri))

    def __repr__(self):
        # type: () -> str
        return f'ShallowObject(dn={self.dn})'


class References:

    def __init__(self, obj=None):
        # type: (Optional[Object]) -> None
        self.obj = obj
        self.udm = self.obj.udm if self.obj is not None else None

    def __getitem__(self, item):
        # type: (str) -> List[ShallowObject]
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

    def __get__(self, obj, cls=None):
        # type: (Any, Type) -> References
        return type(self)(obj)


class Object(Client):

    objects = References()

    @property
    def module(self):
        # FIXME: use "type" relation link
        # object_type = self.udm.get_relation(self.hal, 'type')['href']
        return self.udm.get(self.object_type)

    @property
    def object_type(self):
        # type: () -> str
        return self.representation['objectType']

    @property
    def dn(self):
        # type: () -> Optional[str]
        return self.representation.get('dn')

    @property
    def properties(self):
        return self.representation['properties']

    @property
    def options(self):
        # type: () -> Dict
        return self.representation.get('options', {})

    @property
    def policies(self):
        # type: () -> Dict
        return self.representation.get('policies', {})

    @property
    def superordinate(self):
        # type: () -> Optional[str]
        return self.representation.get('superordinate')

    @superordinate.setter
    def superordinate(self, superordinate):
        # type. (str) -> None
        self.representation['superordinate'] = superordinate

    @property
    def position(self):
        # type: () -> Optional[str]
        return self.representation.get('position')

    @position.setter
    def position(self, position):
        # type. (str) -> None
        self.representation['position'] = position

    @property
    def uri(self):
        # type: () -> Optional[str]
        try:
            uri = self.client.get_relation(self.hal, 'self')
        except _NoRelation:
            uri = None
        if uri:
            return uri['href']
        return self.representation.get('uri')

    @classmethod
    def from_response(cls, udm, response):
        # type: (UDM, Response) -> Object
        return cls.from_data(udm, response.data, response.response.headers)

    @classmethod
    def from_data(cls, udm, entry, headers=None):
        # type: (UDM, Dict, Optional[Mapping[str, str]]) -> Object
        headers = headers or {}
        return cls(udm, entry, etag=headers.get('Etag'), last_modified=headers.get('Last-Modified'))

    def __init__(self, udm, representation, etag=None, last_modified=None, *args, **kwargs):
        # type: (UDM, Dict, Optional[str], Optional[str], *Any, **Any) -> None
        super().__init__(udm.client, *args, **kwargs)
        self.udm = udm
        self.representation = representation
        self.hal = {
            '_links': representation.pop('_links', {}),
            '_embedded': representation.pop('_embedded', {}),
        }
        self.etag = etag
        self.last_modified = last_modified

    def __repr__(self):
        # type: () -> str
        return f'Object(module={self.object_type}, dn={self.dn}, uri={self.uri})'

    async def reload(self):
        # type: () -> None
        uri = self.client.get_relation(self.hal, 'self')
        if uri:
            obj = await ShallowObject(self.udm, self.dn, uri['href']).open()
        else:
            obj = await self.module.get(self.dn)
        self._copy_from_obj(obj)

    async def save(self, reload=True):
        # type: (bool) -> Response
        if self.dn:
            return await self._modify(reload)
        else:
            return await self._create(reload)

    async def delete(self, remove_referring=False):
        # type: (bool) -> bytes
        assert self.uri
        return await self.client.request('DELETE', self.uri)

    async def move(self, position):
        # type: (str) -> None
        self.position = position
        self.save()

    async def _modify(self, reload=True):
        # type: (bool) -> Response
        assert self.uri
        headers = {key: value for key, value in {
            'If-Unmodified-Since': self.last_modified,
            'If-Match': self.etag,
        }.items() if value}

        response = await self.client.make_request('PUT', self.uri, data=self.representation, allow_redirects=False, **headers)  # type: ignore # <https://github.com/python/mypy/issues/10008>
        response = await self._follow_redirection(response, reload)  # move() causes multiple redirections!
        return response

    async def _create(self, reload=True):
        # type: (bool) -> Response
        uri = self.client.get_relation(self.hal, 'create')
        response = await self.client.make_request('POST', uri['href'], data=self.representation, allow_redirects=False)
        response = await self._follow_redirection(response, reload)
        return response

    async def _reload_from_response(self, response, reload):
        # type: (Response, bool) -> None
        if 200 <= response.response.status <= 299 and 'Location' in response.response.headers:
            uri = response.response.headers['Location']
            obj = ShallowObject(self.udm, None, uri)
            if reload:
                self._copy_from_obj(await obj.open())
        elif reload:
            self.reload()

    async def _follow_redirection(self, response, reload=True):
        # type: (Response, bool) -> Response
        location = None
        # python-requests doesn't follow redirects for 202
        if response.response.status in (201, 202) and 'Location' in response.response.headers:
            location = response.response.headers['Location']
            response = await self.client.make_request('GET', location, allow_redirects=False)

        # prevent allow_redirects because it does not wait Retry-After time causing a break up after 30 fast redirections
        while 300 <= response.response.status <= 399 and 'Location' in response.response.headers:
            location = response.response.headers['Location']
            if response.response.headers.get('Retry-After', '').isdigit():
                await asyncio.sleep(min(30, max(0, int(response.response.headers['Retry-After']))))
            response = await self.client.make_request('GET', location, allow_redirects=False)

        if location and response.response.status == 200:
            # the response already contains a new representation
            self._copy_from_obj(Object.from_response(self.udm, response))
        elif reload:
            await self._reload_from_response(response, reload)
        return response

    def _copy_from_obj(self, obj):
        # type: (Object) -> None
        self.udm = obj.udm
        self.representation = copy.deepcopy(obj.representation)
        self.hal = copy.deepcopy(obj.hal)
        self.etag = obj.etag
        self.last_modified = obj.last_modified

    async def generate_service_specific_password(self, service):
        # type: (str) -> Optional[Any]
        uri = self.client.get_relation(self.hal, 'udm:service-specific-password')['href']
        response = await self.client.make_request('POST', uri, data={"service": service})
        return response.data.get('password', None)

    async def get_layout(self):
        # type: () -> Optional[Any]
        return await self.udm.client.resolve_relation(self.hal, 'udm:layout').get('layout')

    async def get_properties(self):
        # type: () -> Optional[Any]
        return await self.udm.client.resolve_relation(self.hal, 'udm:properties').get('properties')

    async def get_property_choices(self, property):
        # type: (str) -> Optional[Any]
        hal = await self.udm.client.resolve_relation(self.hal, 'udm:properties')
        return await self.udm.client.resolve_relation(hal, 'udm:property-choices', name=property).get('choices')

    async def policy_result(self, policy_module, policy=None):
        # type: (str, Optional[str]) -> Dict
        policy_result = await self.udm.client.resolve_relation(self.hal, 'udm:policy-result', name=policy_module, template={'policy': policy})
        policy_result.pop('_links', None)
        policy_result.pop('_embedded', None)
        return policy_result
