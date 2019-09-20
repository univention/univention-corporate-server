# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Univention GmbH
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals
from collections import namedtuple
from typing import Any, Text


ConnectionConfig = namedtuple('ConnectionConfig', ['klass', 'method', 'args', 'kwargs'])


is_interactive = bool()


class UDebug(object):
	"""univention.debug convenience wrapper"""
	target = 0x0A  # type: int
	level2str = {
		4: 'DEBUG',
		0: 'ERROR',
		3: 'INFO',
		2: 'INFO',
		1: 'WARN',
	}

	@classmethod
	def all(cls, msg):  # type: (Text) -> None
		...

	debug = all

	@classmethod
	def error(cls, msg):  # type: (Text) -> None
		...

	@classmethod
	def info(cls, msg):  # type: (Text) -> None
		...

	@classmethod
	def process(cls, msg):  # type: (Text) -> None
		...

	@classmethod
	def warn(cls, msg):  # type: (Text) -> None
		...

	warning = warn

	@classmethod
	def _log(cls, level, msg):  # type: (int, Text) -> None
		...


def load_class(module_path, class_name):  # type: (str, str) -> type
	...


def get_connection(connection_config):  # type: (ConnectionConfig) -> Any
	...
