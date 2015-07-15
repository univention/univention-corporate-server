#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#
# Copyright 2015 Univention GmbH
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

import time
import functools
import ldap
from errno import ENOENT

from univention.admin.uldap import getMachineConnection as _getMachineConnection
from univention.admin.uexceptions import base, noObject, objectExists


class reload_ucr(object):
	_last_reload = dict()

	def __init__(self, ucr, timeout=0.2):
		self._ucr_ref = ucr
		self._wait_until_reload = timeout

	def __call__(self, func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			last_reload = self._last_reload.get(id(self._ucr_ref), 0)
			if last_reload == 0 or time.time() - last_reload > self._wait_until_reload:
				self._ucr_ref.load()
				self._last_reload[id(self._ucr_ref)] = time.time()
			return func(*args, **kwargs)
		return wrapper


class LDAP(object):

	_LDAP_CONNECTION = 'ldap_connection'
	_LDAP_POSITION = 'ldap_position'

	def __init__(self):
		self.__ldap_connections = {}

	def machine_connection(self, func=None, write=True, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, **kwargs):
		hash_ = ('machine', bool(write))
		kwargs.update({'ldap_master': write})

		def connection():
			try:
				return _getMachineConnection(**kwargs)
			except IOError as exc:  # /etc/machine.secret does not exists
				if exc.errno == ENOENT:
					return
				raise
		return self._wrapped(func, hash_, connection, loarg, poarg)

	def get_machine_connection(self, *args, **kwargs):
		@self.machine_connection(*args, **kwargs)
		def connection(ldap_connection=None, ldap_position=None):
			return ldap_connection, ldap_position
		return connection()

	def _wrapped(self, func, hash_, connection, loarg, poarg):
		def setter(conn):
			self.__ldap_connections[hash_] = conn

		def _decorator(func):
			@functools.wraps(func)
			def _decorated(*args, **kwargs):
				try:
					conn = self.__ldap_connections[hash_]
				except KeyError:
					conn = connection()
					setter(conn)

				try:
					lo, po = conn
				except (TypeError, ValueError):
					lo, po = conn, None

				kwargs[loarg], kwargs[poarg] = conn = lo, po

				try:
					return func(*args, **kwargs)
				except (ldap.LDAPError, base) as exc:
					if isinstance(exc, base) and hasattr(exc, 'original_exception'):
						exc = exc.original_exception
					# ignore often occuring exceptions which doesn't indicate the the connection is broken
					if not isinstance(exc, (ldap.NO_SUCH_OBJECT, ldap.ALREADY_EXISTS, noObject, objectExists)):
						# unset the cached connection
						setter(None)
					raise
			return _decorated
		if func is None:
			return _decorator
		return _decorator(func)


_LDAP = LDAP()
machine_connection = _LDAP.machine_connection
get_machine_connection = _LDAP.get_machine_connection
del _LDAP
