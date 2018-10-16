# -*- coding: utf-8 -*-
#
# Copyright 2018 Univention GmbH
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
# <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals
import sys
import inspect
import importlib
import univention.debug

try:
	from typing import Dict, Optional, Text, Tuple
except ImportError:
	pass


is_interactive = bool(getattr(sys, 'ps1', sys.flags.interactive))


class UDebug(object):
	"""univention.debug convenience wrapper"""
	target = univention.debug.ADMIN  # type: int
	level2str = {
		univention.debug.ALL: 'DEBUG',
		univention.debug.ERROR: 'ERROR',
		univention.debug.INFO: 'INFO',
		univention.debug.PROCESS: 'INFO',
		univention.debug.WARN: 'WARN',
	}

	@classmethod
	def all(cls, msg):  # type: (Text) -> None
		"""Write a debug message with level ALL (as in DEBUG)"""
		cls._log(univention.debug.ALL, msg)

	debug = all

	@classmethod
	def error(cls, msg):  # type: (Text) -> None
		"""Write a debug message with level ERROR"""
		cls._log(univention.debug.ERROR, msg)

	@classmethod
	def info(cls, msg):  # type: (Text) -> None
		"""Write a debug message with level INFO"""
		cls._log(univention.debug.INFO, msg)

	@classmethod
	def process(cls, msg):  # type: (Text) -> None
		"""Write a debug message with level PROCESS"""
		cls._log(univention.debug.PROCESS, msg)

	@classmethod
	def warn(cls, msg):  # type: (Text) -> None
		"""Write a debug message with level WARN"""
		cls._log(univention.debug.WARN, msg)

	warning = warn

	@classmethod
	def _log(cls, level, msg):  # type: (int, Text) -> None
		univention.debug.debug(cls.target, level, msg)
		if is_interactive and level <= univention.debug.INFO:
			print('{}: {}'.format(cls.level2str[level], msg))


def load_class(module_path, class_name):  # type: (str, str) -> type
	"""
	Load Python class from module.

	:param str module_path: module from which to load class ``class_name``
	:param str class_name: class in module ``module_path`` from which to
		load supported API versions
	:return: loaded class
	:rtype: type
	:raises ImportError: if the module at ``module_path`` could not be loaded
	:raises ValueError: if the object in ``class_name`` is not a class
	"""
	UDebug.debug('Trying to load Python module {!r}...'.format(module_path))
	module = importlib.import_module(module_path)
	UDebug.debug('Trying to load class {!r} from module {!r}...'.format(class_name, module.__name__))
	candidate_cls = getattr(module, class_name)
	UDebug.debug('Loaded {!r}.'.format(candidate_cls))
	if not inspect.isclass(candidate_cls):
		raise ValueError(
			'Found {!r}, which is not a class, when looking for class with name {!r} in module path {!r}.'.format(
				candidate_cls, class_name, module_path))
	return candidate_cls
