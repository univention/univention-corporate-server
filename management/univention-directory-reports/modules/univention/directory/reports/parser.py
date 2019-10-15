# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  splits a text into tokens
#
# Copyright 2007-2019 Univention GmbH
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

import re
import shlex

from .tokens import Token, TextToken, AttributeToken, PolicyToken, QueryToken, HeaderToken, FooterToken, IContextToken, ResolveToken, DateToken


class Parser(object):

	REGEX_OPEN = re.compile('<@(?P<tag>[^/][^ ]+)( +(?P<attrs>([a-z-0-9]+="[^"]*" *)*)|)@>')
	REGEX_CLOSE = re.compile('<@/(?P<tag>[^ ]+) *@>')
	START = '<@'
	END = '@>'

	def __init__(self, filename=None, data=None):
		if filename:
			self._filename = filename
			fd = open(self._filename, 'r')
			self._data = fd.read()
			fd.close()
		elif data:
			self._data = data
		self._tokens = []
		self._header = None
		self._footer = None
		self._context = self._tokens
		self._stack = [self._tokens]

	def parse_token(self, token):
		attrs = {}
		closing = False
		m = Parser.REGEX_OPEN.match(token)
		if not m:
			m = Parser.REGEX_CLOSE.match(token)
			if not m:
				raise SyntaxError("failed to parse token: '%s'" % token)
			closing = True
		d = m.groupdict()
		if not closing and d.get('attrs', None):
			for attr in shlex.split(d['attrs']):
				key, value = attr.split('=', 1)
				attrs[key] = value

		return (d['tag'], attrs, closing)

	def next_token(self):
		if not self._data:
			# empty token
			return Token()

		start = self._data.find(Parser.START)
		# no further tags -> rest is text
		if start < 0:
			token = TextToken(self._data)
			self._data = None
			return token
		# is text before next tag?
		if start > 0:
			token = TextToken(self._data[: start])
			self._data = self._data[start:]
			return token
		# find end of tag
		end = self._data.find(Parser.END)
		if end < 0:
			max_len = len(self._data) - start
			raise SyntaxError('No matching end tag (tag: %s)' % self._data[start: min(20, max_len)])
		name, attrs, closing = self.parse_token(self._data[start: end + len(Parser.END)])
		self._data = self._data[end + len(Parser.END):]
		if name == 'attribute':
			return AttributeToken(attrs)
		elif name == 'policy':
			return PolicyToken(attrs)
		elif name == 'query':
			return QueryToken(attrs, closing)
		elif name == 'resolve':
			return ResolveToken(attrs, closing)
		elif name == 'header':
			return HeaderToken(attrs, closing)
		elif name == 'footer':
			return FooterToken(attrs, closing)
		elif name == 'date':
			return DateToken(attrs)
		else:
			raise SyntaxError('Unknown tag: %s' % name)

	def tokenize(self):
		token = self.next_token()
		while token:
			if isinstance(token, (TextToken, AttributeToken, PolicyToken, DateToken)):
				if isinstance(token, TextToken):
					if token.data == '\n' and len(self._context) and isinstance(self._context[-1], HeaderToken):
						# ignore line feed after header
						pass
					else:
						self._context.append(token)
				else:
					self._context.append(token)
			elif isinstance(token, IContextToken):
				if not token.closing:
					self._stack.append(self._context)
					self._context.append(token)
					self._context = self._context[-1]
				else:
					self._context[-1].closing = True
					self._context = self._stack.pop()
			token = self.next_token()
		# strip header and footer, if exist
		trash = []
		for i in range(len(self._context)):
			if isinstance(self._context[i], HeaderToken):
				self._header = self._context[i]
				if len(self._header) and isinstance(self._header[0], TextToken):
					self._header = self._header[0]
				trash.append(i)
			elif isinstance(self._context[i], FooterToken):
				self._footer = self._context[i]
				if len(self._footer) and isinstance(self._footer[0], TextToken):
					self._footer = self._footer[0]
				if i > 0 and isinstance(self._context[i - 1], TextToken) and \
					self._context[i - 1].data == '\n':
					trash.append(i - 1)
				trash.append(i)
		trash.reverse()
		for rm in trash:
			self._context.pop(rm)
