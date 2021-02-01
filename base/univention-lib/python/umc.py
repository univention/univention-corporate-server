#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Univention common Python library to manage
connections to remote |UMC| servers

>>> umc = Client()
>>> umc.authenticate_with_machine_account()
>>> response = umc.umc_get('session-info')
>>> response.status
200
>>> response = umc.umc_logout()
>>> response.status
303
"""
# Copyright 2017-2021 Univention GmbH
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

import six
import ssl
import json
import locale
import base64
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union  # noqa F401
_T = TypeVar("_T")

from six.moves.http_cookies import SimpleCookie
from six.moves.http_client import HTTPSConnection, HTTPException
from six.moves import http_client as httplib  # noqa F401

from univention.config_registry import ConfigRegistry
ucr = ConfigRegistry()
ucr.load()


class _HTTPType(type):
	"""
	Metaclass for HTTP Error exceptions.
	Sub-classes of this meta class are automatically added to the :py:data:`HTTPError.codes` mapping.
	"""
	def __init__(mcs, name, bases, dict):
		try:
			HTTPError.codes[mcs.code] = mcs
		except (NameError, AttributeError):
			pass
		return type.__init__(mcs, name, bases, dict)


class ConnectionError(Exception):
	"""
	Signal an error during connection setup.

	:param str msg: A message string.
	:param reason: The optional underlying exception.
	"""

	def __init__(self, msg, reason=None):
		# type: (str, Exception) -> None
		super(ConnectionError, self).__init__(msg, reason)
		self.reason = reason


class HTTPError(six.with_metaclass(_HTTPType, Exception)):
	"""
	Base class for |HTTP| errors.
	A specialized sub-class if automatically instantiated based on the |HTTP| return code.

	:param request: The |HTTP| request.
	:param httplib.HTTPResponse response: The |HTTP| response.
	:param str hostname: The host name of the failed server.
	"""
	codes = {}  # type: Dict[int, Type[HTTPError]]
	"""Specialized sub-classes for individual |HTTP| error codes."""

	@property
	def status(self):
		# type: () -> int
		"""
		Return the |HTTP| status code.

		:returns: the numerical status code.
		:rtype: int
		"""
		return self.response.status

	@property
	def message(self):
		# type: () -> str
		"""
		Return the |HTTP| status message.

		:returns: the textual status message.
		:rtype: str
		"""
		return self.response.message

	@property
	def result(self):
		# type: () -> str
		"""
		Return the |HTTP| result.

		:returns: the result data
		:rtype: str
		"""

		return self.response.result

	def __new__(cls, request, response, hostname):
		err = cls.codes.get(response.status, cls)
		return super(HTTPError, cls).__new__(err, request, response, hostname)  # type: ignore

	def __init__(self, request, response, hostname):
		self.request = request
		self.hostname = hostname
		self.response = response

	def __repr__(self):
		# type: () -> str
		return '<HTTPError %s>' % (self,)

	def __str__(self):
		# type: () -> str
		traceback = ''
		data = self.response.data
		if self.status >= 500 and isinstance(self.response.data, dict) and isinstance(self.response.data.get('traceback'), six.string_types) and 'Traceback (most recent call last)' in self.response.data['traceback']:
			data = data.copy()
			traceback = '\n%s' % (data.pop('traceback'),)
		return '%s on %s (%s): %s%s' % (self.status, self.hostname, self.request.path, data, traceback)


class HTTPRedirect(HTTPError):
	""":py:data:`httplib.MULTIPLE_CHOICES` |HTTP|/1.1, :rfc:`2616`, Section 10.3.1"""
	code = 300


class MovedPermanently(HTTPRedirect):
	""":py:data:`httplib.MOVED_PERMANENTLY` |HTTP|/1.1, :rfc:`2616`, Section 10.3.2"""
	code = 301


class Found(HTTPRedirect):
	""":py:data:`httplib.FOUND` |HTTP|/1.1, :rfc:`2616`, Section 10.3.3"""
	code = 302


class SeeOther(HTTPRedirect):
	""":py:data:`httplib.SEE_OTHER` |HTTP|/1.1, :rfc:`2616`, Section 10.3.4"""
	code = 303


class NotModified(HTTPRedirect):
	""":py:data:`httplib.NOT_MODIFIED` |HTTP|/1.1, :rfc:`2616`, Section 10.3.5"""
	code = 304


class BadRequest(HTTPError):
	""":py:data:`httplib.BAD_REQUEST` |HTTP|/1.1, :rfc:`2616`, Section 10.4.1"""
	code = 400


class Unauthorized(HTTPError):
	""":py:data:`httplib.UNAUTHORIZED` |HTTP|/1.1, :rfc:`2616`, Section 10.4.2"""
	code = 401


class Forbidden(HTTPError):
	""":py:data:`httplib.UNAUTHORIZED` |HTTP|/1.1, :rfc:`2616`, Section 10.4.4"""
	code = 403


class NotFound(HTTPError):
	""":py:data:`httplib.NOT_FOUND` |HTTP|/1.1, :rfc:`2616`, Section 10.4.5"""
	code = 404


class MethodNotAllowed(HTTPError):
	""":py:data:`httplib.METHOD_NOT_ALLOWED` |HTTP|/1.1, :rfc:`2616`, Section 10.4.6"""
	code = 405


class NotAcceptable(HTTPError):
	""":py:data:`httplib.NOT_ACCEPTABLE` |HTTP|/1.1, :rfc:`2616`, Section 10.4.7"""
	code = 406


class UnprocessableEntity(HTTPError):
	""":py:data:`httplib.UNPROCESSABLE_ENTITY` WEBDAV, :rfc:`22518`, Section 10.3"""
	code = 422


class InternalServerError(HTTPError):
	""":py:data:`httplib.INTERNAL_SERVER_ERROR` |HTTP|/1.1, :rfc:`2616`, Section 10.5.1"""
	code = 500


class BadGateway(HTTPError):
	""":py:data:`httplib.BAD_GATEWAY` |HTTP|/1.1, :rfc:`2616`, Section 10.5.3"""
	code = 502


class ServiceUnavailable(HTTPError):
	""":py:data:`httplib.SERVICE_UNAVAILABLE` |HTTP|/1.1, :rfc:`2616`, Section 10.5.4"""
	code = 503


class Request(object):
	"""
	The |HTTP| request.

	:param str method: `GET` / `POST` / `PUT` / `DELETE`
	:param str path: the relative path to `/univention/`.
	:param str data: either the raw request payload or some data which must be encoded by get_body()
	:param dict headers: a mapping of HTTP headers
	"""

	def __init__(self, method, path, data=None, headers=None):
		# type: (str, str, Optional[bytes], Optional[Dict[str, str]]) -> None
		self.method = method
		self.path = path
		self.data = data
		self.headers = headers or {}

	def get_body(self):
		# type: () -> Optional[bytes]
		"""
		Return the request data.

		:returns: encodes data in JSON if Content-Type wants it
		:rtype: bytes
		"""
		if self.headers.get('Content-Type', '').startswith('application/json'):
			return json.dumps(self.data).encode('ASCII')
		return self.data


class Response(object):
	"""
	The |HTTP| response.

	:param int status: |HTTP| status code between 200 and 599.
	:param str reason: string with the reason phrase e.g. 'OK'
	:param str body: the raw response body
	:param list headers: the response headers as list of tuples
	:param httplib.HTTPResponse _response: The original |HTTP| response.
	"""

	@property
	def result(self):
		# type: () -> Any
		"""
		Return `result` from |JSON| data.

		:returns: The `result`.
		"""
		if isinstance(self.data, dict):
			return self.data.get('result')

	@property
	def message(self):
		# type: () -> Any
		"""
		Return `message` from |JSON| data.

		:returns: The `message`.
		"""
		if isinstance(self.data, dict):
			return self.data.get('message')

	def __init__(self, status, reason, body, headers, _response):
		# type: (int, str, bytes, List[Tuple[str, str]], httplib.HTTPResponse) -> None
		self.status = status
		self.reason = reason
		self.body = body
		self.headers = headers
		self._response = _response
		self.data = self.decode_body()

	def get_header(self, name, default=None):
		# type: (str, _T) -> _T
		"""
		Return original |HTTP| response header.

		:param str name: |HTTP| respone header name, e.g. `Content-Type`.
		:param default: Default value of the header is not set. Defaults to `None`.
		:returns: The header value or `None`.
		:rtype: str or None
		"""
		return self._response.getheader(name, default)

	def decode_body(self):
		# type: () -> Union[bytes, dict]
		"""
		Decode |HTTP| response and return |JSON| data as dictionary.

		:returns: |JSON| data is returned as a dictionary, all other as raw.
		:rtype: dict or str
		"""
		data = self.body
		if self.get_header('Content-Type', '').startswith('application/json'):
			try:
				data = json.loads(data.decode('UTF-8'))
			except ValueError as exc:
				raise ConnectionError('Malformed response data: %r' % (data,), reason=exc)
		return data

	@classmethod
	def _from_httplib_response(cls, response):
		# type: (httplib.HTTPResponse) -> Response
		"""
		Create class instance from |HTTP| response.

		:param httplib.HTTPResponse response: The |HTTP| response.
		"""
		data = response.read()
		return cls(response.status, response.reason, data, response.getheaders(), response)


class Client(object):
	"""
	A client capable to speak with a |UMC| server.

	:param str hostname: The name of the host to connect. Defaults to the |FQDN| of the localhost.
	:param str username: A user name.
	:param str password: The password of the user.
	:param str language: The preferred language.
	:param float timeout: Set the default timeout in seconds (float) for new connections.
	:param bool automatic_reauthentication: Automatically re-authenticate and re-do requests if the authentication cookie expires.
	"""

	ConnectionType = HTTPSConnection

	def __init__(self, hostname=None, username=None, password=None, language=None, timeout=None, automatic_reauthentication=False):
		# type: (Optional[str], Optional[str], Optional[str], Optional[str], Optional[float], bool) -> None
		self.hostname = hostname or '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))
		self._language = language or locale.getdefaultlocale()[0] or ''
		self._headers = {
			'Content-Type': 'application/json; charset=UTF-8',
			'Accept': 'application/json; q=1, text/html; q=0.5; */*; q=0.1',
			'Accept-Language': self._language.replace('_', '-'),
			'X-Requested-With': 'XMLHttpRequest',
			'User-Agent': 'UCS/%s (univention.lib.umc/%s-errata%s)' % (ucr.get('version/version', '0.0'), ucr.get('version/patchlevel', '0'), ucr.get('version/erratalevel', '0')),
		}
		self._base_uri = '/univention/'
		self._timeout = timeout
		self._raise_errors = True
		self._automatic_reauthentication = automatic_reauthentication
		self.cookies = {}  # type: Dict[str, str]
		self.username = username or ''
		self.password = password or ''
		if username:
			self.authenticate(self.username, self.password)

	def authenticate(self, username, password):
		# type: (str, str) -> Response
		"""
		Authenticate against the host and preserves the
		cookie. Has to be done only once (but keep in mind that the
		session probably expires after 10 minutes of inactivity)

		:param str username: A user name.
		:param str password: The password of the user.
		"""
		self.username = username
		self.password = password
		return self.umc_auth(username, password)

	def reauthenticate(self):
		# type: () -> Response
		"""
		Re-authenticate using the stored username and password.
		"""
		return self.authenticate(self.username, self.password)

	def set_basic_http_authentication(self, username, password):
		# type: (str, str) -> None
		"""
		Setup authentication using |HTTP| Basic authentication.

		:param str username: A user name.
		:param str password: The password of the user.
		"""
		self._headers['Authorization'] = 'Basic %s' % (base64.b64encode(b'%s:%s' % (username.encode('UTF-8'), password.encode('UTF-8'))).decode('ASCII'),)

	def authenticate_saml(self, username, password):
		# type: (str, str) -> None
		"""
		Setup authentication using |SAML|.

		:param str username: A user name.
		:param str password: The password of the user.

		.. warning::
			not implemented.
		"""
		raise ConnectionError('SAML authentication currently not supported.')

	def authenticate_with_machine_account(self):
		# type: () -> None
		"""
		Setup authentication using the machine account.

		:raises ConnectionError: if :file:`/etc/machine.secret` cannot be read.
		"""
		username = '%s$' % ucr.get('hostname')
		try:
			with open('/etc/machine.secret') as machine_file:
				password = machine_file.readline().strip()
		except EnvironmentError as exc:
			raise ConnectionError('Could not read /etc/machine.secret', reason=exc)
		self.authenticate(username, password)

	def umc_command(self, path, options=None, flavor=None, headers=None):
		# type: (str, Optional[dict], Optional[str], Optional[dict]) -> Response
		"""
		Perform generic |UMC| command.

		:param str path: The |URL| path of the command after the `command/` prefix.
		:param dict options: The argument for the |UMC| command.
		:param str flavor: Optional name of the |UMC| module flavor, e.g. `users/user` for |UDM| modules.
		:param dict headers: Optional |HTTP| headers.
		:returns: The |UMC| response.
		:rtype: Response
		"""
		data = self.__build_data(options, flavor)
		return self.request('POST', 'command/%s' % (path,), data, headers)

	def umc_set(self, options, headers=None):
		# type: (Optional[dict], Optional[dict]) -> Response
		"""
		Perform |UMC| `set` command.

		:param dict options: The argument for the |UMC| `set` command.
		:param dict headers: Optional |HTTP| headers.
		:returns: The |UMC| response.
		:rtype: Response
		"""
		data = self.__build_data(options)
		return self.request('POST', 'set', data, headers)

	def umc_get(self, path, options=None, headers=None):
		# type: (str, Optional[dict], Optional[dict]) -> Response
		"""
		Perform |UMC| `get` command.

		:param str path: The |URL| path of the command after the `get/` prefix.
		:param dict options: The argument for the |UMC| `get` command.
		:param dict headers: Optional |HTTP| headers.
		:returns: The |UMC| response.
		:rtype: Response
		"""
		return self.request('POST', 'get/%s' % path, self.__build_data(options), headers)

	def umc_upload(self):
		# type: () -> None
		"""
		Perform |UMC| upload action.

		.. warning::
			not implemented.
		"""
		raise NotImplementedError('File uploads currently need to be done manually.')

	def umc_auth(self, username, password, **data):
		# type: (str, str, **str) -> Response
		"""
		Perform |UMC| authentication command.

		:param str username: A user name.
		:param str password: The password of the user.
		:param data: Additional argument for the |UMC| `auth` command.
		:returns: The |UMC| response.
		:rtype: Response
		"""
		data = self.__build_data(dict({'username': username, 'password': password}, **data))
		return self.request('POST', 'auth', data)

	def umc_logout(self):
		# type: () -> Response
		"""
		Perform |UMC| logout action.

		:returns: The |UMC| response.
		:rtype: Response
		"""
		try:
			return self.request('GET', 'logout')
		except (SeeOther, Found, MovedPermanently) as exc:
			return exc.response

	def request(self, method, path, data=None, headers=None):
		# type: (str, str, Any, Optional[dict]) -> Response
		"""
		Send request to |UMC| server handling re-authentication.

		:param str method: The |HTTP| method for the request.
		:param str path: The |URL| of the request.
		:param data: The message body.
		:param dict headers: Optional |HTTP| headers.
		:returns: The |UMC| response.
		:rtype: Response
		:raises Unauthorized: if the session expired and re-authentication was disabled.
		"""
		request = Request(method, path, data, headers)
		try:
			return self.send(request)
		except Unauthorized:
			if not self._automatic_reauthentication:
				raise
			self.reauthenticate()
			return self.send(request)

	def send(self, request):
		# type: (Request) -> Response
		"""
		Low-level function to send request to |UMC| server.

		:param Request request: A |UMC| request.
		:returns: The |UMC| response.
		:rtype: Response
		:raises ConnectionError: if the request cannot be send.
		:raises HTTPError: if an |UMC| error occurs.
		"""
		cookie = '; '.join(['='.join(x) for x in self.cookies.items()])
		request.headers = dict(self._headers, Cookie=cookie, **request.headers)
		if 'UMCSessionId' in self.cookies:
			request.headers['X-XSRF-Protection'] = self.cookies['UMCSessionId']
		try:
			response = self.__request(request)
		except (HTTPException, EnvironmentError, ssl.CertificateError) as exc:
			raise ConnectionError('Could not send request.', reason=exc)
		self._handle_cookies(response)
		response = Response._from_httplib_response(response)
		if self._raise_errors and response.status > 299:
			raise HTTPError(request, response, self.hostname)
		return response

	def _handle_cookies(self, response):
		# type: (httplib.HTTPResponse) -> None
		"""
		Parse cookies from |HTTP| response and store for next request.

		:param httplib.HTTPResponse: The |HTTP| response.
		"""
		# FIXME: this cookie handling doesn't respect path, domain and expiry
		cookies = SimpleCookie()
		cookies.load(response.getheader('set-cookie', ''))
		self.cookies.update(dict((cookie.key, cookie.value) for cookie in cookies.values()))

	def __request(self, request):
		# type: (Request) -> httplib.HTTPResponse
		"""
		Perform a request to the |UMC| server and return its response.

		:param Request request: The |UMC| request.
		:returns: The |HTTP| response.
		:rtype: httplib.HTTPResponse
		"""
		uri = '%s%s' % (self._base_uri, request.path)
		con = self._get_connection()
		con.request(request.method, uri, request.get_body(), headers=request.headers)
		response = con.getresponse()
		if response.status == 404:
			if self._base_uri == '/univention/':
				# UCS 4.1
				self._base_uri = '/univention-management-console/'
				return self.__request(request)
			elif self._base_uri == '/univention-management-console/':
				# UCS 3.X
				self._base_uri = '/umcp/'
				return self.__request(request)
		return response

	def _get_connection(self):
		# type: () -> HTTPSConnection
		"""
		Creates a new connection to the host.

		:returns: A new connection to the stores host.
		:rtype: HTTPSConnection
		"""
		# once keep-alive is over, the socket closes
		#   so create a new connection on every request
		return self.ConnectionType(self.hostname, timeout=self._timeout)

	def __build_data(self, data, flavor=None):
		# type: (Optional[Dict[str, Any]], Optional[str]) -> Dict[str, Any]
		"""
		Create a dictionary as expected by the |UMC| Server.

		:param dict data: The argument for the |UMC| command.
		:param str flavor: Optional name of the |UMC| module flavor, e.g. `users/user` for |UDM| modules.
		:returns: A dictionary suitable for sending to the |UMC| server.
		:rtype: dict
		"""
		data = {'options': data if data is not None else {}}
		if flavor:
			data['flavor'] = flavor
		return data
