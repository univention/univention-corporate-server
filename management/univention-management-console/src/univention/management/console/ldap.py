"""Decorators for common ldap functionality.
Example usage:

@machine_connection(write=True)
def foobar(self, ldap_connection=None, ldap_position=None):
	return ldap_connection.search('uid=Administrator')

def foobar():
	def bind(lo):
		lo.bind('Administrator', 'univention')
	lo, po = get_user_connection(bind=bind, write=True)
	return lo.search('uid=Administrator')

"""

from __future__ import absolute_import

import functools
import ldap
from errno import ENOENT

from univention.admin.uldap import getMachineConnection as _getMachineConnection, getAdminConnection as _getAdminConnection, position as _position, access as _access
from univention.uldap import getBackupConnection as _getBackupConnection
import univention.admin.uexceptions as udm_errors

from univention.config_registry import ConfigRegistry
_ucr = ConfigRegistry()
_ucr.load()

__all__ = ('user_connection', 'get_user_connection', 'machine_connection', 'get_machine_connection', 'admin_connection', 'get_admin_connection')


class LDAP(object):

	_LDAP_CONNECTION = 'ldap_connection'
	_LDAP_POSITION = 'ldap_position'

	def __init__(self):
		self.__ldap_connections = {}

	def user_connection(self, func=None, bind=None, write=True, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, **kwargs):
		host = _ucr.get('ldap/master' if write else 'ldap/server/name')
		port = int(_ucr.get('ldap/master/port' if write else 'ldap/server/port', '7389'))
		base = _ucr.get('ldap/base')
		return self.connection(func, bind, host, port, base, loarg, poarg, **kwargs)

	def connection(self, func=None, bind=None, host=None, port=None, base=None, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, **kwargs):
		hash_ = ('connection', bind, host, port, base, tuple(kwargs.items()))

		def connection():
			lo = _access(host=host, port=port, base=base, **kwargs)
			if bind is not None:
				bind(lo)
			return lo, _position(lo.base)
		return self._wrapped(func, hash_, connection, loarg, poarg)

	def machine_connection(self, func=None, write=True, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, **kwargs):
		hash_ = ('machine', bool(write), tuple(kwargs.items()))
		kwargs.update({'ldap_master': write})

		def connection():
			try:
				return _getMachineConnection(**kwargs)
			except IOError as exc:
				if exc.errno == ENOENT:
					return  # /etc/machine.secret does not exists
				raise
		return self._wrapped(func, hash_, connection, loarg, poarg)

	def admin_connection(self, func=None, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, **kwargs):
		hash_ = ('admin', tuple(kwargs.items()))

		def connection():
			try:
				return _getAdminConnection(**kwargs)
			except IOError as exc:
				if exc.errno == ENOENT:
					return  # /etc/ldap.secret does not exists
				raise
		return self._wrapped(func, hash_, connection, loarg, poarg)

	def backup_connection(self, func=None, loarg=_LDAP_CONNECTION, poarg=_LDAP_POSITION, **kwargs):
		hash_ = ('backup', tuple(kwargs.items()))

		def connection():
			lo = _getBackupConnection(**kwargs)
			return _access(lo=lo), _position(lo.base)
		return self._wrapped(func, hash_, connection, loarg, poarg)

	def get_user_connection(self, *args, **kwargs):
		@self.user_connection(*args, **kwargs)
		def connection(ldap_connection=None, ldap_position=None):
			return ldap_connection, ldap_position
		return connection()

	def get_machine_connection(self, *args, **kwargs):
		@self.machine_connection(*args, **kwargs)
		def connection(ldap_connection=None, ldap_position=None):
			return ldap_connection, ldap_position
		return connection()

	def get_admin_connection(self, *args, **kwargs):
		@self.admin_connection(*args, **kwargs)
		def connection(ldap_connection=None, ldap_position=None):
			return ldap_connection, ldap_position
		return connection()

	def get_backup_connection(self, *args, **kwargs):
		@self.backup_connection(*args, **kwargs)
		def connection(ldap_connection=None, ldap_position=None):
			return ldap_connection, ldap_position
		return connection()

	def reset_cache(self):
		self.__ldap_connections.clear()

	def _wrapped(self, func, hash_, connection, loarg, poarg):
		def setter(conn):
			if conn is None:
				self.__ldap_connections.pop(hash_, None)
			else:
				self.__ldap_connections[hash_] = conn

		def getter():
			try:
				lo, po = self.__ldap_connections[hash_]
				if lo is None:
					raise KeyError()
			except KeyError:
				conn = connection()
				try:
					lo, po = conn
				except (TypeError, ValueError):
					lo, po = None, None
			return lo, po

		def _decorator(func):
			@functools.wraps(func)
			def _decorated(*args, **kwargs):
				kwargs[loarg], kwargs[poarg] = lo, po = getter()

				try:
					result = func(*args, **kwargs)
					setter((lo, po))
					return result
				except (ldap.LDAPError, udm_errors.ldapError):
					setter(None)
					raise
			return _decorated
		if func is None:
			return _decorator
		return _decorator(func)


_LDAP = LDAP()
machine_connection = _LDAP.machine_connection
get_machine_connection = _LDAP.get_machine_connection
admin_connection = _LDAP.admin_connection
get_admin_connection = _LDAP.get_admin_connection
backup_connection = _LDAP.backup_connection
get_backup_connection = _LDAP.get_backup_connection
user_connection = _LDAP.user_connection
get_user_connection = _LDAP.get_user_connection
reset_cache = _LDAP.reset_cache
del _LDAP
