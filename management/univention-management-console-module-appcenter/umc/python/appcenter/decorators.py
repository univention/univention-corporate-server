#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software management / app center
#
# Copyright 2012-2015 Univention GmbH
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
from univention.admin.uldap import getMachineConnection as _getMachineConnection, getAdminConnection as _getAdminConnection
from univention.admin.uexceptions import base


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


def _wraps(func):
	return functools.wraps(func)

class _LDAP(object):

	__ldap_connections = {}
	_LDAP_CONNECTION = 'ldap_connection'
	_LDAP_POSITION = 'ldap_position'


	@classmethod
	def machine_connection(cls, func=None, write=False, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, **kwargs):
		"""
		@machine_connection(write=True)
		def foobar(self, ldap_connection=None, ldap_position=None):
			pass
		"""
		return cls._wrapped(func, cls._get_machine_connection(write, kwargs), cls._set_machine_connection(write), loarg, poarg)
	__ldap_connections['machine_connection'] = {'write': None, 'read': None}

	@classmethod
	def _get_machine_connection(cls, write, kwargs):
		def connection():
			conn = cls.__ldap_connections['machine_connection']['write' if write else 'read']
			if conn is None:
				kwargs.update({'ldap_master': write})
				try:
					conn = _getMachineConnection(**kwargs)
				except IOError:  # /etc/machine.secret does not exists
					return
			return conn
		return connection

	@classmethod
	def _set_machine_connection(cls, write):
		def setter(conn):
			cls.__ldap_connections['machine_connection']['write' if write else 'read'] = conn
		return setter

	@classmethod
	def _wrapped(cls, func, connection, setter, loarg, poarg):
		def _decorator(func):
			@_wraps(func)
			def _decorated(*args, **kwargs):
				kwargs[loarg], kwargs[poarg] = conn = connection()
				try:
					return func(*args, **kwargs)
				except ldap.SERVER_DOWN:
					setter(None)
					raise
				except base as exc:
					if isinstance(getattr(exc, 'original_exception', None), (ldap.SERVER_DOWN, )):
						setter(None)
					raise
				else:
					setter(conn)
			return _decorated
		if func is None:
			return _decorator
		return _decorator(func)
machine_connection = _LDAP.machine_connection
