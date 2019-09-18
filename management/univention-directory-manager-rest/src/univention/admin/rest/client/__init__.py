#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Copyright 2019 Univention GmbH
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

import six
import uritemplate

if sys.version_info.major > 2:
	import http.client
	http.client._MAXHEADERS = 1000
else:
	import httplib
	httplib._MAXHEADERS = 1000


class HTTPError(Exception):

	def __init__(self, code, message, response):
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


class Response(object):

	def __init__(self, response, data, uri):
		self.response = response
		self.data = data
		self.uri = uri


class Session(object):

	def __init__(self, credentials, language='en-US', reconnect=True, user_agent='univention.lib/1.0', enable_caching=False):
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
		sess = self.session
		return {
			'GET': sess.get,
			'POST': sess.post,
			'PUT': sess.put,
			'DELETE': sess.delete,
			'PATCH': sess.patch,
			'OPTIONS': sess.options,
		}.get(method.upper(), sess.get)

	def request(self, method, uri, data=None, **headers):
		return self.make_request(method, uri, data, **headers).data

	def make_request(self, method, uri, data=None, **headers):
		if method in ('GET', 'HEAD'):
			params = data
			json = None
		else:
			params = None
			json = data

		def doit():
			try:
				response = self.get_method(method)(uri, params=params, json=json, headers=dict(self.default_headers, **headers))
			except requests.exceptions.ConnectionError as exc:
				raise ConnectionError(exc)
			data = self.eval_response(response)
			return Response(response, data, uri)
		for i in range(5):
			try:
				return doit()
			except ServiceUnavailable as exc:   # TODO: same for ConnectionError? python-request does it itself.
				if not self.reconnect:
					raise
				try:
					retry_after = min(5, int(exc.response.headers.get('Retry-After', 1)))
				except ValueError:
					retry_after = 1
				time.sleep(retry_after)
				return doit()

	def eval_response(self, response):
		if response.status_code >= 299:
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
		return response.text

	def get_relations(self, entry, relation, name=None, template=None):
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
		return next(self.get_relations(entry, relation, name, template))

	def resolve_relations(self, entry, relation, name=None, template=None):
		embedded = entry.get('_embedded', {})
		if isinstance(embedded, dict) and relation in embedded:
			for x in embedded[relation]:
				yield x
			return

		for relation in self.get_relations(entry, relation, name, template):
			yield self.make_request('GET', relation['href']).data

	def resolve_relation(self, entry, relation, name=None, template=None):
		return next(self.resolve_relations(entry, relation, name, template))


class Client(object):

	def __init__(self, client):
		self.client = client


class UDM(Client):

	@classmethod
	def http(cls, uri, username, password):
		return cls(uri, username, password)

	def __init__(self, uri, username, password, *args, **kwargs):
		self.uri = uri
		self.username = username
		self.password = password
		self._api_version = None
		self.entry = None
		super(UDM, self).__init__(Session(self, *args, **kwargs))

	def load(self):
		# FIXME: use HTTP caching instead of memory caching
		if self.entry is None:
			self.reload()

	def reload(self):
		self.entry = self.client.request('GET', self.uri)

	def modules(self, name=None):
		self.load()
		for module in self.client.resolve_relations(self.entry, 'udm:object-modules'):
			for module_info in self.client.get_relations(module, 'udm:object-types', name):
				yield Module(self, module_info['href'], module_info['name'], module_info['title'])

	def version(self, api_version):
		self._api_version = api_version
		return self

	def obj_by_dn(self, dn):
		self.load()
		return Object.from_response(self.udm, self.client.resolve_relation(self.entry, 'udm:object/get-by-dn', template={'dn': dn}))

	def obj_by_uuid(self, uuid):
		self.load()
		return Object.from_response(self.udm, self.client.resolve_relation(self.entry, 'udm:object/get-by-uuid', template={'uuid': uuid}))

	def get(self, name):
		for module in self.modules(name):
			return module

	def __repr__(self):
		return 'UDM(uri={}, username={}, password=****, version={})'.format(self.uri, self.username, self._api_version)


class Module(Client):

	def __init__(self, udm, uri, name, title, *args, **kwargs):
		super(Module, self).__init__(udm.client, *args, **kwargs)
		self.udm = udm
		self.uri = uri
		self.username = udm.username
		self.password = udm.password
		self.name = name
		self.title = title
		self.relations = {}

	def load_relations(self):
		if self.relations:
			return
		self.relations = self.client.request('GET', self.uri)

	def __repr__(self):
		return 'Module(uri={}, name={})'.format(self.uri, self.name)

	def new(self, position=None, superordinate=None, template=None):
		self.load_relations()
		data = {'position': position, 'superordinate': superordinate, 'template': template}
		resp = self.client.resolve_relation(self.relations, 'create-form', template=data)
		return Object.from_data(self.udm, resp)

	def get(self, dn):
		# TODO: use a link relation instead of a search
		for obj in self.search(position=dn, scope='base'):
			return obj.open()

	def get_by_entry_uuid(self, uuid):
		# TODO: use a link relation instead of a search
		#return self.udm.get_by_uuid(uuid)
		for obj in self.search(filter={'entryUUID': uuid}, scope='base'):
			return obj.open()

	def get_by_id(self, dn):
		# TODO: Needed?
		raise NotImplementedError()

	def search(self, filter=None, position=None, scope='sub', hidden=False, superordinate=None, opened=False):
		data = {}
		if isinstance(filter, dict):
			for prop, val in filter.items():
				data['query[%s]' % (prop,)] = val
		elif isinstance(filter, six.string_types):
			data['filter'] = filter
		if superordinate:
			data['superordinate'] = superordinate
		data['position'] = position
		data['scope'] = scope
		data['hidden'] = '1' if hidden else '0'
		if not opened:
			data['properties'] = 'dn'
		self.load_relations()
		entries = self.client.resolve_relation(self.relations, 'search', template=data)
		for obj in self.client.resolve_relations(entries, 'udm:object'):
			if opened:
				yield Object.from_data(self.udm, obj)  # NOTE: this is missing last-modified, therefore no conditional request is done on modification!
			else:
				objself = self.client.get_relation(obj, 'self')
				uri = objself['href']
				dn = objself['name']
				yield ShallowObject(self.udm, dn, uri)


class ShallowObject(Client):

	def __init__(self, udm, dn, uri, *args, **kwargs):
		super(ShallowObject, self).__init__(udm.client, *args, **kwargs)
		self.dn = dn
		self.udm = udm
		self.uri = uri

	def open(self):
		return Object.from_response(self.udm, self.client.make_request('GET', self.uri))

	def __repr__(self):
		return 'ShallowObject(dn={})'.format(self.dn)


class References(object):

	def __init__(self, obj=None):
		self.obj = obj
		self.udm = self.obj.udm if self.obj is not None else None

	def __getitem__(self, item):
		return [
			ShallowObject(self.obj.udm, x['name'], x['href'])
			for x in self.udm.get_relations(self.obj.hal, 'udm:object/property/reference/%s' % (item,))
		]

	def __getattribute__(self, key):
		try:
			return super(References, self).__getattribute__(key)
		except AttributeError:
			return self[key]

	def __get__(self, obj, cls=None):
		return type(self)(obj)


class Object(Client):

	objects = References()

	@property
	def module(self):
		# FIXME: use "type" relation link
		#object_type = self.udm.get_relation(self.hal, 'type')['href']
		return self.udm.get(self.object_type)

	@property
	def object_type(self):
		return self.representation['objectType']

	@property
	def dn(self):
		return self.representation.get('dn')

	@property
	def properties(self):
		return self.representation['properties']

	@property
	def options(self):
		return self.representation.get('options', {})

	@property
	def policies(self):
		return self.representation.get('policies', {})

	@property
	def superordinate(self):
		return self.representation.get('superordinate')

	@superordinate.setter
	def superordinate(self, superordinate):
		self.representation['superordinate'] = superordinate

	@property
	def position(self):
		return self.representation.get('position')

	@position.setter
	def position(self, position):
		self.representation['position'] = position

	@property
	def uri(self):
		uri = self.client.get_relation(self.hal, 'self')
		if uri:
			return uri['href']
		return self.representation.get('uri')

	@classmethod
	def from_response(cls, udm, response):
		return cls.from_data(udm, response.data, response.response.headers)

	@classmethod
	def from_data(cls, udm, entry, headers=None):
		headers = headers or {}
		return cls(udm, entry, etag=headers.get('Etag'), last_modified=headers.get('Last-Modified'))

	def __init__(self, udm, representation, etag=None, last_modified=None, *args, **kwargs):
		super(Object, self).__init__(udm.client, *args, **kwargs)
		self.udm = udm
		self.representation = representation
		self.hal = {}
		self.hal['_links'] = representation.pop('_links', {})
		self.hal['_embedded'] = representation.pop('_embedded', {})
		self.etag = etag
		self.last_modified = last_modified

	def __repr__(self):
		return 'Object(module={}, dn={}, uri={})'.format(self.object_type, self.dn, self.uri)

	def reload(self):
		uri = self.client.get_relation(self.hal, 'self')
		if uri:
			obj = ShallowObject(self.udm, self.dn, uri['href']).open()
		else:
			obj = self.module.get(self.dn)
		self._copy_from_obj(obj)

	def save(self, reload=True):
		if self.dn:
			return self._modify(reload)
		else:
			return self._create(reload)

	def delete(self, remove_referring=False):
		return self.client.request('DELETE', self.uri)

	def move(self, position):
		self.position = position
		self.save()

	def _modify(self, reload=True):
		headers = dict((key, value) for key, value in {
			'If-Unmodified-Since': self.last_modified,
			'If-Match': self.etag,
		}.items() if value)

		response = self.client.make_request('PUT', self.uri, data=self.representation, **headers)
		response = self._follow_redirection(response)  # move() causes multiple redirections!
		self._reload_from_response(response)
		return response

	def _create(self, reload=True):
		uri = self.client.get_relation(self.hal, 'create')
		response = self.client.make_request('POST', uri['href'], data=self.representation)
		response = self._follow_redirection(response)
		self._reload_from_response(response)
		return response

	def _reload_from_response(self, response):
		if 200 <= response.response.status_code <= 299 and 'Location' in response.response.headers:
			uri = response.response.headers['Location']
			obj = ShallowObject(self.udm, None, uri)
			if reload:
				self._copy_from_obj(obj.open())
		elif reload:
			self.reload()

	def _follow_redirection(self, response):
		while 300 <= response.response.status_code <= 399 and 'Location' in response.response.headers:
			if response.response.headers.get('Retry-After', '').isdigit():
				time.sleep(min(30, max(0, int(response.response.headers['Retry-After']) - 1)))
			response = self.client.make_request('GET', response.response.headers['Location'])
		return response

	def _copy_from_obj(self, obj):
		self.udm = obj.udm
		self.representation = copy.deepcopy(obj.representation)
		self.hal = copy.deepcopy(obj.hal)
		self.etag = obj.etag
		self.last_modified = obj.last_modified
