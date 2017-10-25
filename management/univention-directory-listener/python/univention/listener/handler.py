# -*- coding: utf-8 -*-
#
# Copyright 2017 Univention GmbH
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

import os
from contextlib import contextmanager
import listener
import univention.admin.objects


listener.configRegistry.load()


class ListenerModuleHandler(object):
	"""
	Subclass this to implement the logic of your listener module and have
	ListenerModuleConfiguration.get_listener_module_class return the name of
	your subclass.

	This class is not intended to be used directly. It should only be
	instantiated by ListenerModuleConfiguration.get_listener_module_instance().
	"""

	_metadata_attributes = ('entryCSN', 'entryDN', 'modifyTimestamp')
	_udm_module_cache = dict()
	ucr = listener.configRegistry

	def __init__(self, module_configuration, *args, **kwargs):  # type: (object) -> None
		"""
		When subclassing, call super()__init__() first!

		:param module_configuration: ListenerModuleConfiguration object
		"""
		self.config = module_configuration
		self.logger = self.config.logger  # Python logging object
		self.ucr.load()
		self.logger.info('Starting with configuration: %r', module_configuration)

	def create(self, dn, new):  # type: (str, dict) -> None
		"""
		Called when a new object was created.

		:param dn: str
		:param new: dict
		:return: None
		"""
		pass

	def modify(self, dn, old, new, old_dn):  # type: (str, dict, dict, str) -> None
		"""
		Called when an existing object was modified or moved.

		A move can be be detected by looking at old_dn. Attributes can be
		modified during a move.

		:param dn: str
		:param old: dict
		:param new: dict
		:param old_dn: str if object was moved/renamed, None otherwise
		:return: None
		"""
		pass

	def remove(self, dn, old):  # type: (str, dict) -> None
		"""
		Called when an object was deleted.

		:param dn: str
		:param old: dict
		:return: None
		"""
		pass

	def initialize(self):  # type: () -> None
		"""
		Called once when the Univention Directory Listener loads the module
		for the first time or when a resync it triggered.

		:return: None
		"""
		pass

	def clean(self):  # type: () -> None
		"""
		Called once when the Univention Directory Listener loads the module
		for the first time or when a resync it triggered.

		:return: None
		"""
		pass

	def pre_run(self):  # type: () -> None
		"""
		Called before create/modify/remove if either the Univention Directory
		Listener has been restarted or when post_run() has run before.

		Use for example to open an LDAP connection.

		:return: None
		"""
		pass

	def post_run(self):  # type: () -> None
		"""
		Called only, when no change happens for 15 seconds - for *any* listener
		module.

		Use for example to close an LDAP connection.

		:return: None
		"""
		pass

	@staticmethod
	@contextmanager
	def set_uid():  # type: () -> None
		"""
		Temporarily change the UID of the current process to 0.

		with self.set_uid():
			do something

		Use listener.setuid(<int|str>) for any other user that root. But be
		aware that listener.unsetuid() will not be possible afterwards, as
		that requires root privileges.

		:return: None
		"""
		old_uid = os.geteuid()
		try:
			if old_uid != 0:
				listener.setuid(0)
			yield
		finally:
			if old_uid != 0:
				listener.unsetuid()

	@classmethod
	def diff(cls, old, new, keys=None, ignore_metadata=True):  # type: (dict, dict, list, bool) -> dict
		"""
		Find differences in old and new. Returns dict with keys pointing to old
		and new values.

		:param old: dict
		:param new: dict
		:param keys: list: optional list of keys to consider in search
		:param ignore_metadata: bool: whether to ignore changed metadata attributes
		:return: dict: key -> (old[key], new[key])
		"""
		res = dict()
		if keys:
			keys = set(keys)
		else:
			keys = set(old.keys()).union(set(new.keys()))
		if ignore_metadata:
			keys.difference_update(cls._metadata_attributes)
		for key in keys:
			if set(old.get(key, '<not set>')) != set(new.get(key, '<not set>')):
				res[key] = old.get(key), new.get(key)
		return res

	def error_handler(self, dn, old, new, command, exc_type, exc_value, exc_traceback):
		"""
		Will be called for unhandled exceptions in create/modify/remove.

		:param dn: str
		:param old: dict
		:param new: dict
		:param command: str
		:param exc_type: exception type
		:param exc_value: exception parameter
		:param exc_traceback: traceback object
		:return: None
		"""
		self.logger.error('Exception for dn=%r command=%r: %r', dn, command, exc_type(exc_value))
		raise exc_type, exc_value, exc_traceback

	@classmethod
	def get_udm_objects(cls, module_name, filter_s, base_dn, lo, po, **kwargs):
		"""
		Search LDAP for UDM objects.

		:param module_name: str: UDM module ("users/user", "groups/group" etc)
		:param filter_s: str: LDAP filter
		:param base_dn: str: LDAP DN to start search from
		:param lo: univention.admin.uldap.access object
		:param po: univention.admin.uldap.position object
		:param kwargs: dict: arguments to pass to udm_module.lookup()
		:return: list of (not yet opened) UDM (simpleLdap) objects
		"""
		key = (lo.base, lo.binddn, lo.bindpw, po.getDn())
		if key not in cls._udm_module_cache:
			univention.admin.modules.update()
			udm_module = univention.admin.modules.get(module_name)
			univention.admin.modules.init(lo, po, udm_module)
			cls._udm_module_cache[key] = udm_module
		udm_module = cls._udm_module_cache[key]
		return udm_module.lookup(None, lo, filter_s=filter_s, base=base_dn, **kwargs)

	@property
	def lo(self):
		"""
		LDAP connection object.

		:return: univention.admin.uldap.access object
		"""
		return self.config.lo
