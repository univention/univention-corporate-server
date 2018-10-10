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

"""
A generic UDM module and object implementation.
Will work for all kinds of UDM modules.
"""

from __future__ import absolute_import, unicode_literals
import inspect
from ldap.dn import dn2str, str2dn
import univention.admin.objects
import univention.admin.modules
import univention.admin.uexceptions
import univention.admin.uldap
from ..encoders import dn_list_property_encoder_for
from ..udm import Udm
from ..base import BaseUdmModule, BaseUdmModuleMetadata, BaseUdmObject, BaseUdmObjectProperties, UdmLdapMapping
from ..exceptions import (
	CreateError, DeleteError, DeletedError, NotYetSavedError, ModifyError, MoveError, NoObject, UnknownProperty,
	UnknownUdmModuleType, WrongObjectType
)
from ..utils import UDebug as ud


class GenericUdmObjectProperties(BaseUdmObjectProperties):
	"""
	Container for UDM properties.

	:py:attr:`_encoders` is a mapping from property names to subclasses of
	_encoders.BaseEncoder, which will be used to transparently map between the
	properties representation in UDM1 and the new UDM APIs.
	"""

	_encoders = {}

	def __init__(self, udm_obj):
		super(GenericUdmObjectProperties, self).__init__(udm_obj)
		for property_names, encoder_class in self._encoders.iteritems():
			assert hasattr(encoder_class, 'decode')
			assert hasattr(encoder_class, 'encode')

	def __setattr__(self, key, value):
		if not str(key).startswith('_') and key not in self._udm_obj._orig_udm_object:
			raise UnknownProperty(
				'Unknown property {!r} for UDM module {!r}.'.format(key, self._udm_obj._udm_module.name),
				dn=self._udm_obj.dn,
				module_name=self._udm_obj._udm_module.name
			)
		super(GenericUdmObjectProperties, self).__setattr__(key, value)


class GenericUdmObject(BaseUdmObject):
	"""
	Generic UdmObject class that can be used with all UDM module types.

	Usage:
	* Creation of instances :py:class:`GenericUdmObject` is always done through a
	:py:class:`GenericUdmModul` instances py:meth:`new()`, py:meth:`get()` or
	py:meth:`search()` methods.
	* Modify an object:
		user.props.firstname = 'Peter'
		user.props.lastname = 'Pan'
		user.save()
	* Move an object:
		user.position = 'cn=users,ou=Company,dc=example,dc=com'
		user.save()
	* Delete an object:
		obj.delete()

	After saving a :py:class:`GenericUdmObject`, it is :py:meth:`reload()`ed
	automtically because UDM hooks and listener modules often add, modify or
	remove properties when saving to LDAP. As this involves LDAP, it can be
	disabled if the object is not used afterwards and performance is an issue:
		user_mod.meta.auto_reload = False
	"""
	udm_prop_class = GenericUdmObjectProperties
	_policies_encoder = None

	def __init__(self):
		"""
		Don't instantiate a :py:class:`UdmObject` directly. Use a
		:py:class:`UdmModule`.
		"""
		super(GenericUdmObject, self).__init__()
		self._udm_module = None
		self._lo = None
		self._orig_udm_object = None
		self._old_position = ''
		self._fresh = True
		self._deleted = False

	def reload(self):
		"""
		Refresh object from LDAP.

		:return: self
		:rtype: UdmObject
		:raises NotYetSavedError: if object does not yet exist (has no dn)
		"""
		if self._deleted:
			raise DeletedError('{} has been deleted.'.format(self), dn=self.dn, module_name=self._udm_module.name)
		if not self.dn or not self._orig_udm_object:
			raise NotYetSavedError(module_name=self._udm_module.name)
		self._orig_udm_object = self._udm_module._get_orig_udm_object(self.dn)
		self._copy_from_udm_obj()
		return self

	def save(self):
		"""
		Save object to LDAP.

		:return: self
		:rtype: UdmObject
		:raises MoveError: when a move operation fails
		"""
		if self._deleted:
			raise DeletedError('{} has been deleted.'.format(self), dn=self.dn, module_name=self._udm_module.name)
		if not self._fresh:
			ud.warn('Saving stale UDM object instance.')
		self._copy_to_udm_obj()
		if self.dn:
			if self._old_position and self._old_position != self.position:
				new_dn_li = [str2dn(self._orig_udm_object.dn)[0]]
				new_dn_li.extend(str2dn(self.position))
				new_dn = dn2str(new_dn_li)
				try:
					self.dn = self._orig_udm_object.move(new_dn)
				except univention.admin.uexceptions.invalidOperation as exc:
					raise MoveError(
						'Error moving {!r} object from {!r} to {!r}: {}'.format(
							self._udm_module.name, self.dn, self.position, exc
						), dn=self.dn, module_name=self._udm_module.name
					)
				assert self.dn == self._orig_udm_object.dn
				self.position = self._lo.parentDn(self.dn)
				self._old_position = self.position
				self._orig_udm_object.position.setDn(self.position)
			try:
				self.dn = self._orig_udm_object.modify()
			except univention.admin.uexceptions.base as exc:
				raise ModifyError(
					'Error saving {!r} object at {!r}: {} ({})'.format(
						self._udm_module.name, self.dn, exc.message, exc
					), dn=self.dn, module_name=self._udm_module.name
				)
		else:
			print('create')
			try:
				self.dn = self._orig_udm_object.create()
			except univention.admin.uexceptions.base as exc:
				raise CreateError(
					'Error creating {!r} object: {} ({})'.format(
						self._udm_module.name, exc.message, exc
					), module_name=self._udm_module.name
				)

		assert self.dn == self._orig_udm_object.dn
		assert self.position == self._lo.parentDn(self.dn)
		self._fresh = False
		if self.meta.auto_reload:
			self.reload()
		return self

	def delete(self):
		"""
		Remove the object from the LDAP database.

		:return: None
		:raises NotYetSavedError: if object does not yet exist (has no dn)
		:raises DeletedError: if the operation fails
		"""
		if self._deleted:
			ud.warn('{} has already been deleted.'.format(self))
			return
		if not self.dn or not self._orig_udm_object:
			raise NotYetSavedError()
		try:
			self._orig_udm_object.remove()
		except univention.admin.uexceptions.base as exc:
			raise DeleteError(
				'Error deleting {!r} object {!r}: {}'.format(
					self._udm_module.name, self.dn, exc
				), dn=self.dn, module_name=self._udm_module.name
			)
		if univention.admin.objects.wantsCleanup(self._orig_udm_object):
			univention.admin.objects.performCleanup(self._orig_udm_object)
		self._orig_udm_object = None
		self._deleted = True

	def _copy_from_udm_obj(self):
		"""
		Copy UDM property values from low-level UDM object to `props`
		container as well as its `policies` and `options`.

		:return: None
		"""
		self.dn = self._orig_udm_object.dn
		self.options = self._orig_udm_object.options
		if not self._policies_encoder:
			# 'auto', because list contains policies/*
			policies_encoder_class = dn_list_property_encoder_for('auto')
			self.__class__._policies_encoder = self._init_encoder(
				policies_encoder_class, property_name='__policies', lo=self._lo
			)
		self.policies = self._policies_encoder.decode(self._orig_udm_object.policies)
		if self.dn:
			self.position = self._lo.parentDn(self.dn)
			self._old_position = self.position
		else:
			self.position = self._udm_module._get_default_positions()[0]
		self.props = self.udm_prop_class(self)
		if not self.dn:
			self._init_new_object_props()
		for k in self._orig_udm_object.keys():
			# workaround Bug #47971: _orig_udm_object.items() changes object
			v = self._orig_udm_object.get(k)
			if not self.dn and v is None:
				continue
			if self._udm_module.meta.api_version > 0:
				# encoders exist from API version 1 on
				try:
					encoder_class = self.props._encoders[k]
				except KeyError:
					val = v
				else:
					encoder = self._init_encoder(encoder_class, property_name=k)
					val = encoder.decode(v)
			else:
				val = v
			if v is None and self._orig_udm_object.descriptions[k].multivalue:
				val = []
			setattr(self.props, k, val)
		self._fresh = True

	def _copy_to_udm_obj(self):
		"""
		Copy UDM property values from `props` container to low-level UDM
		object.

		:return: None
		"""
		self._orig_udm_object.options = self.options
		self._orig_udm_object.policies = self.policies
		self._orig_udm_object.position.setDn(self.position)
		for k in self._orig_udm_object.keys():
			# workaround Bug #47971: _orig_udm_object.items() changes object
			v = self._orig_udm_object.get(k)
			new_val = getattr(self.props, k, None)
			if self._udm_module.meta.api_version > 0:
				# encoders exist from API version 1 on
				try:
					encoder_class = self.props._encoders[k]
				except KeyError:
					new_val2 = new_val
				else:
					encoder = self._init_encoder(encoder_class, property_name=k)
					new_val2 = encoder.encode(new_val)
			else:
				new_val2 = new_val
			if v != new_val2:
				self._orig_udm_object[k] = new_val2

	def _init_new_object_props(self):
		"""
		This is a modified copy of the code of
		:py:meth:`univention.admin.handlers.simpleLdap.__getitem__()` which
		creates the default values for a new object, without setting them on
		the underlying UDM object.
		"""
		for key in self._orig_udm_object.keys():
			if key in self._orig_udm_object.info:
				if self._orig_udm_object.descriptions[key].multivalue and not isinstance(self._orig_udm_object.info[key], list):
					# why isn't this correct in the first place?
					setattr(self.props, key, [self._orig_udm_object.info[key]])
					continue
				setattr(self.props, key, self._orig_udm_object.info[key])
			# Disabled if branch, because the defaults should be calculated
			# when saving and not when accessing (which is the reason this code
			# needs to be here):
			# elif key not in self._orig_udm_object._simpleLdap__no_default and self._orig_udm_object.descriptions[key].editable:
			#     ...
			elif self._orig_udm_object.descriptions[key].multivalue:
				setattr(self.props, key, [])
			else:
				setattr(self.props, key, None)

	def _init_encoder(self, encoder_class, **kwargs):
		"""
		Instantiate encoder object if required. Optionally assemble additional
		arguments.

		:param encoder_class: a subclass of BaseEncoder
		:type encoder_class: type(BaseEncoder)
		:param kwargs: named arguments to pass to __init__ when instantiating encoder object
		:return: either a class object or an instance, depending on the class variable :py:attr:`static`
		:rtype: BaseEncoder or type(BaseEncoder)
		"""
		if encoder_class.static:
			# don't create an object if not necessary
			return encoder_class
		else:
			# initialize with required arguments
			for arg in inspect.getargspec(encoder_class.__init__).args:
				if arg == 'self':
					continue
				elif arg in kwargs:
					continue
				elif arg == 'lo':
					kwargs['lo'] = self._lo
				else:
					raise TypeError('Unknown argument {!r} for {}.__init__.'.format(arg, encoder_class.__class__.__name__))
			return encoder_class(**kwargs)


class GenericUdmModuleMetadata(BaseUdmModuleMetadata):
	@property
	def identifying_property(self):
		"""
		UDM Property of which the mapped LDAP attribute is used as first
		component in a DN, e.g. `username` (LDAP attribute `uid`) or `name`
		(LDAP attribute `cn`).
		"""
		for key, udm_property in self._udm_module._orig_udm_module.property_descriptions.iteritems():
			if udm_property.identifies:
				return key
		return ''

	def lookup_filter(self, filter_s=None):
		"""
		Filter the UDM module uses to find its corresponding LDAP objects.

		This can be used in two ways:

		* get the filter to find all objects:
			`myfilter_s = obj.meta.lookup_filter()`
		* get the filter to find a subset of the corresponding LDAP objects (`filter_s` will be combined with `&` to the filter for alle objects):
			`myfilter = obj.meta.lookup_filter('(|(givenName=A*)(givenName=B*))')`

		:param str filter_s: optional LDAP filter expression
		:return: an LDAP filter string
		:rtype: str
		"""
		return str(self._udm_module._orig_udm_module.lookup_filter(filter_s, self._udm_module.lo))

	@property
	def mapping(self):
		"""
		UDM properties to LDAP attributes mapping and vice versa.

		:return: a namedtuple containing two mappings: a) from UDM property to LDAP attribute and b) from LDAP attribute to UDM property
		:rtype: UdmLdapMapping
		"""
		return UdmLdapMapping(
			udm2ldap=dict((k, v[0]) for k, v in self._udm_module._orig_udm_module.mapping._map.iteritems()),
			ldap2udm=dict((k, v[0]) for k, v in self._udm_module._orig_udm_module.mapping._unmap.iteritems())
		)


class GenericUdmModule(BaseUdmModule):
	"""
	Simple API to use UDM modules. Basically a GenericUdmObject factory.

	Usage:
	0. Get module using
		user_mod = Udm.using_*().get('users/user')
	1 Create fresh, not yet saved GenericUdmObject:
		new_user = user_mod.new()
	2 Load an existing object:
		group = group_mod.get('cn=test,cn=groups,dc=example,dc=com')
		group = group_mod.get_by_id('Domain Users')
	3 Search and load existing objects:
		dc_slaves = dc_slave_mod.search(filter_s='cn=s10*')
		campus_groups = group_mod.search(base='ou=campus,dc=example,dc=com')
	"""
	_udm_object_class = GenericUdmObject
	_udm_module_meta_class = GenericUdmModuleMetadata
	_udm_module_cache = {}
	_default_directory_object = None
	supported_api_versions = (0, 1)

	def __init__(self, name, lo, api_version):
		super(GenericUdmModule, self).__init__(name, lo, api_version)
		self._orig_udm_module = self._get_orig_udm_module()

	def new(self):
		"""
		Create a new, unsaved GenericUdmObject object.

		:return: a new, unsaved GenericUdmObject object
		:rtype: GenericUdmObject
		"""
		return self._load_obj('')

	def get(self, dn):
		"""
		Load UDM object from LDAP.

		:param str dn: DN of the object to load
		:return: an existing GenericUdmObject object
		:rtype: GenericUdmObject
		:raises NoObject: if no object is found at `dn`
		:raises WrongObjectType: if the object found at `dn` is not of type :py:attr:`self.name`
		"""
		return self._load_obj(dn)

	def search(self, filter_s='', base='', scope='sub'):
		"""
		Get all UDM objects from LDAP that match the given filter.

		:param str filter_s: LDAP filter (only object selector like uid=foo
			required, objectClasses will be set by the UDM module)
		:param str base: subtree to search
		:param str scope: depth to search
		:return: generator to iterate over GenericUdmObject objects
		:rtype: Iterator(GenericUdmObject)
		"""
		try:
			udm_module_lookup_filter = str(self._orig_udm_module.lookup_filter(filter_s, self.lo))
			dns = self.lo.searchDn(filter=udm_module_lookup_filter, base=base, scope=scope)
		except AttributeError:
			# not all modules have 'lookup_filter'
			dns = (obj.dn for obj in self._orig_udm_module.lookup(None, self.lo, filter_s, base=base, scope=scope))
		for dn in dns:
			yield self.get(dn)

	def _get_default_positions_property(self):
		"""
		TODO

		:return:
		:rtype: str
		"""
		return ''

	@classmethod
	def _get_default_directory_object(cls, udm):
		"""
		TODO

		:return:
		:rtype: GenericUdmObject ?
		"""
		if cls._default_directory_object is None:
			try:
				cls._default_directory_object = udm.get('settings/directory').get(
						'cn=default containers,cn=univention,{}'.format(udm.lo.base)
					)
			except NoObject:
				pass
		return cls._default_directory_object

	def _get_default_positions(self):
		"""
		Get default containers for the UDM module.

		:return: list of container DNs
		:rtype: list(str)
		"""
		default_positions_property = self._get_default_positions_property()
		default_containers = []
		if default_positions_property:
			udm = Udm(self.lo, self.meta.api_version)
			default_directory_object = self._get_default_directory_object(udm)
			if default_directory_object is not None:
				dns = getattr(default_directory_object.props, default_positions_property)
				default_containers = [dn for dn in dns if udm.dn_exists(dn)]
		default_containers.append(self.lo.base)
		return default_containers

	def _get_orig_udm_module(self):
		"""
		Load a UDM module, initializing it if required.

		:return: a UDM module
		:rtype: univention.admin.handlers.simpleLdap
		"""
		# While univention.admin.modules already implements a modules cache we
		# cannot know if update() or init() are required. So we'll also cache.
		key = (self.lo.base, self.lo.binddn, self.lo.host, self.name)
		if key not in self._udm_module_cache:
			if self.name not in [k[3] for k in self._udm_module_cache.keys()]:
				univention.admin.modules.update()
			udm_module = univention.admin.modules.get(self.name)
			if not udm_module:
				raise UnknownUdmModuleType(
					msg='UDM module {!r} does not exist.'.format(self.name),
					module_name=self.name
				)
			po = univention.admin.uldap.position(self.lo.base)
			univention.admin.modules.init(self.lo, po, udm_module)
			self._udm_module_cache[key] = udm_module
		return self._udm_module_cache[key]

	def _get_orig_udm_object(self, dn):
		"""
		Retrieve UDM object from LDAP.

		May raise from NoObject if no object is found at DN or WrongObjectType
		if the object found is not of type :py:attr:`self.name`.

		:param str dn: the DN of the object to load
		:return: UDM object
		:rtype: univention.admin.handlers.simpleLdap
		:raises NoObject: if no object is found at `dn`
		:raises WrongObjectType: if the object found at `dn` is not of type :py:attr:`self.name`
		"""
		udm_module = self._get_orig_udm_module()
		po = univention.admin.uldap.position(self.lo.base)
		try:
			obj = univention.admin.objects.get(udm_module, None, self.lo, po, dn=dn)
		except univention.admin.uexceptions.noObject:
			raise NoObject(dn=dn, module_name=self.name)
		self._verify_univention_object_type(obj)
		if self.meta.auto_open:
			obj.open()
		return obj

	def _load_obj(self, dn):
		"""
		GenericUdmObject factory.

		:param str dn: the DN of the UDM object to load, if '' a new one
		:return: a GenericUdmObject
		:rtype: GenericUdmObject
		:raises NoObject: if no object is found at `dn`
		:raises WrongObjectType: if the object found at `dn` is not of type :py:attr:`self.name`
		"""
		obj = self._udm_object_class()
		obj._lo = self.lo
		obj._udm_module = self
		obj._orig_udm_object = self._get_orig_udm_object(dn)
		obj.props = obj.udm_prop_class(obj)
		obj._copy_from_udm_obj()
		return obj

	def _verify_univention_object_type(self, orig_udm_obj):
		"""
		Check that the ``univentionObjectType`` of the LDAP objects matches the
		UDM module name.

		:param orig_udm_obj: UDM1 object
		:type orig_udm_obj: univention.admin.handlers.simpleLdap
		:return: None
		:raises WrongObjectType: if ``univentionObjectType`` of the LDAP object
			does not match the UDM module name
		"""
		uni_obj_type = getattr(orig_udm_obj, 'oldattr', {}).get('univentionObjectType')
		if uni_obj_type and self.name.split('/', 1)[0] not in [uot.split('/', 1)[0] for uot in uni_obj_type]:
			raise WrongObjectType(dn=orig_udm_obj.dn, module_name=self.name, univention_object_type=', '.join(uni_obj_type))
