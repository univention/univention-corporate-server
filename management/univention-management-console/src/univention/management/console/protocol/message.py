#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP 2.0 messages
#
# Copyright 2006-2015 Univention GmbH
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

"""
UMCP is a simple RPC protocol using two message types (request and
response message). The API of the Python objects representing the
messages are based on the class :class:`.Message`.
"""

import mimetypes
import time
import re
import copy

try:
	import simplejson as json
except:
	import json

from .definitions import (
	command_has_arguments, command_is_known, SUCCESS_PARTIAL, UMCP_ERR_ARGS_MISSMATCH,
	UMCP_ERR_UNKNOWN_COMMAND, UMCP_ERR_UNPARSABLE_BODY, UMCP_ERR_UNPARSABLE_HEADER
)
from univention.management.console.log import PARSER, PROTOCOL

from univention.lib.i18n import Translation

_ = Translation('univention.management.console').translate

# Exceptions


class ParseError(Exception):
	pass


class IncompleteMessageError(Exception):
	pass


class UnknownCommandError(Exception):
	pass


class InvalidArgumentsError(Exception):
	pass


class InvalidOptionsError(Exception):
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
	_header = re.compile('(?P<type>REQUEST|RESPONSE)/(?P<id>[\d-]+)/(?P<length>\d+)(/(?P<mimetype>[a-z-/]+))?: ?(?P<command>\w+) ?(?P<arguments>[^\n]+)?', re.UNICODE)
	__counter = 0

	def __init__(self, type=REQUEST, command='', mime_type=MIMETYPE_JSON, data=None, arguments=[], options={}):
		self._id = None
		self._length = 0
		self._type = type
		if mime_type == MIMETYPE_JSON:
			self.body = {}
		else:
			self.body = ''
		self.command = command
		self.arguments = arguments
		self.mimetype = mime_type
		if mime_type == MIMETYPE_JSON:
			self.options = options
		if data:
			self.parse(data)

	@staticmethod
	def _formattedMessage(_id, _type, mimetype, command, body, arguments):
		'''Returns formatted message.'''
		type = 'RESPONSE'
		if _type == Message.REQUEST:
			type = 'REQUEST'
		if mimetype == MIMETYPE_JSON:
			data = json.dumps(body)
		else:
			data = body
		args = ''
		if arguments:
			args = ' '.join(map(lambda x: str(x), arguments))
		return '%s/%s/%d/%s: %s %s\n%s' % (type, _id, len(data), mimetype, command, args, data)

	def __str__(self):
		'''Returns the formatted message'''
		return Message._formattedMessage(self._id, self._type, self.mimetype, self.command, self.body, self.arguments)

	def _create_id(self):
		# cut off 'L' for long
		self._id = '%lu-%d' % (long(time.time() * 100000), Message.__counter)
		Message.__counter += 1

	def recreate_id(self):
		"""Creates a new unique ID for the message"""
		self._create_id()

	def is_type(self, type):
		"""Checks the message type"""
		return (self._type == type)

	# property: id
	def _set_id(self, id):
		self._id = id

	def _get_id(self):
		return self._id

	#: The property id contains the unique identifier for the message
	id = property(_get_id, _set_id)

	# JSON body properties
	def _set_key(self, key, value, cast=None):
		if self.mimetype == MIMETYPE_JSON:
			if cast is not None:
				self.body[key] = cast(value)
			else:
				self.body[key] = value
		else:
			PARSER.info('Attribute %s just available for MIME type %s' % (key, MIMETYPE_JSON))

	def _get_key(self, key):
		if self.mimetype == MIMETYPE_JSON:
			return self.body.get(key)
		else:
			PARSER.info('Attribute %s just available for MIME type %s' % (key, MIMETYPE_JSON))
			return None

	#: contains a human readable error message
	message = property(lambda self: self._get_key('message'), lambda self, value: self._set_key('message', value))

	#: contains the data that represents the result of the request
	result = property(lambda self: self._get_key('result'), lambda self, value: self._set_key('result', value))

	#: contains the status code defining the success or failure of a request (see also :mod:`univention.management.console.protocol.definitions.STATUS`)
	status = property(lambda self: self._get_key('status'), lambda self, value: self._set_key('status', value, int))

	#: defines options to pass on to the module command
	options = property(lambda self: self._get_key('options'), lambda self, value: self._set_key('options', value))

	#: flavor of the request
	flavor = property(lambda self: self._get_key('flavor'), lambda self, value: self._set_key('flavor', value))

	def parse(self, msg):
		"""Parses data and creates in case of a vaild UMCP message the
		corresponding object. If the data contains more than the message
		the rest of the data is returned.

		:raises: :class:`.ParseError`, :class:`.UnknownCommandError`, :class:`.InvalidArgumentsError`
		"""
		header, nl, body = msg.partition('\n')

		# is the format of the header line valid?
		match = Message._header.match(header)
		if not match:
			if not nl:
				raise IncompleteMessageError(_('The message header is not (yet) complete'))
			raise ParseError(UMCP_ERR_UNPARSABLE_HEADER, _('Unparsable message header'))

		groups = match.groupdict()
		self._type = groups['type'] == 'REQUEST' and Message.REQUEST or Message.RESPONSE
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

		# known command?
		if not command_is_known(self.command):
			PROTOCOL.process('Unknown UMCP command: %s' % self.command)
			raise UnknownCommandError(UMCP_ERR_UNKNOWN_COMMAND, _('Unknown UMCP command: %s') % self.command)

		if groups.get('arguments'):
			if command_has_arguments(self.command):
				self.arguments = groups['arguments'].split(' ')
			else:
				PROTOCOL.process("The command '%s' do not have any arguments" % self.command)
				raise InvalidArgumentsError(UMCP_ERR_ARGS_MISSMATCH, _("The command '%s' do not have any arguments") % self.command)

		# invalid/missing message body?
		current_length = len(body)
		if (not body and self._length) or self._length > current_length:
			PARSER.info('The message body is not complete: %d of %d bytes' % (current_length, self._length))
			raise IncompleteMessageError(_('The message body is not (yet) complete'))

		remains = ''
		if len(body) > self._length:
			self.body, remains = body[:self._length], body[self._length:]
		else:
			self.body = body

		if self.mimetype == MIMETYPE_JSON:
			try:
				self.body = json.loads(self.body)
			except:
				self.body = {}
				PARSER.process('Error parsing UMCP message body')
				raise ParseError(UMCP_ERR_UNPARSABLE_BODY, _('error parsing UMCP message body'))

			for key in ('options', ):
				if key in self.body:
					setattr(self, key[1:], self.body[key])

		PARSER.info('UMCP %(type)s %(id)s parsed successfully' % groups)

		return remains


class Request(Message):

	'''Represents an UMCP request message'''

	def __init__(self, command, arguments=[], options={}, mime_type=MIMETYPE_JSON):
		if not command_is_known(command):
			PROTOCOL.process("'%s' is not a valid UMCP command" % command)
			raise UnknownCommandError(_("'%s' is not a valid UMCP command") % command)
		Message.__init__(self, Message.REQUEST, command, arguments=arguments, options=options, mime_type=mime_type)
		self._create_id()


class Command(Request):

	def __init__(self, arguments=[], options={}, mime_type=MIMETYPE_JSON):
		Request.__init__(self, 'COMMAND', arguments, options)


class SimpleCommand(Request):

	def __init__(self, command, options={}, mime_type=MIMETYPE_JSON):
		Request.__init__(self, 'COMMAND', [command], options)


class Response(Message):

	"""This class describes a response to a request from the console
	frontend to the console daemon"""

	def __init__(self, request=None, data=None, mime_type=MIMETYPE_JSON):
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

	def is_final(self):
		return (self._id and (self.mimetype != MIMETYPE_JSON or self.status != SUCCESS_PARTIAL))

	recreate_id = None

	def set_body(self, filename, mimetype=None):
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

	def __str__(self):
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
			print ">>> a request:",
		if msg.isType(Message.RESPONSE):
			print "<<< a response:",
		print msg

	print Message(data=str(auth))
	# decode
	data = str(req)
	msg = Message(data=data)
	print msg
