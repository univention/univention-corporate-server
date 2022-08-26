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
from typing import Any, Dict, Iterable, List, Optional, Set, Text, Tuple, Union  # noqa: F401

import six
from ipaddress import ip_address, ip_network, IPv4Address, IPv6Address
import ldap
from ldap.filter import filter_format
from ldap.dn import explode_rdn, escape_dn_chars, str2dn, dn2str
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

_Attributes = Dict[Text, Union[bytes, List[bytes]]]
_Properties = Dict[Text, Union[Text, List[Text]]]

translation = univention.admin.localization.translation('univention/admin/handlers')
_ = translation.translate

# global caching variable
if configRegistry.is_true('directory/manager/samba3/legacy', False):
	s4connector_present = False  # type: Optional[bool]
elif configRegistry.is_false('directory/manager/samba3/legacy', False):
	s4connector_present = True
else:
	s4connector_present = None


def disable_ad_restrictions(disable=True):  # type: (bool) -> None
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
			If given make sure the dict contains all attributes which are required by :meth:`_ldap_attributes`.
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

	module = ''  # the name of the module
	use_performant_ldap_search_filter = False

	def __init__(self, co, lo, position, dn=u'', superordinate=None, attributes=None):  # type: (None, univention.admin.uldap.access, univention.admin.uldap.position, Text, simpleLdap, _Attributes) -> None
		self._exists = False
		self.co = None
		if isinstance(lo, univention.admin.uldap.access):
			self.lo = lo  # type: univention.admin.uldap.access
		elif isinstance(lo, univention.uldap.access):
			ud.debug(ud.ADMIN, ud.ERROR, 'using univention.uldap.access instance is deprecated. Use univention.admin.uldap.access instead.')
			self.lo = univention.admin.uldap.access(lo=lo)
		else:
			raise TypeError('lo must be instance of univention.admin.uldap.access.')

		self.dn = dn.decode('utf-8') if isinstance(dn, bytes) else dn  # type: Optional[Text]
		self.old_dn = self.dn  # type: Optional[Text]
		self.superordinate = superordinate  # type: Optional[univention.admin.handlers.simpleLdap]

		self.set_defaults = not self.dn  # this object is newly created and so we can use the default values

		self.position = position or univention.admin.uldap.position(lo.base)  # type: univention.admin.uldap.position
		if not position and self.dn:
			self.position.setDn(self.dn)
		self.info = {}  # type: _Properties
		self.oldinfo = {}  # type: _Properties
		self.policies = []  # type: List[Text]
		self.oldpolicies = []  # type: List[Text]
		self.policyObjects = {}  # type: Dict[Text, simplePolicy]
		self.__no_default = []  # type: List[Text]

		self._open = False
		self.options = []  # type: List[Text]
		self.old_options = []  # type: List[Text]
		self.alloc = []  # type: List[Union[Tuple[str, str], Tuple[str, str, bool]]] # name,value,updateLastUsedValue

		# s4connector_present is a global caching variable than can be
		# None ==> ldap has not been checked for servers with service "S4 Connector"
		# True ==> at least one server with IP address (aRecord) is present
		# False ==> no server is present
		global s4connector_present
		if s4connector_present is None:
			s4connector_present = False
			searchResult = self.lo.searchDn(u'(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=S4 Connector)(|(aRecord=*)(aAAARecord=*)))')
			s4connector_present = bool(searchResult)
		self.s4connector_present = s4connector_present

		if not univention.admin.modules.modules:
			ud.debug(ud.ADMIN, ud.WARN, 'univention.admin.modules.update() was not called')
			univention.admin.modules.update()

		m = univention.admin.modules.get(self.module)
		if not hasattr(self, 'mapping'):
			self.mapping = getattr(m, 'mapping', None)

		self.oldattr = {}  # type: _Attributes
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
			if not univention.admin.modules.virtual(self.module) and not univention.admin.modules.recognize(self.module, self.dn, self.oldattr):
				raise univention.admin.uexceptions.wrongObjectType('%s is not recognized as %s.' % (self.dn, self.module))
			oldinfo = self.mapping.unmapValues(self.oldattr)
			oldinfo = self._post_unmap(oldinfo, self.oldattr)
			oldinfo = self._falsy_boolean_extended_attributes(oldinfo)
			self.info.update(oldinfo)

		self.policies = [x.decode('utf-8') for x in self.oldattr.get('univentionPolicyReference', [])]
		self.__set_options()
		self.save()

		self._validate_superordinate(False)

	@property
	def descriptions(self):  # type: () -> Dict[Text, univention.admin.property]
		return univention.admin.modules.get(self.module).property_descriptions

	@property
	def entry_uuid(self):  # type: () -> Optional[str]
		"""The entry UUID of the object (if object exists)"""
		if 'entryUUID' in self.oldattr:
			return self.oldattr['entryUUID'][0].decode('ASCII')

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
		changes = []  # type: List[Tuple[str, Any, Any]]

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
		if not isinstance(key, six.string_types):
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

			if p.required and (not self[name] or (isinstance(self[name], list) and self[name] == [u''])):
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

	if six.PY2:
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
			if isinstance(value, six.string_types):
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

	def keys(self):  # type: () -> Iterable[str]
		"""
		Returns the names of all properties this module has.

		:returns: The list of property names.
		:rtype: list[str]
		"""
		return self.descriptions.keys()

	def items(self):  # type: () -> Iterable[Tuple[str, Any]]
		"""
		Return all items which belong to the current options - even if they are empty.

		:returns: a list of 2-tuples (udm-property-name, property-value).
		:rtype: list[tuple]

		.. warning:: In certain circumstances this sets the default value for every property (e.g. when having a new object).
		"""
		return [(key, self[key]) for key in self.keys() if self.has_property(key)]

	def create(self, serverctrls=None, response=None):  # type: (List[ldap.controls.LDAPControl], Dict[Text, Any]) -> Text
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
		except Exception:
			self._safe_cancel()
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
		return [
			name
			for name in self.descriptions
			if name in event.args
		]

	def _get_admin_diary_args(self, event):
		args = {'module': self.module}
		if event.name.startswith('UDM_GENERIC_'):
			value = self.dn
			for k, v in self.descriptions.items():
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

	def modify(self, modify_childs=True, ignore_license=False, serverctrls=None, response=None):  # type: (bool, bool, List[ldap.controls.LDAPControl], Dict[Text, Any]) -> Text
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
		except Exception:
			self._safe_cancel()
			raise

		for c in response.get('ctrls', []):
			if c.controlType == PostReadControl.controlType:
				self.oldattr.update(c.entry)
		return dn

	def _write_admin_diary_modify(self):
		self._write_admin_diary_event('MODIFIED')

	def _create_temporary_ou(self):  # type: () -> Text
		name = u'temporary_move_container_%s' % time.time()

		module = univention.admin.modules.get('container/ou')
		position = univention.admin.uldap.position(u'%s' % self.lo.base)

		temporary_object = module.object(None, self.lo, position)
		temporary_object.open()
		temporary_object['name'] = name
		temporary_object.create()

		return u'ou=%s' % ldap.dn.escape_dn_chars(name)

	def _delete_temporary_ou_if_empty(self, temporary_ou):  # type: (str) -> None
		"""
		Try to delete the organizational unit entry if it is empty.

		:param str temporary_ou: The distinguished name of the container.
		"""
		if not temporary_ou:
			return

		dn = u'%s,%s' % (temporary_ou, self.lo.base)

		module = univention.admin.modules.get('container/ou')
		temporary_object = univention.admin.modules.lookup(module, None, self.lo, scope='base', base=dn, required=True, unique=True)[0]
		temporary_object.open()
		try:
			temporary_object.remove()
		except (univention.admin.uexceptions.ldapError, ldap.NOT_ALLOWED_ON_NONLEAF):
			pass

	def move(self, newdn, ignore_license=False, temporary_ou=None):  # type: (str, bool, str) -> str
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
				pattern = re.compile(u'%s$' % (re.escape(self.dn),), flags=re.I)
				try:
					for subolddn, suboldattrs in subelements:
						# Convert the DNs to lowercase before the replacement. The cases might be mixed up if the Python lib is
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
							subold_rdn = u'+'.join(explode_rdn(subolddn, 1))
							type_ = univention.admin.modules.identifyOne(subolddn, suboldattrs)
							raise univention.admin.uexceptions.invalidOperation(_('Unable to move object %(name)s (%(type)s) in subtree, trying to revert changes.') % {
								'name': subold_rdn,
								'type': type_ and type_.module,
							})
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

	def move_subelements(self, olddn, newdn, subelements, ignore_license=False):  # type: (str, str, List[Tuple[str, Dict]], bool) -> Optional[List[Tuple[str, str]]]
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
					subnewdn = re.sub(u'%s$' % (re.escape(olddn),), newdn, subolddn)  # FIXME: looks broken
					submodule = univention.admin.modules.identifyOne(subolddn, suboldattrs)
					submodule = univention.admin.modules.get(submodule)
					subobject = univention.admin.objects.get(submodule, None, self.lo, position='', dn=subolddn)
					if not subobject or not (univention.admin.modules.supports(submodule, 'move') or univention.admin.modules.supports(submodule, 'subtree_move')):
						subold_rdn = u'+'.join(explode_rdn(subolddn, 1))
						raise univention.admin.uexceptions.invalidOperation(_('Unable to move object %(name)s (%(type)s) in subtree, trying to revert changes.') % {'name': subold_rdn, 'type': univention.admin.modules.identifyOne(subolddn, suboldattrs)})
					subobject.open()
					subobject._move(subnewdn)
					moved.append((subolddn, subnewdn))
				return moved
			except Exception:
				ud.debug(ud.ADMIN, ud.ERROR, 'move: subtree move failed, try to move back')
				for subolddn, subnewdn in moved:
					submodule = univention.admin.modules.identifyOne(subnewdn, self.lo.get(subnewdn))
					submodule = univention.admin.modules.get(submodule)
					subobject = univention.admin.objects.get(submodule, None, self.lo, position='', dn=subnewdn)
					subobject.open()
					subobject.move(subolddn)
				raise

		return None  # FIXME

	def remove(self, remove_childs=False):  # type: (bool) -> None
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
		gidNum = u'99999'
		if self['primaryGroup']:
			try:
				gidNum = self.lo.getAttr(self['primaryGroup'], 'gidNumber', required=True)[0].decode('ASCII')
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
			sidNum = self.lo.getAttr(self['primaryGroup'], 'sambaSID', required=True)[0].decode('ASCII')
		except ldap.NO_SUCH_OBJECT:
			raise univention.admin.uexceptions.primaryGroupWithoutSamba(self['primaryGroup'])
		return sidNum

	def _ldap_pre_ready(self):  # type: () -> None
		"""Hook which is called before :func:`univention.admin.handlers.simpleLdap.ready`."""
		pass

	def _ldap_pre_create(self):  # type: () -> None
		"""Hook which is called before the object creation."""
		self.dn = self._ldap_dn()
		self.request_lock('cn-uid-position', self.dn)

	def _ldap_dn(self):  # type: () -> Text
		"""
		Builds the LDAP DN of the object before creation by using the identifying properties to build the RDN.

		:returns: the distringuised name.
		:rtype: str
		"""
		identifier = [
			(self.mapping.mapName(name), self.mapping.mapValueDecoded(name, self.info[name]), 2)
			for name, prop in self.descriptions.items()
			if prop.identifies
		]
		return u'%s,%s' % (dn2str([identifier]), dn2str(str2dn(self.dn)[1:]) if self.exists() else self.position.getDn())

	def _ldap_post_create(self):  # type: () -> None
		"""Hook which is called after the object creation."""
		self._confirm_locks()

	def _ldap_pre_modify(self):  # type: () -> None
		"""Hook which is called before the object modification."""
		pass

	def _ldap_post_modify(self):  # type: () -> None
		"""Hook which is called after the object modification."""
		self._confirm_locks()

	def _ldap_pre_rename(self, newdn):  # type: (str) -> None
		"""
		Hook which is called before renaming the object.

		:param str newdn: The new distiguished name the object will be renamed to.
		"""
		self.request_lock('cn-uid-position', newdn)

	def _ldap_post_rename(self, olddn):  # type: (str) -> None
		"""
		Hook which is called after renaming the object.

		:param str olddn: The old distiguished name the object was renamed from.
		"""
		pass

	def _ldap_pre_move(self, newdn):  # type: (str) -> None
		"""
		Hook which is called before the object moving.

		:param str newdn: The new distiguished name the object will be moved to.
		"""
		self.request_lock('cn-uid-position', newdn)

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
		self._release_locks()

	def _safe_cancel(self):  # type: () -> None
		try:
			self.cancel()
		except (KeyboardInterrupt, SystemExit, SyntaxError):
			raise
		except Exception:
			ud.debug(ud.ADMIN, ud.ERROR, "cancel() failed: %s" % (traceback.format_exc(),))

	def _falsy_boolean_extended_attributes(self, info):  # type: (_Properties) -> _Properties
		m = univention.admin.modules.get(self.module)
		for prop in getattr(m, 'extended_udm_attributes', []):
			if prop.syntax == 'boolean' and not info.get(prop.name):
				info[prop.name] = u'0'
		return info

	def exists(self):  # type: () -> bool
		"""
		Indicates that this object exists in LDAP.

		:returns: True if the object exists in LDAP, False otherwise.
		:rtype: bool
		"""
		return self._exists

	def _validate_superordinate(self, must_exists=True):  # type: (bool) -> None
		"""Checks if the superordinate is set to a valid :class:`univention.admin.handlers.simpleLdap` object if this module requires a superordinate.
			It is ensured that the object type of the superordinate is correct.
			It is ensured that the object lies underneath of the superordinate position.

			:raises: :class:`univention.admin.uexceptions.insufficientInformation`

			:raises: :class:`univention.admin.uexceptions.noSuperordinate`
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
			if superordinate_names == {'settings/cn'}:
				ud.debug(ud.ADMIN, ud.WARN, 'No settings/cn superordinate was given.')
				return   # settings/cn might be misued as superordinate, don't risk currently
			if not must_exists:
				return
			raise univention.admin.uexceptions.noSuperordinate(_('No superordinate object given'))

		# check if the superordinate is of the correct object type
		if not {self.superordinate.module} & superordinate_names:
			raise univention.admin.uexceptions.insufficientInformation(_('The given %r superordinate is expected to be of type %s.') % (self.superordinate.module, ', '.join(superordinate_names)))

		if self.dn and not self._ensure_dn_in_subtree(self.superordinate.dn, self.lo.parentDn(self.dn)):
			raise univention.admin.uexceptions.insufficientInformation(_('The DN must be underneath of the superordinate.'))

	def _ensure_dn_in_subtree(self, parent, dn):  # type: (Text, Text) -> bool
		"""
		Checks if the given DN is underneath of the subtree of the given parent DN.

		:param str parent: The distiguished name of the parent container.
		:param str dn: The distinguished name to check.
		:returns: True if `dn` is underneath of `parent`, False otherwise.
		:rtype: bool
		"""
		while dn:
			if self.lo.compare_dn(dn, parent):
				return True
			dn = self.lo.parentDn(dn)
		return False

	def call_udm_property_hook(self, hookname, module, changes=None):  # types: (Text, Text, Dict[str, Tuple]) -> Dict[str, Tuple]
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
		options = univention.admin.modules.options(self.module)
		if 'objectClass' in self.oldattr:
			ocs = {x.decode('UTF-8') for x in self.oldattr['objectClass']}
			self.options = [
				opt
				for opt, option in options.items()
				if not option.disabled and option.matches(ocs) and self.__app_option_enabled(opt, option)
			]
		else:
			ud.debug(ud.ADMIN, ud.INFO, 'reset options to default by _define_options')
			self.options = []
			self._define_options(options)

	def _define_options(self, module_options):
		# type: (Dict[str, Any]) -> None
		"""
		Enables all UDM options which are enabled by default.

		:param dict module_options: A mapping of option-name to option.
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'modules/__init__.py _define_options: reset to default options')
		self.options.extend(
			name
			for name, opt in module_options.items()
			if not opt.disabled and opt.default
		)

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
				if b'univentionPolicy' not in self.lo.getAttr(policy, 'objectClass', required=True):
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
		# type: () -> bool
		return set(self.oldpolicies) != set(self.policies)

	def __app_option_enabled(self, name, option):
		if option.is_app_option:
			return all(self[pname] in ('TRUE', '1', 'OK') for pname, prop in self.descriptions.items() if name in prop.options and prop.syntax.name in ('AppActivatedBoolean', 'AppActivatedTrue', 'AppActivatedOK'))
		return True

	def description(self):  # type: () -> str
		"""
		Return a descriptive string for the object.
		By default the relative distinguished name is returned.

		:returns: A descriptive string or `none` if no :py:attr:`dn` is not yet set.
		:rtype: str
		"""
		if self.dn:
			return u'+'.join(explode_rdn(self.dn, 1))
		return u'none'

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

	def _ldap_addlist(self):  # type: () -> List[Tuple[Text, Any]]
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
		diff_ml = self.diff()
		ml = univention.admin.mapping.mapDiff(self.mapping, diff_ml)
		ml = self._post_map(ml, diff_ml)

		if self.policiesChanged():
			policy_ocs_set = b'univentionPolicyReference' in self.oldattr.get('objectClass', [])
			if self.policies and not policy_ocs_set:
				ml.append(('objectClass', b'', [b'univentionPolicyReference']))
			elif not self.policies and policy_ocs_set:
				ml.append(('objectClass', b'univentionPolicyReference', b''))
			ml.append(('univentionPolicyReference', [x.encode('UTF-8') for x in self.oldpolicies], [x.encode('UTF-8') for x in self.policies]))

		return ml

	def _create(self, response=None, serverctrls=None):
		"""Create the object. Should only be called by :func:`univention.admin.handlers.simpleLdap.create`."""
		self._ldap_pre_create()
		self._update_policies()
		self.call_udm_property_hook('hook_ldap_pre_create', self)

		self.set_default_values()

		# iterate over all properties and call checkLdap() of corresponding syntax
		self._call_checkLdap_on_all_property_syntaxes()

		al = self._ldap_addlist()
		al.extend(self._ldap_modlist())
		al = self._ldap_object_classes_add(al)
		al = self.call_udm_property_hook('hook_ldap_addlist', self, al)

		# ensure univentionObject is set
		al.append(('objectClass', [b'univentionObject', ]))
		al.append(('univentionObjectType', [self.module.encode('utf-8'), ]))

		ud.debug(ud.ADMIN, ud.INFO, "create object with dn: %s" % (self.dn,))
		ud.debug(ud.ADMIN, 99, 'Create dn=%r;\naddlist=%r;' % (self.dn, al))

		# if anything goes wrong we need to remove the already created object, otherwise we run into 'already exists' errors
		try:
			self.lo.add(self.dn, al, serverctrls=serverctrls, response=response)
			self._exists = True
			self._ldap_post_create()
		except Exception:
			# ensure that there is no lock left
			exc = sys.exc_info()
			ud.debug(ud.ADMIN, ud.PROCESS, "Creating %r failed: %r" % (self.dn, exc[1]))
			try:
				self.cancel()
			except Exception:
				ud.debug(ud.ADMIN, ud.ERROR, "Post-create: cancel() failed: %s" % (traceback.format_exc(),))
			try:
				if self._exists:  # add succeeded but _ldap_post_create failed!
					obj = univention.admin.objects.get(univention.admin.modules.get(self.module), None, self.lo, self.position, self.dn)
					obj.open()
					obj.remove()
			except Exception:
				ud.debug(ud.ADMIN, ud.ERROR, "Post-create: remove() failed: %s" % (traceback.format_exc(),))
			six.reraise(exc[0], exc[1], exc[2])

		self.call_udm_property_hook('hook_ldap_post_create', self)

		self.save()
		return self.dn

	def _ldap_object_classes_add(self, al):
		m = univention.admin.modules.get(self.module)
		# evaluate extended attributes
		ocs = set()  # type: Set[str]
		for prop in getattr(m, 'extended_udm_attributes', []):
			ud.debug(ud.ADMIN, ud.INFO, 'simpleLdap._create: info[%s]:%r = %r' % (prop.name, self.has_property(prop.name), self.info.get(prop.name)))
			if prop.syntax == 'boolean' and self.info.get(prop.name) == u'0':
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
				val_list = [val] if not isinstance(val, (tuple, list)) else val
				val_unicode = [x.decode('UTF-8') if isinstance(x, bytes) else x for x in val_list]
				ocs -= set(val_unicode)  # TODO: check six.string_types vs bytes everywhere for ocs calculations
		if ocs:
			al.append(('objectClass', [x.encode('UTF-8') for x in ocs]))

		return al

	def _modify(self, modify_childs=True, ignore_license=False, response=None, serverctrls=None):
		"""Modify the object. Should only be called by :func:`univention.admin.handlers.simpleLdap.modify`."""
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

		class wouldRename(Exception):
			@classmethod
			def on_rename(cls, dn, new_dn, ml):
				raise cls(dn, new_dn)

		# FIXME: timeout without exception if objectClass of Object is not exsistant !!
		ud.debug(ud.ADMIN, 99, 'Modify dn=%r;\nmodlist=%r;\noldattr=%r;' % (self.dn, ml, self.oldattr))
		try:
			self.dn = self.lo.modify(self.dn, ml, ignore_license=ignore_license, serverctrls=serverctrls, response=response, rename_callback=wouldRename.on_rename)
		except wouldRename as exc:
			self._ldap_pre_rename(exc.args[1])
			self.dn = self.lo.modify(self.dn, ml, ignore_license=ignore_license, serverctrls=serverctrls, response=response)
			self._ldap_post_rename(exc.args[0])
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

	def _fix_app_options(self):  # type: () -> None
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
			# type: (Iterable[str]) -> Set[str]
			return {x.lower() for x in vals}

		ocs = lowerset(x.decode('UTF-8') for x in _MergedAttributes(self, ml).get_attribute('objectClass'))
		unneeded_ocs = set()  # type: Set[Text]
		required_ocs = set()  # type: Set[Text]

		# evaluate (extended) options
		module_options = univention.admin.modules.options(self.module)
		available_options = set(module_options)
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
				required_ocs |= {prop.objClass}
				continue

			if prop.deleteObjClass:
				unneeded_ocs |= {prop.objClass}

			# if the value is unset we need to remove the attribute completely
			if self.oldattr.get(prop.ldapMapping):
				ml = [x for x in ml if x[0].lower() != prop.ldapMapping.lower()]
				ml.append((prop.ldapMapping, self.oldattr.get(prop.ldapMapping), b''))

		unneeded_ocs |= {oc for option in removed_options for oc in module_options[option].objectClasses}
		required_ocs |= {oc for option in added_options for oc in module_options[option].objectClasses}

		ocs -= lowerset(unneeded_ocs)
		ocs |= lowerset(required_ocs)
		if lowerset(x.decode('utf-8') for x in self.oldattr.get('objectClass', [])) == ocs:
			return ml

		ud.debug(ud.ADMIN, ud.INFO, 'OCS=%r; required=%r; removed: %r' % (ocs, required_ocs, unneeded_ocs))

		# case normalize object class names
		schema = self.lo.get_schema()
		ocs = {x.names[0] for x in (schema.get_obj(ldap.schema.models.ObjectClass, x) for x in ocs) if x}

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
		allowed = {name.lower() for attr in may.values() for name in attr.names} | {name.lower() for attr in must.values() for name in attr.names}

		ml = [x for x in ml if x[0].lower() != 'objectclass']
		ml.append(('objectClass', self.oldattr.get('objectClass', []), [x.encode('utf-8') for x in ocs]))
		newattr = ldap.cidict.cidict(_MergedAttributes(self, ml).get_attributes())

		# make sure only attributes known by the object classes are set
		for attr, val in newattr.items():
			if not val:
				continue
			if re.sub(u';binary$', u'', attr.lower()) not in allowed:
				ud.debug(ud.ADMIN, ud.WARN, 'The attribute %r is not allowed by any object class.' % (attr,))
				# ml.append((attr, val, [])) # TODO: Remove the now invalid attribute instead
				return ml

		# require all MUST attributes to be set
		for attr in must.values():
			if not any(newattr.get(name) or newattr.get(u'%s;binary' % (name,)) for name in attr.names):
				ud.debug(ud.ADMIN, ud.WARN, 'The attribute %r is required by the current object classes.' % (attr.names,))
				return ml

		ml = [x for x in ml if x[0].lower() != 'objectclass']
		ml.append(('objectClass', self.oldattr.get('objectClass', []), [x.encode('utf-8') for x in ocs]))

		return ml

	def _move_in_subordinates(self, olddn):
		result = self.lo.searchDn(base=self.lo.base, filter=filter_format(u'(&(objectclass=person)(secretary=%s))', [olddn]))
		for subordinate in result:
			self.lo.modify(subordinate, [('secretary', olddn.encode('utf-8'), self.dn.encode('utf-8'))])

	def _move_in_groups(self, olddn):
		for group in self.oldinfo.get('groups', []) + [self.oldinfo.get('machineAccountGroup', '')]:
			if group != '':
				members = self.lo.getAttr(group, 'uniqueMember')
				newmembers = [
					member
					for member in members
					if dn2str(str2dn(member)).lower() not in (dn2str(str2dn(olddn)).lower(), dn2str(str2dn(self.dn)).lower(), )
				]
				newmembers.append(self.dn.encode('UTF-8'))
				self.lo.modify(group, [('uniqueMember', members, newmembers)])

	def _move(self, newdn, modify_childs=True, ignore_license=False):  # type: (str, bool, bool) -> str
		"""Moves this object to the new DN. Should only be called by :func:`univention.admin.handlers.simpleLdap.move`."""
		self._ldap_pre_move(newdn)

		olddn = self.dn
		self.lo.rename(self.dn, newdn)
		self.dn = newdn

		try:
			self._move_in_groups(olddn)  # can be done always, will do nothing if oldinfo has no attribute 'groups'
			self._move_in_subordinates(olddn)
			self._ldap_post_move(olddn)
		except Exception:
			# move back
			ud.debug(ud.ADMIN, ud.WARN, 'simpleLdap._move: self._ldap_post_move failed, move object back to %s' % olddn)
			self.lo.rename(self.dn, olddn)
			self.dn = olddn
			raise
		self._write_admin_diary_move(newdn)
		return self.dn

	def _write_admin_diary_move(self, position):
		self._write_admin_diary_event('MOVED', {'position': position})

	def _remove(self, remove_childs=False):  # type: (bool) -> None
		"""Removes this object. Should only be called by :func:`univention.admin.handlers.simpleLdap.remove`."""
		ud.debug(ud.ADMIN, ud.INFO, 'handlers/__init__._remove() called for %r with remove_childs=%r' % (self.dn, remove_childs))

		if _prevent_to_change_ad_properties and self._is_synced_object():
			raise univention.admin.uexceptions.invalidOperation(_('Objects from Active Directory can not be removed.'))

		self._ldap_pre_remove()
		self.call_udm_property_hook('hook_ldap_pre_remove', self)

		if remove_childs:
			subelements = []  # type: List[Tuple[str, Dict[str, List[str]]]]
			if b'FALSE' not in self.lo.getAttr(self.dn, 'hasSubordinates'):
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
		# type: () -> None
		self._write_admin_diary_event('REMOVED')

	def loadPolicyObject(self, policy_type, reset=0):  # type: (str, int) -> simplePolicy
		pathlist = []

		ud.debug(ud.ADMIN, ud.INFO, "loadPolicyObject: policy_type: %s" % policy_type)
		policy_module = univention.admin.modules.get(policy_type)

		# overwrite property descriptions
		univention.admin.ucr_overwrite_properties(policy_module, self.lo)
		# re-build layout if there any overwrites defined
		univention.admin.ucr_overwrite_module_layout(policy_module)

		# retrieve path info from 'cn=directory,cn=univention,<current domain>' object
		pathResult = self.lo.get('cn=directory,cn=univention,' + self.position.getDomain())
		if not pathResult:
			pathResult = self.lo.get('cn=default containers,cn=univention,' + self.position.getDomain())
		for i in pathResult.get('univentionPolicyObject', []):
			i = i.decode('utf-8')
			try:
				self.lo.searchDn(base=i, scope='base')
				pathlist.append(i)
				ud.debug(ud.ADMIN, ud.INFO, "loadPolicyObject: added path %s" % i)
			except Exception:
				ud.debug(ud.ADMIN, ud.INFO, "loadPolicyObject: invalid path setting: %s does not exist in LDAP" % i)
				continue  # looking for next policy container
			break  # at least one item has been found; so we can stop here since only pathlist[0] is used

		if not pathlist:
			policy_position = self.position
		else:
			policy_position = univention.admin.uldap.position(self.position.getBase())
			policy_path = pathlist[0]
			try:
				prefix = univention.admin.modules.policyPositionDnPrefix(policy_module)
				self.lo.searchDn(base=u"%s,%s" % (prefix, policy_path), scope='base')
				policy_position.setDn(u"%s,%s" % (prefix, policy_path))
			except Exception:
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

	def _init_ldap_search(self, policy):  # type: (simplePolicy) -> None
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
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'release_lock(%s): %r' % (name, value))
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

	def request_lock(self, name, value=None, updateLastUsedValue=True):
		"""Request a lock for the given value"""
		try:
			if name == 'sid+user':
				value = univention.admin.allocators.requestUserSid(self.lo, self.position, value)
				name = 'sid'
			else:
				value = univention.admin.allocators.request(self.lo, self.position, name, value)
		except univention.admin.uexceptions.noLock:
			self._release_locks()
			raise
		if not updateLastUsedValue:  # backwards compatibility: 2er-tuples required!
			self.alloc.append((name, value, updateLastUsedValue))
		else:
			self.alloc.append((name, value))
		return value

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
		return b'synced' in flags and b'docker' not in flags

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
	def lookup(cls, co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):  # type: (None, univention.admin.uldap.access, str, str, Optional[str], str, bool, bool, int, int, Optional[List], Optional[Dict]) -> List[simpleLdap]
		"""
		Perform a LDAP search and return a list of instances.

		:param None co: obsolete config
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
		filter_str = six.text_type(filter_s or u'')
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
			filter_conditions.append(univention.admin.filter.expression(u'univentionObjectType', cls.module, escape=True))
		else:
			object_classes = univention.admin.modules.options(cls.module).get(u'default', univention.admin.option()).objectClasses - {u'top', u'univentionPolicy', u'univentionObjectMetadata', u'person'}
			filter_conditions.extend(univention.admin.filter.expression(u'objectClass', ocs) for ocs in object_classes)

		return univention.admin.filter.conjunction(u'&', filter_conditions)

	@classmethod
	def rewrite_filter(cls, filter, mapping):
		key = filter.variable

		try:
			should_map = mapping.shouldMap(key)
		except KeyError:
			should_map = False

		if should_map:
			filter.variable = mapping.mapName(key)

		if filter.operator == '=*':
			# 1. presence match. We only need to change the variable name. value is not set
			# 2. special case for syntax classes IStates and boolean:
			# properties that are represented as Checkboxes in the
			# frontend should include '(!(propertyName=*))' in the ldap filter
			# if the Checkbox is set to False to also find objects where the property
			# is not set. In that case we don't want to map the '*' to a different value.
			return

		# management/univention-management-console/src/univention/management/console/acl.py does not call univention.admin.modules.update()
		mod = univention.admin.modules.get_module(cls.module)
		property_ = mod.property_descriptions.get(key)

		# map options to corresponding objectClass
		if not property_ and key == 'options' and filter.value in getattr(mod, 'options', {}):
			ocs = mod.options[filter.value]
			filter.variable = u'objectClass'
			if len(ocs.objectClasses) > 1:
				con = univention.admin.filter.conjunction(u'&', [univention.admin.filter.expression(u'objectClass', oc, escape=True) for oc in ocs.objectClasses])
				filter.transform_to_conjunction(con)
			elif ocs.objectClasses:
				filter.value = list(ocs.objectClasses)[0]
			return

		if not should_map:
			return

		if property_ and not isinstance(filter.value, (list, tuple)):
			if property_.multivalue:
				# special case: mutlivalue properties need to be a list when map()-ing
				filter.value = [filter.value]
			if issubclass(property_.syntax if inspect.isclass(property_.syntax) else type(property_.syntax), univention.admin.syntax.complex):
				# special case: complex syntax properties need to be a list (of lists, if multivalue)
				filter.value = [filter.value]

		filter.value = mapping.mapValueDecoded(key, filter.value, encoding_errors='ignore')

		if isinstance(filter.value, (list, tuple)) and filter.value:
			# complex syntax
			filter.value = filter.value[0]

	@classmethod
	def identify(cls, dn, attr, canonical=False):
		ocs = {x.decode('utf-8') for x in attr.get('objectClass', [])}
		required_object_classes = univention.admin.modules.options(cls.module).get('default', univention.admin.option()).objectClasses - {'top', 'univentionPolicy', 'univentionObjectMetadata', 'person'}
		return (ocs & required_object_classes) == required_object_classes

	@classmethod
	def _ldap_attributes(cls):
		return ['*', 'entryUUID', 'entryCSN', 'modifyTimestamp']


class simpleComputer(simpleLdap):

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[]):
		simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes)

		self.newPrimaryGroupDn = 0
		self.oldPrimaryGroupDn = 0
		self.ip = []
		self.network_object = False
		self.old_network = 'None'
		self.__saved_dhcp_entry = None
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
			ips = [ip_address(addr.decode('ASCII')).exploded for key in ('aRecord', 'aAAARecord') for addr in self.oldattr.get(key, [])]
			self.oldinfo['ip'] += ips
			self.info['ip'] += ips

	def getMachineSid(self, lo, position, uidNum, rid=None):
		# if rid is given, use it regardless of s4 connector
		if rid:
			searchResult = self.lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
			domainsid = searchResult[0][1]['sambaSID'][0].decode('ASCII')
			sid = domainsid + u'-' + rid
			return self.request_lock('sid', sid)
		else:
			# if no rid is given, create a domain sid or local sid if connector is present
			if self.s4connector_present:
				return u'S-1-4-%s' % uidNum
			else:
				num = uidNum
				while True:
					try:
						return self.request_lock('sid+user', num)
					except univention.admin.uexceptions.noLock:
						num = str(int(num) + 1)

	# HELPER
	@classmethod
	def _ip_from_ptr(cls, zoneName, relativeDomainName):  # type: (str, str) -> str
		"""
		Extract IP address from reverse DNS record.

		>>> simpleComputer._ip_from_ptr("2.1.in-addr.arpa", "4.3")
		'1.2.3.4'
		>>> simpleComputer._ip_from_ptr("0.0.0.0.0.0.0.0.0.8.b.d.1.0.0.2.ip6.arpa", "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0")
		'2001:db80:0000:0000:0000:0000:0000:0001'
		"""
		if 'ip6' in zoneName:
			return cls._ipv6_from_ptr(zoneName, relativeDomainName)
		else:
			return cls._ipv4_from_ptr(zoneName, relativeDomainName)

	@staticmethod
	def _ipv4_from_ptr(zoneName, relativeDomainName):  # type: (str, str) -> str
		"""
		Extract IPv4 address from reverse DNS record.

		>>> simpleComputer._ipv4_from_ptr("2.1.in-addr.arpa", "4.3")
		'1.2.3.4'
		"""
		return '%s.%s' % (
			'.'.join(reversed(zoneName.replace('.in-addr.arpa', '').split('.'))),
			'.'.join(reversed(relativeDomainName.split('.'))))

	@staticmethod
	def _ipv6_from_ptr(zoneName, relativeDomainName):  # type: (str, str) -> str
		"""
		Extract IPv6 address from reverse DNS record.

		>>> simpleComputer._ipv6_from_ptr("0.0.0.0.0.0.0.0.0.8.b.d.1.0.0.2.ip6.arpa", "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0")
		'2001:db80:0000:0000:0000:0000:0000:0001'
		"""
		fullName = relativeDomainName + '.' + zoneName.replace('.ip6.arpa', '')
		digits = fullName.split('.')
		blocks = [''.join(reversed(digits[i:i + 4])) for i in range(0, len(digits), 4)]
		return ':'.join(reversed(blocks))

	@staticmethod
	def _is_ip(ip):  # type: (str) -> bool
		"""
		Check if valid IPv4 (0.0.0.0 is allowed) or IPv6 address.

		:param ip: string.
		:returns: `True` if it is a valid IPv4 or IPv6 address., `False` otherwise.

		>>> simpleComputer._is_ip('192.0.2.0')
		True
		>>> simpleComputer._is_ip('::1')
		True
		>>> simpleComputer._is_ip('')
		False
		"""
		try:
			ip_address(u'%s' % (ip,))
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
			zones = []

			searchFilter = filter_format('(&(objectClass=dNSZone)(relativeDomainName=%s)(!(cNAMERecord=*)))', [self['name']])
			try:
				result = self.lo.search(base=tmppos.getBase(), scope='domain', filter=searchFilter, attr=['zoneName', 'aRecord', 'aAAARecord'], unique=False)
				for dn, attr in result:
					zoneName = attr['zoneName'][0].decode('UTF-8')
					for key in ('aRecord', 'aAAARecord'):
						if key in attr:
							zones.append((zoneName, [ip_address(x.decode('ASCII')).exploded for x in attr[key]]))

				ud.debug(ud.ADMIN, ud.INFO, 'zoneNames: %s' % zones)
				for zoneName, ips in zones:
					searchFilter = filter_format('(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=@))', [zoneName])
					results = self.lo.searchDn(base=tmppos.getBase(), scope='domain', filter=searchFilter, unique=False)
					for dn in results:
						for ip in ips:
							self['dnsEntryZoneForward'].append([dn, ip])
				ud.debug(ud.ADMIN, ud.INFO, 'dnsEntryZoneForward: %s' % (self['dnsEntryZoneForward'],))
			except univention.admin.uexceptions.insufficientInformation:
				self['dnsEntryZoneForward'] = []
				raise

			for zoneName, ips in zones:
				searchFilter = filter_format('(&(objectClass=dNSZone)(|(PTRRecord=%s)(PTRRecord=%s.%s.)))', (self['name'], self['name'], zoneName))
				try:
					results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['relativeDomainName', 'zoneName'], filter=searchFilter, unique=False)
					for dn, attr in results:
						ip = self._ip_from_ptr(attr['zoneName'][0].decode('UTF-8'), attr['relativeDomainName'][0].decode('UTF-8'))
						if not self._is_ip(ip):
							ud.debug(ud.ADMIN, ud.WARN, 'simpleComputer: dnsEntryZoneReverse: invalid IP address generated: %r' % (ip,))
							continue
						entry = [self.lo.parentDn(dn), ip]
						if entry not in self['dnsEntryZoneReverse']:
							self['dnsEntryZoneReverse'].append(entry)
				except univention.admin.uexceptions.insufficientInformation:
					self['dnsEntryZoneReverse'] = []
					raise
			ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: dnsEntryZoneReverse: %s' % self['dnsEntryZoneReverse'])

			for zoneName, ips in zones:
				searchFilter = filter_format('(&(objectClass=dNSZone)(|(cNAMERecord=%s)(cNAMERecord=%s.%s.)))', (self['name'], self['name'], zoneName))
				try:
					results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['relativeDomainName', 'cNAMERecord', 'zoneName'], filter=searchFilter, unique=False)
					for dn, attr in results:
						dnsAlias = attr['relativeDomainName'][0].decode('UTF-8')
						self['dnsAlias'].append(dnsAlias)
						dnsAliasZoneContainer = self.lo.parentDn(dn)
						if attr['cNAMERecord'][0].decode('UTF-8') == self['name']:
							dnsForwardZone = attr['zoneName'][0].decode('UTF-8')
						else:
							dnsForwardZone = zoneName

						entry = [dnsForwardZone, dnsAliasZoneContainer, dnsAlias]
						if entry not in self['dnsEntryZoneAlias']:
							self['dnsEntryZoneAlias'].append(entry)
				except univention.admin.uexceptions.insufficientInformation:
					self['dnsEntryZoneAlias'] = []
					raise
			ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: dnsEntryZoneAlias: %s' % self['dnsEntryZoneAlias'])

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
								entry = (service, ip.decode('ASCII'), macAddress)
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
			self['groups'] = self.lo.searchDn(base=self.lo.base, filter=filter_format('(&(objectclass=univentionGroup)(uniqueMember=%s))', [self.dn]))

		if 'name' in self.info and 'domain' in self.info:
			self.info['fqdn'] = '%s.%s' % (self['name'], self['domain'])

	def __modify_dhcp_object(self, position, mac, ip=None):
		# identify the dhcp object with the mac address

		name = self['name']
		ud.debug(ud.ADMIN, ud.INFO, '__modify_dhcp_object: position: "%s"; name: "%s"; mac: "%s"; ip: "%s"' % (position, name, mac, ip))
		if not all((name, mac)):
			return

		ethernet = 'ethernet %s' % mac
		bip = ip.encode('ASCII') if ip else b''

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
				taken = {int(m.group(1)) for m in (RE.match(dn) for dn in results) if m}
				n = min(set(range(max(taken) + 2)) - taken) if taken else 0
				name = '%s_uv%d' % (name, n)

			dn = 'cn=%s,%s' % (escape_dn_chars(name), position)
			ml = [
				('objectClass', [b'top', b'univentionObject', b'univentionDhcpHost']),
				('univentionObjectType', [b'dhcp/host']),
				('cn', [name.encode('UTF-8')]),
				('dhcpHWAddress', [ethernet.encode('ASCII')]),
			]
			if ip:
				ml.append(('univentionDhcpFixedAddress', [bip]))
			self.lo.add(dn, ml)
			ud.debug(ud.ADMIN, ud.INFO, 'we just added the object "%s"' % (dn,))
		elif ip:
			# if the object already exists, we append or remove the ip address
			ud.debug(ud.ADMIN, ud.INFO, 'the dhcp object with the mac address "%s" exists, we change the ip' % ethernet)
			for dn, attr in results:
				if bip in attr.get('univentionDhcpFixedAddress', []):
					continue
				self.lo.modify(dn, [('univentionDhcpFixedAddress', b'', bip)])
				ud.debug(ud.ADMIN, ud.INFO, 'we added the ip "%s"' % ip)

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
			if self._is_ip(entry[-2]):
				ip = entry[-2]
		except univention.admin.uexceptions.valueError:
			mac = ''
		return (service, ip, mac)

	def __split_dns_line(self, entry):
		zone = entry[0]
		if len(entry) > 1:
			ip = self._is_ip(entry[1]) and entry[1] or None
		else:
			ip = None

		ud.debug(ud.ADMIN, ud.INFO, 'Split entry %s into zone %s and ip %s' % (entry, zone, ip))
		return (zone, ip)

	def __remove_dns_reverse_object(self, name, dnsEntryZoneReverse, ip):  # type: (str, str, str) -> None
		def modify(rdn, zoneDN):  # type: (Text, str) -> None
			zone_name = explode_rdn(zoneDN, True)[0]
			for dn, attributes in self.lo.search(scope='domain', attr=['pTRRecord'], filter=filter_format('(&(relativeDomainName=%s)(zoneName=%s))', (rdn, zone_name))):
				ptr_records = attributes.get('pTRRecord', [])
				removals = []
				if len(ptr_records) > 1:
					removals = [b'%s.%s.' % (name.encode('UTF-8'), attributes2['zoneName'][0]) for dn2, attributes2 in self.lo.search(scope='domain', attr=['zoneName'], filter=filter_format('(&(relativeDomainName=%s)(objectClass=dNSZone))', [name]), unique=False)]

				if len(ptr_records) <= 1 or set(ptr_records) == set(removals):
					self.lo.delete('relativeDomainName=%s,%s' % (escape_dn_chars(rdn), zoneDN))
				else:
					self.lo.modify(dn, [('pTRRecord', removals, b'')])

				zone = univention.admin.handlers.dns.reverse_zone.object(self.co, self.lo, self.position, zoneDN)
				zone.open()
				zone.modify()

		ud.debug(ud.ADMIN, ud.INFO, 'we should remove a dns reverse object: dnsEntryZoneReverse="%s", name="%s", ip="%s"' % (dnsEntryZoneReverse, name, ip))
		if dnsEntryZoneReverse:
			try:
				rdn = self.calc_dns_reverse_entry_name(ip, dnsEntryZoneReverse)
			except ValueError:
				pass
			else:
				modify(rdn, dnsEntryZoneReverse)

		elif ip:
			tmppos = univention.admin.uldap.position(self.position.getDomain())
			results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['zoneDn'], filter=filter_format('(&(objectClass=dNSZone)(|(pTRRecord=%s)(pTRRecord=%s.*)))', (name, name)), unique=False)
			for dn, attr in results:
				ud.debug(ud.ADMIN, ud.INFO, 'DEBUG: dn: "%s"' % dn)
				zone = self.lo.parentDn(dn)
				ud.debug(ud.ADMIN, ud.INFO, 'DEBUG: zone: "%s"' % zone)
				try:
					rdn = self.calc_dns_reverse_entry_name(ip, zone)
					ud.debug(ud.ADMIN, ud.INFO, 'DEBUG: rdn: "%s"' % rdn)
					modify(rdn, zone)
				except ValueError as ex:
					ud.debug(ud.ADMIN, ud.INFO, 'DEBUG: rdn: "%s"' % ex)
				except univention.admin.uexceptions.noObject:
					pass

	def __add_dns_reverse_object(self, name, zoneDn, ip):  # type: (str, str, str) -> None
		ud.debug(ud.ADMIN, ud.INFO, 'we should create a dns reverse object: zoneDn="%s", name="%s", ip="%s"' % (zoneDn, name, ip))
		if not all((name, zoneDn, ip)):
			return

		addr, attr = self._ip2dns(ip)
		try:
			ipPart = self.calc_dns_reverse_entry_name(ip, zoneDn)
		except ValueError:
			raise univention.admin.uexceptions.missingInformation(_('Reverse zone and IP address are incompatible.'))

		tmppos = univention.admin.uldap.position(self.position.getDomain())
		results = self.lo.search(base=tmppos.getBase(), scope='domain', attr=['zoneName'], filter=filter_format('(&(relativeDomainName=%s)(zoneName=*)(%s=%s))', (name, attr, addr.exploded)), unique=False)
		hostname_list = {
			u'%s.%s.' % (name, attr['zoneName'][0].decode('UTF-8'))
			for dn, attr in results
		}
		if not hostname_list:
			ud.debug(ud.ADMIN, ud.ERROR, 'Could not determine host record for name=%r, ip=%r. Not creating pointer record.' % (name, ip))
			return

		results = self.lo.searchDn(base=tmppos.getBase(), scope='domain', filter=filter_format('(&(relativeDomainName=%s)(%s=%s))', [ipPart] + list(str2dn(zoneDn)[0][0][:2])), unique=False)
		if not results:
			self.lo.add('relativeDomainName=%s,%s' % (escape_dn_chars(ipPart), zoneDn), [
				('objectClass', [b'top', b'dNSZone', b'univentionObject']),
				('univentionObjectType', [b'dns/ptr_record']),
				('zoneName', [explode_rdn(zoneDn, True)[0].encode('UTF-8')]),
				('relativeDomainName', [ipPart.encode('ASCII')]),
				('PTRRecord', [x.encode('UTF-8') for x in hostname_list])
			])

			# update Serial
			zone = univention.admin.handlers.dns.reverse_zone.object(self.co, self.lo, self.position, zoneDn)
			zone.open()
			zone.modify()

	def __remove_dns_forward_object(self, name, zoneDn, ip=None):  # type: (str, str, str) -> None
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
					ip = IPv6Address(u'%s' % (ip,)).exploded
					(attrEdit, attrOther, ) = ('aAAARecord', 'aRecord', )
				else:
					(attrEdit, attrOther, ) = ('aRecord', 'aAAARecord', )
				results = self.lo.search(base=base, scope='domain', attr=['aRecord', 'aAAARecord', ], filter=filter_format('(&(relativeDomainName=%s)(%s=%s))', (name, attrEdit, ip)), unique=False, required=False)
				for dn, attr in results:
					if [x.decode('ASCII') for x in attr[attrEdit]] == [ip, ] and not attr.get(attrOther):  # the <ip> to be removed is the last on the object
						# remove the object
						self.lo.delete(dn)
					else:
						# remove only the ip address attribute
						new_ip_list = copy.deepcopy(attr[attrEdit])
						new_ip_list.remove(ip.encode('ASCII'))

						self.lo.modify(dn, [(attrEdit, attr[attrEdit], new_ip_list, ), ])

					zone = zoneDn or self.lo.parentDn(dn)
					zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, zone)
					zone.open()
					zone.modify()

	def __add_related_ptrrecords(self, zoneDN, ip):  # type: (str, str) -> None
		if not all((zoneDN, ip)):
			return
		ptrrecord = '%s.%s.' % (self.info['name'], explode_rdn(zoneDN, True)[0])
		ip_split = ip.split('.')
		ip_split.reverse()
		search_filter = filter_format('(|(relativeDomainName=%s)(relativeDomainName=%s)(relativeDomainName=%s))', (ip_split[0], '.'.join(ip_split[:1]), '.'.join(ip_split[:2])))

		for dn, attributes in self.lo.search(base=zoneDN, scope='domain', attr=['pTRRecord'], filter=search_filter):
			self.lo.modify(dn, [('pTRRecord', '', ptrrecord)])

	def __remove_related_ptrrecords(self, zoneDN, ip):  # type: (str, str) -> None
		ptrrecord = '%s.%s.' % (self.info['name'], explode_rdn(zoneDN, True)[0])
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
				zoneName = explode_rdn(zone[0], True)[0]
				if len(zoneName) + len(self['name']) >= 63:
					ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: length of Common Name is too long: %d' % (len(zoneName) + len(self['name']) + 1))
					raise univention.admin.uexceptions.commonNameTooLong()

	@staticmethod
	def _ip2dns(addr):  # type: (str) -> Tuple[Union[IPv4Address, IPv6Address], str]
		"""
		Convert IP address string to 2-tuple (IPAddress, LdapAttributeName).

		:param addr: an IPv4 or IPv6 address.
		:returns: 2-tuple (IPAddress, LdapAttributeName)

		>>> simpleComputer._ip2dns('127.0.0.1')
		(IPv4Address(u'127.0.0.1'), 'aRecord')
		>>> simpleComputer._ip2dns('::1')
		(IPv6Address(u'::1'), 'aAAARecord')
		"""
		ip = ip_address(u'%s' % (addr, ))
		return (ip, 'aAAARecord' if isinstance(ip, IPv6Address) else 'aRecord')

	def __modify_dns_forward_object(self, name, zoneDn, new_ip, old_ip):  # type: (str, str, str, str) -> None
		ud.debug(ud.ADMIN, ud.INFO, 'we should modify a dns forward object: zoneDn="%s", name="%s", new_ip="%s", old_ip="%s"' % (zoneDn, name, new_ip, old_ip))
		zone = None
		if old_ip and new_ip:
			if not zoneDn:
				tmppos = univention.admin.uldap.position(self.position.getDomain())
				base = tmppos.getBase()
			else:
				base = zoneDn

			naddr, nattr = self._ip2dns(new_ip)
			oaddr, oattr = self._ip2dns(old_ip)
			results = self.lo.search(base=base, scope='domain', attr=['aRecord', 'aAAARecord'], filter=filter_format('(&(relativeDomainName=%s)(%s=%s))', (name, oattr, old_ip)), unique=False)

			for dn, attr in results:
				old_aRecord = attr.get('aRecord', [])
				new_aRecord = copy.deepcopy(old_aRecord)
				old_aAAARecord = attr.get('aAAARecord', [])
				new_aAAARecord = copy.deepcopy(old_aAAARecord)

				if isinstance(oaddr, IPv6Address):
					new_aAAARecord.remove(old_ip.encode('ASCII'))
				else:
					new_aRecord.remove(old_ip.encode('ASCII'))

				new_ip = naddr.exploded.encode('ASCII')
				if isinstance(naddr, IPv6Address):
					if new_ip not in new_aAAARecord:
						new_aAAARecord.append(new_ip)
				else:
					if new_ip not in new_aRecord:
						new_aRecord.append(new_ip)

				modlist = []
				if old_aAAARecord != new_aAAARecord:
					modlist.append(('aAAARecord', old_aAAARecord, new_aAAARecord, ))
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

	def __add_dns_forward_object(self, name, zoneDn, ip):  # type: (str, str, str) -> None
		ud.debug(ud.ADMIN, ud.INFO, 'we should add a dns forward object: zoneDn="%s", name="%s", ip="%s"' % (zoneDn, name, ip))
		if not all((name, ip, zoneDn)):
			return
		addr = ip_address(u'%s' % (ip,))
		if isinstance(addr, IPv6Address):
			self.__add_dns_forward_object_ipv6(name, zoneDn, addr)
		elif isinstance(addr, IPv4Address):
			self.__add_dns_forward_object_ipv4(name, zoneDn, addr)

	def __add_dns_forward_object_ipv6(self, name, zoneDn, addr):  # type: (str, str, IPv6Address) -> None
		ip = addr.exploded.encode('ASCII')
		results = self.lo.search(base=zoneDn, scope='domain', attr=['aAAARecord'], filter=filter_format('(&(relativeDomainName=%s)(!(cNAMERecord=*)))', (name,)), unique=False)
		if not results:
			try:
				self.lo.add('relativeDomainName=%s,%s' % (escape_dn_chars(name), zoneDn), [
					('objectClass', [b'top', b'dNSZone', b'univentionObject']),
					('univentionObjectType', [b'dns/host_record']),
					('zoneName', explode_rdn(zoneDn, True)[0].encode('UTF-8')),
					('aAAARecord', [ip]),
					('relativeDomainName', [name.encode('UTF-8')])
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
					self.lo.modify(dn, [('aAAARecord', b'', ip)])

	def __add_dns_forward_object_ipv4(self, name, zoneDn, addr):  # type: (str, str, IPv4Address) -> None
		ip = addr.exploded.encode('ASCII')
		results = self.lo.search(base=zoneDn, scope='domain', attr=['aRecord'], filter=filter_format('(&(relativeDomainName=%s)(!(cNAMERecord=*)))', (name,)), unique=False)
		if not results:
			try:
				self.lo.add('relativeDomainName=%s,%s' % (escape_dn_chars(name), zoneDn), [
					('objectClass', [b'top', b'dNSZone', b'univentionObject']),
					('univentionObjectType', [b'dns/host_record']),
					('zoneName', explode_rdn(zoneDn, True)[0].encode('UTF-8')),
					('ARecord', [ip]),
					('relativeDomainName', [name.encode('UTF-8')])
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
					self.lo.modify(dn, [('aRecord', b'', ip)])

	def __add_dns_alias_object(self, name, dnsForwardZone, dnsAliasZoneContainer, alias):  # type: (str, str, str, str) -> None
		ud.debug(ud.ADMIN, ud.INFO, 'add a dns alias object: name="%s", dnsForwardZone="%s", dnsAliasZoneContainer="%s", alias="%s"' % (name, dnsForwardZone, dnsAliasZoneContainer, alias))
		alias = alias.rstrip('.')
		if name and dnsForwardZone and dnsAliasZoneContainer and alias:
			results = self.lo.search(base=dnsAliasZoneContainer, scope='domain', attr=['cNAMERecord'], filter=filter_format('relativeDomainName=%s', (alias,)), unique=False)
			if not results:
				self.lo.add('relativeDomainName=%s,%s' % (escape_dn_chars(alias), dnsAliasZoneContainer), [
					('objectClass', [b'top', b'dNSZone', b'univentionObject']),
					('univentionObjectType', [b'dns/alias']),
					('zoneName', explode_rdn(dnsAliasZoneContainer, True)[0].encode('UTF-8')),
					('cNAMERecord', [b"%s.%s." % (name.encode('UTF-8'), dnsForwardZone.encode('UTF-8'))]),
					('relativeDomainName', [alias.encode('UTF-8')])
				])

				# TODO: check if dnsAliasZoneContainer really is a forwardZone, maybe it is a container under a zone
				zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, dnsAliasZoneContainer)
				zone.open()
				zone.modify()
			else:
				# throw exception, cNAMERecord is single value
				raise univention.admin.uexceptions.dnsAliasAlreadyUsed(_('DNS alias is already in use.'))

	def __remove_dns_alias_object(self, name, dnsForwardZone, dnsAliasZoneContainer, alias=None):  # type: (str, str, str, str) -> None
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
						results = self.lo.searchDn(base=tmppos.getBase(), scope='domain', filter=filter_format('(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=@))', (attr['zoneName'][0].decode('UTF-8'),)), unique=False)
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
						results = self.lo.searchDn(base=tmppos.getBase(), scope='domain', filter=filter_format('(&(objectClass=dNSZone)(zoneName=%s)(relativeDomainName=@))', (attr['zoneName'][0].decode('UTF-8'),)), unique=False)
						for zoneDn in results:
							zone = univention.admin.handlers.dns.forward_zone.object(self.co, self.lo, self.position, zoneDn)
							zone.open()
							zone.modify()
				else:  # not enough info to remove alias entries
					pass

	def _ldap_post_modify(self):
		super(simpleComputer, self)._ldap_post_modify()

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
						except Exception:
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
					zoneIsV6 = explode_rdn(x, True)[0].endswith('.ip6.arpa')
					entryIsV6 = ':' in entry
					if zoneIsV6 == entryIsV6:
						self.__add_dns_reverse_object(self['name'], x, entry)

		if self.__changes['name']:
			ud.debug(ud.ADMIN, ud.INFO, 'simpleComputer: name has changed')
			self.__update_groups_after_namechange()
			self.__rename_dhcp_object(old_name=self.__changes['name'][0], new_name=self.__changes['name'][1])
			self.__rename_dns_object(position=None, old_name=self.__changes['name'][0], new_name=self.__changes['name'][1])

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
					self.__changes['mac']['add'].append(self.request_lock('mac', macAddress))
				except univention.admin.uexceptions.noLock:
					raise univention.admin.uexceptions.macAlreadyUsed(macAddress)
			for macAddress in self.oldinfo.get('mac', []):
				if macAddress in self.info.get('mac', []):
					continue
				self.__changes['mac']['remove'].append(macAddress)

		oldAddresses = self.oldinfo.get('ip') or ()
		newAddresses = self.info.get('ip') or ()
		if oldAddresses != newAddresses:
			old_addr = [ip_address(u'%s' % addr) for addr in oldAddresses]
			old_ipv4 = [addr.exploded.encode('ASCII') for addr in old_addr if isinstance(addr, IPv4Address)]
			old_ipv6 = [addr.exploded.encode('ASCII') for addr in old_addr if isinstance(addr, IPv6Address)]
			new_addr = [ip_address(u'%s' % addr) for addr in newAddresses]
			new_ipv4 = [addr.exploded.encode('ASCII') for addr in new_addr if isinstance(addr, IPv4Address)]
			new_ipv6 = [addr.exploded.encode('ASCII') for addr in new_addr if isinstance(addr, IPv6Address)]
			ml.append(('aRecord', old_ipv4, new_ipv4))
			ml.append(('aAAARecord', old_ipv6, new_ipv6))

		if self.hasChanged('ip'):
			for ipAddress in self['ip']:
				if not ipAddress:
					continue
				if ipAddress in self.oldinfo.get('ip'):
					continue
				if not self.ip_alredy_requested:
					try:
						ipAddress = self.request_lock('aRecord', ipAddress)
					except univention.admin.uexceptions.noLock:
						self.ip_alredy_requested = 0
						raise univention.admin.uexceptions.ipAlreadyUsed(ipAddress)

				self.__changes['ip']['add'].append(ipAddress)

			for ipAddress in self.oldinfo.get('ip', []):
				if ipAddress in self.info['ip']:
					continue
				self.__changes['ip']['remove'].append(ipAddress)

		if self.hasChanged('name'):
			ml.append(('sn', self.oldattr.get('sn', [None])[0], self['name'].encode('UTF-8')))
			self.__changes['name'] = (self.oldattr.get('sn', [b''])[0].decode("UTF-8") or None, self['name'])

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
	def calc_dns_reverse_entry_name(cls, sip, reverseDN):  # type: (Text, Text) -> Text
		"""
		>>> simpleComputer.calc_dns_reverse_entry_name('10.200.2.5', 'subnet=2.200.10.in-addr.arpa')
		u'5'
		>>> simpleComputer.calc_dns_reverse_entry_name('10.200.2.5', 'subnet=200.10.in-addr.arpa')
		u'5.2'
		>>> simpleComputer.calc_dns_reverse_entry_name('2001:db8::3', 'subnet=0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa')
		u'3.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0'
		>>> simpleComputer.calc_dns_reverse_entry_name('1.2.3.4', 'subnet=2.in-addr.arpa')
		Traceback (most recent call last):
			...
		ValueError: 4.3.2.1.in-addr.arpa not in .2.in-addr.arpa
		"""
		addr = ip_address(u'%s' % (sip,))
		rev = addr.reverse_pointer
		subnet = u".%s" % (explode_rdn(reverseDN, True)[0],)
		if not rev.endswith(subnet):
			raise ValueError("%s not in %s" % (rev, subnet))
		return rev[:-len(subnet)]

	def _ldap_pre_create(self):
		super(simpleComputer, self)._ldap_pre_create()
		self.check_common_name_length()

	def _ldap_pre_modify(self):
		super(simpleComputer, self)._ldap_pre_modify()
		self.check_common_name_length()

	def _ldap_post_create(self):
		super(simpleComputer, self)._ldap_post_create()
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

		self.update_groups()

	def _ldap_post_remove(self):
		if self['mac']:
			for macAddress in self['mac']:
				if macAddress:
					self.alloc.append(('mac', macAddress))
		if self['ip']:
			for ipAddress in self['ip']:
				if ipAddress:
					self.alloc.append(('aRecord', ipAddress))
		super(simpleComputer, self)._ldap_post_remove()

		# remove computer from groups
		groups = copy.deepcopy(self['groups'])
		if self.oldinfo.get('primaryGroup'):
			groups.append(self.oldinfo.get('primaryGroup'))
		for group in groups:
			groupObject = univention.admin.objects.get(univention.admin.modules.get('groups/group'), self.co, self.lo, self.position, group)
			groupObject.fast_member_remove([self.dn], [x.decode('UTF-8') for x in self.oldattr.get('uid', [])], ignore_license=True)

	def __update_groups_after_namechange(self):
		oldname = self.oldinfo.get('name')
		newname = self.info.get('name')
		if not oldname:
			ud.debug(ud.ADMIN, ud.ERROR, '__update_groups_after_namechange: oldname is empty')
			return

		olddn = self.old_dn.encode('UTF-8')
		newdn = self.dn.encode('UTF-8')

		oldUid = b'%s$' % oldname.encode('UTF-8')
		newUid = b'%s$' % newname.encode('UTF-8')
		ud.debug(ud.ADMIN, ud.INFO, '__update_groups_after_namechange: olddn=%s' % olddn)
		ud.debug(ud.ADMIN, ud.INFO, '__update_groups_after_namechange: newdn=%s' % newdn)

		new_groups = set(self.info.get('groups', []))
		old_groups = set(self.oldinfo.get('groups', []))
		for group in new_groups | old_groups:

			# Using the UDM groups/group object does not work at this point. The computer object has already been renamed.
			# During open() of groups/group each member is checked if it exists. Because the computer object with "olddn" is missing,
			# it won't show up in groupobj['hosts']. That's why the uniqueMember/memberUid updates is done directly via
			# self.lo.modify()

			oldMemberUids = self.lo.getAttr(group, 'memberUid')
			newMemberUids = copy.deepcopy(oldMemberUids)
			if group in new_groups:
				ud.debug(ud.ADMIN, ud.INFO, '__update_groups_after_namechange: changing memberUid in grp=%s' % (group,))
				if oldUid in newMemberUids:
					newMemberUids.remove(oldUid)
				if newUid not in newMemberUids:
					newMemberUids.append(newUid)
				self.lo.modify(group, [('memberUid', oldMemberUids, newMemberUids)])
			else:
				ud.debug(ud.ADMIN, ud.INFO, '__update_groups_after_namechange: removing memberUid from grp=%s' % (group,))
				if oldUid in oldMemberUids:
					oldMemberUids = oldUid
					newMemberUids = b''
					self.lo.modify(group, [('memberUid', oldMemberUids, newMemberUids)])

			# we are doing the uniqueMember seperately because of a potential refint overlay that already changed the dn for us
			oldUniqueMembers = self.lo.getAttr(group, 'uniqueMember')
			newUniqueMembers = copy.deepcopy(oldUniqueMembers)
			if group in new_groups:
				ud.debug(ud.ADMIN, ud.INFO, '__update_groups_after_namechange: changing uniqueMember in grp=%s' % (group,))
				if olddn in newUniqueMembers:
					newUniqueMembers.remove(olddn)
				if newdn not in newUniqueMembers:
					newUniqueMembers.append(newdn)
				self.lo.modify(group, [('uniqueMember', oldUniqueMembers, newUniqueMembers)])
			else:
				if olddn in oldUniqueMembers:
					ud.debug(ud.ADMIN, ud.INFO, '__update_groups_after_namechange: removing uniqueMember from grp=%s' % (group,))
					oldUniqueMembers = olddn
					newUniqueMembers = b''
					self.lo.modify(group, [('uniqueMember', oldUniqueMembers, newUniqueMembers)])
				if newdn in oldUniqueMembers:
					ud.debug(ud.ADMIN, ud.INFO, '__update_groups_after_namechange: removing uniqueMember from grp=%s' % (group,))
					oldUniqueMembers = newdn
					newUniqueMembers = b''
					self.lo.modify(group, [('uniqueMember', oldUniqueMembers, newUniqueMembers)])

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
			groupObject.modify(ignore_license=True)

	def primary_group(self):  # type: () -> None
		if not self.hasChanged('primaryGroup'):
			return
		ud.debug(ud.ADMIN, ud.INFO, 'updating primary groups')

		primaryGroupNumber = self.lo.getAttr(self['primaryGroup'], 'gidNumber', required=True)
		self.newPrimaryGroupDn = self['primaryGroup']
		self.lo.modify(self.dn, [('gidNumber', b'None', primaryGroupNumber[0])])

		if 'samba' in self.options:
			primaryGroupSambaNumber = self.lo.getAttr(self['primaryGroup'], 'sambaSID', required=True)
			self.lo.modify(self.dn, [('sambaPrimaryGroupSID', b'None', primaryGroupSambaNumber[0])])

	def cleanup(self):  # type: () -> None
		self.open()
		if self['dnsEntryZoneForward']:
			for dnsEntryZoneForward in self['dnsEntryZoneForward']:
				dn, ip = self.__split_dns_line(dnsEntryZoneForward)
				try:
					self.__remove_dns_forward_object(self['name'], dn, None)
				except Exception as e:
					ud.debug(ud.ADMIN, ud.WARN, 'dnsEntryZoneForward.delete(%s): %s' % (dnsEntryZoneForward, e))

		if self['dnsEntryZoneReverse']:
			for dnsEntryZoneReverse in self['dnsEntryZoneReverse']:
				dn, ip = self.__split_dns_line(dnsEntryZoneReverse)
				try:
					self.__remove_dns_reverse_object(self['name'], dn, ip)
				except Exception as e:
					ud.debug(ud.ADMIN, ud.WARN, 'dnsEntryZoneReverse.delete(%s): %s' % (dnsEntryZoneReverse, e))

		if self['dhcpEntryZone']:
			for dhcpEntryZone in self['dhcpEntryZone']:
				dn, ip, mac = self.__split_dhcp_line(dhcpEntryZone)
				try:
					self.__remove_from_dhcp_object(mac=mac)
				except Exception as e:
					ud.debug(ud.ADMIN, ud.WARN, 'dhcpEntryZone.delete(%s): %s' % (dhcpEntryZone, e))

		if self['dnsEntryZoneAlias']:
			for entry in self['dnsEntryZoneAlias']:
				dnsForwardZone, dnsAliasZoneContainer, alias = entry
				try:
					self.__remove_dns_alias_object(self['name'], dnsForwardZone, dnsAliasZoneContainer, alias)
				except Exception as e:
					ud.debug(ud.ADMIN, ud.WARN, 'dnsEntryZoneAlias.delete(%s): %s' % (entry, e))

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

		ips = [ip for ip in self['ip'] if ip] if self.has_property('ip') and self['ip'] else []
		ip1 = self['ip'][0] if len(ips) == 1 else ''
		macs = [mac for mac in self['mac'] if mac] if self.has_property('mac') and self['mac'] else []
		mac1 = self['mac'][0] if len(macs) == 1 else ''

		if key == 'network':
			if self.old_network != value:
				if value and value != 'None':
					network_object = univention.admin.handlers.networks.network.object(self.co, self.lo, self.position, value)
					network_object.open()
					subnet = ip_network(u"%(network)s/%(netmask)s" % network_object, strict=False)

					if not ips or ip_address(u'%s' % (ip1,)) not in subnet:
						if self.ip_freshly_set:
							raise_after = univention.admin.uexceptions.ipOverridesNetwork
						else:
							# get next IP
							network_object.refreshNextIp()
							self['ip'] = network_object['nextIp']
							ips = [ip for ip in self['ip'] if ip] if self.has_property('ip') and self['ip'] else []
							ip1 = self['ip'][0] if len(ips) == 1 else ''
							try:
								self.ip = self.request_lock('aRecord', self['ip'][0])
								self.ip_alredy_requested = True
							except univention.admin.uexceptions.noLock:
								pass

						self.network_object = network_object
					if network_object['dnsEntryZoneForward'] and ip1:
						self['dnsEntryZoneForward'] = [[network_object['dnsEntryZoneForward'], ip1]]
					if network_object['dnsEntryZoneReverse'] and ip1:
						self['dnsEntryZoneReverse'] = [[network_object['dnsEntryZoneReverse'], ip1]]
					if network_object['dhcpEntryZone']:
						if ip1 and mac1:
							self['dhcpEntryZone'] = [(network_object['dhcpEntryZone'], ip1, mac1)]
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
					if self.network_object['dnsEntryZoneForward'] and ip1:
						self['dnsEntryZoneForward'] = [[self.network_object['dnsEntryZoneForward'], ip1]]
					if self.network_object['dnsEntryZoneReverse'] and ip1:
						self['dnsEntryZoneReverse'] = [[self.network_object['dnsEntryZoneReverse'], ip1]]
					if self.network_object['dhcpEntryZone']:
						if ip1 and macs:
							self['dhcpEntryZone'] = [(self.network_object['dhcpEntryZone'], ip1, mac1)]
						else:
							self.__saved_dhcp_entry = self.network_object['dhcpEntryZone']
			if not self.ip:
				self.ip_freshly_set = False

		elif key == 'mac' and self.__saved_dhcp_entry:
			if ip1 and macs:
				if isinstance(value, list):
					self['dhcpEntryZone'] = [(self.__saved_dhcp_entry, ip1, value[0])]
				else:
					self['dhcpEntryZone'] = [(self.__saved_dhcp_entry, ip1, value)]

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

	def _ldap_post_remove(self):
		super(simplePolicy, self)._ldap_post_remove()
		for object_dn in self.lo.searchDn(filter_format('univentionPolicyReference=%s', [self.dn])):
			try:
				self.lo.modify(object_dn, [('univentionPolicyReference', self.dn.encode('UTF-8'), None)])
			except (univention.admin.uexceptions.base, ldap.LDAPError) as exc:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'Could not remove policy reference %r from %r: %s' % (self.dn, object_dn, exc))

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
		# type: () -> str
		for key, property in self.descriptions.items():
			if property.identifies and key in self.info and self.info[key]:
				return key
		raise ValueError()

	def __makeUnique(self):
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

			self.__load_policies(policies)

		if hasattr(self, '_custom_policy_result_map'):
			self._custom_policy_result_map()
		else:
			values = {}
			for attr_name, value_dict in self.policy_attrs.items():
				value_dict = copy.deepcopy(value_dict)
				values[attr_name] = copy.copy(value_dict['value'])
				value_dict['value'] = [x.decode('UTF-8') for x in value_dict['value']]
				self.polinfo_more[self.mapping.unmapName(attr_name)] = value_dict

			self.polinfo = univention.admin.mapping.mapDict(self.mapping, values)
			self.polinfo = self._post_unmap(self.polinfo, values)

	def __load_policies(self, policies=None):
		if not self.policy_attrs:
			# the referring object does not exist yet
			if not self.referring_object_dn == self.referring_object_position_dn:
				result = self.lo.getPolicies(self.lo.parentDn(self.referring_object_dn), policies=policies)
			else:
				result = self.lo.getPolicies(self.referring_object_position_dn, policies=policies)
			for policy_oc, attrs in result.items():
				if univention.admin.objects.ocToType(policy_oc) == self.module:
					self.policy_attrs = attrs

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
		# type: () -> Dict[str, bool]
		"""
		Return effectively fixed attributes.
		"""
		if not self.resultmode:
			return {}

		self.__load_policies(None)
		return {
			self.mapping.unmapName(attr_name): value_dict.get('fixed', False)
			for attr_name, value_dict in self.policy_attrs.items()
		}

	def emptyAttributes(self):
		# type: () -> Dict[str, bool]
		"""
		return effectively empty attributes.
		"""
		if not self.has_property('emptyAttributes'):
			return {}

		return {
			self.mapping.unmapName(attrib): True
			for attrib in simpleLdap.__getitem__(self, 'emptyAttributes') or ()
		}

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
		attributes = set(self.obj.oldattr.keys()) | {x[0] for x in self.modlist}
		return {attr: self.get_attribute(attr) for attr in attributes}

	def get_attribute(self, attr):
		values = set(self.obj.oldattr.get(attr, []))
		# evaluate the modlist and apply all changes to the current values
		for (att, old, new) in self.modlist:
			if att.lower() != attr.lower():
				continue
			new = [] if not new else [new] if isinstance(new, bytes) else new
			old = [] if not old else [old] if isinstance(old, bytes) else old
			if not old and new:  # MOD_ADD
				values |= set(new)
			elif not new and old:  # MOD_DELETE
				values -= set(old)
			elif old and new:  # MOD_REPLACE
				values = set(new)
		return list(values)
