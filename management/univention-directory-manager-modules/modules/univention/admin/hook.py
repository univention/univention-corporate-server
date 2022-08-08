# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2022 Univention GmbH
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
|UDM| hook definitions for modifying |LDAP| calls when objects are created, modifier or deleted.
"""

import sys
import io
import os
import traceback
import six
from typing import TYPE_CHECKING, List, Tuple, Union  # noqa: F401

import univention.debug as ud
from univention.admin import localization
if TYPE_CHECKING:
	import univention.admin.handlers  # noqa: F401
	AddList = List[Tuple[str, List[str]]]
	_Mod2 = Tuple[str, List[str]]
	_Mod3 = Tuple[str, List[str], List[str]]
	ModList = List[Union[_Mod2, _Mod3]]

translation = localization.translation('univention/admin')
_ = translation.translate


def import_hook_files():
	# type: () -> None
	"""
	Load all additional hook files from :file:`.../univention/admin/hooks.d/*.py`
	"""
	for dir_ in sys.path:
		hooks_d = os.path.join(dir_, 'univention/admin/hooks.d/')
		if os.path.isdir(hooks_d):
			hooks_files = (os.path.join(hooks_d, f) for f in os.listdir(hooks_d) if f.endswith('.py'))
			for fn in hooks_files:
				try:
					with io.open(fn, 'rb') as fd:
						exec(fd.read(), sys.modules[__name__].__dict__)
					ud.debug(ud.ADMIN, ud.INFO, 'admin.hook.import_hook_files: importing %r' % (fn,))
				except Exception:
					ud.debug(ud.ADMIN, ud.ERROR, 'admin.hook.import_hook_files: loading %r failed' % (fn,))
					ud.debug(ud.ADMIN, ud.ERROR, 'admin.hook.import_hook_files: TRACEBACK:\n%s' % traceback.format_exc())


class simpleHook(object):
	"""
	Base class for a |UDM| hook performing logging.
	"""
	type = 'simpleHook'

	#
	# To use the LDAP connection of the parent UDM call in any of the following
	# methods, use obj.lo and obj.position.
	#

	def hook_open(self, obj):
		# type: (univention.admin.handlers.simpleLdap) -> None
		"""
		This method is called by the default open handler just before the current state of all properties is saved.

		:param obj: The |UDM| object instance.
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.simpleHook: _open called')

	def hook_ldap_pre_create(self, obj):
		# type: (univention.admin.handlers.simpleLdap) -> None
		"""
		This method is called before an |UDM| object is created.
		It is called after the module validated all properties but before the add-list is created.

		:param obj: The |UDM| object instance.
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.simpleHook: _ldap_pre_create called')

	def hook_ldap_addlist(self, obj, al=[]):
		# type: (univention.admin.handlers.simpleLdap, AddList) -> AddList
		"""
		This method is called before an |UDM| object is created.

		Notice that :py:meth:`hook_ldap_modlist` will also be called next.

		:param obj: The |UDM| object instance.
		:param al: A list of two-tuples (ldap-attribute-name, list-of-values) which will be used to create the LDAP object.
		:returns: The (modified) add-list.
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.simpleHook: _ldap_addlist called')
		return al

	def hook_ldap_post_create(self, obj):
		# type: (univention.admin.handlers.simpleLdap) -> None
		"""
		This method is called after the object was created in |LDAP|.

		:param obj: The |UDM| object instance.
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.simpleHook: _ldap_post_create called')

	def hook_ldap_pre_modify(self, obj):
		# type: (univention.admin.handlers.simpleLdap) -> None
		"""
		This method is called before an |UDM| object is modified.
		It is called after the module validated all properties but before the modification-list is created.

		:param obj: The |UDM| object instance.
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.simpleHook: _ldap_pre_modify called')

	def hook_ldap_modlist(self, obj, ml=[]):
		# type: (univention.admin.handlers.simpleLdap, ModList) -> ModList
		"""
		This method is called before an |UDM| object is created or modified.

		:param obj: The |UDM| object instance.
		:param ml: A list of tuples, which are either two-tuples (ldap-attribute-name, list-of-new-values) or three-tuples (ldap-attribute-name, list-of-old-values, list-of-new-values). It will be used to create or modify the |LDAP| object.
		:returns: The (modified) modification-list.
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.simpleHook: _ldap_modlist called')
		return ml

	def hook_ldap_post_modify(self, obj):
		# type: (univention.admin.handlers.simpleLdap) -> None
		"""
		This method is called after the object was modified in |LDAP|.

		:param obj: The |UDM| object instance.
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.simpleHook: _ldap_post_modify called')

	def hook_ldap_pre_remove(self, obj):
		# type: (univention.admin.handlers.simpleLdap) -> None
		"""
		This method is called before an |UDM| object is removed.

		:param obj: The |UDM| object instance.
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.simpleHook: _ldap_pre_remove called')

	def hook_ldap_post_remove(self, obj):
		# type: (univention.admin.handlers.simpleLdap) -> None
		"""
		This method is called after the object was removed from |LDAP|.

		:param obj: The |UDM| object instance.
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.simpleHook: _ldap_post_remove called')


class AttributeHook(simpleHook):
	"""
	Convenience Hook that essentially implements a mapping
	between |UDM| and |LDAP| for your extended attributes.
	Derive from this class, set :py:attr:`attribute_name` to the name of
	the |UDM| attribute and implement :py:meth:`map_attribute_value_to_udm`
	and :py:meth:`map_attribute_value_to_ldap`.

	.. warning::
		Only derive from this class when you are sure
		every system in your domain has the update installed that
		introduced this hook. (Nov 2018; UCS 4.3-2)
		Otherwise you will get errors when you are distributing your new
		hook via `ucs_registerLDAPExtension --udm_hook`
	"""
	udm_attribute_name = None
	ldap_attribute_name = None

	def hook_open(self, obj):
		# type: (univention.admin.handlers.simpleLdap) -> None
		"""
		Open |UDM| object by loading value from |LDAP|.

		:param obj: The |UDM| object instance.
		"""
		assert isinstance(self.udm_attribute_name, six.string_types), "udm_attribute_name has to be a str"  # noqa: F821
		ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.AttributeHook: Mapping %s (LDAP) -> %s (UDM)' % (self.ldap_attribute_name, self.udm_attribute_name))
		old_value = obj[self.udm_attribute_name]
		new_value = self.map_attribute_value_to_udm(old_value)
		ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.AttributeHook: Setting UDM value from %r to %r' % (old_value, new_value))
		obj[self.udm_attribute_name] = new_value

	def hook_ldap_addlist(self, obj, al):
		# type: (univention.admin.handlers.simpleLdap, AddList) -> AddList
		"""
		Extend |LDAP| add list.

		:param obj: The |UDM| object instance.
		:param al: The add list to extend.
		:returns: The extended add list.
		"""
		return self.hook_ldap_modlist(obj, al)

	def hook_ldap_modlist(self, obj, ml):
		# type: (univention.admin.handlers.simpleLdap, ModList) -> ModList
		"""
		Extend |LDAP| modification list.

		:param obj: The |UDM| object instance.
		:param ml: The modification list to extend.
		:returns: The extended modification list.
		"""
		assert isinstance(self.ldap_attribute_name, six.string_types), "ldap_attribute_name has to be a str"  # noqa: F821
		new_ml = []
		for ml_value in ml:
			if len(ml_value) == 2:
				key, old_value, new_value = ml_value[0], [], ml_value[1]
			else:
				key, old_value, new_value = ml_value
			if key == self.ldap_attribute_name:
				ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.AttributeHook: Mapping %s (UDM) -> %s (LDAP)' % (self.udm_attribute_name, self.ldap_attribute_name))
				old_value = self.map_attribute_value_to_ldap(old_value)
				new_new_value = self.map_attribute_value_to_ldap(new_value)
				ud.debug(ud.ADMIN, ud.INFO, 'admin.syntax.hook.AttributeHook: Setting LDAP value from %r to %r' % (new_value, new_new_value))
				new_value = new_new_value
			new_ml.append((key, old_value, new_value))
		return new_ml

	def map_attribute_value_to_ldap(self, value):
		# type: (bytes) -> bytes
		"""
		Return value as it shall be saved in |LDAP|.

		:param value: The |UDM| value.
		:returns: The |LDAP| value.
		"""
		return value

	def map_attribute_value_to_udm(self, value):
		# type: (str) -> str
		"""
		Return value as it shall be used in |UDM| objects.

		The mapped value needs to be syntax compliant.

		:param value: The |LDAP| value.
		:returns: The |UDM| value.
		"""
		return value
