#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP 2.0 messages
#
# Copyright 2006-2022 Univention GmbH
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
UMCP is a simple RPC protocol using two message types (request and
response message). The API of the Python objects representing the
messages are based on the class :class:`.Message`.
"""
from __future__ import print_function

import mimetypes
import time
import re
import copy
import json

import six

from .definitions import UMCP_ERR_UNPARSABLE_BODY, UMCP_ERR_UNPARSABLE_HEADER
from univention.management.console.log import PARSER, PROTOCOL

from univention.lib.i18n import Translation

try:
	from typing import Any, Dict, List, Optional, Text, Union  # noqa F401
	RequestType = int
	UmcpBody = Union[dict, str, bytes]
except ImportError:
	pass

_ = Translation('univention.management.console').translate


class ParseError(Exception):
	pass


class IncompleteMessageError(Exception):
	pass


# Constants
MIMETYPE_JSON = 'application/json'
MIMETYPE_JPEG = 'image/jpeg'
MIMETYPE_PNG = 'image/png'
MIMETYPE_PLAIN = 'text/plain'
MIMETYPE_HTML = 'text/html'


class Message(object):

	"""Represents a protocol message of UMCP. It is able to parse
	request as well as response messages.

	:param type: message type (RESPONSE or REQUEST)
	:param str command: UMCP command
	:param str mime_type: defines the MIME type of the message body
	:param data: binary data that should contain a message
	:param arguments: arguments for the UMCP command
	:param options: options passed to the command handler. This works for request messages with MIME type application/JSON only.
	"""

	RESPONSE, REQUEST = range(0, 2)
	_header = re.compile(u'(?P<type>REQUEST|RESPONSE)/(?P<id>[\d-]+)/(?P<length>\d+)(/(?P<mimetype>[a-z-/]+))?: ?(?P<command>\w+) ?(?P<arguments>[^\n]+)?', re.UNICODE)
	__counter = 0

	def __init__(self, type=REQUEST, command=u'', mime_type=MIMETYPE_JSON, data=None, arguments=None, options=None):
		# type: (RequestType, Text, str, bytes, List[str], Dict[str, Any]) -> None
		self._id = None  # type: Optional[Text]
		self._length = 0
		self._type = type
		if mime_type == MIMETYPE_JSON:
			self.body = {}  # type: UmcpBody
		else:
			self.body = b''
		self.command = command
		self.arguments = arguments if arguments is not None else []
		self.mimetype = mime_type
		if mime_type == MIMETYPE_JSON:
			self.options = options if options is not None else {}
		if data:
			self.parse(data)

	@staticmethod
	def _formattedMessage(_id, _type, mimetype, command, body, arguments):
		# type: (Text, RequestType, str, str, UmcpBody, List[str]) -> bytes
		'''Returns formatted message.'''
		type = b'RESPONSE'
		if _type == Message.REQUEST:
			type = b'REQUEST'
		if mimetype == MIMETYPE_JSON:
			data = json.dumps(body)
			if not isinstance(data, bytes):  # Python 3
				data = data.encode('utf-8')
		else:
			data = bytes(body)
		args = b''
		if arguments:
			args = b' '.join(x.encode('utf-8') if hasattr(bytes, 'encode') else bytes(x, 'utf-8') for x in arguments)
		return b'%s/%s/%d/%s: %s %s\n%s' % (type, _id.encode('utf-8'), len(data), mimetype.encode('utf-8'), (command or u'NONE').encode('utf-8'), args, data)

	def __bytes__(self):
		# type: () -> bytes
		'''Returns the formatted message'''
		return Message._formattedMessage(self._id, self._type, self.mimetype, self.command, self.body, self.arguments)

	if six.PY2:
		def __str__(self):
			# type: () -> str
			return self.__bytes__()

	def _create_id(self):
		# type: () -> None
		# cut off 'L' for long
		self._id = u'%lu-%d' % (int(time.time() * 100000), Message.__counter)
		Message.__counter += 1

	def recreate_id(self):
		# type: () -> None
		"""Creates a new unique ID for the message"""
		self._create_id()

	def is_type(self, type):
		# type: (Any) -> bool
		"""Checks the message type"""
		return (self._type == type)

	#: The property id contains the unique identifier for the message
	@property
	def id(self):
		# type: () -> Optional[Text]
		return self._id

	@id.setter
	def id(self, id):
		# type: (Text) -> None
		self._id = id

	# JSON body properties
	def _set_key(self, key, value, cast=None):
		if self.mimetype == MIMETYPE_JSON:
			if cast is not None:
				self.body[key] = cast(value)
			else:
				self.body[key] = value
		else:
			PARSER.warn('Attribute %s just available for MIME type %s' % (key, MIMETYPE_JSON))

	def _get_key(self, key, default=None):
		if isinstance(default, dict):
			default = default.copy()
		if self.mimetype == MIMETYPE_JSON:
			if isinstance(default, dict):
				self.body.setdefault(key, default)
			return self.body.get(key, default)
		else:
			PARSER.info('Attribute %s just available for MIME type %s' % (key, MIMETYPE_JSON))
			return default

	#: contains a human readable error message
	message = property(lambda self: self._get_key('message'), lambda self, value: self._set_key('message', value))

	#: contains error information
	error = property(lambda self: self._get_key('error'), lambda self, value: self._set_key('error', value))

	#: contains the data that represents the result of the request
	result = property(lambda self: self._get_key('result'), lambda self, value: self._set_key('result', value))

	#: contains the status code defining the success or failure of a request (see also :mod:`univention.management.console.protocol.definitions.STATUS`)
	status = property(lambda self: self._get_key('status'), lambda self, value: self._set_key('status', value, int))

	#: contains the reason phrase for the status code
	reason = property(lambda self: self._get_key('reason'), lambda self, value: self._set_key('reason', value))

	#: defines options to pass on to the module command
	options = property(lambda self: self._get_key('options'), lambda self, value: self._set_key('options', value))

	#: flavor of the request
	flavor = property(lambda self: self._get_key('flavor'), lambda self, value: self._set_key('flavor', value))

	#: contains HTTP request / response headers
	headers = property(lambda self: self._get_key('headers', {}), lambda self, value: self._set_key('headers', value))

	#: contains parsed request / response cookies
	cookies = property(lambda self: self._get_key('cookies', {}), lambda self, value: self._set_key('cookies', value))

	#: contains the HTTP request method
	http_method = property(lambda self: self._get_key('method'), lambda self, value: self._set_key('method', value))

	def parse(self, msg):
		# type: (bytes) -> bytes
		"""Parses data and creates in case of a valid UMCP message the
		corresponding object. If the data contains more than the message
		the rest of the data is returned.

		:raises: :class:`.ParseError`
		"""
		_header, nl, body = msg.partition(b'\n')

		try:
			header = _header.decode('utf-8')
		except ValueError:
			PARSER.error('Error decoding UMCP message header: %r' % (_header[:100],))
			raise ParseError(UMCP_ERR_UNPARSABLE_HEADER, _('Invalid message header encoding.'))

		# is the format of the header line valid?
		match = Message._header.match(header)
		if not match:
			if not nl:
				raise IncompleteMessageError(_('The message header is not (yet) complete'))
			PARSER.error('Error parsing UMCP message header: %r' % (header[:100],))
			raise ParseError(UMCP_ERR_UNPARSABLE_HEADER, _('Unparsable message header'))

		groups = match.groupdict()
		self._type = groups['type'] == u'REQUEST' and Message.REQUEST or Message.RESPONSE
		self._id = groups['id']
		if 'mimetype' in groups and groups['mimetype']:
			self.mimetype = groups['mimetype']

		self._id = groups['id']
		try:
			self._length = int(groups['length'])
		except ValueError:
			PARSER.process('Invalid length information')
			raise ParseError(UMCP_ERR_UNPARSABLE_HEADER, _('Invalid length information'))
		self.command = groups['command']

		if groups.get('arguments'):
			self.arguments = groups['arguments'].split(u' ')

		# invalid/missing message body?
		current_length = len(body)
		if (not body and self._length) or self._length > current_length:
			PARSER.info('The message body is not complete: %d of %d bytes' % (current_length, self._length))
			raise IncompleteMessageError(_('The message body is not (yet) complete'))

		remains = b''
		if len(body) > self._length:
			self.body, remains = body[:self._length], body[self._length:]
		else:
			self.body = body

		if self.mimetype == MIMETYPE_JSON:
			try:
				self.body = json.loads(self.body.decode('utf-8', 'ignore'))
				if not isinstance(self.body, dict):
					raise ValueError('body is a %r' % (type(self.body).__name__,))
			except ValueError as exc:
				self.body = {}
				PARSER.error('Error parsing UMCP message body: %s' % (exc,))
				raise ParseError(UMCP_ERR_UNPARSABLE_BODY, _('error parsing UMCP message body'))

		PARSER.info('UMCP %(type)s %(id)s parsed successfully' % groups)

		return remains


class Request(Message):

	'''Represents an UMCP request message'''

	def __init__(self, command, arguments=None, options=None, mime_type=MIMETYPE_JSON):
		# type: (str, Any, Any, str) -> None
		Message.__init__(self, Message.REQUEST, command, arguments=arguments, options=options, mime_type=mime_type)
		self._create_id()


class Response(Message):

	"""This class describes a response to a request from the console
	frontend to the console daemon"""

	def __init__(self, request=None, data=None, mime_type=MIMETYPE_JSON):
		# type: (Request, Any, str) -> None
		Message.__init__(self, Message.RESPONSE, mime_type=mime_type)
		if request:
			self._id = request._id
			self.command = request.command
			self.arguments = request.arguments
			if request.mimetype == MIMETYPE_JSON:
				self.options = request.options
				if 'status' in request.body:
					self.status = request.status
		elif data:
			self.parse(data)

	recreate_id = None

	def set_body(self, filename, mimetype=None):
		# type: (str, Optional[str]) -> None
		'''Set body of response by guessing the mime type of the given
		file if not specified and adding the content of the file to the body. The mime
		type is guessed using the extension of the filename.'''
		if mimetype is None:
			self.mimetype, encoding = mimetypes.guess_type(filename)
		else:
			self.mimetype = mimetype

		if self.mimetype is None:
			PROTOCOL.process('Failed to guess MIME type of %s' % filename)
			raise TypeError(_('Unknown mime type'))

		with open(filename, 'rb') as fd:
			# FIXME: should check size first
			self.body = fd.read()

	def __bytes__(self):
		'''Returns the formatted message without request options'''
		body = copy.copy(self.body)
		if isinstance(body, dict) and 'options' in body:
			del body['options']
		return Message._formattedMessage(self._id, self._type, self.mimetype, self.command, body, self.arguments)


if __name__ == '__main__':
	# encode
	auth = Request('AUTH')
	auth.body['username'] = 'fasel'
	auth.body['password'] = 'secret'
	req = Request('COMMAND', arguments=['cups/list'], options=['slave.domain.tld'])
	res = Response(req)

	for msg in (req, res, auth):
		if msg.isType(Message.REQUEST):
			print(">>> a request:", end=' ')
		if msg.isType(Message.RESPONSE):
			print("<<< a response:", end=' ')
		print(msg)

	print(Message(data=str(auth)))
	# decode
	data = str(req)
	msg = Message(data=data)
	print(msg)
