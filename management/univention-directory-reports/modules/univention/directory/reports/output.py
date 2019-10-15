# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  write an interpreted token structure to a file
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

import codecs
import os

from .tokens import TextToken, ResolveToken, QueryToken, AttributeToken, PolicyToken, DateToken


class Output(object):

	def __init__(self, tokens, filename=None, fd=None):
		self._tokens = tokens
		self._filename = filename
		self._fd = fd

	def _create_dir(self):
		if not os.path.isdir(os.path.dirname(self._filename)):
			os.makedir(self.path, mode=0o700)

	def open(self):
		if self._fd:
			return
		self._create_dir()
		self._fd = codecs.open(self._filename, 'wb', encoding='utf8')

	def close(self):
		if self._fd:
			self._fd.close()
		self._fd = None

	def write(self, tokens=[]):
		if not self._fd:
			return
		if not tokens:
			tokens = self._tokens
		for token in tokens:
			if isinstance(token, TextToken):
				self._fd.write(unicode(token.data, 'utf8'))
			elif isinstance(token, (ResolveToken, QueryToken)):
				if len(token):
					self.write(token)
			elif isinstance(token, (DateToken, AttributeToken, PolicyToken)):
				self._fd.write(token.value)
