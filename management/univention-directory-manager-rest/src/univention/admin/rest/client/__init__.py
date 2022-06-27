#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Copyright 2019-2022 Univention GmbH
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
>>> 	obj = obj.open()
>>> print('Object {}'.format(obj))
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import time
import copy
import requests
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Text, Type, Union  # noqa: F401

import six
import uritemplate

if sys.version_info.major > 2:
	import http.client
	http.client._MAXHEADERS = 1000  # type: ignore
else:
	import httplib
	httplib._MAXHEADERS = 1000


class HTTPError(Exception):

	def __init__(self, code, message, response):
		# type: (int, str, Optional[requests.Response]) -> None
		self.code = code
		self.response = response
		super(HTTPError, self).__init__(message)


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


class Response(object):

	def __init__(self, response, data, uri):
		# type: (requests.Response, Any, str) -> None
		self.response = response
		self.data = data
		self.uri = uri


class Session(object):

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

	def create_session(self):
		# type: () -> requests.Session
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

	def get_method(self, method):
		# type: (str) -> Callable[..., requests.Response]
		sess = self.session
		return {
			'GET': sess.get,
			'POST': sess.post,
			'PUT': sess.put,
			'DELETE': sess.delete,
			'PATCH': sess.patch,
			'OPTIONS': sess.options,
		}.get(method.upper(), sess.get)

	def request(self, method, uri, data=None, expect_json=False, **headers):
		# type: (str, str, Dict, bool, **str) -> Any
		return self.make_request(method, uri, data, expect_json=expect_json, **headers).data  # type: ignore # <https://github.com/python/mypy/issues/10008>

	def make_request(self, method, uri, data=None, expect_json=False, allow_redirects=True, **headers):
		# type: (str, str, Dict, bool, bool, **str) -> Response
		if method in ('GET', 'HEAD'):
			params = data
			json = None
		else:
			params = None
			json = data

		def doit():
			# type: () -> Response
			try:
				response = self.get_method(method)(uri, params=params, json=json, headers=dict(self.default_headers, **headers), allow_redirects=allow_redirects)
			except requests.exceptions.ConnectionError as exc:
				raise ConnectionError(exc)
			data = self.eval_response(response, expect_json=expect_json)
			return Response(response, data, uri)

		for i in range(5):
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

	def eval_response(self, response, expect_json=False):
		# type: (requests.Response, bool) -> Any
		if response.status_code >= 399:
			msg = '{} {}: {}'.format(response.request.method, response.url, response.status_code)
			try:
				json = response.json()
			except ValueError:
				pass
			else:
				if isinstance(json, dict):
					if 'error' in json:
						server_message = json['error'].get('message')
						# traceback = json['error'].get('traceback')
						if server_message:
							msg += '\n{}'.format(server_message)
			errors = {400: BadRequest, 404: NotFound, 403: Forbidden, 401: Unauthorized, 412: PreconditionFailed, 422: UnprocessableEntity, 500: ServerError, 503: ServiceUnavailable}
			cls = HTTPError
			cls = errors.get(response.status_code, cls)
			raise cls(response.status_code, msg, response)
		if response.headers.get('Content-Type') in ('application/json', 'application/hal+json'):
			return response.json()
		elif expect_json:
			raise UnexpectedResponse(response.text)
		return response.text

	def get_relations(self, entry, relation, name=None, template=None):
		# type: (Dict, str, Optional[str], Optional[Dict[str, Any]]) -> Iterator[Dict[str, str]]
		links = entry.get('_links', {})
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

	def resolve_relations(self, entry, relation, name=None, template=None):
		# type: (Dict, str, Optional[str], Optional[Dict[str, Any]]) -> Iterator[Any]
		embedded = entry.get('_embedded', {})
		if isinstance(embedded, dict) and relation in embedded:
			for x in embedded[relation]:
				yield x
			return

		for rel in self.get_relations(entry, relation, name, template):
			yield self.make_request('GET', rel['href']).data

	def resolve_relation(self, entry, relation, name=None, template=None):
		# type: (Dict, str, Optional[str], Optional[Dict[str, Any]]) -> Any
		return next(self.resolve_relations(entry, relation, name, template))


class Client(object):

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
		super(UDM, self).__init__(Session(self, *args, **kwargs))

	def load(self):
		# type: () -> None
		# FIXME: use HTTP caching instead of memory caching
		if self.entry is None:
			self.reload()

	def reload(self):
		# type: () -> None
		self.entry = self.client.request('GET', self.uri, expect_json=True)

	def get_ldap_base(self):
		# type: () -> Optional[str]
		self.load()
		return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:ldap-base')).dn

	def modules(self, name=None):
		# type: (Optional[str]) -> Iterator[Module]
		self.load()
		for module in self.client.resolve_relations(self.entry, 'udm:object-modules'):
			for module_info in self.client.get_relations(module, 'udm:object-types', name):
				yield Module(self, module_info['href'], module_info['name'], module_info['title'])

	def version(self, api_version):
		# type: (str) -> UDM
		self._api_version = api_version
		return self

	def obj_by_dn(self, dn):
		# type: (str) -> Object
		self.load()
		return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:object/get-by-dn', template={'dn': dn}))

	def obj_by_uuid(self, uuid):
		# type: (str) -> Object
		self.load()
		return Object.from_data(self, self.client.resolve_relation(self.entry, 'udm:object/get-by-uuid', template={'uuid': uuid}))

	def get(self, name):
		# type: (str) -> Optional[Module]
		for module in self.modules(name):
			return module

		return None

	def get_object(self, object_type, dn):
		# type: (str, str) -> Optional[Object]
		mod = self.get(object_type)
		assert mod
		obj = mod.get(dn)
		return obj

	def __repr__(self):
		# type: () -> str
		return 'UDM(uri={}, username={}, password=****, version={})'.format(self.uri, self.username, self._api_version)


class Module(Client):

	def __init__(self, udm, uri, name, title, *args, **kwargs):
		# type: (UDM, str, str, str, *Any, **Any) -> None
		super(Module, self).__init__(udm.client, *args, **kwargs)
		self.udm = udm
		self.uri = uri
		self.username = udm.username
		self.password = udm.password
		self.name = name
		self.title = title
		self.relations = {}  # type: Dict

	def load_relations(self):
		# type: () -> None
		if self.relations:
			return
		self.relations = self.client.request('GET', self.uri)

	def __repr__(self):
		# type: () -> str
		return 'Module(uri={}, name={})'.format(self.uri, self.name)

	def new(self, position=None, superordinate=None, template=None):
		# type: (Optional[str], Optional[str], Optional[Dict[str, Any]]) -> Object
		self.load_relations()
		data = {'position': position, 'superordinate': superordinate, 'template': template}
		resp = self.client.resolve_relation(self.relations, 'create-form', template=data)
		return Object.from_data(self.udm, resp)

	def get(self, dn):
		# type: (str) -> Optional[Object]
		# TODO: use a link relation instead of a search
		for obj in self._search_closed(position=dn, scope='base'):
			return obj.open()
		raise NotFound(404, 'Wrong object type!?', None)  # FIXME: object exists but is of different module. should be fixed on the server.

	def get_by_entry_uuid(self, uuid):
		# type: (str) -> Optional[Object]
		# TODO: use a link relation instead of a search
		# return self.udm.get_by_uuid(uuid)
		for obj in self._search_closed(filter={'entryUUID': uuid}, scope='base'):
			return obj.open()
		raise NotFound(404, 'Wrong object type!?', None)  # FIXME: object exists but is of different module. should be fixed on the server.

	def get_by_id(self, dn):
		# type: (str) -> Optional[Object]
		# TODO: Needed?
		raise NotImplementedError()

	def search(self, filter=None, position=None, scope='sub', hidden=False, superordinate=None, opened=False):
		# type: (Union[Dict[str, str], Text, bytes, None], Optional[str], Optional[str], bool, Optional[str], bool) -> Iterator[Any]
		if opened:
			return self._search_opened(filter, position, scope, hidden, superordinate)
		else:
			return self._search_closed(filter, position, scope, hidden, superordinate)

	def _search_opened(self, filter=None, position=None, scope='sub', hidden=False, superordinate=None):
		# type: (Union[Dict[str, str], Text, bytes, None], Optional[str], Optional[str], bool, Optional[str]) -> Iterator[Object]
		for obj in self._search(filter, position, scope, hidden, superordinate, True):
			yield Object.from_data(self.udm, obj)  # NOTE: this is missing last-modified, therefore no conditional request is done on modification!

	def _search_closed(self, filter=None, position=None, scope='sub', hidden=False, superordinate=None):
		# type: (Union[Dict[str, str], Text, bytes, None], Optional[str], Optional[str], bool, Optional[str]) -> Iterator[ShallowObject]
		for obj in self._search(filter, position, scope, hidden, superordinate, False):
			objself = self.client.get_relation(obj, 'self')
			uri = objself['href']
			dn = objself['name']
			yield ShallowObject(self.udm, dn, uri)

	def _search(self, filter=None, position=None, scope='sub', hidden=False, superordinate=None, opened=False):
		# type: (Union[Dict[str, str], Text, bytes, None], Optional[str], Optional[str], bool, Optional[str], bool) -> Iterator[Any]
		data = {
			'position': position,
			'scope': scope,
			'hidden': '1' if hidden else '0',
		}
		if isinstance(filter, dict):
			for prop, val in filter.items():
				data['query[%s]' % (prop,)] = val
		elif isinstance(filter, six.string_types):
			data['filter'] = filter
		if superordinate:
			data['superordinate'] = superordinate
		if not opened:
			data['properties'] = 'dn'
		self.load_relations()
		entries = self.client.resolve_relation(self.relations, 'search', template=data)
		for obj in self.client.resolve_relations(entries, 'udm:object'):
			yield obj

	def get_layout(self):
		# type: () -> Optional[Any]
		self.load_relations()
		return self.udm.client.resolve_relation(self.relations, 'udm:layout').get('layout')

	def get_properties(self):
		# type: () -> Optional[Any]
		self.load_relations()
		return self.udm.client.resolve_relation(self.relations, 'udm:properties').get('properties')

	def get_property_choices(self, property):
		# type: (str) -> Optional[Any]
		self.load_relations()
		relations = self.udm.client.resolve_relation(self.relations, 'udm:properties')
		return self.udm.client.resolve_relation(relations, 'udm:property-choices', name=property).get('choices')

	def policy_result(self, policy_module, position, policy=None):
		# type: (str, str, Optional[str]) -> Dict
		self.load_relations()
		policy_result = self.udm.client.resolve_relation(self.relations, 'udm:policy-result', name=policy_module, template={'position': position, 'policy': policy})
		policy_result.pop('_links', None)
		policy_result.pop('_embedded', None)
		return policy_result

	def get_report_types(self):
		# type: () -> List[str]
		self.load_relations()
		return [x['name'] for x in self.udm.client.get_relations(self.relations, 'udm:report', template={'dn': ''}) if x.get('name')]

	def create_report(self, report_type, object_dns):
		# type: (str, List[str]) -> Any
		self.load_relations()
		return self.udm.client.resolve_relation(self.relations, 'udm:report', name=report_type, template={'dn': object_dns})


class ShallowObject(Client):

	def __init__(self, udm, dn, uri, *args, **kwargs):
		# type: (UDM, Optional[str], str, *Any, **Any) -> None
		super(ShallowObject, self).__init__(udm.client, *args, **kwargs)
		self.dn = dn
		self.udm = udm
		self.uri = uri

	def open(self):
		# type: () -> Object
		return Object.from_response(self.udm, self.client.make_request('GET', self.uri))

	def __repr__(self):
		# type: () -> str
		return 'ShallowObject(dn={})'.format(self.dn)


class References(object):

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
			for x in self.udm.client.get_relations(self.obj.hal, 'udm:object/property/reference/%s' % (item,))
		]

	def __getattribute__(self, key):
		try:
			return super(References, self).__getattribute__(key)
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
		super(Object, self).__init__(udm.client, *args, **kwargs)
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
		return 'Object(module={}, dn={}, uri={})'.format(self.object_type, self.dn, self.uri)

	def reload(self):
		# type: () -> None
		uri = self.client.get_relation(self.hal, 'self')
		if uri:
			obj = ShallowObject(self.udm, self.dn, uri['href']).open()
		else:
			obj = self.module.get(self.dn)
		self._copy_from_obj(obj)

	def save(self, reload=True):
		# type: (bool) -> Response
		if self.dn:
			return self._modify(reload)
		else:
			return self._create(reload)

	def delete(self, remove_referring=False):
		# type: (bool) -> bytes
		assert self.uri
		return self.client.request('DELETE', self.uri)

	def move(self, position):
		# type: (str) -> None
		self.position = position
		self.save()

	def _modify(self, reload=True):
		# type: (bool) -> Response
		assert self.uri
		headers = {key: value for key, value in {
			'If-Unmodified-Since': self.last_modified,
			'If-Match': self.etag,
		}.items() if value}

		response = self.client.make_request('PUT', self.uri, data=self.representation, allow_redirects=False, **headers)  # type: ignore # <https://github.com/python/mypy/issues/10008>
		response = self._follow_redirection(response, reload)  # move() causes multiple redirections!
		return response

	def _create(self, reload=True):
		# type: (bool) -> Response
		uri = self.client.get_relation(self.hal, 'create')
		response = self.client.make_request('POST', uri['href'], data=self.representation, allow_redirects=False)
		response = self._follow_redirection(response, reload)
		return response

	def _reload_from_response(self, response, reload):
		# type: (Response, bool) -> None
		if 200 <= response.response.status_code <= 299 and 'Location' in response.response.headers:
			uri = response.response.headers['Location']
			obj = ShallowObject(self.udm, None, uri)
			if reload:
				self._copy_from_obj(obj.open())
		elif reload:
			self.reload()

	def _follow_redirection(self, response, reload=True):
		# type: (Response, bool) -> Response
		location = None
		# python-requests doesn't follow redirects for 201
		if response.response.status_code == 201 and 'Location' in response.response.headers:
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

	def _copy_from_obj(self, obj):
		# type: (Object) -> None
		self.udm = obj.udm
		self.representation = copy.deepcopy(obj.representation)
		self.hal = copy.deepcopy(obj.hal)
		self.etag = obj.etag
		self.last_modified = obj.last_modified

	def generate_service_specific_password(self, service):
		# type: (str) -> Optional[Any]
		uri = self.client.get_relation(self.hal, 'udm:service-specific-password')['href']
		response = self.client.make_request('POST', uri, data={"service": service})
		return response.data.get('password', None)

	def get_layout(self):
		# type: () -> Optional[Any]
		return self.udm.client.resolve_relation(self.hal, 'udm:layout').get('layout')

	def get_properties(self):
		# type: () -> Optional[Any]
		return self.udm.client.resolve_relation(self.hal, 'udm:properties').get('properties')

	def get_property_choices(self, property):
		# type: (str) -> Optional[Any]
		hal = self.udm.client.resolve_relation(self.hal, 'udm:properties')
		return self.udm.client.resolve_relation(hal, 'udm:property-choices', name=property).get('choices')

	def policy_result(self, policy_module, policy=None):
		# type: (str, Optional[str]) -> Dict
		policy_result = self.udm.client.resolve_relation(self.hal, 'udm:policy-result', name=policy_module, template={'policy': policy})
		policy_result.pop('_links', None)
		policy_result.pop('_embedded', None)
		return policy_result
