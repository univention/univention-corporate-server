# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  base class for the handlers
#
# Copyright 2004-2019 Univention GmbH
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
This module is the base for all Univention Directory Management handler modules.
A UDM handler represents an abstraction of an LDAP object.

.. seealso:: :mod:`univention.admin.uldap`
.. seealso:: :mod:`univention.admin.modules`
.. seealso:: :mod:`univention.admin.objects`
.. seealso:: :mod:`univention.admin.mapping`
.. seealso:: :mod:`univention.admin.syntax`
.. seealso:: :mod:`univention.admin.uexceptions`
"""

from __future__ import absolute_import

import copy
import re
import time
import sys
import inspect
import traceback

import six
import ipaddr
import ldap
from ldap.filter import filter_format
from ldap.dn import explode_rdn, explode_dn, escape_dn_chars, str2dn, dn2str
from ldap.controls.readentry import PostReadControl

import univention.debug as ud

from univention.admindiary.client import write_event
from univention.admindiary.events import DiaryEvent

import univention.admin.filter
import univention.admin.uldap
import univention.admin.mapping
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.localization
import univention.admin.syntax
from univention.admin import configRegistry
from univention.admin.uldap import DN
try:
	import univention.lib.admember
	_prevent_to_change_ad_properties = univention.lib.admember.is_localhost_in_admember_mode()
except ImportError:
	ud.debug(ud.ADMIN, ud.WARN, "Failed to import univention.lib.admember")
	_prevent_to_change_ad_properties = False
try:
	from typing import Any, Dict, List, Optional, Set, Tuple, Union  # noqa F401
except ImportError:
	pass

translation = univention.admin.localization.translation('univention/admin/handlers')
_ = translation.translate

# global caching variable
if configRegistry.is_true('directory/manager/samba3/legacy', False):
	s4connector_present = False  # type: Optional[bool]
elif configRegistry.is_false('directory/manager/samba3/legacy', False):
	s4connector_present = True
else:
	s4connector_present = None


def disable_ad_restrictions(disable=True):
	global _prevent_to_change_ad_properties
	_prevent_to_change_ad_properties = disable


class simpleLdap(object):
	"""The base class for all UDM handler modules.

		:param co:
			*deprecated* parameter for a config. Please pass `None`.
		:type co: None

		:param lo:
			A required LDAP connection object which is used for all LDAP operations (search, create, modify).
			It should be bound to a user which has the LDAP permissions to do the required operations.
		:type lo: :class:`univention.admin.uldap.access`

		:param position:
			The LDAP container where a new object should be created in, or `None` for existing objects.
		:type position: :class:`univention.admin.uldap.position` or `None`

		:param dn:
			The DN of an existing LDAP object. If a object should be created the DN must not be passed here!
		:type dn: str or None

		:param superordinate:
			The superordinate object of this object. Can be omitted. It is automatically searched by the given DN or position.
		:type superordinate: :class:`univention.admin.handlers.simpleLdap` or `None`.

		:param attributes:
			The LDAP attributes of the LDAP object as dict. This should by default be omitted. To save performance when an LDAP search is done this can be used, e.g. by the lookup() method.
		:type attributes: None or dict

		The following attributes hold information about the state of this object:

		:ivar str dn:
			A LDAP distinguished name (DN) of this object (if exists, otherwise None)
		:ivar str module: the UDM handlers name (e.g. users/user)
		:ivar dict oldattr:
			The LDAP attributes of this object as dict. If the object does not exists the dict is empty.
		:ivar dict info:
			A internal dictionary which holds the values for every property.
		:ivar list options:
			A list of UDM options which are enabled on this object. Enabling options causes specific object classes and attributes to be added to the object.
		:ivar list policies:
			A list of DNs containing references to assigned policies.
		:ivar dict properties: a dict which maps all UDM properties to :class:`univention.admin.property` instances.
		:ivar univention.admin.mapping.mapping mapping:
			A :class:`univention.admin.mapping.mapping` instance containing a mapping of UDM property names to LDAP attribute names.
		:ivar dict oldinfo:
			A private copy of :attr:`info` containing the original properties which were set during object loading. This is only set by :func:`univention.admin.handlers.simpleLdap.save`.
		:ivar list old_options:
			A private copy of :attr:`options` containing the original options which were set during object loading. This is only set by :func:`univention.admin.handlers.simpleLdap.save`.
		:ivar list oldpolicies:
			A private copy of :attr:`policies` containing the original policies which were set during object loading. This is only set by :func:`univention.admin.handlers.simpleLdap.save`.

		.. caution::
			Do not operate on :attr:`info` directly because this would bypass syntax validations. This object should be used like a dict.
			Properties should be assigned in the following way: obj['name'] = 'value'
	"""

	use_performant_ldap_search_filter = False

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=None):
		self._exists = False
		self.exceptions = []
		self.co = co
		self.lo = lo
		self.dn = dn
		self.old_dn = self.dn
		self.superordinate = superordinate

		self.set_defaults = 0
		if not self.dn:  # this object is newly created and so we can use the default values
			self.set_defaults = 1

		if not hasattr(self, 'position'):
			self.position = position
		if not hasattr(self, 'info'):
			self.info = {}
		if not hasattr(self, 'oldinfo'):
			self.oldinfo = {}
		if not hasattr(self, 'policies'):
			self.policies = []
		if not hasattr(self, 'oldpolicies'):
			self.oldpolicies = []
		if not hasattr(self, 'policyObjects'):
			self.policyObjects = {}
		self.__no_default = []

		if not self.position:
			self.position = univention.admin.uldap.position(lo.base)
			if dn:
				self.position.setDn(dn)
		self._open = False
		self.options = []
		self.old_options = []
		self.alloc = []

		if not isinstance(self.lo, univention.admin.uldap.access):
			if not isinstance(self.lo, univention.uldap.access):
				raise TypeError('lo must be instance of univention.admin.uldap.access.')
			ud.debug(ud.ADMIN, ud.ERROR, 'using univention.uldap.access instance is deprecated. Use univention.admin.uldap.access instead.')
			self.lo = univention.admin.uldap.access(lo=self.lo)

		# s4connector_present is a global caching variable than can be
		# None ==> ldap has not been checked for servers with service "S4 Connector"
		# True ==> at least one server with IP address (aRecord) is present
		# False ==> no server is present
		global s4connector_present
		if s4connector_present is None:
			s4connector_present = False
			searchResult = self.lo.search('(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=S4 Connector))', attr=['aRecord', 'aAAARecord'])
			s4connector_present = any(ddn for (ddn, attr) in searchResult if set(['aAAARecord', 'aRecord']) & set(attr))
		self.s4connector_present = s4connector_present

		if not univention.admin.modules.modules:
			ud.debug(ud.ADMIN, ud.WARN, 'univention.admin.modules.update() was not called')
			univention.admin.modules.update()

		m = univention.admin.modules.get(self.module)
		if not hasattr(self, 'mapping'):
			self.mapping = getattr(m, 'mapping', None)
		if not hasattr(self, 'descriptions'):
			self.descriptions = getattr(m, 'property_descriptions', None)

		self.info = {}
		self.oldattr = {}
		if attributes:
			self.oldattr = attributes
		elif self.dn:
			try:
				attr = self._ldap_attributes()
				self.oldattr = self.lo.get(self.dn, attr=attr, required=True)
			except ldap.NO_SUCH_OBJECT:
				raise univention.admin.uexceptions.noObject(self.dn)

		if self.oldattr:
			self._exists = True
			if not univention.admin.modules.recognize(self.module, self.dn, self.oldattr):
				if self.use_performant_ldap_search_filter:
					raise univention.admin.uexceptions.wrongObjectType('%s is not recognized as %s.' % (self.dn, self.module))
				else:
					ud.debug(ud.ADMIN, ud.ERROR, 'object %s is not recognized as %s. Ignoring for now. Please report!' % (self.dn, self.module))
			oldinfo = self.mapping.unmapValues(self.oldattr)
			oldinfo = self._post_unmap(oldinfo, self.oldattr)
			oldinfo = self._falsy_boolean_extended_attributes(oldinfo)
			self.info.update(oldinfo)

		self.policies = self.oldattr.get('univentionPolicyReference', [])
		self.__set_options()
		self.save()

		self._validate_superordinate(False)

	def save(self):  # type: () -> None
		"""Saves the current internal object state as old state for later comparison when e.g. modifying this object.

		.. seealso:: This method should be called by :func:`univention.admin.handlers.simpleLdap.open` and after further modifications in modify() / create().

		.. note:: self.oldattr is not set and must be set manually
		"""

		self.oldinfo = copy.deepcopy(self.info)
		self.old_dn = self.dn
		self.oldpolicies = copy.deepcopy(self.policies)
		self.options = list(set(self.options))
		self.old_options = []
		if self.exists():
			self.old_options = copy.deepcopy(self.options)

	def diff(self):  # type: () -> List[Tuple[str, Any, Any]]
		"""
		Returns the difference between old and current state as a UDM modlist.

		:returns: A list of 3-tuples (udm-property-name, old-property-value, new-property-values).
		:rtype: list
		"""
		changes = []

		for key, prop in self.descriptions.items():
			null = [] if prop.multivalue else None  # type: Union[List, None]
			# remove properties which are disabled by options
			if prop.options and not set(prop.options) & set(self.options):
				if self.oldinfo.get(key, null) not in (null, None):
					ud.debug(ud.ADMIN, ud.INFO, "simpleLdap.diff: key %s not valid (option not set)" % key)
					changes.append((key, self.oldinfo[key], null))
				continue
			if (self.oldinfo.get(key) or self.info.get(key)) and self.oldinfo.get(key, null) != self.info.get(key, null):
				changes.append((key, self.oldinfo.get(key, null), self.info.get(key, null)))

		return changes

	def hasChanged(self, key):  # type: (Union[str, List[str], Tuple[str]]) -> bool
		"""
		Checks if the given attribute(s) was (were) changed.

		:param key: The name of a property.
		:type key: str or list[str] or tuple[str]
		:returns: True if the property changed, False otherwise.
		:rtype: bool
		"""
		# FIXME: key can even be nested
		if isinstance(key, (list, tuple)):
			return any(self.hasChanged(i) for i in key)
		if (not self.oldinfo.get(key, '') or self.oldinfo[key] == ['']) and (not self.info.get(key, '') or self.info[key] == ['']):
			return False

		return not univention.admin.mapping.mapCmp(self.mapping, key, self.oldinfo.get(key, ''), self.info.get(key, ''))

	def ready(self):  # type: () -> bool
		"""Makes sure all preconditions are met before creating or modifying this object.

			It checks if all properties marked required are set.
			It checks if the superordinate is valid.

			:returns: True
			:rtype: bool
			:raises: :class:`univention.admin.uexceptions.insufficientInformation`
		"""

		missing = []
		for name, p in self.descriptions.items():
			# skip if this property is not present in the current option set
			if p.options and not set(p.options) & set(self.options):
				continue

			if p.required and (not self[name] or (isinstance(self[name], list) and self[name] == [''])):
				ud.debug(ud.ADMIN, ud.INFO, "property %s is required but not set." % name)
				missing.append(name)
		if missing:
			raise univention.admin.uexceptions.insufficientInformation(_('The following properties are missing:\n%s') % ('\n'.join(missing),))

		# when creating a object make sure that its position is underneath of its superordinate
		if not self.exists() and self.position and self.superordinate:
			if not self._ensure_dn_in_subtree(self.superordinate.dn, self.position.getDn()):
				raise univention.admin.uexceptions.insufficientInformation(_('The position must be in the subtree of the superordinate.'))

		self._validate_superordinate(True)

		return True

	def has_key(self, key):  # type: (str) -> bool
		"""
		Checks if the property exists in this module and if it is enabled in the set UDM options.

		:param str key: The name of a property.
		:returns: True if the property exists and is enabled, False otherwise.
		:rtype: bool

		.. deprecated:: 4.4
		Use :func:`univention.admin.handlers.simpleLdap.has_property` instead!
		"""
		return self.has_property(key)

	def has_property(self, key):  # type: (str) -> bool
		"""
		Checks if the property exists in this module and if it is enabled in the set UDM options.

		:param str key: The name of a property.
		:returns: True if the property exists and is enabled, False otherwise.
		:rtype: bool
		"""
		try:
			p = self.descriptions[key]
		except KeyError:
			return False
		if p.options:
			return bool(set(p.options) & set(self.options))
		return True

	def __setitem__(self, key, value):  # type: (str, Any) -> None
		"""Sets or unsets the property to the given value.

			:param str key: The name of a property.
			:param value: The value to set.

			:raises KeyError: if the property belongs to an option, which is currently not enabled.
			:raises: :class:`univention.admin.uexceptions.noProperty` or :class:`KeyError` if the property does not exists or is not enabled by the UDM options.
			:raises: :class:`univention.admin.uexceptions.valueRequired` if the value is unset but required.
			:raises: :class:`univention.admin.uexceptions.valueMayNotChange` if the values cannot be modified.
			:raises: :class:`univention.admin.uexceptions.valueInvalidSyntax` if the value is invalid.
		"""
		def _changeable():
			yield self.descriptions[key].editable
			if not self.descriptions[key].may_change:
				yield key not in self.oldinfo or self.oldinfo[key] == value
			# if _prevent_to_change_ad_properties:  # FIXME: users.user.object.__init__ modifies firstname and lastname by hand
			#	yield not (self.descriptions[key].readonly_when_synced and self._is_synced_object() and self.exists())

		# property does not exist
		if not self.has_property(key):
			# don't set value if the option is not enabled
			ud.debug(ud.ADMIN, ud.WARN, '__setitem__: Ignoring property %s' % key)
			try:
				self.descriptions[key]
			except KeyError:
				# raise univention.admin.uexceptions.noProperty(key)
				raise
			return
		# attribute may not be changed
		elif not all(_changeable()):
			raise univention.admin.uexceptions.valueMayNotChange(_('key=%(key)s old=%(old)s new=%(new)s') % {'key': key, 'old': self[key], 'new': value}, property=key)
		# required attribute may not be removed
		elif self.descriptions[key].required and not value:
			raise univention.admin.uexceptions.valueRequired(_('The property %s is required') % self.descriptions[key].short_description, property=key)
		# do nothing
		if self.info.get(key, None) == value:
			ud.debug(ud.ADMIN, ud.INFO, 'values are identical: %s:%s' % (key, value))
			return

		if self.info.get(key, None) == self.descriptions[key].default(self):
			self.__no_default.append(key)

		if self.descriptions[key].multivalue:

			# make sure value is list
			if isinstance(value, basestring):
				value = [value]
			elif not isinstance(value, list):
				raise univention.admin.uexceptions.valueInvalidSyntax(_('The property %s must be a list') % (self.descriptions[key].short_description,), property=key)

			self.info[key] = []
			for v in value:
				if not v:
					continue
				err = ""
				p = None
				try:
					s = self.descriptions[key].syntax
					p = s.parse(v)

				except univention.admin.uexceptions.valueError as emsg:
					err = emsg
				if not p:
					if not err:
						err = ""
					try:
						raise univention.admin.uexceptions.valueInvalidSyntax("%s: %s" % (key, err), property=key)
					except UnicodeEncodeError:  # raise fails if err contains umlauts or other non-ASCII-characters
						raise univention.admin.uexceptions.valueInvalidSyntax(self.descriptions[key].short_description, property=key)
				self.info[key].append(p)

		elif not value and key in self.info:
			del self.info[key]

		elif value:
			err = ""
			p = None
			try:
				s = self.descriptions[key].syntax
				p = s.parse(value)
			except univention.admin.uexceptions.valueError as e:
				err = e
			if not p:
				if not err:
					err = ""
				try:
					raise univention.admin.uexceptions.valueInvalidSyntax("%s: %s" % (self.descriptions[key].short_description, err), property=key)
				except UnicodeEncodeError:  # raise fails if err contains umlauts or other non-ASCII-characters
					raise univention.admin.uexceptions.valueInvalidSyntax("%s" % self.descriptions[key].short_description, property=key)
			self.info[key] = p

	def __getitem__(self, key):  # type: (str) -> Any
		"""
		Get the currently set value of the given property.

		:param str key: The name of a property.
		:returns: The currently set value.  If the value is not set the default value is returned.

		.. warning:: this method changes the set value to the default if it is unset. For a side effect free retrieval of the value use :func:`univention.admin.handlers.simpleLdap.get`.
		"""
		_d = ud.function('admin.handlers.base.__getitem__ key = %s' % key)  # noqa  # noqa: F841
		if not key:
			return None

		if key in self.info:
			if self.descriptions[key].multivalue and not isinstance(self.info[key], list):
				# why isn't this correct in the first place?
				ud.debug(ud.ADMIN, ud.WARN, 'The mapping for %s in %s is broken!' % (key, self.module))
				self.info[key] = [self.info[key]]
			return self.info[key]
		elif key not in self.__no_default and self.descriptions[key].editable:
			self.info[key] = self.descriptions[key].default(self)
			return self.info[key]
		elif self.descriptions[key].multivalue:
			return []
		else:
			return None

	def get(self, key, default=None):  # type: (str, Any) -> Any
		"""
		Return the currently set value of the given property.

		:param str key: The name of a property.
		:param default: The default to return if the property is not set.
		:returns: The currently set value.  If the value is not set :attr:`default` is returned.
		"""
		return self.info.get(key, default)

	def __contains__(self, key):  # type: (str) -> bool
		"""
		Checks if the property exists in this module.

		:param key: The name of a property.
		:returns: True if the property exists, False otherwise.
		:rtype: bool

		.. warning:: This does not check if the property is also enabled by the UDM options. Use :func:`univention.admin.handlers.simpleLdap.has_property` instead.
		"""
		return key in self.descriptions

	def keys(self):  # type: () -> List[str]
		"""
		Returns the names of all properties this module has.

		:returns: The list of property names.
		:rtype: list[str]
		"""
		return self.descriptions.keys()

	def items(self):  # type: () -> List[Tuple[str, Any]]
		"""
		Return all items which belong to the current options - even if they are empty.

		:returns: a list of 2-tuples (udm-property-name, property-value).
		:rtype: list[tuple]

		.. warning:: In certain circumstances this sets the default value for every property (e.g. when having a new object).
		"""
		return [(key, self[key]) for key in self.keys() if self.has_property(key)]

	def create(self, serverctrls=None, response=None):
		"""
			Creates the LDAP object if it does not exists by building the list of attributes (addlist) and write it to LDAP.
			If this call raises an exception it is necessary to instantiate a new object before trying to create it again.

			:raises: :class:`univention.admin.uexceptions.invalidOperation` if objects of this type do not support to be created.
			:raises: :class:`univention.admin.uexceptions.objectExists` if the object already exists.
			:raises: :class:`univention.admin.uexceptions.insufficientInformation`

			:param serverctrls: a list of :py:class:`ldap.controls.LDAPControl` instances sent to the server along with the LDAP request.
			:type serverctrls: list[ldap.controls.LDAPControl]
			:param dict response: An optional dictionary to receive the server controls of the result.
			:returns: The DN of the created object.
			:rtype: str
		"""

		if not univention.admin.modules.supports(self.module, 'add'):
			raise univention.admin.uexceptions.invalidOperation(_('Objects of the "%s" object type can not be created.') % (self.module,))

		if self.exists():
			raise univention.admin.uexceptions.objectExists(self.dn)

		if not isinstance(response, dict):
			response = {}

		try:
			self._ldap_pre_ready()
			self.ready()

			dn = self._create(response=response, serverctrls=serverctrls)
		except:
			self._save_cancel()
			raise

		for c in response.get('ctrls', []):
			if c.controlType == PostReadControl.controlType:
				self.oldattr.update(c.entry)
		self._write_admin_diary_create()
		return dn

	def _get_admin_diary_event(self, event_name):
		name = self.module.replace('/', '_').upper()
		return DiaryEvent.get('UDM_%s_%s' % (name, event_name)) or DiaryEvent.get('UDM_GENERIC_%s' % event_name)

	def _get_admin_diary_args_names(self, event):
		ret = []
		for name, prop in self.descriptions.iteritems():
			if name in event.args:
				ret.append(name)
		return ret

	def _get_admin_diary_args(self, event):
		args = {'module': self.module}
		if event.name.startswith('UDM_GENERIC_'):
			value = self.dn
			for k, v in self.descriptions.iteritems():
				if v.identifies:
					value = self[k]
					break
			args['id'] = value
		else:
			for name in self._get_admin_diary_args_names(event):
				args[name] = str(self[name])
		return args

	def _get_admin_diary_username(self):
		username = ldap.dn.explode_rdn(self.lo.binddn)[0]
		if username != 'cn=admin':
			username = username.rsplit('=', 1)[1]
		return username

	def _write_admin_diary_event(self, event, additional_args=None):
		try:
			event = self._get_admin_diary_event(event)
			if not event:
				return
			args = self._get_admin_diary_args(event)
			if args:
				if additional_args:
					args.update(additional_args)
				username = self._get_admin_diary_username()
				write_event(event, args, username=username)
		except Exception as exc:
			ud.debug(ud.ADMIN, ud.WARN, "Failed to write Admin Diary entry: %s" % exc)

	def _write_admin_diary_create(self):
		self._write_admin_diary_event('CREATED')

	def modify(self, modify_childs=1, ignore_license=0, serverctrls=None, response=None):
		"""Modifies the LDAP object by building the difference between the current state and the old state of this object and write this modlist to LDAP.

			:param modify_childs: Specifies if child objects should be modified as well.
			:type modify_childs: bool

			:param ignore_license: If the license is exceeded the modification may fail. Setting this to True causes license checks to be disabled
			:type ignore_license: bool

			:raises: :class:`univention.admin.uexceptions.invalidOperation` if objects of this type do not support to be modified.

			:raises: :class:`univention.admin.uexceptions.noObject` if the object does not exists.

			:raises: :class:`univention.admin.uexceptions.insufficientInformation`

			:returns: The DN of the modified object.
			:rtype: str
		"""

		if not univention.admin.modules.supports(self.module, 'edit'):
			# if the licence is exceeded 'edit' is removed from the modules operations. Nevertheless we need a way to make modifications then.
			if not ignore_license:
				raise univention.admin.uexceptions.invalidOperation(_('Objects of the "%s" object type can not be modified.') % (self.module,))

		if not self.exists():
			raise univention.admin.uexceptions.noObject(self.dn)

		if not isinstance(response, dict):
			response = {}

		try:
			self._ldap_pre_ready()
			self.ready()

			dn = self._modify(modify_childs, ignore_license=ignore_license, response=response)
		except:
			self._save_cancel()
			raise

		for c in response.get('ctrls', []):
			if c.controlType == PostReadControl.controlType:
				self.oldattr.update(c.entry)
		return dn

	def _write_admin_diary_modify(self):
		self._write_admin_diary_event('MODIFIED')

	def _create_temporary_ou(self):
		name = 'temporary_move_container_%s' % time.time()

		module = univention.admin.modules.get('container/ou')
		position = univention.admin.uldap.position('%s' % self.lo.base)

		temporary_object = module.object(None, self.lo, position)
		temporary_object.open()
		temporary_object['name'] = name
		temporary_object.create()

		return 'ou=%s' % ldap.dn.escape_dn_chars(name)

	def _delete_temporary_ou_if_empty(self, temporary_ou):  # type: (str) -> None
		"""
		Try to delete the organizational unit entry if it is empty.

		:param str temporary_ou: The distinguished name of the container.
		"""
		if not temporary_ou:
			return

		dn = '%s,%s' % (temporary_ou, self.lo.base)

		module = univention.admin.modules.get('container/ou')
		temporary_object = univention.admin.modules.lookup(module, None, self.lo, scope='base', base=dn, required=True, unique=True)[0]
		temporary_object.open()
		try:
			temporary_object.remove()
		except (univention.admin.uexceptions.ldapError, ldap.NOT_ALLOWED_ON_NONLEAF):
			pass

	def move(self, newdn, ignore_license=0, temporary_ou=None):  # type: (str, Union[bool, int], Optional[str]) -> str
		"""Moves the LDAP object to the target position.

			:param str newdn: The DN of the target position.
			:param bool ignore_license: If the license is exceeded the modification may fail. Setting this to True causes license checks to be disabled.
			:param str temporary_ou: The distiguished name of a temporary container which is used to rename the object if only is letter casing changes.

			:raises: :class:`univention.admin.uexceptions.invalidOperation` if objects of this type do not support to be moved.
			:raises: :class:`univention.admin.uexceptions.noObject` if the object does not exists.

			:returns: The new DN of the moved object
			:rtype: str
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'move: called for %s to %s' % (self.dn, newdn))

		if not (univention.admin.modules.supports(self.module, 'move') or univention.admin.modules.supports(self.module, 'subtree_move')):
			raise univention.admin.uexceptions.invalidOperation(_('Objects of the "%s" object type can not be moved.') % (self.module,))

		if self.lo.compare_dn(self.dn, self.lo.whoami()):
			raise univention.admin.uexceptions.invalidOperation(_('The own object cannot be moved.'))

		if not self.exists():
			raise univention.admin.uexceptions.noObject(self.dn)

		if _prevent_to_change_ad_properties and self._is_synced_object():
			raise univention.admin.uexceptions.invalidOperation(_('Objects from Active Directory can not be moved.'))

		def n(x):
			return dn2str(str2dn(x))

		newdn = n(newdn)
		self.dn = n(self.dn)

		goaldn = self.lo.parentDn(newdn)
		goalmodule = univention.admin.modules.identifyOne(goaldn, self.lo.get(goaldn))
		goalmodule = univention.admin.modules.get(goalmodule)
		if not goalmodule or not hasattr(goalmodule, 'childs') or not goalmodule.childs == 1:
			raise univention.admin.uexceptions.invalidOperation(_("Destination object can't have sub objects."))

		if self.lo.compare_dn(self.dn.lower(), newdn.lower()):
			if self.dn == newdn:
				raise univention.admin.uexceptions.ldapError(_('Moving not possible: old and new DN are identical.'))
			else:
				# We must use a temporary folder because OpenLDAP does not allow a rename of an container with subobjects
				temporary_ou = self._create_temporary_ou()
				temp_dn = dn2str(str2dn(newdn)[:1] + str2dn(temporary_ou) + str2dn(self.lo.base))
				self.dn = n(self.move(temp_dn, ignore_license, temporary_ou))

		if newdn.lower().endswith(self.dn.lower()):
			raise univention.admin.uexceptions.ldapError(_("Moving into one's own sub container not allowed."))

		if univention.admin.modules.supports(self.module, 'subtree_move'):
			# check if is subtree:
			subelements = self.lo.search(base=self.dn, scope='one', attr=[])
			if subelements:
				olddn = self.dn
				ud.debug(ud.ADMIN, ud.INFO, 'move: found subelements, do subtree move: newdn: %s' % newdn)
				# create copy of myself
				module = univention.admin.modules.get(self.module)
				position = univention.admin.uldap.position(self.lo.base)
				position.setDn(self.lo.parentDn(newdn))
				copyobject = module.object(None, self.lo, position)
				copyobject.options = self.options[:]
				copyobject.open()
				for key in self.keys():
					copyobject[key] = self[key]
				copyobject.policies = self.policies
				copyobject.create()
				to_be_moved = []
				moved = []
				pattern = re.compile('%s$' % (re.escape(self.dn),), flags=re.I)
				try:
					for subolddn, suboldattrs in subelements:
						# Convert the DNs to lowercase before the replacement. The cases might be mixed up if the python lib is
						# used by the connector, for example:
						#   subolddn: uid=user_test_h80,ou=TEST_H81,$LDAP_BASE
						#   self.dn: ou=test_h81,$LDAP_BASE
						#   newdn: OU=TEST_H81,ou=test_h82,$LDAP_BASE
						#   -> subnewdn: uid=user_test_h80,OU=TEST_H81,ou=test_h82,$LDAP_BASE
						subnew_position = pattern.sub(dn2str(str2dn(self.lo.parentDn(subolddn))), newdn)
						subnewdn = dn2str(str2dn(subolddn)[:1] + str2dn(subnew_position))
						ud.debug(ud.ADMIN, ud.INFO, 'move: subelement %r to %r' % (subolddn, subnewdn))

						submodule = univention.admin.modules.identifyOne(subolddn, suboldattrs)
						submodule = univention.admin.modules.get(submodule)
						subobject = univention.admin.objects.get(submodule, None, self.lo, position='', dn=subolddn)
						if not subobject or not (univention.admin.modules.supports(submodule, 'move') or univention.admin.modules.supports(submodule, 'subtree_move')):
							subold_rdn = '+'.join(explode_rdn(subolddn, 1))
							raise univention.admin.uexceptions.invalidOperation(_('Unable to move object %(name)s (%(type)s) in subtree, trying to revert changes.') % {'name': subold_rdn, 'type': univention.admin.modules.identifyOne(subolddn, suboldattrs)})
						to_be_moved.append((subobject, subolddn, subnewdn))

					for subobject, subolddn, subnewdn in to_be_moved:
						subobject.open()
						subobject.move(subnewdn)
						moved.append((subolddn, subnewdn))

					univention.admin.objects.get(univention.admin.modules.get(self.module), None, self.lo, position='', dn=self.dn).remove()
					self._delete_temporary_ou_if_empty(temporary_ou)
				except BaseException:
					ud.debug(ud.ADMIN, ud.ERROR, 'move: subtree move failed, trying to move back.')
					position = univention.admin.uldap.position(self.lo.base)
					position.setDn(self.lo.parentDn(olddn))
					for subolddn, subnewdn in moved:
						submodule = univention.admin.modules.identifyOne(subnewdn, self.lo.get(subnewdn))
						submodule = univention.admin.modules.get(submodule)
						subobject = univention.admin.objects.get(submodule, None, self.lo, position='', dn=subnewdn)
						subobject.open()
						subobject.move(subolddn)
					copyobject.remove()
					self._delete_temporary_ou_if_empty(temporary_ou)
					raise
				self.dn = newdn
				return newdn
			else:
				# normal move, fails on subtrees
				res = n(self._move(newdn, ignore_license=ignore_license))
				self._delete_temporary_ou_if_empty(temporary_ou)
				return res

		else:
			res = n(self._move(newdn, ignore_license=ignore_license))
			self._delete_temporary_ou_if_empty(temporary_ou)
			return res

	def move_subelements(self, olddn, newdn, subelements, ignore_license=False):  # type: (str, str, List[Tuple[str, Dict]], bool) -> List[Tuple[str, str]]
		"""
		Internal function to move all children of a container.

		:param str olddn: The old distinguished name of the parent container.
		:param str newdn: The new distinguished name of the parent container.
		:param subelements: A list of 2-tuples (old-dn, old-attrs) for each child of the parent container.
		:type subelements: tuple[str, dict]
		:param bool ignore_license: If the license is exceeded the modification may fail. Setting this to True causes license checks to be disabled.
		:returns: A list of 2-tuples (old-dn, new-dn)
		:rtype: list[tuple[str, str]]
		"""
		if subelements:
			ud.debug(ud.ADMIN, ud.INFO, 'move: found subelements, do subtree move')
			moved = []
			try:
				for subolddn, suboldattrs in subelements:
					ud.debug(ud.ADMIN, ud.INFO, 'move: subelement %s' % subolddn)
					subnewdn = re.sub('%s$' % (re.escape(olddn),), newdn, subolddn)  # FIXME: looks broken
					submodule = univention.admin.modules.identifyOne(subolddn, suboldattrs)
					submodule = univention.admin.modules.get(submodule)
					subobject = univention.admin.objects.get(submodule, None, self.lo, position='', dn=subolddn)
					if not subobject or not (univention.admin.modules.supports(submodule, 'move') or univention.admin.modules.supports(submodule, 'subtree_move')):
						subold_rdn = '+'.join(explode_rdn(subolddn, 1))
						raise univention.admin.uexceptions.invalidOperation(_('Unable to move object %(name)s (%(type)s) in subtree, trying to revert changes.') % {'name': subold_rdn, 'type': univention.admin.modules.identifyOne(subolddn, suboldattrs)})
					subobject.open()
					subobject._move(subnewdn)
					moved.append((subolddn, subnewdn))
					return moved
			except:
				ud.debug(ud.ADMIN, ud.ERROR, 'move: subtree move failed, try to move back')
				for subolddn, subnewdn in moved:
					submodule = univention.admin.modules.identifyOne(subnewdn, self.lo.get(subnewdn))
					submodule = univention.admin.modules.get(submodule)
					subobject = univention.admin.objects.get(submodule, None, self.lo, position='', dn=subnewdn)
					subobject.open()
					subobject.move(subolddn)
				raise

	def remove(self, remove_childs=0):  # type: (Union[bool, int]) -> None
		"""
		Removes this LDAP object.

		:param bool remove_childs: Specifies to remove children objects before removing this object.

		:raises: :class:`univention.admin.uexceptions.ldapError` (Operation not allowed on non-leaf: subordinate objects must be deleted first) if the object contains childrens and *remove_childs* is False.
		:raises: :class:`univention.admin.uexceptions.invalidOperation` if objects of this type do not support to be removed.
		:raises: :class:`univention.admin.uexceptions.noObject` if the object does not exists.
		"""
		if not univention.admin.modules.supports(self.module, 'remove'):
			raise univention.admin.uexceptions.invalidOperation(_('Objects of the "%s" object type can not be removed.') % (self.module,))

		if not self.dn or not self.lo.get(self.dn):
			raise univention.admin.uexceptions.noObject(self.dn)

		if self.lo.compare_dn(self.dn, self.lo.whoami()):
			raise univention.admin.uexceptions.invalidOperation(_('The own object cannot be removed.'))

		return self._remove(remove_childs)

	def get_gid_for_primary_group(self):  # type: () -> str
		"""
		Return the numerical group ID of the primary group.

		:returns: The numerical group ID as a string or "99999" if no primary group is declared.
		:rtype: str
		:raises univention.admin.uexceptions.primaryGroup: if the object has no primary group.
		"""
		gidNum = '99999'
		if self['primaryGroup']:
			try:
				gidNum = self.lo.getAttr(self['primaryGroup'], 'gidNumber', required=True)[0]
			except ldap.NO_SUCH_OBJECT:
				raise univention.admin.uexceptions.primaryGroup(self['primaryGroup'])
		return gidNum

	def get_sid_for_primary_group(self):  # type: () -> str
		"""
		Return the Windows security ID for the primary group.

		:returns: The security identifier of the primary group.
		:rtype: str
		:raises univention.admin.uexceptions.primaryGroup: if the object has no primary group.
		"""
		try:
			sidNum = self.lo.getAttr(self['primaryGroup'], 'sambaSID', required=True)[0]
		except ldap.NO_SUCH_OBJECT:
			raise univention.admin.uexceptions.primaryGroupWithoutSamba(self['primaryGroup'])
		return sidNum

	def _ldap_pre_ready(self):  # type: () -> None
		"""Hook which is called before :func:`univention.admin.handlers.simpleLdap.ready`."""
		pass

	def _ldap_pre_create(self):  # type: () -> None
		"""Hook which is called before the object creation."""
		self.dn = self._ldap_dn()

	def _ldap_dn(self):  # type: () -> str
		"""
		Builds the LDAP DN of the object before creation by using the identifying properties to build the RDN.

		:returns: the distringuised name.
		:rtype: str
		"""
		identifier = []
		for name, prop in self.descriptions.items():
			if prop.identifies:
				identifier.append((self.mapping.mapName(name), self.mapping.mapValue(name, self.info[name]), 2))
		return '%s,%s' % (dn2str([identifier]), dn2str(str2dn(self.dn)[1:]) if self.exists() else self.position.getDn())

	def _ldap_post_create(self):  # type: () -> None
		"""Hook which is called after the object creation."""
		pass

	def _ldap_pre_modify(self):  # type: () -> None
		"""Hook which is called before the object modification."""
		pass

	def _ldap_post_modify(self):  # type: () -> None
		"""Hook which is called after the object modification."""
		pass

	def _ldap_pre_move(self, newdn):  # type: (str) -> None
		"""
		Hook which is called before the object moving.

		:param str newdn: The new distiguished name the object will be moved to.
		"""
		pass

	def _ldap_post_move(self, olddn):  # type: (str) -> None
		"""
		Hook which is called after the object moving.

		:param str olddn: The old distiguished name the object was moved from.
		"""
		pass

	def _ldap_pre_remove(self):  # type: () -> None
		"""Hook which is called before the object removal."""
		pass

	def _ldap_post_remove(self):  # type: () -> None
		"""Hook which is called after the object removal."""
		pass

	def _save_cancel(self):  # type: () -> None
		try:
			self.cancel()
		except (KeyboardInterrupt, SystemExit, SyntaxError):
			raise
		except Exception:
			ud.debug(ud.ADMIN, ud.ERROR, "cancel() failed: %s" % (traceback.format_exc(),))

	def _falsy_boolean_extended_attributes(self, info):
		m = univention.admin.modules.get(self.module)
		for prop in getattr(m, 'extended_udm_attributes', []):
			if prop.syntax == 'boolean' and not info.get(prop.name):
				info[prop.name] = '0'
		return info

	def exists(self):
		"""
		Indicates that this object exists in LDAP.

		:returns: True if the object exists in LDAP, False otherwise.
		:rtype: bool
		"""
		return self._exists

	def _validate_superordinate(self, must_exists=True):
		"""Checks if the superordinate is set to a valid :class:`univention.admin.handlers.simpleLdap` object if this module requires a superordinate.
			It is ensured that the object type of the superordinate is correct.
			It is ensured that the object lies underneath of the superordinate position.

			:raises: :class:`univention.admin.uexceptions.insufficientInformation`
		"""
		superordinate_names = set(univention.admin.modules.superordinate_names(self.module))
		if not superordinate_names:
			return  # module has no superodinates

		if not self.dn and not self.position:
			# this check existed in all modules with superordinates, so still check it here, too
			raise univention.admin.uexceptions.insufficientInformation(_('Neither DN nor position given.'))

		if not self.superordinate:
			self.superordinate = univention.admin.objects.get_superordinate(self.module, None, self.lo, self.dn or self.position.getDn())

		if not self.superordinate:
			if superordinate_names == set(['settings/cn']):
				ud.debug(ud.ADMIN, ud.WARN, 'No settings/cn superordinate was given.')
				return   # settings/cn might be misued as superordinate, don't risk currently
			if not must_exists:
				return
			raise univention.admin.uexceptions.insufficientInformation(_('No superordinate object given'))

		# check if the superordinate is of the correct object type
		if not set([self.superordinate.module]) & superordinate_names:
			raise univention.admin.uexceptions.insufficientInformation(_('The given %r superordinate is expected to be of type %s.') % (self.superordinate.module, ', '.join(superordinate_names)))

		if self.dn and not self._ensure_dn_in_subtree(self.superordinate.dn, self.lo.parentDn(self.dn)):
			raise univention.admin.uexceptions.insufficientInformation(_('The DN must be underneath of the superordinate.'))

	def _ensure_dn_in_subtree(self, parent, dn):
		"""
		Checks if the given DN is underneath of the subtree of the given parent DN.

		:param str parent: The distiguished name of the parent container.
		:param str dn: The distinguished name to check.
		:returns: True if `dn` is underneath of `parent`, False otherwise.
		:rtype: bool
		"""
		while dn:
			if self.lo.lo.compare_dn(dn, parent):
				return True
			dn = self.lo.parentDn(dn)
		return False

	def call_udm_property_hook(self, hookname, module, changes=None):  # types: (str, str, dict[str, tuple]) -> dict[str, tuple]
		"""
		Internal method to call a hook scripts of extended attributes.

		:param str hookname: The name of the hook function to call.
		:param str module: The name of the UDM module.
		:param dict changes: A list of changes.
		:returns: The (modified) list of changes.
		:rtype: dict or None
		"""
		m = univention.admin.modules.get(module.module)
		if hasattr(m, 'extended_udm_attributes'):
			for prop in m.extended_udm_attributes:
				if prop.hook is not None:
					func = getattr(prop.hook, hookname, None)
					if changes is None:
						func(module)
					else:
						changes = func(module, changes)
		return changes

	def open(self):  # type: () -> None
		"""Opens this object.

			During the initialization of this object the current set LDAP attributes are mapped into :py:attr:`info`.
			This method makes it possible to e.g. resolve external references to other objects which are not represented in the raw LDAP attributes
			of this object, for example the group memberships of a user.

			By default only the `open` hook for extended attributes is called.
			This method can be subclassed.

			.. warning::
				If this method changes anything in self.info it *must* call :py:meth:`save` afterwards.

			.. warning::
				If your are going to do any modifications (such as creating, modifying, moving, removing this object)
				this method must be called directly after the constructor and before modifying any property.
		"""
		self._open = True
		self.exceptions = []
		self.call_udm_property_hook('hook_open', self)
		self.save()

	def _remove_option(self, name):  # type: (str) -> None
		"""
		Removes the UDM option if it is set.

		:param str name: The name of the option to remove.
		"""
		if name in self.options:
			self.options.remove(name)

	def __set_options(self):  # type: () -> None
		"""Enables the UDM options of this object by evaluating the currently set LDAP object classes. If the object does not exists yet the default options are enabled."""
		self.options = []
		options = univention.admin.modules.options(self.module)
		if 'objectClass' in self.oldattr:
			ocs = set(self.oldattr['objectClass'])
			for opt, option in options.iteritems():
				if not option.disabled and option.matches(ocs) and self.__app_option_enabled(opt, option):
					self.options.append(opt)
		else:
			ud.debug(ud.ADMIN, ud.INFO, 'reset options to default by _define_options')
			self._define_options(options)

	def _define_options(self, module_options):  # type: (dict) -> None
		"""
		Enables all UDM options which are enabled by default.

		:param dict module_options: A mapping of option-name to option.
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'modules/__init__.py _define_options: reset to default options')
		for name, opt in module_options.items():
			if not opt.disabled and opt.default:
				self.options.append(name)

	def option_toggled(self, option):  # type: (str) -> bool
		"""
		Checks if an UDM option was changed.

		:param str option: The name of the option to check.
		:returns: True if the option was changed, False otherwise.
		:rtype: bool

		.. warning::
			This does not work for not yet existing objects.
		"""
		return option in set(self.options) ^ set(self.old_options)

	def policy_reference(self, *policies):
		for policy in policies:
			if not ldap.dn.is_dn(policy):
				raise univention.admin.uexceptions.valueInvalidSyntax(policy)
			try:
				if 'univentionPolicy' not in self.lo.getAttr(policy, 'objectClass', required=True):
					raise univention.admin.uexceptions.valueError('Object is not a policy', policy)
			except ldap.NO_SUCH_OBJECT:
				raise univention.admin.uexceptions.noObject('Policy does not exists', policy)
		self.policies.extend(policy for policy in policies if not any(self.lo.compare_dn(pol, policy) for pol in self.policies))

	def policy_dereference(self, *policies):
		for policy in policies:
			if not ldap.dn.is_dn(policy):
				raise univention.admin.uexceptions.valueInvalidSyntax(policy)
		self.policies = [policy for policy in self.policies if not any(self.lo.compare_dn(pol, policy) for pol in policies)]

	def policiesChanged(self):
		return set(self.oldpolicies) != set(self.policies)

	def __app_option_enabled(self, name, option):
		if option.is_app_option:
			return all(self[pname] in ('TRUE', '1', 'OK') for pname, prop in self.descriptions.iteritems() if name in prop.options and prop.syntax.name in ('AppActivatedBoolean', 'AppActivatedTrue', 'AppActivatedOK'))
		return True

	def description(self):  # type: () -> str
		"""
		Return a descriptive string for the object.
		By default the relative distinguished name is returned.

		:returns: A descriptive string or `none` if no :py:attr:`dn` is not yet set.
		:rtype: str
		"""
		if self.dn:
			return '+'.join(explode_rdn(self.dn, 1))
		return 'none'

	def _post_unmap(self, info, values):
		"""
		This method can be overwritten to define special un-map methods to map
		back from LDAP to UDM that can not be done with the default mapping API.

		:param info: The list of UDM properties.
		:param values: The list of LDAP attributes.
		:returns: The (modified) list of UDM properties.
		:rtype:
		"""
		return info

	def _post_map(self, modlist, diff):
		"""
		This method can be overwritten to define special map methods to map from
		UDM to LDAP that can not be done with the default mapping API.

		:param modlist: The list of LDAP modifications.
		:param list diff: A list of modified UDM properties.
		:returns: The (modified) list of LDAP modifications.
		:rtype:
		"""
		return modlist

	def _ldap_addlist(self):
		return []

	def _ldap_modlist(self):
		"""Builds the list of modifications when creating and modifying this object.

			It compares the old properties (:py:attr:`oldinfo`) with the new properties (:py:attr:`info`) and applies the LDAP mapping.
			Differences are added to the modlist which consists of a tuple with three items:

			("LDAP attribute-name", [old, values], [new, values])

			("LDAP attribute-name", old_value, new_value)

			("LDAP attribute-name", None, added_value)

			.. seealso:: :mod:`univention.uldap` for further information about the format of the modlist.

			This method can be overridden in a subclass to add special behavior, e.g. for properties which have no mapping defined.

			.. caution:: The final modlist used for creation of objects is mixed with the :func:`univention.admin.handlers.simpleLdap._ldap_addlist`.
					Make sure this method don't add attributes which are already set.

			:rtype: list of tuples
		"""
		self.exceptions = []

		diff_ml = self.diff()
		ml = univention.admin.mapping.mapDiff(self.mapping, diff_ml)
		ml = self._post_map(ml, diff_ml)

		if self.policiesChanged():
			policy_ocs_set = 'univentionPolicyReference' in self.oldattr.get('objectClass', [])
			if self.policies and not policy_ocs_set:
				ml.append(('objectClass', '', ['univentionPolicyReference']))
			elif not self.policies and policy_ocs_set:
				ml.append(('objectClass', 'univentionPolicyReference', ''))
			ml.append(('univentionPolicyReference', self.oldpolicies, self.policies))

		return ml

	def _create(self, response=None, serverctrls=None):
		"""Create the object. Should only be called by :func:`univention.admin.handlers.simpleLdap.create`."""
		self.exceptions = []
		self._ldap_pre_create()
		self._update_policies()
		self.call_udm_property_hook('hook_ldap_pre_create', self)

		self.set_default_values()

		# iterate over all properties and call checkLdap() of corresponding syntax
		self._call_checkLdap_on_all_property_syntaxes()

		al = self._ldap_addlist()
		al.extend(self._ldap_modlist())
		m = univention.admin.modules.get(self.module)

		# evaluate extended attributes
		ocs = set()
		for prop in getattr(m, 'extended_udm_attributes', []):
			ud.debug(ud.ADMIN, ud.INFO, 'simpleLdap._create: info[%s]:%r = %r' % (prop.name, self.has_property(prop.name), self.info.get(prop.name)))
			if prop.syntax == 'boolean' and self.info.get(prop.name) == '0':
				continue
			if self.has_property(prop.name) and self.info.get(prop.name):
				ocs.add(prop.objClass)

		module_options = univention.admin.modules.options(self.module)
		# add object classes of (especially extended) options
		for option in ['default'] + self.options:
			try:
				opt = module_options[option]
			except KeyError:
				ud.debug(ud.ADMIN, ud.INFO, '%r does not specify option %r' % (m.module, option))
				continue
			ocs |= set(opt.objectClasses)

		# remove duplicated object classes
		for i in al:
			key, val = i[0], i[-1]  # might be a triple
			if val and key.lower() == 'objectclass':
				ocs -= set([val] if isinstance(val, basestring) else val)
		if ocs:
			al.append(('objectClass', list(ocs)))

		al = self.call_udm_property_hook('hook_ldap_addlist', self, al)

		# ensure univentionObject is set
		al.append(('objectClass', ['univentionObject', ]))
		al.append(('univentionObjectType', [self.module, ]))

		ud.debug(ud.ADMIN, ud.INFO, "create object with dn: %s" % (self.dn,))
		ud.debug(ud.ADMIN, 99, 'Create dn=%r;\naddlist=%r;' % (self.dn, al))

		# if anything goes wrong we need to remove the already created object, otherwise we run into 'already exists' errors
		try:
			self.lo.add(self.dn, al, serverctrls=serverctrls, response=response)
			self._exists = True
			self._ldap_post_create()
		except:
			# ensure that there is no lock left
			exc = sys.exc_info()
			ud.debug(ud.ADMIN, ud.ERROR, "Creating %r failed: %s" % (self.dn, traceback.format_exc(),))
			try:
				self.cancel()
			except:
				ud.debug(ud.ADMIN, ud.ERROR, "Post-create: cancel() failed: %s" % (traceback.format_exc(),))
			try:
				if self._exists:  # add succeeded but _ldap_post_create failed!
					self.remove()
			except:
				ud.debug(ud.ADMIN, ud.ERROR, "Post-create: remove() failed: %s" % (traceback.format_exc(),))
			six.reraise(exc[0], exc[1], exc[2])

		self.call_udm_property_hook('hook_ldap_post_create', self)

		self.save()
		return self.dn

	def _modify(self, modify_childs=1, ignore_license=0, response=None, serverctrls=None):
		"""Modify the object. Should only be called by :func:`univention.admin.handlers.simpleLdap.modify`."""
		self.exceptions = []

		self.__prevent_ad_property_change()

		self._ldap_pre_modify()
		self._update_policies()
		self.call_udm_property_hook('hook_ldap_pre_modify', self)

		self.set_default_values()
		self._fix_app_options()

		# iterate over all properties and call checkLdap() of corresponding syntax
		self._call_checkLdap_on_all_property_syntaxes()

		ml = self._ldap_modlist()
		ml = self.call_udm_property_hook('hook_ldap_modlist', self, ml)
		ml = self._ldap_object_classes(ml)

		# FIXME: timeout without exception if objectClass of Object is not exsistant !!
		ud.debug(ud.ADMIN, 99, 'Modify dn=%r;\nmodlist=%r;\noldattr=%r;' % (self.dn, ml, self.oldattr))
		self.dn = self.lo.modify(self.dn, ml, ignore_license=ignore_license, serverctrls=serverctrls, response=response)
		if ml:
			self._write_admin_diary_modify()

		self._ldap_post_modify()
		self.call_udm_property_hook('hook_ldap_post_modify', self)

		self.save()
		return self.dn

	def set_default_values(self):  # type: () -> None
		"""Sets all the default values of all properties."""
		# Make sure all default values are set...
		for name, p in self.descriptions.items():
			# ... if property has no option or any required option is currently enabled
			if not self.has_property(name):
				continue
			set_defaults = self.set_defaults
			if not self.set_defaults and p.options and not set(self.old_options) & set(p.options):
				# set default values of properties which depend on an option but weren't activated prior modifying
				self.set_defaults = True
			try:
				if p.default(self):
					self[name]  # __getitem__ sets default value
			finally:
				self.set_defaults = set_defaults

	def _fix_app_options(self):
		# for objects with objectClass=appObject and appObjectActivated=0 we must set appObjectActivated=1
		for option, opt in getattr(univention.admin.modules.get(self.module), 'options', {}).items():
			if not opt.is_app_option or not self.option_toggled(option) or option not in self.options:
				continue
			for pname, prop in self.descriptions.items():
				if option in prop.options and prop.syntax.name in ('AppActivatedBoolean', 'AppActivatedTrue', 'AppActivatedOK'):
					self[pname] = True

	def _ldap_object_classes(self, ml):  # type: (list) -> list
		"""Detects the attributes changed in the given modlist, calculates the changes of the object class and appends it to the modlist."""
		m = univention.admin.modules.get(self.module)

		def lowerset(vals):
			return set(x.lower() for x in vals)

		ocs = lowerset(_MergedAttributes(self, ml).get_attribute('objectClass'))
		unneeded_ocs = set()  # type: Set[str]
		required_ocs = set()  # type: Set[str]

		# evaluate (extended) options
		module_options = univention.admin.modules.options(self.module)
		available_options = set(module_options.keys())
		options = set(self.options)
		if 'default' in available_options:
			options |= {'default', }
		old_options = set(self.old_options)
		if options != old_options:
			ud.debug(ud.ADMIN, ud.INFO, 'options=%r; old_options=%r' % (options, old_options))
		unavailable_options = (options - available_options) | (old_options - available_options)
		if unavailable_options:
			# Bug #46586: as we simulate legacy options, this is no longer an error
			ud.debug(ud.ADMIN, ud.INFO, '%r does not provide options: %r' % (self.module, unavailable_options))
		added_options = options - old_options - unavailable_options
		removed_options = old_options - options - unavailable_options

		# evaluate extended attributes
		for prop in getattr(m, 'extended_udm_attributes', []):
			ud.debug(ud.ADMIN, ud.INFO, 'simpleLdap._modify: extended attribute=%r  oc=%r' % (prop.name, prop.objClass))

			if self.has_property(prop.name) and self.info.get(prop.name) and (True if prop.syntax != 'boolean' else self.info.get(prop.name) != '0'):
				required_ocs |= set([prop.objClass])
				continue

			if prop.deleteObjClass:
				unneeded_ocs |= set([prop.objClass])

			# if the value is unset we need to remove the attribute completely
			if self.oldattr.get(prop.ldapMapping):
				ml = [x for x in ml if x[0].lower() != prop.ldapMapping.lower()]
				ml.append((prop.ldapMapping, self.oldattr.get(prop.ldapMapping), ''))

		unneeded_ocs |= reduce(set.union, (set(module_options[option].objectClasses) for option in removed_options), set())
		required_ocs |= reduce(set.union, (set(module_options[option].objectClasses) for option in added_options), set())

		ocs -= lowerset(unneeded_ocs)
		ocs |= lowerset(required_ocs)
		if lowerset(self.oldattr.get('objectClass', [])) == ocs:
			return ml

		ud.debug(ud.ADMIN, ud.INFO, 'OCS=%r; required=%r; removed: %r' % (ocs, required_ocs, unneeded_ocs))

		# case normalize object class names
		schema = self.lo.get_schema()
		ocs = (schema.get_obj(ldap.schema.models.ObjectClass, x) for x in ocs)
		ocs = set(x.names[0] for x in ocs if x)

		# make sure we still have a structural object class
		if not schema.get_structural_oc(ocs):
			structural_ocs = schema.get_structural_oc(unneeded_ocs)
			if not structural_ocs:
				ud.debug(ud.ADMIN, ud.ERROR, 'missing structural object class. Modify will fail.')
				return ml
			ud.debug(ud.ADMIN, ud.WARN, 'Preventing to remove last structural object class %r' % (structural_ocs,))
			ocs -= set(schema.get_obj(ldap.schema.models.ObjectClass, structural_ocs).names)

		# validate removal of object classes
		must, may = schema.attribute_types(ocs)
		allowed = set(name.lower() for attr in may.values() for name in attr.names) | set(name.lower() for attr in must.values() for name in attr.names)

		ml = [x for x in ml if x[0].lower() != 'objectclass']
		ml.append(('objectClass', self.oldattr.get('objectClass', []), list(ocs)))
		newattr = ldap.cidict.cidict(_MergedAttributes(self, ml).get_attributes())

		# make sure only attributes known by the object classes are set
		for attr, val in newattr.items():
			if not val:
				continue
			if re.sub(';binary$', '', attr.lower()) not in allowed:
				ud.debug(ud.ADMIN, ud.WARN, 'The attribute %r is not allowed by any object class.' % (attr,))
				# ml.append((attr, val, [])) # TODO: Remove the now invalid attribute instead
				return ml

		# require all MUST attributes to be set
		for attr in must.values():
			if not any(newattr.get(name) or newattr.get('%s;binary' % (name,)) for name in attr.names):
				ud.debug(ud.ADMIN, ud.WARN, 'The attribute %r is required by the current object classes.' % (attr.names,))
				return ml

		ml = [x for x in ml if x[0].lower() != 'objectclass']
		ml.append(('objectClass', self.oldattr.get('objectClass', []), list(ocs)))

		return ml

	def _move_in_subordinates(self, olddn):
		result = self.lo.search(base=self.lo.base, filter=filter_format('(&(objectclass=person)(secretary=%s))', [olddn]), attr=['dn'])
		for subordinate, attr in result:
			self.lo.modify(subordinate, [('secretary', olddn, self.dn)])

	def _move_in_groups(self, olddn):
		for group in self.oldinfo.get('groups', []) + [self.oldinfo.get('machineAccountGroup', '')]:
			if group != '':
				members = self.lo.getAttr(group, 'uniqueMember')
				newmembers = []
				for member in members:
					if dn2str(str2dn(member)).lower() not in (dn2str(str2dn(olddn)).lower(), dn2str(str2dn(self.dn)).lower(), ):
						newmembers.append(member)
				newmembers.append(self.dn)
				self.lo.modify(group, [('uniqueMember', members, newmembers)])

	def _move(self, newdn, modify_childs=1, ignore_license=0):  # type: (str, int, int) -> str
		"""Moves this object to the new DN. Should only be called by :func:`univention.admin.handlers.simpleLdap.move`."""
		self._ldap_pre_move(newdn)

		olddn = self.dn
		self.lo.rename(self.dn, newdn)
		self.dn = newdn

		try:
			self._move_in_groups(olddn)  # can be done always, will do nothing if oldinfo has no attribute 'groups'
			self._move_in_subordinates(olddn)
			self._ldap_post_move(olddn)
		except:
			# move back
			ud.debug(ud.ADMIN, ud.WARN, 'simpleLdap._move: self._ldap_post_move failed, move object back to %s' % olddn)
			self.lo.rename(self.dn, olddn)
			self.dn = olddn
			raise
		self._write_admin_diary_move(newdn)
		return self.dn

	def _write_admin_diary_move(self, position):
		self._write_admin_diary_event('MOVED', {'position': position})

	def _remove(self, remove_childs=0):  # type: (int) -> None
		"""Removes this object. Should only be called by :func:`univention.admin.handlers.simpleLdap.remove`."""
		ud.debug(ud.ADMIN, ud.INFO, 'handlers/__init__._remove() called for %r with remove_childs=%r' % (self.dn, remove_childs))
		self.exceptions = []

		if _prevent_to_change_ad_properties and self._is_synced_object():
			raise univention.admin.uexceptions.invalidOperation(_('Objects from Active Directory can not be removed.'))

		self._ldap_pre_remove()
		self.call_udm_property_hook('hook_ldap_pre_remove', self)

		if remove_childs:
			subelements = []  # type: List[Tuple[str, Dict[str, List[str]]]]
			if 'FALSE' not in self.lo.getAttr(self.dn, 'hasSubordinates'):
				ud.debug(ud.ADMIN, ud.INFO, 'handlers/__init__._remove() children of base dn %s' % (self.dn,))
				subelements = self.lo.search(base=self.dn, scope='one', attr=[])

			for subolddn, suboldattrs in subelements:
				ud.debug(ud.ADMIN, ud.INFO, 'remove: subelement %s' % (subolddn,))
				for submodule in univention.admin.modules.identify(subolddn, suboldattrs):
					subobject = submodule.object(None, self.lo, None, dn=subolddn, attributes=suboldattrs)
					subobject.open()
					try:
						subobject.remove(remove_childs)
					except univention.admin.uexceptions.base as exc:
						ud.debug(ud.ADMIN, ud.ERROR, 'remove: could not remove %r: %s: %s' % (subolddn, type(exc).__name__, exc))
					break
				else:
					ud.debug(ud.ADMIN, ud.WARN, 'remove: could not identify UDM module of %r' % (subolddn,))

		self.lo.delete(self.dn)
		self._exists = False

		self._ldap_post_remove()

		self.call_udm_property_hook('hook_ldap_post_remove', self)
		self.oldattr = {}
		self._write_admin_diary_remove()
		self.save()

	def _write_admin_diary_remove(self):
		self._write_admin_diary_event('REMOVED')

	def loadPolicyObject(self, policy_type, reset=0):  # type: (str, int) -> "simplePolicy"
		pathlist = []
		errors = 0
		pathResult = None

		ud.debug(ud.ADMIN, ud.INFO, "loadPolicyObject: policy_type: %s" % policy_type)
		policy_module = univention.admin.modules.get(policy_type)

		# overwrite property descriptions
		univention.admin.ucr_overwrite_properties(policy_module, self.lo)
		# re-build layout if there any overwrites defined
		univention.admin.ucr_overwrite_module_layout(policy_module)

		# retrieve path info from 'cn=directory,cn=univention,<current domain>' object
		try:
			pathResult = self.lo.get('cn=directory,cn=univention,' + self.position.getDomain())
			if not pathResult:
				pathResult = self.lo.get('cn=default containers,cn=univention,' + self.position.getDomain())
		except:
			errors = 1
		infoattr = "univentionPolicyObject"
		if pathResult.get(infoattr):
			for i in pathResult[infoattr]:
				try:
					self.lo.searchDn(base=i, scope='base')
					pathlist.append(i)
					ud.debug(ud.ADMIN, ud.INFO, "loadPolicyObject: added path %s" % i)
				except Exception:
					ud.debug(ud.ADMIN, ud.INFO, "loadPolicyObject: invalid path setting: %s does not exist in LDAP" % i)
					continue  # looking for next policy container
				break  # at least one item has been found; so we can stop here since only pathlist[0] is used

		if not pathlist or errors:
			policy_position = self.position
		else:
			policy_position = univention.admin.uldap.position(self.position.getBase())
			policy_path = pathlist[0]
			try:
				prefix = univention.admin.modules.policyPositionDnPrefix(policy_module)
				self.lo.searchDn(base="%s,%s" % (prefix, policy_path), scope='base')
				policy_position.setDn("%s,%s" % (prefix, policy_path))
			except:
				policy_position.setDn(policy_path)

		for dn in self.policies:
			if univention.admin.modules.recognize(policy_module, dn, self.lo.get(dn)) and self.policyObjects.get(policy_type, None) and self.policyObjects[policy_type].cloned == dn and not reset:
				return self.policyObjects[policy_type]

		for dn in self.policies:
			modules = univention.admin.modules.identify(dn, self.lo.get(dn))
			for module in modules:
				if univention.admin.modules.name(module) == policy_type:
					self.policyObjects[policy_type] = univention.admin.objects.get(module, None, self.lo, policy_position, dn=dn)
					self.policyObjects[policy_type].clone(self)
					self._init_ldap_search(self.policyObjects[policy_type])

					return self.policyObjects[policy_type]
			if not modules:
				self.policies.remove(dn)

		if not self.policyObjects.get(policy_type, None) or reset:
			self.policyObjects[policy_type] = univention.admin.objects.get(policy_module, None, self.lo, policy_position)
			self.policyObjects[policy_type].copyIdentifier(self)
			self._init_ldap_search(self.policyObjects[policy_type])

		return self.policyObjects[policy_type]

	def _init_ldap_search(self, policy):  # type: ("simplePolicy") -> None
		properties = {}  # type: Dict[str, univention.admin.property]
		if hasattr(policy, 'property_descriptions'):
			properties = policy.property_descriptions
		elif hasattr(policy, 'descriptions'):
			properties = policy.descriptions
		for pname, prop in properties.items():
			if prop.syntax.name == 'LDAP_Search':
				prop.syntax._load(self.lo)
				if prop.syntax.viewonly:
					policy.mapping.unregister(pname, False)

	def _update_policies(self):  # type: () -> None
		_d = ud.function('admin.handlers.simpleLdap._update_policies')  # noqa  # noqa: F841
		for policy_type, policy_object in self.policyObjects.items():
			ud.debug(ud.ADMIN, ud.INFO, "simpleLdap._update_policies: processing policy of type: %s" % policy_type)
			if policy_object.changes:
				ud.debug(ud.ADMIN, ud.INFO, "simpleLdap._update_policies: trying to create policy of type: %s" % policy_type)
				ud.debug(ud.ADMIN, ud.INFO, "simpleLdap._update_policies: policy_object.info=%s" % policy_object.info)
				policy_object.create()
				univention.admin.objects.replacePolicyReference(self, policy_type, policy_object.dn)

	def closePolicyObjects(self):  # type: () -> None
		self.policyObjects = {}

	def savePolicyObjects(self):  # type: () -> None
		self._update_policies()
		self.closePolicyObjects()

	def cancel(self):  # type: () -> None
		"""Cancels the object creation or modification. This method can be subclassed to revert changes for example releasing locks."""
		self._release_locks()

	def _release_locks(self):  # type: () -> None
		"""Release all temporary done locks"""
		while self.alloc:
			name, value = self.alloc.pop()[0:2]
			univention.admin.allocators.release(self.lo, self.position, name, value)

	def _confirm_locks(self):  # type: () -> None
		"""
		Confirm all temporary done locks. self.alloc should contain a 2-tuple or 3-tuple:
		(name:str, value:str) or (name:str, value:str, updateLastUsedValue:bool)
		"""
		while self.alloc:
			item = self.alloc.pop()
			name, value = item[0:2]
			updateLastUsedValue = True
			if len(item) > 2:
				updateLastUsedValue = item[2]
			univention.admin.allocators.confirm(self.lo, self.position, name, value, updateLastUsedValue=updateLastUsedValue)

	def _call_checkLdap_on_all_property_syntaxes(self):  # type: () -> None
		"""Calls checkLdap() method on every property if present.
			checkLdap() may raise an exception if the value does not match the constraints of the underlying syntax.
		"""
		properties = {}  # type: Dict[str, univention.admin.property]
		if hasattr(self, 'descriptions'):
			properties = self.descriptions
		for pname, prop in properties.items():
			if hasattr(prop.syntax, 'checkLdap'):
				if not self.exists() or self.hasChanged(pname):
					prop.syntax.checkLdap(self.lo, self.info.get(pname))

	def __prevent_ad_property_change(self):  # type: () -> None
		if not _prevent_to_change_ad_properties or not self._is_synced_object():
			return

		for key in self.descriptions:
			if self.descriptions[key].readonly_when_synced:
				value = self.info.get(key)
				oldval = self.oldinfo.get(key)
				if oldval != value:
					raise univention.admin.uexceptions.valueMayNotChange(_('key=%(key)s old=%(old)s new=%(new)s') % {'key': key, 'old': oldval, 'new': value}, property=key)

	def _is_synced_object(self):  # type: () -> bool
		"""Checks whether this object was synchronized from Active Directory to UCS."""
		flags = self.oldattr.get('univentionObjectFlag', [])
		return 'synced' in flags and 'docker' not in flags

	@classmethod
	def get_default_containers(cls, lo):
		"""
		Returns list of default containers for this module.

		:param univention.admin.uldap.access lo: UDM LDAP access object.
		"""
		containers = univention.admin.modules.defaultContainers(univention.admin.modules.get_module(cls.module))
		settings_directory = univention.admin.modules.get_module('settings/directory')
		try:
			default_containers = settings_directory.lookup(None, lo, '', required=True)[0]
		except univention.admin.uexceptions.noObject:
			return containers

		base = cls.module.split('/', 1)[0]
		if cls.module in ('shares/print', 'shares/printer', 'shares/printergroup'):
			base = 'printers'
		elif cls.module in ('computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/windows_domaincontroller'):
			base = 'domaincontroller'

		containers.extend(default_containers.info.get(base, []))
		return containers

	@classmethod
	def lookup(cls, co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):  # type: (univention.admin.uldap.config, univention.admin.uldap.access, str, str, Optional[str], str, bool, bool, int, int, Optional[List], Optional[Dict]) -> List[simpleLdap]
		"""
		Perform a LDAP search and return a list of instances.

		:param NoneType co: obsolete config
		:param univention.admin.uldap.access lo: UDM LDAP access object.
		:param str filter_s: LDAP filter string.
		:param str base: LDAP search base distinguished name.
		:param str superordinate: Distinguished name of a superordinate object.
		:param str scope: Specify the scope of the search to be one of `base`, `base+one`, `one`, `sub`, or `domain` to specify a base object, base plus one-level, one-level, subtree, or children search.
		:param bool unique: Raise an exception if more than one object matches.
		:param bool required: Raise an exception instead of returning an empty dictionary.
		:param int timeout: wait at most `timeout` seconds for a search to complete. `-1` for no limit.
		:param int sizelimit: retrieve at most `sizelimit` entries for a search. `0` for no limit.
		:param serverctrls: a list of :py:class:`ldap.controls.LDAPControl` instances sent to the server along with the LDAP request.
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		:return: A list of UDM objects.
		:rtype: list[simpleLdap]
		"""
		filter_s = cls.lookup_filter(filter_s, lo)
		if superordinate:
			filter_s = cls.lookup_filter_superordinate(filter_s, superordinate)
		filter_str = unicode(filter_s or '')
		attr = cls._ldap_attributes()
		result = []
		for dn, attrs in lo.search(filter_str, base, scope, attr, unique, required, timeout, sizelimit, serverctrls=serverctrls, response=response):
			try:
				result.append(cls(co, lo, None, dn=dn, superordinate=superordinate, attributes=attrs))
			except univention.admin.uexceptions.base as exc:
				ud.debug(ud.ADMIN, ud.ERROR, 'lookup() of object %r failed: %s' % (dn, exc))
		if required and not result:
			raise univention.admin.uexceptions.noObject('lookup(base=%r, filter_s=%r)' % (base, filter_s))
		return result

	@classmethod
	def lookup_filter(cls, filter_s=None, lo=None):  # type: (Optional[str], Optional[univention.admin.uldap.access]) -> univention.admin.filter.conjunction
		"""
		Return a LDAP filter as a UDM filter expression.

		:param str filter_s: LDAP filter string.
		:param univention.admin.uldap.access lo: UDM LDAP access object.
		:returns: A LDAP filter expression.
		:rtype: univention.admin.filter.conjunction

		See :py:meth:`lookup`.
		"""
		filter_p = cls.unmapped_lookup_filter()
		# there are instances where the lookup/lookup_filter method of an module handler is called before
		# univention.admin.modules.update() was performed. (e.g. management/univention-directory-manager-modules/univention-dnsedit)
		module = univention.admin.modules.get_module(cls.module)
		filter_p.append_unmapped_filter_string(filter_s, cls.rewrite_filter, module.mapping)
		return filter_p

	@classmethod
	def lookup_filter_superordinate(cls, filter, superordinate):
		return filter

	@classmethod
	def unmapped_lookup_filter(cls):  # type: () -> univention.admin.filter.conjunction
		"""
		Return a LDAP filter UDM filter expression.

		:returns: A LDAP filter expression.
		:rtype: univention.admin.filter.conjunction

		See :py:meth:`lookup_filter`.
		"""
		filter_conditions = []
		if cls.use_performant_ldap_search_filter:
			filter_conditions.append(univention.admin.filter.expression('univentionObjectType', cls.module, escape=True))
		else:
			object_classes = univention.admin.modules.options(cls.module).get('default', univention.admin.option()).objectClasses - {'top', 'univentionPolicy', 'univentionObjectMetadata', 'person'}
			filter_conditions.extend(univention.admin.filter.expression('objectClass', ocs) for ocs in object_classes)

		return univention.admin.filter.conjunction('&', filter_conditions)

	@classmethod
	def rewrite_filter(cls, filter, mapping):
		key = filter.variable
		# management/univention-management-console/src/univention/management/console/acl.py does not call univention.admin.modules.update()
		mod = univention.admin.modules.get_module(cls.module)
		property_ = mod.property_descriptions.get(key)
		if property_ and not isinstance(filter.value, (list, tuple)):
			if property_.multivalue:
				# special case: mutlivalue properties need to be a list when map()-ing
				filter.value = [filter.value]
			if issubclass(property_.syntax if inspect.isclass(property_.syntax) else type(property_.syntax), univention.admin.syntax.complex):
				# special case: complex syntax properties need to be a list (of lists, if multivalue)
				filter.value = [filter.value]
		elif not property_ and key == 'options' and filter.value in getattr(mod, 'options', {}):
			ocs = mod.options[filter.value]
			filter.variable = 'objectClass'
			if len(ocs.objectClasses) > 1:
				con = univention.admin.filter.conjunction('&', [univention.admin.filter.expression('objectClass', oc, escape=True) for oc in ocs.objectClasses])
				filter.transform_to_conjunction(con)
			elif ocs.objectClasses:
				filter.value = list(ocs.objectClasses)[0]
			return

		try:
			if not mapping.shouldMap(filter.variable):
				return
		except KeyError:
			return

		filter.variable = mapping.mapName(key)
		if filter.value == '*' and property_ and issubclass(property_.syntax if inspect.isclass(property_.syntax) else type(property_.syntax), (univention.admin.syntax.IStates, univention.admin.syntax.boolean)):
			# special case: properties that are represented as Checkboxes in the
			# frontend should include '(!(propertyName=*))' in the ldap filter
			# if the Checkboxe is set to False to also find objects where the property
			# is not set. In that case we don't want to map the '*' to a different value.
			pass
		else:
			filter.value = mapping.mapValue(key, filter.value)

		if isinstance(filter.value, (list, tuple)) and filter.value:
			# complex syntax
			filter.value = filter.value[0]

	@classmethod
	def identify(cls, dn, attr, canonical=False):
		ocs = set(attr.get('objectClass', []))
		required_object_classes = univention.admin.modules.options(cls.module).get('default', univention.admin.option()).objectClasses - {'top', 'univentionPolicy', 'univentionObjectMetadata', 'person'}
		return (ocs & required_object_classes) == required_object_classes

	@classmethod
	def _ldap_attributes(cls):
		return []


class simpleComputer(simpleLdap):

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes)

		self.newPrimaryGroupDn = 0
		self.oldPrimaryGroupDn = 0
		self.ip = []
		self.network_object = False
		self.old_network = 'None'
		self.__saved_dhcp_entry = None
		self.macRequest = 0
		self.ipRequest = 0
		# read-only attribute containing the FQDN of the host
		self.descriptions['fqdn'] = univention.admin.property(
			short_description='FQDN',
			long_description='',
			syntax=univention.admin.syntax.string,
			may_change=False,
		)
		self['dnsAlias'] = []  # defined here to avoid pseudo non-None value of [''] in modwizard search
		self.oldinfo['ip'] = []
		self.info['ip'] = []
		if self.exists():
			if 'aRecord' in self.oldattr:
				self.oldinfo['ip'].extend(self.oldattr['aRecord'])
				self.info['ip'].extend(self.oldattr['aRecord'])
			if 'aAAARecord' in self.oldattr:
				self.oldinfo['ip'].extend(map(lambda x: ipaddr.IPv6Address(x).exploded, self.oldattr['aAAARecord']))
				self.info['ip'].extend(map(lambda x: ipaddr.IPv6Address(x).exploded, self.oldattr['aAAARecord']))

	def getMachineSid(self, lo, position, uidNum, rid=None):
		# if rid is given, use it regardless of s4 connector
		if rid:
			searchResult = self.lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
			domainsid = searchResult[0][1]['sambaSID'][0]
			sid = domainsid + '-' + rid
			univention.admin.allocators.request(self.lo, self.position, 'sid', sid)
			return sid
		else:
			# if no rid is given, create a domain sid or local sid if connector is present
			if self.s4connector_present:
				return 'S-1-4-%s' % uidNum
			else:
				num = uidNum
				machineSid = ""
				while not machineSid or machineSid == 'None':
					try:
						machineSid = univention.admin.allocators.requestUserSid(lo, position, num)
					except univention.admin.uexceptions.noLock:
						num = str(int(num) + 1)
				return machineSid

	# HELPER
	def __ip_from_ptr(self, zoneName, relativeDomainName):
		if 'ip6' in zoneName:
			return self.__ip_from_ptr_ipv6(zoneName, relativeDomainName)
		else:
			return self.__ip_from_ptr_ipv4(zoneName, relativeDomainName)

	def __ip_from_ptr_ipv4(self, zoneName, relativeDomainName):
		return '%s.%s' % (
			'.'.join(reversed(zoneName.replace('.in-addr.arpa', '').split('.'))),
			'.'.join(reversed(relativeDomainName.split('.'))))

	def __ip_from_ptr_ipv6(self, zoneName, relativeDomainName):
		fullName = relativeDomainName + '.' + zoneName.replace('.ip6.arpa', '')
		fullName = fullName.split('.')
		fullName = [''.join(reversed(fullName[i:i + 4])) for i in xrange(0, len(fullName), 4)]
		fullName.reverse()
		return ':'.join(fullName)

	def __is_ip(self, ip):
		# return True if valid IPv4 (0.0.0.0 is allowed) or IPv6 address
		try:
			ipaddr.IPAddress(ip)
			ud.debug(ud.ADMIN, ud.INFO, 'IP[%s]? -> Yes' % ip)
			return True
		except ValueError:
			ud.debug(ud.ADMIN, ud.INFO, 'IP[%s]? -> No' % ip)
			return False

	def open(self):
		"""
		Load the computer object from LDAP.
		"""
		simpleLdap.open(self)

		self.newPrimaryGroupDn = 0
		self.oldPrimaryGroupDn = 0
		self.ip_alredy_requested = 0
		self.ip_freshly_set = False

		self.__multiip = len(self['mac']) > 1 or len(self['ip']) > 1

		self['dnsEntryZoneForward'] = []
		self['dnsEntryZoneReverse'] = []
		self['dhcpEntryZone'] = []
		self['groups'] = []
		self['dnsEntryZoneAlias'] = []

		# search forward zone and insert into the object
		if self['name']:
			tmppos = univention.admin.uldap.position(self.position.getDomain())

			searchFilter = filter_format('(&(objectClass=dNSZone)(relativeDomainName=%s)(!(cNAMERecord=*)))', [self['name']])
			try:
				result = self.lo.search(base=tmppos.getBase(), scope='domain', filter=searchFilter, attr=['zoneName', 'aRecord', 'aAAARecord'], unique=False)

				zoneNames = []

				if result:
					for dn, attr in result:
						if 'aRecord' in attr:
							zoneNames.append((attr['zoneName'][0], attr['aRecord']))
						if 'aAAARecord' in attr:
							zoneNames.append((attr['zoneName'][0], map(lambda x: ipaddr.IPv6Address(x).exploded, attr['aAAARecord'])))

				ud.debug(ud.ADMIN, ud.INFO, 'zoneNames: %s' % zoneNames)

				if zoneNames:
					for zoneName in zoneNames:
						searchFilter = filter_format('(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=@))', [zoneName[0]])

						try:
							results = self.lo.searchDn(base=tmppos.getBase(), scope='domain', filter=searchFilter, unique=False)
						except univention.admin.uexceptions.insufficientInformation:
							raise

						ud.debug(ud.ADMIN, ud.INFO, 'results: %s' % results)
						if results:
							for result in results:
								for ip in zoneName[1]:
									self['dnsEntryZoneForward'].append([result, ip])
							ud.debug(ud.ADMIN, ud.INFO, 'dnsEntryZoneForward: %s' % str(self['dnsEntryZoneForward']))

			except univention.admin.uexceptions.insufficientInformation:
				self['dnsEntryZoneForward'] = []
				raise

			if zoneNames:
				for zoneName in zoneNames:
					searchFilter = filter_format('(&(objectClass=dNSZone)(|(PTRRecord=%s)(PTRRecord=%s.%s.)))', (self['name'], self['name'], zoneName[0]))
					try:
						results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['relativeDomainName', 'zoneName'], filter=searchFilter, unique=False)
						for dn, attr in results:
							ip = self.__ip_from_ptr(attr['zoneName'][0], attr['relativeDomainName'][0])
							if not self.__is_ip(ip):
								ud.debug(ud.ADMIN, ud.WARN, 'simpleComputer: dnsEntryZoneReverse: invalid IP address generated: %r' % (ip,))
								continue
							entry = [self.lo.parentDn(dn), ip]
							if entry not in self['dnsEntryZoneReverse']:
								self['dnsEntryZoneReverse'].append(entry)
					except univention.admin.uexceptions.insufficientInformation:
						self['dnsEntryZoneReverse'] = []
						raise
			ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: dnsEntryZoneReverse: %s' % self['dnsEntryZoneReverse'])

			if zoneNames:
				for zoneName in zoneNames:
					searchFilter = filter_format('(&(objectClass=dNSZone)(|(cNAMERecord=%s)(cNAMERecord=%s.%s.)))', (self['name'], self['name'], zoneName[0]))
					try:
						results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['relativeDomainName', 'cNAMERecord', 'zoneName'], filter=searchFilter, unique=False)
						for dn, attr in results:
							dnsAlias = attr['relativeDomainName'][0]
							self['dnsAlias'].append(dnsAlias)
							dnsAliasZoneContainer = self.lo.parentDn(dn)
							if attr['cNAMERecord'][0] == self['name']:
								dnsForwardZone = attr['zoneName'][0]
							else:
								dnsForwardZone = zoneName[0]

							entry = [dnsForwardZone, dnsAliasZoneContainer, dnsAlias]
							if entry not in self['dnsEntryZoneAlias']:
								self['dnsEntryZoneAlias'].append(entry)
					except univention.admin.uexceptions.insufficientInformation:
						self['dnsEntryZoneAlias'] = []
						raise
			ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: dnsEntryZoneAlias: %s' % self['dnsEntryZoneAlias'])

			if self['mac']:
				for macAddress in self['mac']:
					# mac address may be an empty string (Bug #21958)
					if not macAddress:
						continue

					ud.debug(ud.ADMIN, ud.INFO, 'open: DHCP; we have a mac address: %s' % macAddress)
					ethernet = 'ethernet ' + macAddress
					searchFilter = filter_format('(&(dhcpHWAddress=%s)(objectClass=univentionDhcpHost))', (ethernet,))
					ud.debug(ud.ADMIN, ud.INFO, 'open: DHCP; we search for "%s"' % searchFilter)
					try:
						results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['univentionDhcpFixedAddress'], filter=searchFilter, unique=False)
						ud.debug(ud.ADMIN, ud.INFO, 'open: DHCP; the result: "%s"' % results)
						for dn, attr in results:
							service = self.lo.parentDn(dn)
							if 'univentionDhcpFixedAddress' in attr:
								for ip in attr['univentionDhcpFixedAddress']:
									entry = (service, ip, macAddress)
									if entry not in self['dhcpEntryZone']:
										self['dhcpEntryZone'].append(entry)

							else:
								entry = (service, '', macAddress)
								if entry not in self['dhcpEntryZone']:
									self['dhcpEntryZone'].append(entry)
						ud.debug(ud.ADMIN, ud.INFO, 'open: DHCP; self[ dhcpEntryZone ] = "%s"' % self['dhcpEntryZone'])

					except univention.admin.uexceptions.insufficientInformation:
						raise

		if self.exists():
			if self.has_property('network'):
				self.old_network = self['network']

			# get groupmembership
			result = self.lo.search(base=self.lo.base, filter=filter_format('(&(objectclass=univentionGroup)(uniqueMember=%s))', [self.dn]), attr=['dn'])
			self['groups'] = [(x[0]) for x in result]

		if 'name' in self.info and 'domain' in self.info:
			self.info['fqdn'] = '%s.%s' % (self['name'], self['domain'])

	def __modify_dhcp_object(self, position, mac, ip=None):
		# identify the dhcp object with the mac address

		name = self['name']
		ud.debug(ud.ADMIN, ud.INFO, '__modify_dhcp_object: position: "%s"; name: "%s"; mac: "%s"; ip: "%s"' % (position, name, mac, ip))
		if not all((name, mac)):
			return

		ethernet = 'ethernet %s' % mac

		tmppos = univention.admin.uldap.position(self.position.getDomain())
		if not position:
			ud.debug(ud.ADMIN, ud.WARN, 'could not access network object and given position is "None", using LDAP root as position for DHCP entry')
			position = tmppos.getBase()
		results = self.lo.search(base=position, scope='domain', attr=['univentionDhcpFixedAddress'], filter=filter_format('dhcpHWAddress=%s', [ethernet]), unique=False)

		if not results:
			# if the dhcp object doesn't exists, then we create it
			# but it is possible, that the hostname for the dhcp object is already used, so we use the _uv$NUM extension

			ud.debug(ud.ADMIN, ud.INFO, 'the dhcp object with the mac address "%s" does not exists, we create one' % ethernet)

			results = self.lo.searchDn(base=position, scope='domain', filter=filter_format('(&(objectClass=univentionDhcpHost)(|(cn=%s)(cn=%s_uv*)))', (name, name)), unique=False)
			if results:
				ud.debug(ud.ADMIN, ud.INFO, 'the host "%s" already has a dhcp object, so we search for the next free uv name' % (name))
				RE = re.compile(r'cn=[^,]+_uv(\d+),')
				taken = set(int(m.group(1)) for m in (RE.match(dn) for dn in results) if m)
				n = min(set(range(max(taken) + 2)) - taken) if taken else 0
				name = '%s_uv%d' % (name, n)

			dn = 'cn=%s,%s' % (escape_dn_chars(name), position)
			self.lo.add(dn, [
				('objectClass', ['top', 'univentionObject', 'univentionDhcpHost']),
				('univentionObjectType', ['dhcp/host']),
				('cn', [name]),
				('univentionDhcpFixedAddress', [ip]),
				('dhcpHWAddress', [ethernet]),
			])
			ud.debug(ud.ADMIN, ud.INFO, 'we just added the object "%s"' % (dn,))
		else:
			# if the object already exists, we append or remove the ip address
			ud.debug(ud.ADMIN, ud.INFO, 'the dhcp object with the mac address "%s" exists, we change the ip' % ethernet)
			for dn, attr in results:
				if ip:
					if ip in attr.get('univentionDhcpFixedAddress', []):
						continue
					self.lo.modify(dn, [('univentionDhcpFixedAddress', '', ip)])
					ud.debug(ud.ADMIN, ud.INFO, 'we added the ip "%s"' % ip)
				else:
					self.lo.modify(dn, [('univentionDhcpFixedAddress', ip, '')])
					ud.debug(ud.ADMIN, ud.INFO, 'we removed the ip "%s"' % ip)

	def __rename_dns_object(self, position=None, old_name=None, new_name=None):
		for dns_line in self['dnsEntryZoneForward']:
			# dns_line may be the empty string
			if not dns_line:
				continue
			dn, ip = self.__split_dns_line(dns_line)
			if ':' in ip:  # IPv6
				results = self.lo.searchDn(base=dn, scope='domain', filter=filter_format('(&(relativeDomainName=%s)(aAAARecord=%s))', (old_name, ip)), unique=False)
			else:
				results = self.lo.searchDn(base=dn, scope='domain', filter=filter_format('(&(relativeDomainName=%s)(aRecord=%s))', (old_name, ip)), unique=False)
			for result in results:
				object = univention.admin.objects.get(univention.admin.modules.get('dns/host_record'), self.co, self.lo, position=self.position, dn=result)
				object.open()
				object['name'] = new_name
				object.modify()
		for dns_line in self['dnsEntryZoneReverse']:
			# dns_line may be the empty string
			if not dns_line:
				continue
			dn, ip = self.__split_dns_line(dns_line)
			results = self.lo.searchDn(base=dn, scope='domain', filter=filter_format('(|(pTRRecord=%s)(pTRRecord=%s.*))', (old_name, old_name)), unique=False)
			for result in results:
				object = univention.admin.objects.get(univention.admin.modules.get('dns/ptr_record'), self.co, self.lo, position=self.position, dn=result)
				object.open()
				object['ptr_record'] = [ptr_record.replace(old_name, new_name) for ptr_record in object.get('ptr_record', [])]
				object.modify()
		for entry in self['dnsEntryZoneAlias']:
			# entry may be the empty string
			if not entry:
				continue
			dnsforwardzone, dnsaliaszonecontainer, alias = entry
			results = self.lo.searchDn(base=dnsaliaszonecontainer, scope='domain', filter=filter_format('relativedomainname=%s', [alias]), unique=False)
			for result in results:
				object = univention.admin.objects.get(univention.admin.modules.get('dns/alias'), self.co, self.lo, position=self.position, dn=result)
				object.open()
				object['cname'] = '%s.%s.' % (new_name, dnsforwardzone)
				object.modify()

	def __rename_dhcp_object(self, old_name, new_name):
		module = univention.admin.modules.get('dhcp/host')
		tmppos = univention.admin.uldap.position(self.position.getDomain())
		for mac in self['mac']:
			# mac may be the empty string
			if not mac:
				continue
			ethernet = 'ethernet %s' % mac

			results = self.lo.searchDn(base=tmppos.getBase(), scope='domain', filter=filter_format('dhcpHWAddress=%s', [ethernet]), unique=False)
			if not results:
				continue
			ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: filter [ dhcpHWAddress = %s ]; results: %s' % (ethernet, results))

			for result in results:
				object = univention.admin.objects.get(module, self.co, self.lo, position=self.position, dn=result)
				object.open()
				object['host'] = object['host'].replace(old_name, new_name)
				object.modify()

	def __remove_from_dhcp_object(self, mac=None, ip=None):
		# if we got the mac address, then we remove the object
		# if we only got the ip address, we remove the ip address

		ud.debug(ud.ADMIN, ud.INFO, 'we should remove a dhcp object: mac="%s", ip="%s"' % (mac, ip))

		dn = None

		tmppos = univention.admin.uldap.position(self.position.getDomain())
		if ip and mac:
			ethernet = 'ethernet %s' % mac
			ud.debug(ud.ADMIN, ud.INFO, 'we only remove the ip "%s" from the dhcp object' % ip)
			results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['univentionDhcpFixedAddress'], filter=filter_format('(&(dhcpHWAddress=%s)(univentionDhcpFixedAddress=%s))', (ethernet, ip)), unique=False)
			for dn, attr in results:
				object = univention.admin.objects.get(univention.admin.modules.get('dhcp/host'), self.co, self.lo, position=self.position, dn=dn)
				object.open()
				if ip in object['fixedaddress']:
					ud.debug(ud.ADMIN, ud.INFO, 'fixedaddress: "%s"' % object['fixedaddress'])
					object['fixedaddress'].remove(ip)
					if len(object['fixedaddress']) == 0:
						object.remove()
					else:
						object.modify()
					dn = object.dn

		elif mac:
			ethernet = 'ethernet %s' % mac
			ud.debug(ud.ADMIN, ud.INFO, 'Remove the following mac: ethernet: "%s"' % ethernet)
			results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['univentionDhcpFixedAddress'], filter=filter_format('dhcpHWAddress=%s', [ethernet]), unique=False)
			for dn, attr in results:
				ud.debug(ud.ADMIN, ud.INFO, '... done')
				object = univention.admin.objects.get(univention.admin.modules.get('dhcp/host'), self.co, self.lo, position=self.position, dn=dn)
				object.remove()
				dn = object.dn

		elif ip:
			ud.debug(ud.ADMIN, ud.INFO, 'Remove the following ip: "%s"' % ip)
			results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['univentionDhcpFixedAddress'], filter=filter_format('univentionDhcpFixedAddress=%s', [ip]), unique=False)
			for dn, attr in results:
				ud.debug(ud.ADMIN, ud.INFO, '... done')
				object = univention.admin.objects.get(univention.admin.modules.get('dhcp/host'), self.co, self.lo, position=self.position, dn=dn)
				object.remove()
				dn = object.dn

		return dn

	def __split_dhcp_line(self, entry):
		service = entry[0]
		ip = ''
		try:
			# sanitize mac address
			#   0011.2233.4455 -> 00:11:22:33:44:55 -> is guaranteed to work together with our DHCP server
			#   __split_dhcp_line may be used outside of UDM which means that MAC_Address.parse may not be called.
			mac = univention.admin.syntax.MAC_Address.parse(entry[-1])
			if self.__is_ip(entry[-2]):
				ip = entry[-2]
		except univention.admin.uexceptions.valueError:
			mac = ''
		return (service, ip, mac)

	def __split_dns_line(self, entry):
		zone = entry[0]
		if len(entry) > 1:
			ip = self.__is_ip(entry[1]) and entry[1] or None
		else:
			ip = None

		ud.debug(ud.ADMIN, ud.INFO, 'Split entry %s into zone %s and ip %s' % (entry, zone, ip))
		return (zone, ip)

	def __remove_dns_reverse_object(self, name, dnsEntryZoneReverse, ip):
		def modify(rdn, zoneDN):
			zone_name = zoneDN.split('=')[1].split(',')[0]
			for dn, attributes in self.lo.search(scope='domain', attr=['pTRRecord'], filter=filter_format('(&(relativeDomainName=%s)(zoneName=%s))', (rdn, zone_name))):
				if len(attributes['pTRRecord']) == 1:
					self.lo.delete('relativeDomainName=%s,%s' % (escape_dn_chars(rdn), zoneDN))
				else:
					for dn2, attributes2 in self.lo.search(scope='domain', attr=['zoneName'], filter=filter_format('(&(relativeDomainName=%s)(objectClass=dNSZone))', [name]), unique=False):
						self.lo.modify(dn, [('pTRRecord', '%s.%s.' % (name, attributes2['zoneName'][0]), '')])

				zone = univention.admin.handlers.dns.reverse_zone.object(self.co, self.lo, self.position, zoneDN)
				zone.open()
				zone.modify()

		ud.debug(ud.ADMIN, ud.INFO, 'we should remove a dns reverse object: dnsEntryZoneReverse="%s", name="%s", ip="%s"' % (dnsEntryZoneReverse, name, ip))
		if dnsEntryZoneReverse:
			rdn = self.calc_dns_reverse_entry_name(ip, dnsEntryZoneReverse)
			if rdn:
				modify(rdn, dnsEntryZoneReverse)

		elif ip:
			tmppos = univention.admin.uldap.position(self.position.getDomain())
			results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['zoneDn'], filter=filter_format('(&(objectClass=dNSZone)(|(pTRRecord=%s)(pTRRecord=%s.*)))', (name, name)), unique=False)
			for dn, attr in results:
				ud.debug(ud.ADMIN, ud.INFO, 'DEBUG: dn: "%s"' % dn)
				zone = self.lo.parentDn(dn)
				ud.debug(ud.ADMIN, ud.INFO, 'DEBUG: zone: "%s"' % zone)
				rdn = self.calc_dns_reverse_entry_name(ip, zone)
				ud.debug(ud.ADMIN, ud.INFO, 'DEBUG: rdn: "%s"' % rdn)
				if rdn:
					try:
						modify(rdn, zone)
					except univention.admin.uexceptions.noObject:
						pass

	def __add_dns_reverse_object(self, name, zoneDn, ip):
		ud.debug(ud.ADMIN, ud.INFO, 'we should create a dns reverse object: zoneDn="%s", name="%s", ip="%s"' % (zoneDn, name, ip))
		if name and zoneDn and ip:
			ud.debug(ud.ADMIN, ud.INFO, 'dns reverse object: start')
			hostname_list = []
			if ':' in ip:  # IPv6, e.g. ip=2001:db8:100::5
				# 0.1.8.b.d.0.1.0.0.2.ip6.arpa → 0.1.8.b.d.1.0.0.2 → ['0', '1', '8', 'b', 'd', '0', '1', '0', '0', '2', ]
				subnet = explode_dn(zoneDn, 1)[0].replace('.ip6.arpa', '').split('.')
				# ['0', '1', '8', 'b', 'd', '0', '1', '0', '0', '2', ] → ['2', '0', '0', '1', '0', 'd', 'b', '8', '1', '0', ]
				subnet.reverse()
				# ['2', '0', '0', '1', '0', 'd', 'b', '8', '1', '0', ] → ['2001', '0db8', '10', ] → '2001:0db8:10'
				subnet = ':'.join([''.join(subnet[i:i + 4]) for i in xrange(0, len(subnet), 4)])
				# '2001:db8:100:5' → '2001:0db8:0100:0000:0000:0000:0000:0005'
				ip = ipaddr.IPv6Address(ip).exploded
				if not ip.startswith(subnet):
					raise univention.admin.uexceptions.missingInformation(_('Reverse zone and IP address are incompatible.'))
				# '2001:0db8:0100:0000:0000:0000:0000:0005' → '00:0000:0000:0000:0000:0005'
				ipPart = ip[len(subnet):]
				# '00:0000:0000:0000:0000:0005' → '0000000000000000000005' → ['0', '0', …, '0', '0', '5', ]
				pointer = list(ipPart.replace(':', ''))
				# ['0', '0', …, '0', '0', '5', ] → ['5', '0', '0', …, '0', '0', ]
				pointer.reverse()
				# ['5', '0', '0', …, '0', '0', ] → '5.0.0.….0.0'
				ipPart = '.'.join(pointer)
				tmppos = univention.admin.uldap.position(self.position.getDomain())
				# check in which forward zone the ip is set
				results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['zoneName'], filter=filter_format('(&(relativeDomainName=%s)(aAAARecord=%s))', (name, ip)), unique=False)
			else:
				subnet = '%s.' % ('.'.join(reversed(explode_dn(zoneDn, 1)[0].replace('.in-addr.arpa', '').split('.'))))
				ipPart = re.sub('^%s' % (re.escape(subnet),), '', ip)
				if ipPart == ip:
					raise univention.admin.uexceptions.InvalidDNS_Information(_('Reverse zone and IP address are incompatible.'))
				ipPart = '.'.join(reversed(ipPart.split('.')))
				tmppos = univention.admin.uldap.position(self.position.getDomain())
				# check in which forward zone the ip is set
				results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['zoneName'], filter=filter_format('(&(relativeDomainName=%s)(aRecord=%s))', (name, ip)), unique=False)
			if results:
				for dn, attr in results:
					if 'zoneName' in attr:
						hostname = '%s.%s.' % (name, attr['zoneName'][0])
						if hostname not in hostname_list:
							hostname_list.append(hostname)

			if not hostname_list:
				ud.debug(ud.ADMIN, ud.ERROR, 'Could not determine host record for name=%r, ip=%r. Not creating pointer record.' % (name, ip))
				return

			# check if the object exists
			results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['dn'], filter=filter_format('(&(relativeDomainName=%s)(%s=%s))', [ipPart] + list(str2dn(zoneDn)[0][0][:2])), unique=False)
			if not results:
				self.lo.add('relativeDomainName=%s,%s' % (escape_dn_chars(ipPart), zoneDn), [
					('objectClass', ['top', 'dNSZone', 'univentionObject']),
					('univentionObjectType', ['dns/ptr_record']),
					('zoneName', [explode_dn(zoneDn, 1)[0]]),
					('relativeDomainName', [ipPart]),
					('PTRRecord', hostname_list)
				])

				# update Serial
				zone = univention.admin.handlers.dns.reverse_zone.object(self.co, self.lo, self.position, zoneDn)
				zone.open()
				zone.modify()

	def __remove_dns_forward_object(self, name, zoneDn, ip=None):
		ud.debug(ud.ADMIN, ud.INFO, 'we should remove a dns forward object: zoneDn="%s", name="%s", ip="%s"' % (zoneDn, name, ip))
		if name:
			# check if dns forward object has more than one ip address
			if not ip:
				if zoneDn:
					self.lo.delete('relativeDomainName=%s,%s' % (escape_dn_chars(name), zoneDn))
					zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, zoneDn)
					zone.open()
					zone.modify()
			else:
				if zoneDn:
					base = zoneDn
				else:
					tmppos = univention.admin.uldap.position(self.position.getDomain())
					base = tmppos.getBase()
				ud.debug(ud.ADMIN, ud.INFO, 'search base="%s"' % base)
				if ':' in ip:
					ip = ipaddr.IPv6Address(ip).exploded
					(attrEdit, attrOther, ) = ('aAAARecord', 'aRecord', )
				else:
					(attrEdit, attrOther, ) = ('aRecord', 'aAAARecord', )
				results = self.lo.search(base=base, scope='domain', attr=['aRecord', 'aAAARecord', ], filter=filter_format('(&(relativeDomainName=%s)(%s=%s))', (name, attrEdit, ip)), unique=False, required=False)
				for dn, attr in results:
					if attr[attrEdit] == [ip, ] and not attr.get(attrOther):  # the <ip> to be removed is the last on the object
						# remove the object
						self.lo.delete(dn)
						if not zoneDn:
							zone = self.lo.parentDn(dn)
						else:
							zone = zoneDn

						zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, zone)
						zone.open()
						zone.modify()
					else:
						# remove only the ip address attribute
						new_ip_list = copy.deepcopy(attr[attrEdit])
						new_ip_list.remove(ip)

						self.lo.modify(dn, [(attrEdit, attr[attrEdit], new_ip_list, ), ])

						if not zoneDn:
							zone = self.lo.parentDn(zoneDn)
						else:
							zone = zoneDn

						zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, zone)
						zone.open()
						zone.modify()

	def __add_related_ptrrecords(self, zoneDN, ip):
		if not all((zoneDN, ip)):
			return
		ptrrecord = '%s.%s.' % (self.info['name'], zoneDN.split('=')[1].split(',')[0])
		ip_split = ip.split('.')
		ip_split.reverse()
		search_filter = filter_format('(|(relativeDomainName=%s)(relativeDomainName=%s)(relativeDomainName=%s))', (ip_split[0], '.'.join(ip_split[:1]), '.'.join(ip_split[:2])))

		for dn, attributes in self.lo.search(base=zoneDN, scope='domain', attr=['pTRRecord'], filter=search_filter):
			self.lo.modify(dn, [('pTRRecord', '', ptrrecord)])

	def __remove_related_ptrrecords(self, zoneDN, ip):
		ptrrecord = '%s.%s.' % (self.info['name'], zoneDN.split('=')[1].split(',')[0])
		ip_split = ip.split('.')
		ip_split.reverse()
		search_filter = filter_format('(|(relativeDomainName=%s)(relativeDomainName=%s)(relativeDomainName=%s))', (ip_split[0], '.'.join(ip_split[:1]), '.'.join(ip_split[:2])))

		for dn, attributes in self.lo.search(base=zoneDN, scope='domain', attr=['pTRRecord'], filter=search_filter):
			if ptrrecord in attributes['pTRRecord']:
				self.lo.modify(dn, [('pTRRecord', ptrrecord, '')])

	def check_common_name_length(self):  # type: () -> None
		ud.debug(ud.ADMIN, ud.INFO, 'check_common_name_length with self["ip"] = %r and self["dnsEntryZoneForward"] = %r' % (self['ip'], self['dnsEntryZoneForward'], ))
		if len(self['ip']) > 0 and len(self['dnsEntryZoneForward']) > 0:
			for zone in self['dnsEntryZoneForward']:
				if zone == '':
					continue
				zoneName = univention.admin.uldap.explodeDn(zone[0], 1)[0]
				if len(zoneName) + len(self['name']) >= 63:
					ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: length of Common Name is too long: %d' % (len(zoneName) + len(self['name']) + 1))
					raise univention.admin.uexceptions.commonNameTooLong

	def __modify_dns_forward_object(self, name, zoneDn, new_ip, old_ip):
		ud.debug(ud.ADMIN, ud.INFO, 'we should modify a dns forward object: zoneDn="%s", name="%s", new_ip="%s", old_ip="%s"' % (zoneDn, name, new_ip, old_ip))
		zone = None
		if old_ip and new_ip:
			if not zoneDn:
				tmppos = univention.admin.uldap.position(self.position.getDomain())
				base = tmppos.getBase()
			else:
				base = zoneDn
			if ':' in old_ip:  # IPv6
				old_ip = ipaddr.IPv6Address(old_ip).exploded
				results = self.lo.search(base=base, scope='domain', attr=['aAAARecord'], filter=filter_format('(&(relativeDomainName=%s)(aAAARecord=%s))', (name, old_ip)), unique=False)
			else:
				results = self.lo.search(base=base, scope='domain', attr=['aRecord'], filter=filter_format('(&(relativeDomainName=%s)(aRecord=%s))', (name, old_ip)), unique=False)
			for dn, attr in results:
				old_aRecord = attr.get('aRecord', [])
				new_aRecord = copy.deepcopy(attr.get('aRecord', []))
				old_aAAARecord = attr.get('aAAARecord', [])
				new_aAAARecord = copy.deepcopy(attr.get('aAAARecord', []))
				if ':' in old_ip:  # IPv6
					new_aAAARecord.remove(old_ip)
				else:
					new_aRecord.remove(old_ip)
				if ':' in new_ip:  # IPv6
					new_ip = ipaddr.IPv6Address(new_ip).exploded
					if new_ip not in new_aAAARecord:
						new_aAAARecord.append(new_ip)
				else:
					if new_ip not in new_aRecord:
						new_aRecord.append(new_ip)
				modlist = []
				if ':' in old_ip or ':' in new_ip:
					if old_aAAARecord != new_aAAARecord:
						modlist.append(('aAAARecord', old_aAAARecord, new_aAAARecord, ))
				if ':' not in old_ip or ':' not in new_ip:
					if old_aRecord != new_aRecord:
						modlist.append(('aRecord', old_aRecord, new_aRecord, ))
				self.lo.modify(dn, modlist)
				if not zoneDn:
					zone = self.lo.parentDn(dn)

			if zoneDn:
				zone = zoneDn

			if zone:
				ud.debug(ud.ADMIN, ud.INFO, 'update the zon sOARecord for the zone: %s' % zone)

				zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, zone)
				zone.open()
				zone.modify()

	def __add_dns_forward_object(self, name, zoneDn, ip):
		ud.debug(ud.ADMIN, ud.INFO, 'we should add a dns forward object: zoneDn="%s", name="%s", ip="%s"' % (zoneDn, name, ip))
		if not all((name, ip, zoneDn)):
			return
		if ip.find(':') != -1:  # IPv6
			self.__add_dns_forward_object_ipv6(name, zoneDn, ipaddr.IPv6Address(ip).exploded)
		else:
			self.__add_dns_forward_object_ipv4(name, zoneDn, ip)

	def __add_dns_forward_object_ipv6(self, name, zoneDn, ip):
			ip = ipaddr.IPv6Address(ip).exploded
			results = self.lo.search(base=zoneDn, scope='domain', attr=['aAAARecord'], filter=filter_format('(&(relativeDomainName=%s)(!(cNAMERecord=*)))', (name,)), unique=False)
			if not results:
				try:
					self.lo.add('relativeDomainName=%s,%s' % (escape_dn_chars(name), zoneDn), [
						('objectClass', ['top', 'dNSZone', 'univentionObject']),
						('univentionObjectType', ['dns/host_record']),
						('zoneName', univention.admin.uldap.explodeDn(zoneDn, 1)[0]),
						('aAAARecord', [ip]),
						('relativeDomainName', [name])
					])
				except univention.admin.uexceptions.objectExists as ex:
					raise univention.admin.uexceptions.dnsAliasRecordExists(ex)
				# TODO: check if zoneDn really a forwardZone, maybe it is a container under a zone
				zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, zoneDn)
				zone.open()
				zone.modify()
			else:
				for dn, attr in results:
					if 'aAAARecord' in attr:
						new_ip_list = copy.deepcopy(attr['aAAARecord'])
						if ip not in new_ip_list:
							new_ip_list.append(ip)
							self.lo.modify(dn, [('aAAARecord', attr['aAAARecord'], new_ip_list)])
					else:
						self.lo.modify(dn, [('aAAARecord', '', ip)])

	def __add_dns_forward_object_ipv4(self, name, zoneDn, ip):
			results = self.lo.search(base=zoneDn, scope='domain', attr=['aRecord'], filter=filter_format('(&(relativeDomainName=%s)(!(cNAMERecord=*)))', (name,)), unique=False)
			if not results:
				try:
					self.lo.add('relativeDomainName=%s,%s' % (escape_dn_chars(name), zoneDn), [
						('objectClass', ['top', 'dNSZone', 'univentionObject']),
						('univentionObjectType', ['dns/host_record']),
						('zoneName', univention.admin.uldap.explodeDn(zoneDn, 1)[0]),
						('ARecord', [ip]),
						('relativeDomainName', [name])
					])
				except univention.admin.uexceptions.objectExists as ex:
					raise univention.admin.uexceptions.dnsAliasRecordExists(ex)
				# TODO: check if zoneDn really a forwardZone, maybe it is a container under a zone
				zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, zoneDn)
				zone.open()
				zone.modify()
			else:
				for dn, attr in results:
					if 'aRecord' in attr:
						new_ip_list = copy.deepcopy(attr['aRecord'])
						if ip not in new_ip_list:
							new_ip_list.append(ip)
							self.lo.modify(dn, [('aRecord', attr['aRecord'], new_ip_list)])
					else:
						self.lo.modify(dn, [('aRecord', '', ip)])

	def __add_dns_alias_object(self, name, dnsForwardZone, dnsAliasZoneContainer, alias):
		ud.debug(ud.ADMIN, ud.INFO, 'add a dns alias object: name="%s", dnsForwardZone="%s", dnsAliasZoneContainer="%s", alias="%s"' % (name, dnsForwardZone, dnsAliasZoneContainer, alias))
		alias = alias.rstrip('.')
		if name and dnsForwardZone and dnsAliasZoneContainer and alias:
			results = self.lo.search(base=dnsAliasZoneContainer, scope='domain', attr=['cNAMERecord'], filter=filter_format('relativeDomainName=%s', (alias,)), unique=False)
			if not results:
				self.lo.add('relativeDomainName=%s,%s' % (escape_dn_chars(alias), dnsAliasZoneContainer), [
					('objectClass', ['top', 'dNSZone', 'univentionObject']),
					('univentionObjectType', ['dns/alias']),
					('zoneName', univention.admin.uldap.explodeDn(dnsAliasZoneContainer, 1)[0]),
					('cNAMERecord', ["%s.%s." % (name, dnsForwardZone)]),
					('relativeDomainName', [alias])
				])

				# TODO: check if dnsAliasZoneContainer really is a forwardZone, maybe it is a container under a zone
				zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, dnsAliasZoneContainer)
				zone.open()
				zone.modify()
			else:
				# throw exception, cNAMERecord is single value
				raise univention.admin.uexceptions.dnsAliasAlreadyUsed(_('DNS alias is already in use.'))

	def __remove_dns_alias_object(self, name, dnsForwardZone, dnsAliasZoneContainer, alias=None):
		ud.debug(ud.ADMIN, ud.INFO, 'remove a dns alias object: name="%s", dnsForwardZone="%s", dnsAliasZoneContainer="%s", alias="%s"' % (name, dnsForwardZone, dnsAliasZoneContainer, alias))
		if name:
			if alias:
				if dnsAliasZoneContainer:
					self.lo.delete('relativeDomainName=%s,%s' % (escape_dn_chars(alias), dnsAliasZoneContainer))
					zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, dnsAliasZoneContainer)
					zone.open()
					zone.modify()
				elif dnsForwardZone:
					tmppos = univention.admin.uldap.position(self.position.getDomain())
					base = tmppos.getBase()
					ud.debug(ud.ADMIN, ud.INFO, 'search base="%s"' % base)
					results = self.lo.search(base=base, scope='domain', attr=['zoneName'], filter=filter_format('(&(objectClass=dNSZone)(relativeDomainName=%s)(cNAMERecord=%s.%s.))', (alias, name, dnsForwardZone)), unique=False, required=False)
					for dn, attr in results:
						# remove the object
						self.lo.delete(dn)
						# and update the SOA version number for the zone
						results = self.lo.searchDn(base=tmppos.getBase(), scope='domain', filter=filter_format('(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=@))', (attr['zoneName'][0],)), unique=False)
						for zoneDn in results:
							zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, zoneDn)
							zone.open()
							zone.modify()
					else:
						# could throw some exception
						pass
			else:
				if dnsForwardZone:
					tmppos = univention.admin.uldap.position(self.position.getDomain())
					base = tmppos.getBase()
					ud.debug(ud.ADMIN, ud.INFO, 'search base="%s"' % base)
					results = self.lo.search(base=base, scope='domain', attr=['zoneName'], filter=filter_format('(&(objectClass=dNSZone)(&(cNAMERecord=%s)(cNAMERecord=%s.%s.))', (name, name, dnsForwardZone)), unique=False, required=False)
					for dn, attr in results:
						# remove the object
						self.lo.delete(dn)
						# and update the SOA version number for the zone
						results = self.lo.searchDn(base=tmppos.getBase(), scope='domain', filter=filter_format('(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=@))', (attr['zoneName'][0],)), unique=False)
						for zoneDn in results:
							zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, zoneDn)
							zone.open()
							zone.modify()
				else:  # not enough info to remove alias entries
					pass

	def _ldap_post_modify(self):

		self.__multiip |= len(self['mac']) > 1 or len(self['ip']) > 1

		for entry in self.__changes['dhcpEntryZone']['remove']:
			ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: dhcp check: removed: %s' % (entry,))
			dn, ip, mac = self.__split_dhcp_line(entry)
			if not ip and not mac and not self.__multiip:
				mac = ''
				if self['mac']:
					mac = self['mac'][0]
				self.__remove_from_dhcp_object(mac=mac)
			else:
				self.__remove_from_dhcp_object(ip=ip, mac=mac)

		for entry in self.__changes['dhcpEntryZone']['add']:
			ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: dhcp check: added: %s' % (entry,))
			dn, ip, mac = self.__split_dhcp_line(entry)
			if not ip and not mac and not self.__multiip:
				ip, mac = ('', '')
				if self['ip']:
					ip = self['ip'][0]
				if self['mac']:
					mac = self['mac'][0]
			self.__modify_dhcp_object(dn, mac, ip=ip)

		for entry in self.__changes['dnsEntryZoneForward']['remove']:
			dn, ip = self.__split_dns_line(entry)
			if not ip and not self.__multiip:
				ip = ''
				if self['ip']:
					ip = self['ip'][0]
				self.__remove_dns_forward_object(self['name'], dn, ip)
				self.__remove_related_ptrrecords(dn, ip)
			else:
				self.__remove_dns_forward_object(self['name'], dn, ip)
				self.__remove_related_ptrrecords(dn, ip)

		for entry in self.__changes['dnsEntryZoneForward']['add']:
			ud.debug(ud.ADMIN, ud.INFO, 'we should add a dns forward object "%s"' % (entry,))
			dn, ip = self.__split_dns_line(entry)
			ud.debug(ud.ADMIN, ud.INFO, 'changed the object to dn="%s" and ip="%s"' % (dn, ip))
			if not ip and not self.__multiip:
				ud.debug(ud.ADMIN, ud.INFO, 'no multiip environment')
				ip = ''
				if self['ip']:
					ip = self['ip'][0]
				self.__add_dns_forward_object(self['name'], dn, ip)
				self.__add_related_ptrrecords(dn, ip)
			else:
				self.__add_dns_forward_object(self['name'], dn, ip)
				self.__add_related_ptrrecords(dn, ip)

		for entry in self.__changes['dnsEntryZoneReverse']['remove']:
			dn, ip = self.__split_dns_line(entry)
			if not ip and not self.__multiip:
				ip = ''
				if self['ip']:
					ip = self['ip'][0]
				self.__remove_dns_reverse_object(self['name'], dn, ip)
			else:
				self.__remove_dns_reverse_object(self['name'], dn, ip)

		for entry in self.__changes['dnsEntryZoneReverse']['add']:
			dn, ip = self.__split_dns_line(entry)
			if not ip and not self.__multiip:
				ip = ''
				if self['ip']:
					ip = self['ip'][0]
				self.__add_dns_reverse_object(self['name'], dn, ip)
			else:
				self.__add_dns_reverse_object(self['name'], dn, ip)

		for entry in self.__changes['dnsEntryZoneAlias']['remove']:
			dnsForwardZone, dnsAliasZoneContainer, alias = entry
			if not alias:
				# nonfunctional code since self[ 'alias' ] should be self[ 'dnsAlias' ], but this case does not seem to occur
				self.__remove_dns_alias_object(self['name'], dnsForwardZone, dnsAliasZoneContainer, self['alias'][0])
			else:
				self.__remove_dns_alias_object(self['name'], dnsForwardZone, dnsAliasZoneContainer, alias)

		for entry in self.__changes['dnsEntryZoneAlias']['add']:
			ud.debug(ud.ADMIN, ud.INFO, 'we should add a dns alias object "%s"' % (entry,))
			dnsForwardZone, dnsAliasZoneContainer, alias = entry
			ud.debug(ud.ADMIN, ud.INFO, 'changed the object to dnsForwardZone [%s], dnsAliasZoneContainer [%s] and alias [%s]' % (dnsForwardZone, dnsAliasZoneContainer, alias))
			if not alias:
				self.__add_dns_alias_object(self['name'], dnsForwardZone, dnsAliasZoneContainer, self['alias'][0])
			else:
				self.__add_dns_alias_object(self['name'], dnsForwardZone, dnsAliasZoneContainer, alias)

		for entry in self.__changes['mac']['remove']:
			self.__remove_from_dhcp_object(mac=entry)

		changed_ip = False
		for entry in self.__changes['ip']['remove']:
			# self.__remove_from_dhcp_object(ip=entry)
			if not self.__multiip:
				if len(self.__changes['ip']['add']) > 0:
					# we change
					single_ip = self.__changes['ip']['add'][0]
					self.__modify_dns_forward_object(self['name'], None, single_ip, entry)
					changed_ip = True
					for mac in self['mac']:
						dn = self.__remove_from_dhcp_object(ip=entry, mac=mac)
						try:
							dn = self.lo.parentDn(dn)
							self.__modify_dhcp_object(dn, mac, ip=single_ip)
						except:
							pass
				else:
					# remove the dns objects
					self.__remove_dns_forward_object(self['name'], None, entry)
			else:
				self.__remove_dns_forward_object(self['name'], None, entry)
				self.__remove_from_dhcp_object(ip=entry)

			self.__remove_dns_reverse_object(self['name'], None, entry)

		for entry in self.__changes['ip']['add']:
			if not self.__multiip:
				if self.get('dnsEntryZoneForward', []) and not changed_ip:
					self.__add_dns_forward_object(self['name'], self['dnsEntryZoneForward'][0][0], entry)
				for dnsEntryZoneReverse in self.get('dnsEntryZoneReverse', []):
					x, ip = self.__split_dns_line(dnsEntryZoneReverse)
					zoneIsV6 = explode_dn(x, 1)[0].endswith('.ip6.arpa')
					entryIsV6 = ':' in entry
					if zoneIsV6 == entryIsV6:
						self.__add_dns_reverse_object(self['name'], x, entry)

		if self.__changes['name']:
			ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: name has changed')
			self.__update_groups_after_namechange()
			self.__rename_dhcp_object(old_name=self.__changes['name'][0], new_name=self.__changes['name'][1])
			self.__rename_dns_object(position=None, old_name=self.__changes['name'][0], new_name=self.__changes['name'][1])

		if self.ipRequest == 1 and self['ip']:
			for ipAddress in self['ip']:
				if ipAddress:
					univention.admin.allocators.confirm(self.lo, self.position, 'aRecord', ipAddress)
			self.ipRequest = 0

		if self.macRequest == 1 and self['mac']:
			for macAddress in self['mac']:
				if macAddress:
					univention.admin.allocators.confirm(self.lo, self.position, 'mac', macAddress)
			self.macRequest = 0

		self.update_groups()

	def __remove_associated_domain(self, entry):
		dn, ip = self.__split_dns_line(entry)
		domain = explode_rdn(dn, 1)[0]
		if self.info.get('domain', None) == domain:
			self.info['domain'] = None

	def __set_associated_domain(self, entry):
		dn, ip = self.__split_dns_line(entry)
		domain = explode_rdn(dn, 1)[0]
		if not self.info.get('domain', None):
			self.info['domain'] = domain

	def _ldap_modlist(self):
		self.__changes = {
			'mac': {'remove': [], 'add': []},
			'ip': {'remove': [], 'add': []},
			'name': None,
			'dnsEntryZoneForward': {'remove': [], 'add': []},
			'dnsEntryZoneReverse': {'remove': [], 'add': []},
			'dnsEntryZoneAlias': {'remove': [], 'add': []},
			'dhcpEntryZone': {'remove': [], 'add': []}
		}
		ml = []
		if self.hasChanged('mac'):
			for macAddress in self.info.get('mac', []):
				if macAddress in self.oldinfo.get('mac', []):
					continue
				try:
					mac = univention.admin.allocators.request(self.lo, self.position, 'mac', value=macAddress)
					if not mac:
						self.cancel()
						raise univention.admin.uexceptions.noLock
					self.alloc.append(('mac', macAddress))
					self.__changes['mac']['add'].append(macAddress)
				except univention.admin.uexceptions.noLock:
					self.cancel()
					univention.admin.allocators.release(self.lo, self.position, "mac", macAddress)
					raise univention.admin.uexceptions.macAlreadyUsed(' %s' % macAddress)
				self.macRequest = 1
			for macAddress in self.oldinfo.get('mac', []):
				if macAddress in self.info.get('mac', []):
					continue
				self.__changes['mac']['remove'].append(macAddress)

		oldAddresses = self.oldinfo.get('ip')
		newAddresses = self.info.get('ip')
		oldARecord = []
		newARecord = []
		oldAaaaRecord = []
		newAaaaRecord = []
		if oldAddresses != newAddresses:
			if oldAddresses:
				for address in oldAddresses:
					if ':' in address:  # IPv6
						oldAaaaRecord.append(address)
					else:
						oldARecord.append(address)
			if newAddresses:
				for address in newAddresses:
					if ':' in address:  # IPv6
						newAaaaRecord.append(ipaddr.IPv6Address(address).exploded)
					else:
						newARecord.append(address)
			ml.append(('aRecord', oldARecord, newARecord, ))
			ml.append(('aAAARecord', oldAaaaRecord, newAaaaRecord, ))

		if self.hasChanged('ip'):
			for ipAddress in self['ip']:
				if not ipAddress:
					continue
				if ipAddress in self.oldinfo.get('ip'):
					continue
				if not self.ip_alredy_requested:
					try:
						IpAddr = univention.admin.allocators.request(self.lo, self.position, 'aRecord', value=ipAddress)
						if not IpAddr:
							self.cancel()
							raise univention.admin.uexceptions.noLock
						self.alloc.append(('aRecord', ipAddress))
					except univention.admin.uexceptions.noLock:
						self.cancel()
						univention.admin.allocators.release(self.lo, self.position, "aRecord", ipAddress)
						self.ip_alredy_requested = 0
						raise univention.admin.uexceptions.ipAlreadyUsed(' %s' % ipAddress)
				else:
					IpAddr = ipAddress

				self.alloc.append(('aRecord', IpAddr))

				self.ipRequest = 1
				self.__changes['ip']['add'].append(ipAddress)

			for ipAddress in self.oldinfo.get('ip', []):
				if ipAddress in self.info['ip']:
					continue
				self.__changes['ip']['remove'].append(ipAddress)

		if self.hasChanged('name'):
			ml.append(('sn', self.oldattr.get('sn', [None])[0], self['name']))
			self.__changes['name'] = (self.oldattr.get('sn', [None])[0], self['name'])

		if self.hasChanged('ip') or self.hasChanged('mac'):
			dhcp = [self.__split_dhcp_line(entry) for entry in self.info.get('dhcpEntryZone', [])]
			if len(newAddresses) <= 1 and len(self.info.get('mac', [])) == 1 and dhcp:
				# In this special case, we assume the mapping between ip/mac address to be
				# unique. The dhcp entry needs to contain the mac address (as specified by
				# the ldap search for dhcp entries), the ip address may not correspond to
				# the ip address associated with the computer ldap object, but this would
				# be erroneous anyway. We therefore update the dhcp entry to correspond to
				# the current ip and mac address. (Bug #20315)
				self.info['dhcpEntryZone'] = [
					(dn, newAddresses[0] if newAddresses else '', self.info['mac'][0])
					for (dn, ip, _mac) in dhcp
				]
			else:
				# in all other cases, we remove old dhcp entries that do not match ip or
				# mac addresses (Bug #18966)
				removedIPs = set(self.oldinfo.get('ip', [])) - set(self['ip'])
				removedMACs = set(self.oldinfo.get('mac', [])) - set(self['mac'])
				self.info['dhcpEntryZone'] = [
					(dn, ip, _mac)
					for (dn, ip, _mac) in dhcp
					if not (ip in removedIPs or _mac in removedMACs)
				]

		if self.hasChanged('dhcpEntryZone'):
			if 'dhcpEntryZone' in self.oldinfo:
				if 'dhcpEntryZone' in self.info:
					for entry in self.oldinfo['dhcpEntryZone']:
						if entry not in self.info['dhcpEntryZone']:
							self.__changes['dhcpEntryZone']['remove'].append(entry)
				else:
					for entry in self.oldinfo['dhcpEntryZone']:
						self.__changes['dhcpEntryZone']['remove'].append(entry)
			if 'dhcpEntryZone' in self.info:
				for entry in self.info['dhcpEntryZone']:
					# check if line is valid
					dn, ip, mac = self.__split_dhcp_line(entry)
					if dn and mac:
						if entry not in self.oldinfo.get('dhcpEntryZone', []):
							self.__changes['dhcpEntryZone']['add'].append(entry)
					else:
						raise univention.admin.uexceptions.invalidDhcpEntry(_('The DHCP entry for this host should contain the zone LDAP-DN, the IP address and the MAC address.'))

		if self.hasChanged('dnsEntryZoneForward'):
			for entry in self.oldinfo.get('dnsEntryZoneForward', []):
				if entry not in self.info.get('dnsEntryZoneForward', []):
					self.__changes['dnsEntryZoneForward']['remove'].append(entry)
					self.__remove_associated_domain(entry)
			for entry in self.info.get('dnsEntryZoneForward', []):
				if entry == '':
					continue
				if entry not in self.oldinfo.get('dnsEntryZoneForward', []):
					self.__changes['dnsEntryZoneForward']['add'].append(entry)
				self.__set_associated_domain(entry)

		if self.hasChanged('dnsEntryZoneReverse'):
			for entry in self.oldinfo.get('dnsEntryZoneReverse', []):
				if entry not in self.info.get('dnsEntryZoneReverse', []):
					self.__changes['dnsEntryZoneReverse']['remove'].append(entry)
			for entry in self.info.get('dnsEntryZoneReverse', []):
				if entry not in self.oldinfo.get('dnsEntryZoneReverse', []):
					self.__changes['dnsEntryZoneReverse']['add'].append(entry)

		if self.hasChanged('dnsEntryZoneAlias'):
			for entry in self.oldinfo.get('dnsEntryZoneAlias', []):
				if entry not in self.info.get('dnsEntryZoneAlias', []):
					self.__changes['dnsEntryZoneAlias']['remove'].append(entry)
			for entry in self.info.get('dnsEntryZoneAlias', []):
				# check if line is valid
				dnsForwardZone, dnsAliasZoneContainer, alias = entry
				if dnsForwardZone and dnsAliasZoneContainer and alias:
					if entry not in self.oldinfo.get('dnsEntryZoneAlias', []):
						self.__changes['dnsEntryZoneAlias']['add'].append(entry)
				else:
					raise univention.admin.uexceptions.invalidDNSAliasEntry(_('The DNS alias entry for this host should contain the zone name, the alias zone container LDAP-DN and the alias.'))

		self.__multiip = len(self['mac']) > 1 or len(self['ip']) > 1

		ml += super(simpleComputer, self)._ldap_modlist()

		return ml

	@classmethod
	def calc_dns_reverse_entry_name(cls, sip, reverseDN):
		"""
		>>> simpleComputer.calc_dns_reverse_entry_name('10.200.2.5', 'subnet=2.200.10.in-addr.arpa')
		'5'
		>>> simpleComputer.calc_dns_reverse_entry_name('10.200.2.5', 'subnet=200.10.in-addr.arpa')
		'5.2'
		>>> simpleComputer.calc_dns_reverse_entry_name('2001:db8::3', 'subnet=0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa')
		'3.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0'
		"""
		if ':' in sip:
			subnet = explode_dn(reverseDN, 1)[0].replace('.ip6.arpa', '').split('.')
			ip = list(ipaddr.IPv6Address(sip).exploded.replace(':', ''))
			return cls.calc_dns_reverse_entry_name_do(32, subnet, ip)
		else:
			subnet = explode_dn(reverseDN, 1)[0].replace('.in-addr.arpa', '').split('.')
			ip = sip.split('.')
			return cls.calc_dns_reverse_entry_name_do(4, subnet, ip)

	@staticmethod
	def calc_dns_reverse_entry_name_do(maxLength, zoneNet, ip):
		"""
		>>> simpleComputer.calc_dns_reverse_entry_name_do(3, ['2','1'], ['1','2','3'])
		'3'
		>>> simpleComputer.calc_dns_reverse_entry_name_do(3, ['1'], ['1','2','3'])
		'3.2'
		>>> simpleComputer.calc_dns_reverse_entry_name_do(4, ['0'], ['1','2','3'])
		0
		"""
		zoneNet.reverse()
		if not ip[:len(zoneNet)] == zoneNet:
			return 0
		ip.reverse()
		return '.'.join(ip[: maxLength - len(zoneNet)])

	def _ldap_pre_create(self):
		super(simpleComputer, self)._ldap_pre_create()
		self.check_common_name_length()

	def _ldap_pre_modify(self):
		self.check_common_name_length()

	def _ldap_post_create(self):
		for entry in self.__changes['dhcpEntryZone']['remove']:
			ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: dhcp check: removed: %s' % (entry,))
			dn, ip, mac = self.__split_dhcp_line(entry)
			if not ip and not mac and not self.__multiip:
				mac = ''
				if self['mac']:
					mac = self['mac'][0]
				self.__remove_from_dhcp_object(mac=mac)
			else:
				self.__remove_from_dhcp_object(ip=ip, mac=mac)

		for entry in self.__changes['dhcpEntryZone']['add']:
			ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: dhcp check: added: %s' % (entry,))
			dn, ip, mac = self.__split_dhcp_line(entry)
			if not ip and not mac and not self.__multiip:
				if len(self['ip']) > 0 and len(self['mac']) > 0:
					self.__modify_dhcp_object(dn, self['mac'][0], ip=self['ip'][0])
			else:
				self.__modify_dhcp_object(dn, mac, ip=ip)

		for entry in self.__changes['dnsEntryZoneForward']['remove']:
			dn, ip = self.__split_dns_line(entry)
			if not ip and not self.__multiip:
				ip = ''
				if self['ip']:
					ip = self['ip'][0]
				self.__remove_dns_forward_object(self['name'], dn, ip)
			else:
				self.__remove_dns_forward_object(self['name'], dn, ip)

		for entry in self.__changes['dnsEntryZoneForward']['add']:
			ud.debug(ud.ADMIN, ud.INFO, 'we should add a dns forward object "%s"' % (entry,))
			dn, ip = self.__split_dns_line(entry)
			ud.debug(ud.ADMIN, ud.INFO, 'changed the object to dn="%s" and ip="%s"' % (dn, ip))
			if not ip and not self.__multiip:
				ud.debug(ud.ADMIN, ud.INFO, 'no multiip environment')
				ip = ''
				if self['ip']:
					ip = self['ip'][0]
				self.__add_dns_forward_object(self['name'], dn, ip)
			else:
				self.__add_dns_forward_object(self['name'], dn, ip)

		for entry in self.__changes['dnsEntryZoneReverse']['remove']:
			dn, ip = self.__split_dns_line(entry)
			if not ip and not self.__multiip:
				ip = ''
				if self['ip']:
					ip = self['ip'][0]
				self.__remove_dns_reverse_object(self['name'], dn, ip)
			else:
				self.__remove_dns_reverse_object(self['name'], dn, ip)

		for entry in self.__changes['dnsEntryZoneReverse']['add']:
			dn, ip = self.__split_dns_line(entry)
			if not ip and not self.__multiip:
				ip = ''
				if self['ip']:
					ip = self['ip'][0]
				self.__add_dns_reverse_object(self['name'], dn, ip)
			else:
				self.__add_dns_reverse_object(self['name'], dn, ip)

		if not self.__multiip:
			if len(self.get('dhcpEntryZone', [])) > 0:
				dn, ip, mac = self['dhcpEntryZone'][0]
				for entry in self.__changes['mac']['add']:
					if len(self['ip']) > 0:
						self.__modify_dhcp_object(dn, entry, ip=self['ip'][0])
					else:
						self.__modify_dhcp_object(dn, entry)
				for entry in self.__changes['ip']['add']:
					if len(self['mac']) > 0:
						self.__modify_dhcp_object(dn, self['mac'][0], ip=entry)

		for entry in self.__changes['dnsEntryZoneAlias']['remove']:
			dnsForwardZone, dnsAliasZoneContainer, alias = entry
			if not alias:
				# nonfunctional code since self[ 'alias' ] should be self[ 'dnsAlias' ], but this case does not seem to occur
				self.__remove_dns_alias_object(self['name'], dnsForwardZone, dnsAliasZoneContainer, self['alias'][0])
			else:
				self.__remove_dns_alias_object(self['name'], dnsForwardZone, dnsAliasZoneContainer, alias)
		for entry in self.__changes['dnsEntryZoneAlias']['add']:
			ud.debug(ud.ADMIN, ud.INFO, 'we should add a dns alias object "%s"' % (entry,))
			dnsForwardZone, dnsAliasZoneContainer, alias = entry
			ud.debug(ud.ADMIN, ud.INFO, 'changed the object to dnsForwardZone [%s], dnsAliasZoneContainer [%s] and alias [%s]' % (dnsForwardZone, dnsAliasZoneContainer, alias))
			if not alias:
				self.__add_dns_alias_object(self['name'], dnsForwardZone, dnsAliasZoneContainer, self['alias'][0])
			else:
				self.__add_dns_alias_object(self['name'], dnsForwardZone, dnsAliasZoneContainer, alias)

		if self.ipRequest == 1 and self['ip']:
			for ipAddress in self['ip']:
				if ipAddress:
					univention.admin.allocators.confirm(self.lo, self.position, 'aRecord', ipAddress)
			self.ipRequest = 0

		if self.macRequest == 1 and self['mac']:
			for macAddress in self['mac']:
				if macAddress:
					univention.admin.allocators.confirm(self.lo, self.position, 'mac', macAddress)
			self.macRequest = 0

		self.update_groups()

	def _ldap_post_remove(self):
		if self['mac']:
			for macAddress in self['mac']:
				if macAddress:
					univention.admin.allocators.release(self.lo, self.position, 'mac', macAddress)
		if self['ip']:
			for ipAddress in self['ip']:
				if ipAddress:
					univention.admin.allocators.release(self.lo, self.position, 'aRecord', ipAddress)

		# remove computer from groups
		groups = copy.deepcopy(self['groups'])
		if self.oldinfo.get('primaryGroup'):
			groups.append(self.oldinfo.get('primaryGroup'))
		for group in groups:
			groupObject = univention.admin.objects.get(univention.admin.modules.get('groups/group'), self.co, self.lo, self.position, group)
			groupObject.fast_member_remove([self.dn], self.oldattr.get('uid', []), ignore_license=1)

	def __update_groups_after_namechange(self):
		oldname = self.oldinfo.get('name')
		newname = self.info.get('name')
		if not oldname:
			ud.debug(ud.ADMIN, ud.ERROR, '__update_groups_after_namechange: oldname is empty')
			return

		olddn = self.old_dn
		newdn = self.dn

		oldUid = '%s$' % oldname
		newUid = '%s$' % newname
		ud.debug(ud.ADMIN, ud.INFO, '__update_groups_after_namechange: olddn=%s' % olddn)
		ud.debug(ud.ADMIN, ud.INFO, '__update_groups_after_namechange: newdn=%s' % newdn)

		for group in self.info.get('groups', []):
			ud.debug(ud.ADMIN, ud.INFO, '__update_groups_after_namechange: grp=%s' % (group,))

			# Using the UDM groups/group object does not work at this point. The computer object has already been renamed.
			# During open() of groups/group each member is checked if it exists. Because the computer object with "olddn" is missing,
			# it won't show up in groupobj['hosts']. That's why the uniqueMember/memberUid updates is done directly via
			# self.lo.modify()

			oldUniqueMembers = self.lo.getAttr(group, 'uniqueMember')
			newUniqueMembers = copy.deepcopy(oldUniqueMembers)
			if olddn in newUniqueMembers:
				newUniqueMembers.remove(olddn)
			if newdn not in newUniqueMembers:
				newUniqueMembers.append(newdn)

			oldMemberUids = self.lo.getAttr(group, 'memberUid')
			newMemberUids = copy.deepcopy(oldMemberUids)
			if oldUid in newMemberUids:
				newMemberUids.remove(oldUid)
			if newUid not in newMemberUids:
				newMemberUids.append(newUid)

			self.lo.modify(group, [('uniqueMember', oldUniqueMembers, newUniqueMembers), ('memberUid', oldMemberUids, newMemberUids)])

		for group in set(self.oldinfo.get('groups', [])) - set(self.info.get('groups', [])):
			ud.debug(ud.ADMIN, ud.INFO, '__update_groups_after_namechange: removing from grp=%s' % (group,))
			self.lo.modify(group, [('uniqueMember', olddn, ''), ('memberUid', oldUid, ''), ])

	def update_groups(self):  # type: () -> None
		if not self.hasChanged('groups') and not self.oldPrimaryGroupDn and not self.newPrimaryGroupDn:
			return
		ud.debug(ud.ADMIN, ud.INFO, 'updating groups')

		old_groups = DN.set(self.oldinfo.get('groups', []))
		new_groups = DN.set(self.info.get('groups', []))

		if self.oldPrimaryGroupDn:
			old_groups += DN.set([self.oldPrimaryGroupDn])

		if self.newPrimaryGroupDn:
			new_groups.add(DN(self.newPrimaryGroupDn))

		# prevent machineAccountGroup from being removed
		if self.has_property('machineAccountGroup'):
			machine_account_group = DN.set([self['machineAccountGroup']])
			new_groups += machine_account_group
			old_groups -= machine_account_group

		for group in old_groups ^ new_groups:
			groupdn = str(group)
			groupObject = univention.admin.objects.get(univention.admin.modules.get('groups/group'), self.co, self.lo, self.position, groupdn)
			groupObject.open()
			# add this computer to the group
			hosts = DN.set(groupObject['hosts'])
			if group not in new_groups:
				# remove this computer from the group
				hosts.discard(DN(self.old_dn))
			else:
				hosts.add(DN(self.dn))
			groupObject['hosts'] = list(DN.values(hosts))
			groupObject.modify(ignore_license=1)

	def primary_group(self):  # type: () -> None
		if not self.hasChanged('primaryGroup'):
			return
		ud.debug(ud.ADMIN, ud.INFO, 'updating primary groups')

		primaryGroupNumber = self.lo.getAttr(self['primaryGroup'], 'gidNumber', required=True)
		self.newPrimaryGroupDn = self['primaryGroup']
		self.lo.modify(self.dn, [('gidNumber', 'None', primaryGroupNumber[0])])

		if 'samba' in self.options:
			primaryGroupSambaNumber = self.lo.getAttr(self['primaryGroup'], 'sambaSID', required=True)
			self.lo.modify(self.dn, [('sambaPrimaryGroupSID', 'None', primaryGroupSambaNumber[0])])

	def cleanup(self):  # type: () -> None
		self.open()
		if self['dnsEntryZoneForward']:
			for dnsEntryZoneForward in self['dnsEntryZoneForward']:
				dn, ip = self.__split_dns_line(dnsEntryZoneForward)
				try:
					self.__remove_dns_forward_object(self['name'], dn, None)
				except Exception as e:
					self.exceptions.append([_('DNS forward zone'), _('delete'), e])

		if self['dnsEntryZoneReverse']:
			for dnsEntryZoneReverse in self['dnsEntryZoneReverse']:
				dn, ip = self.__split_dns_line(dnsEntryZoneReverse)
				try:
					self.__remove_dns_reverse_object(self['name'], dn, ip)
				except Exception as e:
					self.exceptions.append([_('DNS reverse zone'), _('delete'), e])

		if self['dhcpEntryZone']:
			for dhcpEntryZone in self['dhcpEntryZone']:
				dn, ip, mac = self.__split_dhcp_line(dhcpEntryZone)
				try:
					self.__remove_from_dhcp_object(mac=mac)
				except Exception as e:
					self.exceptions.append([_('DHCP'), _('delete'), e])

		if self['dnsEntryZoneAlias']:
			for entry in self['dnsEntryZoneAlias']:
				dnsForwardZone, dnsAliasZoneContainer, alias = entry
				try:
					self.__remove_dns_alias_object(self['name'], dnsForwardZone, dnsAliasZoneContainer, alias)
				except Exception as e:
					self.exceptions.append([_('DNS Alias'), _('delete'), e])

		# remove service record entries (see Bug #26400)
		ud.debug(ud.ADMIN, ud.INFO, '_ldap_post_remove: clean up service records, host records, and IP address saved at the forward zone')
		ips = set(self['ip'] or [])
		fqdn = self['fqdn']
		fqdnDot = '%s.' % fqdn  # we might have entries w/ or w/out trailing '.'

		# iterate over all reverse zones
		for zone in self['dnsEntryZoneReverse'] or []:
			# load zone object
			ud.debug(ud.ADMIN, ud.INFO, 'clean up entries for zone: %s' % zone)
			if len(zone) < 1:
				continue
			zoneObj = univention.admin.objects.get(
				univention.admin.modules.get('dns/reverse_zone'), self.co, self.lo, self.position, dn=zone[0])
			zoneObj.open()

			# clean up nameserver records
			if 'nameserver' in zoneObj:
				if fqdnDot in zoneObj['nameserver']:
					ud.debug(
						ud.ADMIN,
						ud.INFO,
						'removing %s from dns zone %s' % (fqdnDot, zone[0]))
					# nameserver is required in reverse zone
					if len(zoneObj['nameserver']) > 1:
						zoneObj['nameserver'].remove(fqdnDot)
						zoneObj.modify()

		# iterate over all forward zones
		for zone in self['dnsEntryZoneForward'] or []:
			# load zone object
			ud.debug(ud.ADMIN, ud.INFO, 'clean up entries for zone: %s' % zone)
			if len(zone) < 1:
				continue
			zoneObj = univention.admin.objects.get(
				univention.admin.modules.get('dns/forward_zone'), self.co, self.lo, self.position, dn=zone[0])
			zoneObj.open()
			ud.debug(ud.ADMIN, ud.INFO, 'zone aRecords: %s' % zoneObj['a'])

			zone_obj_modified = False
			# clean up nameserver records
			if 'nameserver' in zoneObj:
				if fqdnDot in zoneObj['nameserver']:
					ud.debug(
						ud.ADMIN,
						ud.INFO,
						'removing %s from dns zone %s' % (fqdnDot, zone))
					# nameserver is required in forward zone
					if len(zoneObj['nameserver']) > 1:
						zoneObj['nameserver'].remove(fqdnDot)
						zone_obj_modified = True

			# clean up aRecords of zone itself
			new_entries = list(set(zoneObj['a']) - ips)
			if len(new_entries) != len(zoneObj['a']):
				ud.debug(
					ud.ADMIN,
					ud.INFO,
					'Clean up zone records:\n%s ==> %s' % (zoneObj['a'], new_entries))
				zoneObj['a'] = new_entries
				zone_obj_modified = True

			if zone_obj_modified:
				zoneObj.modify()

			# clean up service records
			for irecord in univention.admin.modules.lookup('dns/srv_record', self.co, self.lo, base=self.lo.base, scope='sub', superordinate=zoneObj):
				irecord.open()
				new_entries = [j for j in irecord['location'] if fqdn not in j and fqdnDot not in j]
				if len(new_entries) != len(irecord['location']):
					ud.debug(ud.ADMIN, ud.INFO, 'Entry found in "%s":\n%s ==> %s' % (irecord.dn, irecord['location'], new_entries))
					irecord['location'] = new_entries
					irecord.modify()

			# clean up host records (that should probably be done correctly by Samba4)
			for irecord in univention.admin.modules.lookup('dns/host_record', self.co, self.lo, base=self.lo.base, scope='sub', superordinate=zoneObj):
				irecord.open()
				new_entries = list(set(irecord['a']) - ips)
				if len(new_entries) != len(irecord['a']):
					ud.debug(ud.ADMIN, ud.INFO, 'Entry found in "%s":\n%s ==> %s' % (irecord.dn, irecord['a'], new_entries))
					irecord['a'] = new_entries
					irecord.modify()

	def __setitem__(self, key, value):
		raise_after = None
		if key == 'network':
			if self.old_network != value:
				if value and value != 'None':
					network_object = univention.admin.handlers.networks.network.object(self.co, self.lo, self.position, value)
					network_object.open()

					if not self['ip'] or len(self['ip']) < 1 or not self['ip'][0] or not univention.admin.ipaddress.ip_is_in_network(network_object['network'], network_object['netmask'], self['ip'][0]):
						if self.ip_freshly_set:
							raise_after = univention.admin.uexceptions.ipOverridesNetwork
						else:
							# get next IP
							network_object.refreshNextIp()
							self['ip'] = network_object['nextIp']
							try:
								IpAddr = univention.admin.allocators.request(self.lo, self.position, 'aRecord', value=self['ip'][0])
								self.ip_alredy_requested = 1
								self.alloc.append(('aRecord', IpAddr))
								self.ip = IpAddr
							except:
								pass

						self.network_object = network_object
					if network_object['dnsEntryZoneForward']:
						if self.has_property('ip') and self['ip'] and len(self['ip']) == 1:
							self['dnsEntryZoneForward'] = [[network_object['dnsEntryZoneForward'], self['ip'][0]], ]
					if network_object['dnsEntryZoneReverse']:
						if self.has_property('ip') and self['ip'] and len(self['ip']) == 1:
							self['dnsEntryZoneReverse'] = [[network_object['dnsEntryZoneReverse'], self['ip'][0]], ]
					if network_object['dhcpEntryZone']:
						if self.has_property('ip') and self['ip'] and len(self['ip']) == 1 and self.has_property('mac') and self['mac'] and len(self['mac']) == 1:
							self['dhcpEntryZone'] = [(network_object['dhcpEntryZone'], self['ip'][0], self['mac'][0])]
						else:
							self.__saved_dhcp_entry = network_object['dhcpEntryZone']

					self.old_network = value

		elif key == 'ip':
			self.ip_freshly_set = True
			if not self.ip or self.ip != value:
				if self.ip_alredy_requested:
					univention.admin.allocators.release(self.lo, self.position, 'aRecord', self.ip)
					self.ip_alredy_requested = 0
				if value and self.network_object:
					if self.network_object['dnsEntryZoneForward']:
						if self.has_property('ip') and self['ip'] and len(self['ip']) == 1:
							self['dnsEntryZoneForward'] = [[self.network_object['dnsEntryZoneForward'], self['ip'][0]], ]
					if self.network_object['dnsEntryZoneReverse']:
						if self.has_property('ip') and self['ip'] and len(self['ip']) == 1:
							self['dnsEntryZoneReverse'] = [[self.network_object['dnsEntryZoneReverse'], self['ip'][0]]]
					if self.network_object['dhcpEntryZone']:
						if self.has_property('ip') and self['ip'] and len(self['ip']) == 1 and self.has_property('mac') and self['mac'] and len(self['mac']) > 0:
							self['dhcpEntryZone'] = [(self.network_object['dhcpEntryZone'], self['ip'][0], self['mac'][0])]
						else:
							self.__saved_dhcp_entry = self.network_object['dhcpEntryZone']
			if not self.ip or self.ip is None:
				self.ip_freshly_set = False

		elif key == 'mac' and self.__saved_dhcp_entry:
			if self.has_property('ip') and self['ip'] and len(self['ip']) == 1 and self['mac'] and len(self['mac']) > 0:
				if isinstance(value, list):
					self['dhcpEntryZone'] = [(self.__saved_dhcp_entry, self['ip'][0], value[0])]
				else:
					self['dhcpEntryZone'] = [(self.__saved_dhcp_entry, self['ip'][0], value)]

		super(simpleComputer, self).__setitem__(key, value)
		if raise_after:
			raise raise_after


class simplePolicy(simpleLdap):

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		self.resultmode = 0

		if not hasattr(self, 'cloned'):
			self.cloned = None

		if not hasattr(self, 'changes'):
			self.changes = 0

		if not hasattr(self, 'policy_attrs'):
			self.policy_attrs = {}

		if not hasattr(self, 'referring_object_dn'):
			self.referring_object_dn = None

		simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes)

	def copyIdentifier(self, from_object):
		"""Activate the result mode and set the referring object"""

		self.resultmode = 1
		for key, property in from_object.descriptions.items():
			if property.identifies:
				for key2, property2 in self.descriptions.items():
					if property2.identifies:
						self.info[key2] = from_object.info[key]
		self.referring_object_dn = from_object.dn
		if not self.referring_object_dn:
			self.referring_object_dn = from_object.position.getDn()
		self.referring_object_position_dn = from_object.position.getDn()

	def clone(self, referring_object):
		"""Marks the object as a not existing one containing values
		retrieved by evaluating the policies for the given object"""

		self.cloned = self.dn
		self.dn = ''
		self.copyIdentifier(referring_object)

	def getIdentifier(self):
		for key, property in self.descriptions.items():
			if property.identifies and key in self.info and self.info[key]:
				return key

	def __makeUnique(self):
		_d = ud.function('admin.handlers.simplePolicy.__makeUnique')  # noqa  # noqa: F841
		identifier = self.getIdentifier()
		components = self.info[identifier].split("_uv")
		if len(components) > 1:
			try:
				n = int(components[1])
				n += 1
			except ValueError:
				n = 1
		else:
			n = 0
		self.info[identifier] = "%s_uv%d" % (components[0], n)
		ud.debug(ud.ADMIN, ud.INFO, 'simplePolicy.__makeUnique: result: %s' % self.info[identifier])

	def create(self, serverctrls=None, response=None):
		if not self.resultmode:
			return super(simplePolicy, self).create(serverctrls=serverctrls, response=response)

		self._exists = False
		try:
			self.oldinfo = {}
			dn = super(simplePolicy, self).create(serverctrls=serverctrls, response=response)
			ud.debug(ud.ADMIN, ud.INFO, 'simplePolicy.create: created object: info=%s' % (self.info))
		except univention.admin.uexceptions.objectExists:
			self.__makeUnique()
			dn = self.create()
		return dn

	def policy_result(self, faked_policy_reference=None):
		"""This method retrieves the policy values currently effective
		for this object. If the 'resultmode' is not active the evaluation
		is cancelled.

		If faked_policy_reference is given at the top object
		(referring_object_dn) this policy object temporarily referenced.

		faked_policy_reference can be a string or a list of strings."""

		if not self.resultmode:
			return

		self.polinfo_more = {}
		if not self.policy_attrs:
			policies = []
			if isinstance(faked_policy_reference, (list, tuple)):
				policies.extend(faked_policy_reference)
			elif faked_policy_reference:
				policies.append(faked_policy_reference)

			# the referring object does not exist yet
			if not self.referring_object_dn == self.referring_object_position_dn:
				result = self.lo.getPolicies(self.lo.parentDn(self.referring_object_dn), policies=policies)
			else:
				result = self.lo.getPolicies(self.referring_object_position_dn, policies=policies)
			for policy_oc, attrs in result.items():
				if univention.admin.objects.ocToType(policy_oc) == self.module:
					self.policy_attrs = attrs

		if hasattr(self, '_custom_policy_result_map'):
			self._custom_policy_result_map()
		else:
			values = {}
			for attr_name, value_dict in self.policy_attrs.items():
				values[attr_name] = value_dict['value']
				self.polinfo_more[self.mapping.unmapName(attr_name)] = value_dict

			self.polinfo = univention.admin.mapping.mapDict(self.mapping, values)
			self.polinfo = self._post_unmap(self.polinfo, values)

	def __getitem__(self, key):
		if not self.resultmode:
			if self.has_property('emptyAttributes') and self.mapping.mapName(key) and self.mapping.mapName(key) in simpleLdap.__getitem__(self, 'emptyAttributes'):
				ud.debug(ud.ADMIN, ud.INFO, 'simplePolicy.__getitem__: empty Attribute %s' % key)
				if self.descriptions[key].multivalue:
					return []
				else:
					return ''
			return simpleLdap.__getitem__(self, key)

		self.policy_result()

		if (key in self.polinfo and not (key in self.info or key in self.oldinfo)) or (key in self.polinfo_more and 'fixed' in self.polinfo_more[key] and self.polinfo_more[key]['fixed']):
			if self.descriptions[key].multivalue and not isinstance(self.polinfo[key], list):
				# why isn't this correct in the first place?
				self.polinfo[key] = [self.polinfo[key]]
			ud.debug(ud.ADMIN, ud.INFO, 'simplePolicy.__getitem__: presult: %s=%s' % (key, self.polinfo[key]))
			return self.polinfo[key]

		result = simpleLdap.__getitem__(self, key)
		ud.debug(ud.ADMIN, ud.INFO, 'simplePolicy.__getitem__: result: %s=%s' % (key, result))
		return result

	def fixedAttributes(self):
		"""
		Return effectively fixed attributes.

		:rtype: dict
		"""

		if not self.resultmode:
			return {}

		fixed_attributes = {}
		if not self.policy_attrs:
			if not self.referring_object_dn == self.referring_object_position_dn:
				result = self.lo.getPolicies(self.lo.parentDn(self.referring_object_dn))
			else:
				result = self.lo.getPolicies(self.referring_object_position_dn)
			for key, value in result.items():
				if univention.admin.objects.ocToType(key) == self.module:
					self.policy_attrs = value

		for attr_name, value_dict in self.policy_attrs.items():
			fixed_attributes[self.mapping.unmapName(attr_name)] = value_dict.get('fixed', 0)

		return fixed_attributes

	def emptyAttributes(self):
		"""
		return effectively empty attributes.

		:rtype: dict
		"""

		empty_attributes = {}

		if self.has_property('emptyAttributes'):
			for attrib in simpleLdap.__getitem__(self, 'emptyAttributes'):
				empty_attributes[self.mapping.unmapName(attrib)] = 1

		return empty_attributes

	def __setitem__(self, key, newvalue):
		if not self.resultmode:
			simpleLdap.__setitem__(self, key, newvalue)
			return

		self.policy_result()

		if key in self.polinfo:
			if self.polinfo[key] != newvalue or self.polinfo_more[key]['policy'] == self.cloned or (key in self.info and self.info[key] != newvalue):
				if self.polinfo_more[key]['fixed'] and self.polinfo_more[key]['policy'] != self.cloned:
					raise univention.admin.uexceptions.policyFixedAttribute(key)
				simpleLdap.__setitem__(self, key, newvalue)
				ud.debug(ud.ADMIN, ud.INFO, 'polinfo: set key %s to newvalue %s' % (key, newvalue))
				if self.hasChanged(key):
					ud.debug(ud.ADMIN, ud.INFO, 'polinfo: key:%s hasChanged' % (key))
					self.changes = 1
			return

		# this object did not exist before
		if not self.oldinfo:
			# if this attribute is of type boolean and the new value is equal to the default, than ignore this "change"
			if isinstance(self.descriptions[key].syntax, univention.admin.syntax.boolean):
				default = self.descriptions[key].base_default
				if type(self.descriptions[key].base_default) in (tuple, list):
					default = self.descriptions[key].base_default[0]
				if (not default and newvalue == '0') or default == newvalue:
					return

		simpleLdap.__setitem__(self, key, newvalue)
		if self.hasChanged(key):
			self.changes = 1


class _MergedAttributes(object):

	"""Evaluates old attributes and the modlist to get a new representation of the object."""

	def __init__(self, obj, modlist):
		self.obj = obj
		self.modlist = [x if len(x) == 3 else (x[0], None, x[-1]) for x in modlist]
		self.case_insensitive_attributes = ['objectClass']

	def get_attributes(self):
		attributes = set(self.obj.oldattr.keys()) | set(x[0] for x in self.modlist)
		return dict((attr, self.get_attribute(attr)) for attr in attributes)

	def get_attribute(self, attr):
		values = set(self.obj.oldattr.get(attr, []))
		# evaluate the modlist and apply all changes to the current values
		for (att, old, new) in self.modlist:
			if att.lower() != attr.lower():
				continue
			new = [] if not new else [new] if isinstance(new, basestring) else new
			old = [] if not old else [old] if isinstance(old, basestring) else old
			if not old and new:  # MOD_ADD
				values |= set(new)
			elif not new and old:  # MOD_DELETE
				values -= set(old)
			elif old and new:  # MOD_REPLACE
				values = set(new)
		return list(values)


__path__ = __import__('pkgutil').extend_path(__path__, __name__)


if __name__ == '__main__':
	import doctest
	doctest.testmod()
