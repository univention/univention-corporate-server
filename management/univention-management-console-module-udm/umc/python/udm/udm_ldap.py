#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages UDM modules
#
# Copyright 2011-2019 Univention GmbH
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

import sys
import copy
import re
import threading
import traceback
import gc
import functools
import inspect
import locale
from json import load

from univention.management.console import Translation
from univention.management.console.protocol.definitions import BAD_REQUEST_UNAUTH
from univention.management.console.modules import UMC_OptionTypeError, UMC_OptionMissing, UMC_Error
from univention.management.console.ldap import user_connection, get_user_connection
from univention.management.console.config import ucr
from univention.management.console.log import MODULE

import univention.admin as udm
import univention.admin.layout as udm_layout
import univention.admin.modules as udm_modules
import univention.admin.objects as udm_objects
import univention.admin.syntax as udm_syntax
import univention.admin.uexceptions as udm_errors
import univention.admin.mapping as udm_mapping

from univention.management.console.modules.udm.syntax import widget, default_value

from ldap import LDAPError, NO_SUCH_OBJECT
from ldap.filter import filter_format
from ldap.dn import explode_dn
from functools import reduce


_ = Translation('univention-management-console-module-udm').translate

udm_modules.update()

__bind_function = None
_licenseCheck = 0


def set_bind_function(connection_getter):
	global __bind_function
	__bind_function = connection_getter


def get_bind_function():
	return __bind_function


def LDAP_Connection(func):
	"""Get a cached ldap connection bound to the user connection.

	.. deprecated :: UCS 4.4
		This must not be used in udm_ldap.py.
		Use something explicit like self.get_ldap_connection() instead.

	"""
	@functools.wraps(func)
	def _decorated(*args, **kwargs):
		method = user_connection(func, bind=get_bind_function(), write=True)
		try:
			return method(*args, **kwargs)
		except (LDAPError, udm_errors.ldapError):
			return method(*args, **kwargs)
	return _decorated


class UMCError(UMC_Error):

	def __init__(self, **kwargs):
		ucr.load()
		self._is_master = ucr.get('server/role') == 'domaincontroller_master'
		self._updates_available = ucr.is_true('update/available')
		self._fqdn = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))
		super(UMCError, self).__init__('\n'.join(self._error_msg()), **kwargs)

	def _error_msg(self):
		# return a generator or a list of strings which are concatenated by a newline
		yield ''


class AppAttributes(object):
	FNAME = '/var/lib/univention-appcenter/attributes/mapping.json'
	_cache = None

	@classmethod
	def reload_cache(cls, module):
		MODULE.info('Loading AppAttributes for %s...' % module)
		cache = cls._read_cache_file()
		if cls._cache is None:
			cls._cache = {}
		module_cache = cache.get(module) or {}
		cls._cache[module] = module_cache
		if module_cache:
			MODULE.info('Found for %s:' % module)
			for attr in module_cache:
				MODULE.info('    %s and with it: %r' % (attr, module_cache[attr]['attributes']))

	@classmethod
	def _read_cache_file(cls):
		current_locale = locale.getlocale()[0]
		try:
			with open(cls.FNAME) as fd:
				cache = load(fd)
		except EnvironmentError:
			MODULE.warn('Error reading %s' % cls.FNAME)
			cache = {}
		except ValueError:
			MODULE.warn('Error parsing %s' % cls.FNAME)
			cache = {}
		else:
			cache = cache.get(current_locale) or cache.get('en_US') or {}
		return cache

	@classmethod
	def data_for_module(cls, module):
		if cls._cache is None:
			cls.reload_cache(module)
		return cls._cache.get(module, {})

	@classmethod
	def options_for_module(cls, module):
		ret = {}
		for option_name, option_def in cls.data_for_module(module).items():
			ret[option_name] = udm.option(
				short_description=option_def['label'],
				long_description=option_def['description'],
				default=option_def['default'],
				editable=True,
				disabled=False,
				objectClasses=[],  # this is not really true, but not important either
				is_app_option=True,
			)
		return ret

	@classmethod
	def options_for_obj(cls, obj):
		ret = []
		if obj:
			for option_name, option_def in cls.data_for_module(obj.module).items():
				if obj[option_def['attribute_name']] == option_def['boolean_values'][0]:
					ret.append(option_name)
		return ret

	@classmethod
	def attributes_for_module(cls, module):
		ret = []
		for option_name, option_def in cls.data_for_module(module).items():
			ret.extend(option_def['attributes'])
		return ret

	@classmethod
	def alter_item_for_prop(cls, module, key, prop, item):
		for option_name, option_def in cls.data_for_module(module).items():
			if key in option_def['attributes']:
				item['options'].append(option_name)

	@classmethod
	def _flatten(cls, attrs):
		ret = []
		for sublist in attrs:
			if isinstance(sublist, (list, tuple)):
				ret.extend(cls._flatten(sublist))
			else:
				ret.append(sublist)
		return ret

	@classmethod
	def _is_option_layout(cls, layout, option):
		return option in cls._flatten(layout['layout'])

	@classmethod
	def _filter_attrs(cls, layout, attrs_to_remove):
		if isinstance(layout, dict):
			_layout = layout.get('layout')
			if _layout:
				cls._filter_attrs(_layout, attrs_to_remove)
		elif isinstance(layout, list):
			for _layout in layout:
				if isinstance(_layout, dict) or isinstance(_layout, list):
					cls._filter_attrs(_layout, attrs_to_remove)
			for attr in attrs_to_remove:
				try:
					layout.remove(attr)
				except ValueError:
					pass

	@classmethod
	def new_layout(cls, module, layout):
		layout = copy.deepcopy(layout)
		options = cls.options_for_module(module)
		if not options:
			return layout
		layout_index = 0
		for _layout in layout:
			if _layout['label'] == 'Apps':
				_layout['is_app_tab'] = False
				break
			layout_index += 1
		attrs_to_remove = []
		for option_name, option_def in cls.data_for_module(module).items():
			option_def = copy.deepcopy(option_def)
			attrs_to_remove.append(option_def['attribute_name'])
			attrs_to_remove.extend(option_def['attributes'])
		for _layout in layout:
			cls._filter_attrs(_layout, attrs_to_remove)
		data = cls.data_for_module(module)
		for option_name in sorted(data):
			option_def = data[option_name]
			if not option_def['attributes']:
				continue
			layout_index += 1
			layout.insert(layout_index, {
				'is_app_tab': True,
				'description': option_def['label'],
				'label': option_def['label'],
				'advanced': False,
				'layout': option_def['layout'],
			})
		return layout


class UserWithoutDN(UMCError):

	def __init__(self, username):
		self._username = username
		super(UserWithoutDN, self).__init__()

	def _error_msg(self):
		yield _('The LDAP DN of the user %s could not be determined.') % (self._username,)
		yield _('The following steps can help to solve this problem:')
		yield ' * ' + _('Ensure that the LDAP server on this system is running and responsive')
		yield ' * ' + _('Make sure the DNS settings of this server are correctly set up and the DNS server is responsive')
		if not self._is_master:
			yield ' * ' + _('Check the join status of this system by using the domain join UMC module')
		yield ' * ' + _('Make sure all join scripts were successfully executed')
		if self._updates_available:
			yield ' * ' + _('Install the latest software updates')
		yield _('If the problem persists additional hints about the cause can be found in the following log file(s):')
		yield ' * /var/log/univention/management-console-module-udm.log'
		yield ' * /var/log/univention/management-console-server.log'


class LDAP_AuthenticationFailed(UMCError):

	def __init__(self):
		super(LDAP_AuthenticationFailed, self).__init__(status=BAD_REQUEST_UNAUTH)

	def _error_msg(self):
		yield _('Authentication failed')


class ObjectDoesNotExist(UMCError):

	def __init__(self, ldap_dn):
		self.ldap_dn = ldap_dn
		super(ObjectDoesNotExist, self).__init__()

	@LDAP_Connection
	def _ldap_object_exists(self, ldap_connection=None, ldap_position=None):
		try:
			ldap_connection.get(self.ldap_dn, required=True)
		except NO_SUCH_OBJECT:
			return False
		else:
			return True

	def _error_msg(self):
		if self._ldap_object_exists():
			yield _('Could not identify the LDAP object type for %s.') % (self.ldap_dn,)
			yield _('If the problem persists please try to relogin into Univention Management Console.')
		else:
			yield _('LDAP object %s could not be found.') % (self.ldap_dn,)
			yield _('It possibly has been deleted or moved. Please update your search results and open the object again.')


class SuperordinateDoesNotExist(ObjectDoesNotExist):

	def _error_msg(self):
		if self._ldap_object_exists():
			yield _('Could not identify the superordinate %s.') % (self.ldap_dn,)
			yield _('If the problem persists please try to relogin into Univention Management Console.')
		else:
			yield _('Superordinate %s could not be found.') % (self.ldap_dn,)
			yield _('It possibly has been deleted or moved. Please update your search results and open the object again.')


class NoIpLeft(UMCError):

	def __init__(self, ldap_dn):
		try:
			self.network_name = udm.uldap.explodeDn(ldap_dn, True)[0]
		except IndexError:
			self.network_name = ldap_dn
		super(NoIpLeft, self).__init__()

	def _error_msg(self):
		yield _('Failed to automatically assign an IP address.')
		yield _('All IP addresses in the specified network "%s" are already in use.') % (self.network_name,)
		yield _('Please specify a different network or make sure that free IP addresses are available for the chosen network.')


class SearchTimeoutError(UMC_Error):

	def __init__(self):
		super(SearchTimeoutError, self).__init__(_('The query you have entered timed out. Please narrow down your search by specifying more query parameters'))


class SearchLimitReached(UMC_Error):

	def __init__(self):
		super(SearchLimitReached, self).__init__(_('The query you have entered yields too many matching entries. Please narrow down your search by specifying more query parameters. The current size limit of %s can be configured with the UCR variable directory/manager/web/sizelimit.') % ucr.get('directory/manager/web/sizelimit', '2000'))


class UDM_Error(Exception):

	def __init__(self, exc, dn=None):
		self.exc = exc
		self.dn = dn
		# if this exception is raised in a exception context we will have the original traceback
		self.exc_info = sys.exc_info()
		Exception.__init__(self, str(exc))

	def reraise(self):
		if self.exc_info and self.exc_info != (None, None, None):
			raise self.__class__, self, self.exc_info[2]
		raise self

	def __str__(self):
		msg = getattr(self.exc, 'message', '')
		for arg in self.exc.args:
			if isinstance(arg, unicode):
				arg = arg.encode('utf-8')
			if str(arg) not in msg:
				msg = '%s %s' % (msg, arg)
		return msg


class UDM_ModuleCache(dict):
	lock = threading.Lock()

	def get(self, name, template_object=None, force_reload=False, ldap_connection=None, ldap_position=None):
		UDM_ModuleCache.lock.acquire()
		try:
			if name in self and not force_reload:
				return self[name]

			module = udm_modules.get(name)
			if module is None:
				return None

			self[name] = module

			udm_modules.init(ldap_connection, ldap_position, self[name], template_object, force_reload=force_reload)
			AppAttributes.reload_cache(name)

			return self[name]
		finally:
			UDM_ModuleCache.lock.release()


_module_cache = UDM_ModuleCache()


class UDM_Module(object):

	"""Wraps UDM modules to provide a simple access to the properties and functions"""

	def __init__(self, module, force_reload=False, ldap_connection=None, ldap_position=None):
		"""Initializes the object"""
		self.ldap_connection = ldap_connection
		self.ldap_position = ldap_position
		self._initialized_with_module = module
		self.module = None
		self.load(force_reload=force_reload)
		if force_reload:
			AppAttributes._cache = None

	def get_ldap_connection(self):
		if get_bind_function():
			try:
				self.ldap_connection, po = get_user_connection(bind=get_bind_function(), write=True)
			except (LDAPError, udm_errors.ldapError):
				self.ldap_connection, po = get_user_connection(bind=get_bind_function(), write=True)
			self.ldap_position = udm.uldap.position(self.ldap_connection.base)
		return self.ldap_connection, udm.uldap.position(self.ldap_connection.base)

	def load(self, module=None, template_object=None, force_reload=False):
		"""Tries to load an UDM module with the given name. Optional a
		template object is passed to the init function of the module. As
		the initialisation of a module is expensive the function uses a
		cache to ensure that each module is just initialized once."""

		if module is None:
			module = self._initialized_with_module
		try:
			self.module = _module_cache.get(module, None, force_reload, *self.get_ldap_connection())  # FIXME: template_object not used?!
		except udm_errors.noObject:
			# can happen if the ldap connection is not bound to any user
			# e.g. due to a rename of the current logged in user
			pass  # keep the old module (if only reloaded)

	def allows_simple_lookup(self):
		return hasattr(self.module, 'lookup_filter')

	def lookup_filter(self, filter_s=None, lo=None):
		return getattr(self.module, 'lookup_filter')(filter_s, lo)

	def __repr__(self):
		return '<%s(%r) at 0x%x>' % (type(self).__name__, self.name, id(self))

	def __getitem__(self, key):
		props = getattr(self.module, 'property_descriptions', {})
		return props[key]

	def get_default_values(self, property_name):
		"""Depending on the syntax of the given property a default
		search pattern/value is returned"""
		MODULE.info('Searching for property %s' % property_name)
		ldap_connection, ldap_position = self.get_ldap_connection()
		for key, prop in getattr(self.module, 'property_descriptions', {}).items():
			if key == property_name:
				value = default_value(prop.syntax)
				if isinstance(value, (list, tuple)):
					value = read_syntax_choices(prop.syntax, ldap_connection=ldap_connection, ldap_position=ldap_position)
				return value

	def _map_properties(self, obj, properties):
		# FIXME: for the automatic IP address assignment, we need to make sure that
		# the network is set before the IP address (see Bug #24077, comment 6)
		# The following code is a workaround to make sure that this is the
		# case, however, this should be fixed correctly.
		# This workaround has been documented as Bug #25163.
		def _tmp_cmp(i, j):
			if i[0] == 'network':
				return -1
			return 0

		password_properties = self.password_properties
		for property_name, value in sorted(properties.items(), _tmp_cmp):
			if property_name in password_properties:
				MODULE.info('Setting password property %s' % (property_name,))
			else:
				MODULE.info('Setting property %s to %s' % (property_name, value))

			property_obj = self.get_property(property_name)
			if property_obj is None:
				raise UMC_OptionMissing(_('Property %s not found') % property_name)

			# check each element if 'value' is a list
			if isinstance(value, (tuple, list)) and property_obj.multivalue:
				if not value and not property_obj.required:
					MODULE.info('Setting of property ignored (is empty)')
					if property_name in obj.info:
						del obj.info[property_name]
					continue
				subResults = []
				for ival in value:
					try:
						subResults.append(property_obj.syntax.parse(ival))
					except TypeError as exc:
						raise UMC_OptionTypeError(_('The property %(property)s has an invalid value: %(value)s') % {'property': property_obj.short_description, 'value': exc})
				if subResults:  # empty list represents removing of the attribute (handlers/__init__.py def diff)
					MODULE.info('Setting of property ignored (is empty)')
					obj[property_name] = subResults
			# otherwise we have a single value
			else:
				# None and empty string represents removing of the attribute (handlers/__init__.py def diff)
				if (value is None or value == '') and not property_obj.required:
					if property_name in obj.info:
						del obj.info[property_name]
					continue
				try:
					obj[property_name] = property_obj.syntax.parse(value)
				except TypeError as exc:
					raise UMC_OptionTypeError(_('The property %(property)s has an invalid value: %(value)s') % {'property': property_obj.short_description, 'value': exc})

		return obj

	def create(self, ldap_object, container=None, superordinate=None):
		"""Creates a LDAP object"""
		ldap_connection, ldap_position = self.get_ldap_connection()
		if superordinate == 'None':
			superordinate = None
		if container:
			try:
				ldap_position.setDn(container)
			except udm_errors.noObject:
				raise ObjectDoesNotExist(container)
		elif superordinate:
			try:
				ldap_position.setDn(superordinate)
			except udm_errors.noObject:
				raise SuperordinateDoesNotExist(superordinate)
		else:
			if hasattr(self.module, 'policy_position_dn_prefix'):
				container = '%s,cn=policies,%s' % (self.module.policy_position_dn_prefix, ldap_position.getBase())
			elif hasattr(self.module, 'default_containers') and self.module.default_containers:
				container = '%s,%s' % (self.module.default_containers[0], ldap_position.getBase())
			else:
				container = ldap_position.getBase()

			ldap_position.setDn(container)

		if superordinate:
			mod = get_module(self.name, superordinate, ldap_connection)
			if not mod:
				MODULE.error('Superordinate module not found: %s' % (superordinate,))
				raise SuperordinateDoesNotExist(superordinate)
			MODULE.info('Found UDM module for superordinate')
			superordinate = mod.get(superordinate)

		obj = self.module.object(None, ldap_connection, ldap_position, superordinate=superordinate)
		try:
			obj.open()
			MODULE.info('Creating LDAP object')
			if '$options$' in ldap_object:
				options = [option for option in ldap_object['$options$'].keys() if ldap_object['$options$'][option] is True]
				for option_name, option_def in AppAttributes.data_for_module(self.name).items():
					if option_name in options:
						options.remove(option_name)
						ldap_object[option_def['attribute_name']] = option_def['boolean_values'][0]
				obj.options = options
				del ldap_object['$options$']
			if '$policies$' in ldap_object:
				obj.policies = reduce(lambda x, y: x + y, ldap_object['$policies$'].values(), [])
				del ldap_object['$policies$']

			self._map_properties(obj, ldap_object)

			obj.create()
		except udm_errors.base as e:
			MODULE.warn('Failed to create LDAP object: %s: %s' % (e.__class__.__name__, str(e)))
			UDM_Error(e, obj.dn).reraise()

		return obj.dn

	def move(self, ldap_dn, container):
		"""Moves an LDAP object"""
		ldap_connection, ldap_position = self.get_ldap_connection()
		superordinate = udm_objects.get_superordinate(self.module, None, ldap_connection, ldap_dn)
		obj = self.module.object(None, ldap_connection, ldap_position, dn=ldap_dn, superordinate=superordinate)
		try:
			obj.open()
			# build new dn
			rdn = udm.uldap.explodeDn(ldap_dn)[0]
			dest = '%s,%s' % (rdn, container)
			MODULE.info('Moving LDAP object %s to %s' % (ldap_dn, dest))
			obj.move(dest)
			return dest
		except udm_errors.base as e:
			MODULE.warn('Failed to move LDAP object %s: %s: %s' % (ldap_dn, e.__class__.__name__, str(e)))
			UDM_Error(e).reraise()

	def remove(self, ldap_dn, cleanup=False, recursive=False):
		"""Removes an LDAP object"""
		ldap_connection, ldap_position = self.get_ldap_connection()
		superordinate = udm_objects.get_superordinate(self.module, None, ldap_connection, ldap_dn)
		obj = self.module.object(None, ldap_connection, ldap_position, dn=ldap_dn, superordinate=superordinate)
		try:
			obj.open()
			MODULE.info('Removing LDAP object %s' % ldap_dn)
			obj.remove(remove_childs=recursive)
			if cleanup:
				udm_objects.performCleanup(obj)
		except udm_errors.base as e:
			MODULE.warn('Failed to remove LDAP object %s: %s: %s' % (ldap_dn, e.__class__.__name__, str(e)))
			UDM_Error(e).reraise()

	def modify(self, ldap_object):
		"""Modifies a LDAP object"""
		ldap_connection, ldap_position = self.get_ldap_connection()
		superordinate = udm_objects.get_superordinate(self.module, None, ldap_connection, ldap_object['$dn$'])
		MODULE.info('Modifying object %s with superordinate %s' % (ldap_object['$dn$'], superordinate))
		obj = self.module.object(None, ldap_connection, ldap_position, dn=ldap_object.get('$dn$'), superordinate=superordinate)
		del ldap_object['$dn$']

		try:
			obj.open()
			if '$options$' in ldap_object:
				options = obj.options[:]
				app_data = AppAttributes.data_for_module(self.name)
				for option_name, enabled in ldap_object['$options$'].items():
					if enabled is None:
						continue
					# handle AppAttributes
					if option_name in app_data:
						option_def = app_data[option_name]
						# use 'not enabled' since a truthy value as integer is 1 but 'boolean_values' stores the truthy value at index 0
						ldap_object[option_def['attribute_name']] = option_def['boolean_values'][int(not enabled)]
						continue
					# handle normal options
					if enabled:
						options.append(option_name)
					else:
						try:
							options.remove(option_name)
						except ValueError:
							pass
				obj.options = options
				MODULE.info('Setting new options to %s' % str(obj.options))
				del ldap_object['$options$']
			MODULE.info('Modifying LDAP object %s' % obj.dn)
			if '$policies$' in ldap_object:
				obj.policies = reduce(lambda x, y: x + y, ldap_object['$policies$'].values(), [])
				del ldap_object['$policies$']

			self._map_properties(obj, ldap_object)

			obj.modify()
		except udm_errors.base as e:
			MODULE.warn('Failed to modify LDAP object %s: %s: %s' % (obj.dn, e.__class__.__name__, str(e)))
			UDM_Error(e).reraise()

	def search(self, container=None, attribute=None, value=None, superordinate=None, scope='sub', filter='', simple=False, simple_attrs=None, hidden=True, serverctrls=None, response=None):
		"""Searches for LDAP objects based on a search pattern"""
		ldap_connection, ldap_position = self.get_ldap_connection()
		if container == 'all':
			container = ldap_position.getBase()
		elif container is None:
			container = ''
		if attribute in [None, 'None'] and filter:
			filter_s = str(filter)
		else:
			filter_s = _object_property_filter(self, attribute, value, hidden)

		MODULE.info('Searching for LDAP objects: container = %s, filter = %s, superordinate = %s' % (container, filter_s, superordinate))
		result = None
		try:
			sizelimit = int(ucr.get('directory/manager/web/sizelimit', '2000') or 2000)
			if simple and self.allows_simple_lookup():
				lookup_filter = self.lookup_filter(filter, ldap_connection)
				if lookup_filter is None:
					result = []
				else:
					if simple_attrs is not None:
						result = ldap_connection.search(filter=unicode(lookup_filter), base=container, scope=scope, sizelimit=sizelimit, attr=simple_attrs, serverctrls=serverctrls, response=response)
					else:
						result = ldap_connection.searchDn(filter=unicode(lookup_filter), base=container, scope=scope, sizelimit=sizelimit, serverctrls=serverctrls, response=response)
			else:
				if self.module:
					kwargs = {}
					if serverctrls and 'serverctrls' in inspect.getargspec(self.module.lookup).args:  # not every UDM handler supports serverctrls
						kwargs['serverctrls'] = serverctrls
						kwargs['response'] = response
					result = self.module.lookup(None, ldap_connection, filter_s, base=container, superordinate=superordinate, scope=scope, sizelimit=sizelimit, **kwargs)
				else:
					result = None
		except udm_errors.insufficientInformation:
			return []
		except udm_errors.ldapTimeout:
			raise SearchTimeoutError()
		except udm_errors.ldapSizelimitExceeded:
			raise SearchLimitReached()
		except (LDAPError, udm_errors.ldapError):
			raise
		except udm_errors.base as e:
			if isinstance(e, udm_errors.noObject):
				if superordinate and not ldap_connection.get(superordinate):
					raise SuperordinateDoesNotExist(superordinate)
				if container and not ldap_connection.get(container):
					raise ObjectDoesNotExist(container)
			UDM_Error(e).reraise()

		# call the garbage collector manually as many parallel request may cause the
		# process to use too much memory
		MODULE.info('Triggering garbage collection')
		gc.collect()

		return result

	def get(self, ldap_dn=None, superordinate=None, attributes=[]):
		"""Retrieves details for a given LDAP object"""
		ldap_connection, ldap_position = self.get_ldap_connection()
		try:
			if ldap_dn is not None:
				if superordinate is None:
					superordinate = udm_objects.get_superordinate(self.module, None, ldap_connection, ldap_dn)
				obj = self.module.object(None, ldap_connection, None, ldap_dn, superordinate, attributes=attributes)
				MODULE.info('Found LDAP object %s' % obj.dn)
				obj.open()
			else:
				obj = self.module.object(None, ldap_connection, None, '', superordinate, attributes=attributes)
		except (LDAPError, udm_errors.ldapError):
			raise
		except udm_errors.base as exc:
			MODULE.info('Failed to retrieve LDAP object: %s' % (exc,))
			if isinstance(exc, udm_errors.noObject):
				if superordinate and not ldap_connection.get(superordinate):
					raise SuperordinateDoesNotExist(superordinate)
			UDM_Error(exc).reraise()
		return obj

	def get_property(self, property_name):
		"""Returns details for a given property"""
		return getattr(self.module, 'property_descriptions', {}).get(property_name, None)

	@property
	def help_link(self):
		help_link = getattr(self.module, 'help_link', None)
		if isinstance(help_link, dict):
			defaults = {'lang': _('manual'), 'version': ucr.get('version/version', ''), 'section': ''}
			defaults.update(help_link)
			help_link = 'https://docs.software-univention.de/%(lang)s-%(version)s.html#%(section)s' % defaults
		return help_link

	@property
	def help_text(self):
		return getattr(self.module, 'help_text', None)

	@property
	def name(self):
		"""Internal name of the UDM module"""
		if self.module is None:
			return
		return self.module.module

	@property
	def columns(self):
		return [{'name': key, 'label': self.module.property_descriptions[key].short_description} for key in getattr(self.module, 'columns', [])]

	@property
	def subtitle(self):
		"""Returns the descriptive name of the UDM module without the part for the module group"""
		descr = getattr(self.module, 'short_description', getattr(self.module, 'module', ''))
		colon = descr.find(':')
		if colon > 0:
			return descr[colon + 1:].strip()
		return descr

	@property
	def title(self):
		"""Descriptive name of the UDM module"""
		return getattr(self.module, 'short_description', getattr(self.module, 'module', ''))

	@property
	def description(self):
		"""Descriptive text of the UDM module"""
		return getattr(self.module, 'long_description', '')

	@property
	def object_name(self):
		return getattr(self.module, 'object_name', self.title)

	@property
	def object_name_plural(self):
		return getattr(self.module, 'object_name_plural', self.object_name)

	@property
	def identifies(self):
		"""Property of the UDM module that identifies objects of this type"""
		for key, prop in getattr(self.module, 'property_descriptions', {}).items():
			if prop.identifies:
				MODULE.info('The property %s identifies to module objects %s' % (key, self.name))
				return key
		return None

	@property
	def virtual(self):
		return bool(getattr(self.module, 'virtual', False))

	@property
	def supports_pagination(self):
		return not self.virtual

	@property
	def childs(self):
		return bool(getattr(self.module, 'childs', False))

	@property
	def child_modules(self):
		"""List of child modules"""
		if self.module is None:
			return []
		MODULE.info('Collecting child modules ...')
		ldap_connection, ldap_position = self.get_ldap_connection()
		children = getattr(self.module, 'childmodules', None) or []
		modules = []
		for child in children:
			mod = UDM_Module(child, ldap_connection=ldap_connection, ldap_position=ldap_position)
			if not mod.module:
				continue
			MODULE.info('Found module %s' % str(mod))
			modules.append({
				'id': child,
				'label': mod.title,
				'object_name': mod.object_name,
				'object_name_plural': mod.object_name_plural,
			})
		if not modules:
			MODULE.info('No child modules were found')
			return [{
				'id': self.name,
				'label': self.title,
				'object_name': self.object_name,
				'object_name_plural': self.object_name_plural,
			}]
		return modules

	@property
	def has_tree(self):
		if not getattr(self.module, 'childmodules', None):
			return False
		return all(getattr(udm_modules.get(mod), 'childmodules', None) for mod in self.module.childmodules)

	@property
	def default_search_attrs(self):
		ret = []
		for key, prop in getattr(self.module, 'property_descriptions', {}).items():
			if prop.include_in_default_search:
				ret.append(key)
		return ret

	def obj_description(self, obj):
		description = None
		description_property_name = ucr.get('directory/manager/web/modules/%s/display' % self.name)
		if description_property_name:
			description = self.property_description(obj, description_property_name)
		if not description:
			description = udm_objects.description(obj)
		if description and description.isdigit():
			description = int(description)
		return description

	def property_description(self, obj, key):
		try:
			value = obj[key]
		except KeyError:
			return
		description_property = self.module.property_descriptions[key]
		if description_property:
			if description_property.multivalue:
				value = [description_property.syntax.tostring(x) for x in value]
			else:
				value = description_property.syntax.tostring(value)
		return value

	def is_policy_module(self):
		return self.name.startswith('policies/') and self.name != 'policies/policy'

	def get_layout(self, ldap_dn=None):
		"""Layout information"""
		ldap_connection, ldap_position = self.get_ldap_connection()
		layout = getattr(self.module, 'layout', [])
		if ldap_dn is not None:
			mod = get_module(None, ldap_dn, ldap_connection)
			if mod is not None and self.name == mod.name and self.is_policy_module():
				layout = copy.copy(layout)
				tab = udm_layout.Tab(_('Referencing objects'), _('Objects referencing this policy object'), layout=['$references$'])
				layout.append(tab)

		layout = AppAttributes.new_layout(self.name, layout)

		if layout and isinstance(layout[0], udm.tab):
			return self._parse_old_layout(layout)

		return layout

	def _parse_old_layout(self, layout):
		"""Parses old layout information"""
		tabs = []
		for tab in layout:
			data = {'name': tab.short_description, 'description': tab.long_description, 'advanced': tab.advanced, 'layout': [{'name': 'General', 'description': 'General settings', 'layout': []}]}
			for item in tab.fields:
				line = []
				for field in item:
					if isinstance(field, (list, tuple)):
						elem = [x.property for x in field]
					else:
						elem = field.property
					line.append(elem)
				data['layout'][0]['layout'].append(line)
			tabs.append(data)
		return tabs

	@property
	def password_properties(self):
		"""All properties with the syntax class passwd or userPasswd"""
		passwords = []
		for key, prop in getattr(self.module, 'property_descriptions', {}).items():
			if udm_syntax.is_syntax(prop.syntax, udm_syntax.passwd) or udm_syntax.is_syntax(prop.syntax, udm_syntax.userPasswd):
				passwords.append(key)

		return passwords

	def get_properties(self, ldap_dn=None):
		# scan the layout to only find elements which are displayed
		# special case: options and the dn: They are not explicitly specified in the module layout
		inLayout = set(('$options$', '$dn$'))

		def _scanLayout(_layout):
			if isinstance(_layout, list):
				for ielement in _layout:
					_scanLayout(ielement)
			elif isinstance(_layout, dict) and 'layout' in _layout:
				_scanLayout(_layout['layout'])
			elif isinstance(_layout, basestring):
				inLayout.add(_layout)
		_scanLayout(self.get_layout(ldap_dn))

		# only return properties that are in the layout
		properties = []
		for iprop in self.properties(ldap_dn):
			if iprop['id'] in inLayout:
				properties.append(iprop)

		return properties

	def properties(self, position_dn):
		"""All properties of the UDM module"""
		ldap_connection, ldap_position = self.get_ldap_connection()
		props = [{'id': '$dn$', 'type': 'HiddenInput', 'label': '', 'searchable': False}]
		for key, prop in getattr(self.module, 'property_descriptions', {}).items():
			if key == 'filler':
				continue  # FIXME: should be removed from all UDM modules
			if key in AppAttributes.options_for_module(self.name):
				# this is a proper (extended) attribute. but it acts as an option
				# in UMC for better usability
				continue
			item = {
				'id': key,
				'label': prop.short_description,
				'description': prop.long_description,
				'syntax': prop.syntax.name,
				'size': prop.size or prop.syntax.size,
				'required': bool(prop.required),
				'editable': bool(prop.may_change),
				'options': prop.options,
				'readonly': not bool(prop.editable),
				'searchable': not prop.dontsearch,
				'multivalue': bool(prop.multivalue),
				'identifies': bool(prop.identifies),
				'threshold': prop.threshold,
				'nonempty_is_default': bool(prop.nonempty_is_default),
				'readonly_when_synced': bool(prop.readonly_when_synced),
			}
			# TODO: remove this from javascript and add here
			#if ucr.is_true('ad/member') and 'synced' in obj.oldattr.get('univentionObjectFlag', [])
			#	if item['readonly_when_synced']:
			#		item['disabled'] = True
			if key in AppAttributes.attributes_for_module(self.name):
				AppAttributes.alter_item_for_prop(self.name, key, prop, item)

			# default value
			if prop.base_default is not None:
				if isinstance(prop.base_default, (list, tuple)):
					if prop.multivalue and prop.base_default and isinstance(prop.base_default[0], (list, tuple)):
						item['default'] = prop.base_default
					else:
						item['default'] = prop.base_default[0]
				else:
					item['default'] = str(prop.base_default)
			elif key == 'primaryGroup':  # set default for primaryGroup
				if position_dn:
					# settings/usertemplate requires a superordinate to be given. The superordinate is automatically searched for if omitted. We need to set the position here.
					# better would be to use the default position, but settings/usertemplate doesn't set one: Bug #43427
					ldap_position.setDn(position_dn)
				obj = self.module.object(None, ldap_connection, ldap_position, None)
				obj.open()
				default_group = obj.get('primaryGroup', None)
				if default_group is not None:
					item['default'] = default_group

			# read UCR configuration
			item.update(widget(prop.syntax, item))

			if prop.nonempty_is_default and 'default' not in item:
				# Some properties have an empty value as first item.
				# In this case this "empty" item is chosen as default
				# by the frontend for new objects. Sometimes this is
				# not wanted: The empty value as option is required
				# but for new objects the first non-empty value should
				# be the default value
				# E.g. users/user mailHomeServer; see Bug #33329, Bug #42903

				try:
					item['default'] = [x['id'] for x in read_syntax_choices(_get_syntax(prop.syntax.name), ldap_connection=ldap_connection, ldap_position=ldap_position) if x['id']][0]
				except IndexError:
					pass

			props.append(item)
		props.append({'id': '$options$', 'type': 'WidgetGroup', 'widgets': self.get_options()})
		props.append({'id': '$references$', 'type': 'umc/modules/udm/ReferencingObjects', 'readonly': True})

		return props

	def get_options(self, object_dn=None, udm_object=None):
		"""Returns the options of the module. If an LDAP DN or an UDM
		object instance is given the values of the options are set"""
		if object_dn is None and udm_object is None:
			obj_options = None
		else:
			if udm_object is None:
				obj = self.get(object_dn)
			else:
				obj = udm_object
			obj_options = getattr(obj, 'options', {})
			obj_options.extend(AppAttributes.options_for_obj(obj))

		options = []
		for name, opt in self.options.items():
			if obj_options is None:
				value = bool(opt.default)
			else:
				value = name in obj_options
			options.append({
				'id': name,
				'is_app_option': opt.is_app_option,
				'type': 'CheckBox',
				'icon': name if opt.is_app_option else '',
				'label': opt.short_description,
				'description': opt.long_description,
				'value': value,
				'editable': bool(opt.editable)
			})
		options.sort(key=lambda x: x['label'].lower())
		return options

	@property
	def options(self):
		"""List of defined options"""
		options = dict(getattr(self.module, 'options', {}))
		options.pop('default', None)  # don't display the "default" pseudo option in UMC
		options.update(AppAttributes.options_for_module(self.name))
		return options

	@property
	def operations(self):
		"""Allowed operations of the UDM module"""
		return getattr(self.module, 'operations', ['add', 'edit', 'remove', 'search', 'move'])

	@property
	def template(self):
		"""List of UDM module names of templates"""
		return getattr(self.module, 'template', None)

	def get_default_container(self):
		ldap_connection, ldap_position = self.get_ldap_connection()
		# TODO: move code below into UDM!
		if hasattr(self.module, 'policy_position_dn_prefix'):
			return '%s,cn=policies,%s' % (self.module.policy_position_dn_prefix, ldap_position.getBase())

		defaults = self.get_default_containers()
		return defaults[0] if defaults else ldap_position.getBase()

	def get_default_containers(self):
		"""List of LDAP DNs of default containers"""
		ldap_connection, ldap_position = self.get_ldap_connection()
		return self.module.object.get_default_containers(ldap_connection)

	@property
	def superordinate_names(self):
		return udm_modules.superordinate_names(self.module)

	@property
	def policies(self):
		"""Searches in all policy objects for the given object type and
		returns a list of all matching policy types"""

		ldap_connection, ldap_position = self.get_ldap_connection()
		policyTypes = udm_modules.policyTypes(self.name)
		if not policyTypes and self.childs:
			# allow all policies for containers
			# TODO: is using self.child correct here? shouldn't it better be container_modules()?
			policyTypes = [x for x in udm_modules.modules if x.startswith('policies/') and x != 'policies/policy']

		policies = []
		for policy in policyTypes:
			module = UDM_Module(policy, ldap_connection=ldap_connection, ldap_position=ldap_position)
			policies.append({'objectType': policy, 'label': module.title, 'description': module.description})

		return policies

	def get_policy_references(self, dn):
		ldap_connection, ldap_position = self.get_ldap_connection()
		if self.is_policy_module():  # TODO: move into the handlers/policies/*.py
			search_filter = filter_format("(&(objectClass=univentionPolicyReference)(univentionPolicyReference=%s))", (dn,))
			return read_syntax_choices(udm_syntax.LDAP_Search(filter=search_filter, viewonly=True), ldap_connection=ldap_connection, ldap_position=ldap_position)
		return []

	def get_references(self, obj):
		references = []
		for key, prop in getattr(self.module, 'property_descriptions', {}).items():
			if not obj.has_property(key):
				continue
			prop = self.get_property(key)
			syntax = prop.syntax() if inspect.isclass(prop.syntax) else prop.syntax
			if isinstance(syntax, udm_syntax.UDM_Objects) and syntax.key == 'dn' and len(syntax.udm_modules) == 1:
				object_type = syntax.udm_modules[0]
				dns = obj[key]
				if not isinstance(dns, (list, tuple)):
					dns = [dns]
				for dn in dns:
					references.append({'module': 'udm', 'property': key, 'flavor': 'navigation', 'objectType': object_type, 'id': dn, 'label': '%s: %s: %s' % (key, object_type, dn,), 'icon': 'udm-%s' % object_type.replace('/', '-')})
		return references + [dict(ref, property='__policies') for ref in self.get_policy_references(obj.dn)]

	@property
	def flavor(self):
		"""Tries to guess the flavor for a given module"""
		if self.name.startswith('container/'):
			return 'navigation'
		if self.name.startswith('dhcp/'):
			return 'dhcp/dhcp'
		if self.name.startswith('dns/'):
			return 'dns/dns'
		ldap_connection, ldap_position = self.get_ldap_connection()
		base, name = split_module_name(self.name)
		for module in [x for x in udm_modules.modules.keys() if x.startswith(base)]:
			mod = UDM_Module(module, ldap_connection=ldap_connection, ldap_position=ldap_position)
			children = getattr(mod.module, 'childmodules', [])
			if self.name in children:
				return mod.name
		return self.name

	@property
	def mapping(self):
		if hasattr(self.module, 'mapping'):
			return self.module.mapping
		return udm_mapping.mapping()


def container_modules():
	containers = []
	for name, mod in udm_modules.modules.items():
		if getattr(mod, 'childs', None):
			containers.append(name)

	return containers


def split_module_name(module_name):
	"""Splits a module name into category and internal name"""

	if '/' in module_name:
		parts = module_name.split('/', 1)
		if len(parts) == 2:
			return parts

	return (None, None)


def ldap_dn2path(ldap_dn, include_rdn=True):
	"""Returns a path representation of an LDAP DN. If include_rdn is
	false just the container of the given object is returned in a path
	representation"""

	ldap_base = ucr.get('ldap/base')
	if not ldap_base or not ldap_dn.lower().endswith(ldap_base.lower()):
		return ldap_dn
	rel_path = ldap_dn[:-(1 + len(ldap_base))]
	rel_path = explode_dn(rel_path, True)[int(not include_rdn):]
	return '%s:/%s' % ('.'.join(reversed(explode_dn(ldap_base, True))), '/'.join(reversed(rel_path)))


def get_module(flavor, ldap_dn, ldap_connection=None, ldap_position=None):
	"""Determines an UDM module handling the LDAP object identified by the given LDAP DN"""
	if flavor is None or flavor == 'navigation':
		base = None
	else:
		base, name = split_module_name(flavor)
	modules = udm_modules.objectType(None, ldap_connection, ldap_dn, module_base=base)

	if not modules:
		return None

	for module in modules:
		module = UDM_Module(module, ldap_connection=ldap_connection, ldap_position=ldap_position)
		if module.module is not None:
			return module

	MODULE.error('Identified modules %r for %s (flavor=%s) does not have a relating UDM module.' % (modules, ldap_dn, flavor))


def list_objects(container, object_type=None, ldap_connection=None, ldap_position=None):
	"""Yields UDM objects"""
	try:
		result = ldap_connection.search(base=container, scope='one')
	except (LDAPError, udm_errors.ldapError):
		raise
	except udm_errors.noObject:
		raise ObjectDoesNotExist(container)
	except udm_errors.ldapTimeout:
		raise SearchTimeoutError()
	except udm_errors.ldapSizelimitExceeded:
		raise SearchLimitReached()
	except udm_errors.base as exc:
		UDM_Error(exc).reraise()
	for dn, attrs in result:
		modules = udm_modules.objectType(None, ldap_connection, dn, attrs)
		if not modules:
			MODULE.warn('Could not identify LDAP object %r' % (dn,))
			continue
		if object_type == '$containers$' and not udm_modules.childs(modules[0]):
			continue
		if len(modules) > 1:
			MODULE.warn('Found multiple object types for %r: %r' % (dn, modules))
			MODULE.info('dn: %r, attrs: %r' % (dn, attrs))
		for mod in modules:
			module = UDM_Module(mod, ldap_connection=ldap_connection, ldap_position=ldap_position)
			if module.module:
				break

		if not module.module:
			MODULE.process('The UDM module %r could not be found. Ignoring LDAP object %r' % (modules[0], dn))
			continue

		try:
			yield (module, module.get(dn, attributes=attrs))
		except BaseException:
			try:
				yield (module, module.get(dn))
			except (UDM_Error, udm_errors.base):
				MODULE.error('Could not load object %r (%r) exception: %s' % (dn, module.module, traceback.format_exc()))


def split_module_attr(value):
	if ': ' in value:
		return value.split(': ', 1)
	return (None, value)


def _object_property_filter(module, object_property, object_property_value, show_hidden=True):
	if object_property in [None, 'None'] and module is not None:
		default_search_attrs = module.default_search_attrs
		if default_search_attrs and object_property_value not in [None, '*']:
			ret = '(|%s)' % ''.join('(%s=%s)' % (attr, object_property_value) for attr in default_search_attrs)
		else:
			ret = ''
	else:
		ret = ''
		prop = module.module.property_descriptions.get(object_property)
		if prop and issubclass(prop.syntax if inspect.isclass(prop.syntax) else type(prop.syntax), (udm_syntax.IStates, udm_syntax.boolean)):
			ret = prop.syntax.get_object_property_filter(object_property, object_property_value)
		if not ret:
			ret = '%s=%s' % (object_property, object_property_value)
			no_substring_value = object_property_value.strip('*')
			if no_substring_value and no_substring_value != object_property_value:
				ret = '(|(%s)(%s=%s))' % (ret, object_property, no_substring_value)
	if module is not None:
		hidden_flag_attribute = 'objectFlag'
		has_hidden_flag = module.get_property(hidden_flag_attribute) is not None
		if has_hidden_flag and not show_hidden:
			if ret:
				if not ret.startswith('('):
					ret = '(%s)' % ret
				ret = '(&(!(%s=hidden))%s)' % (hidden_flag_attribute, ret)
			else:
				ret = '!(%s=hidden)' % hidden_flag_attribute
	return ret


def _create_ldap_filter(syn, options, module=None):
	if syn.depends and syn.depends not in options:
		return None
	if callable(syn.udm_filter):
		filter_s = syn.udm_filter(options)
	else:
		filter_s = syn.udm_filter % options
	if options.get('objectProperty') and options.get('objectPropertyValue'):
		if filter_s and not filter_s.startswith('('):
			# make sure that the LDAP filter is wrapped in brackets
			filter_s = '(%s)' % filter_s
		object_property = options.get('objectProperty')
		object_property_value = options.get('objectPropertyValue')
		show_hidden = options.get('hidden', True)
		property_filter_s = _object_property_filter(module, object_property, object_property_value, show_hidden)
		if property_filter_s and not property_filter_s.startswith('('):
			# make sure that the LDAP filter is wrapped in brackets
			property_filter_s = '(%s)' % property_filter_s
		filter_s = '(&%s%s)' % (property_filter_s, filter_s)
	return filter_s


LDAP_ATTR_RE = re.compile(r'^%\(([^)]*)\)s$')  # '%(username)s' -> 'username'


def _get_syntax(syntax_name):
	if syntax_name not in udm_syntax.__dict__:
		return None
	return udm_syntax.__dict__[syntax_name]()


def search_syntax_choices_by_key(syn, key, ldap_connection, ldap_position):
	if issubclass(syn.__class__, udm_syntax.UDM_Objects):
		if syn.key == 'dn':
			module_search_options = {'scope': 'base', 'container': key}
			try:
				return read_syntax_choices(syn, {}, module_search_options, ldap_connection=ldap_connection, ldap_position=ldap_position)
			except udm_errors.base:  # TODO: which exception is raised here exactly?
				# invalid DN
				return []
		if syn.key is not None:
			match = LDAP_ATTR_RE.match(syn.key)
			if match:
				attr = match.groups()[0]
				options = {'objectProperty': attr, 'objectPropertyValue': key}
				return read_syntax_choices(syn, options, ldap_connection=ldap_connection, ldap_position=ldap_position)

	MODULE.warn('Syntax %r: No fast search function' % syn.name)
	# return them all, as there is no reason to filter after everything has loaded
	# frontend will cache it.
	return read_syntax_choices(syn, ldap_connection=ldap_connection, ldap_position=ldap_position)


def info_syntax_choices(syn, options={}, ldap_connection=None, ldap_position=None):
	if issubclass(syn.__class__, udm_syntax.UDM_Objects):
		size = 0
		if syn.static_values is not None:
			size += len(syn.static_values)
		for udm_module in syn.udm_modules:
			module = UDM_Module(udm_module, ldap_connection=ldap_connection, ldap_position=ldap_position)
			if module.module is None:
				continue
			filter_s = _create_ldap_filter(syn, options, module)
			if filter_s is not None:
				try:
					size += len(module.search(filter=filter_s, simple=not syn.use_objects))
				except (udm_errors.ldapSizelimitExceeded, SearchLimitReached):
					return {'performs_well': True, 'size_limit_exceeded': True}
		return {'size': size, 'performs_well': True}
	return {'size': 0, 'performs_well': False}


def read_syntax_choices(syn, options={}, module_search_options={}, ldap_connection=None, ldap_position=None):
	syn = syn() if inspect.isclass(syn) else syn
	syntax_name = syn.name

	choices = getattr(syn, 'choices', [])

	if issubclass(syn.__class__, udm_syntax.UDM_Objects):
		choices = []
		# try to avoid using the slow udm interface
		simple = False
		attr = set()
		if not syn.use_objects:
			attr.update(re.findall(r'%\(([^)]+)\)', syn.key))
			if syn.label:
				attr.update(re.findall(r'%\(([^)]+)\)', syn.label))
			for udm_module in syn.udm_modules:
				module = UDM_Module(udm_module, ldap_connection=ldap_connection, ldap_position=ldap_position)
				if not module.allows_simple_lookup():
					break
				if module is not None:
					mapping = module.module.mapping
					if not all([mapping.mapName(att) for att in attr]):
						break
			else:
				simple = True
			if not simple:
				MODULE.warn('Syntax %s wants to get optimizations but may not. This is a Bug! We provide a fallback but the syntax will respond much slower than it could!' % syntax_name)

		def extract_key_label(syn, dn, info):
			key = label = None
			if syn.key == 'dn':
				key = dn
			else:
				try:
					key = syn.key % info
				except KeyError:
					pass
			if syn.label == 'dn':
				label = dn
			elif syn.label is None:
				pass
			else:
				try:
					label = syn.label % info
				except KeyError:
					pass
			return key, label
		if not simple:
			def map_choices(obj_list):
				result = []
				for obj in obj_list:
					# first try it without obj.open() (expensive)
					key, label = extract_key_label(syn, obj.dn, obj.info)
					if key is None or label is None:
						obj.open()
						key, label = extract_key_label(syn, obj.dn, obj.info)
						if key is None:
							# ignore the entry as the key is important for a selection, there
							# is no sensible fallback for the key (Bug #26994)
							continue
						if label is None:
							# fallback to the default description as this is just what displayed
							# to the user (Bug #26994)
							label = udm_objects.description(obj)
					result.append((key, label))
				return result

			for udm_module in syn.udm_modules:
				module = UDM_Module(udm_module, ldap_connection=ldap_connection, ldap_position=ldap_position)
				if module.module is None:
					continue
				filter_s = _create_ldap_filter(syn, options, module)
				if filter_s is not None:
					search_options = {'filter': filter_s}
					search_options.update(module_search_options)
					choices.extend(map_choices(module.search(**search_options)))
		else:
			for udm_module in syn.udm_modules:
				module = UDM_Module(udm_module, ldap_connection=ldap_connection, ldap_position=ldap_position)
				if module.module is None:
					continue
				filter_s = _create_ldap_filter(syn, options, module)
				if filter_s is not None:
					if filter_s and not filter_s.startswith('('):
						filter_s = '(%s)' % filter_s
					mapping = module.module.mapping
					ldap_attr = [mapping.mapName(att) for att in attr]
					search_options = {'filter': filter_s, 'simple': True}
					search_options.update(module_search_options)
					if ldap_attr:
						search_options['simple_attrs'] = ldap_attr
						result = module.search(**search_options)
						for dn, ldap_map in result:
							info = udm_mapping.mapDict(mapping, ldap_map)
							key, label = extract_key_label(syn, dn, info)
							if key is None:
								continue
							if label is None:
								label = ldap_connection.explodeDn(dn, 1)[0]
							choices.append((key, label))
					else:
						keys = module.search(**search_options)
						if syn.label == 'dn':
							labels = keys
						else:
							labels = [ldap_connection.explodeDn(dn, 1)[0] for dn in keys]
						choices.extend(zip(keys, labels))
	elif issubclass(syn.__class__, udm_syntax.UDM_Attribute):
		choices = []

		def filter_choice(obj):
			# if attributes does not exist or is empty
			return syn.attribute in obj.info and obj.info[syn.attribute]

		def map_choice(obj):
			obj.open()
			MODULE.info('Loading choices from %s: %s' % (obj.dn, obj.info))
			try:
				values = obj.info[syn.attribute]
			except KeyError:
				MODULE.warn('Object has no attribute %r' % (syn.attribute,))
				# this happens for example in PrinterDriverList
				# if the ldap schema is not installed
				# and thus no 'printmodel' attribute is known.
				return []
			if not isinstance(values, (list, tuple)):  # single value
				values = [values]
			if syn.is_complex:
				return [(x[syn.key_index], x[syn.label_index]) for x in values]
			if syn.label_format is not None:
				_choices = []
				for value in values:
					obj.info['$attribute$'] = value
					_choices.append((value, syn.label_format % obj.info))
				return _choices
			return [(x, x) for x in values]

		module = UDM_Module(syn.udm_module, ldap_connection=ldap_connection, ldap_position=ldap_position)
		if module.module is None:
			return []
		MODULE.info('Found syntax %s with udm_module property' % syntax_name)
		if syn.udm_filter == 'dn':
			choices = map_choice(module.get(options[syn.depends]))
		else:
			filter_s = _create_ldap_filter(syn, options, module)
			if filter_s is not None:
				for element in map(map_choice, filter(filter_choice, module.search(filter=filter_s))):
					for item in element:
						choices.append(item)
	elif issubclass(syn.__class__, udm_syntax.ldapDn) and hasattr(syn, 'searchFilter'):
		try:
			result = ldap_connection.searchDn(filter=syn.searchFilter)
		except udm_errors.base:
			MODULE.process('Failed to initialize syntax class %s' % syntax_name)
			return []
		choices = []
		for dn in result:
			dn_list = ldap_connection.explodeDn(dn)
			choices.append((dn, dn_list[0].split('=', 1)[1]))

	choices = [{'id': x[0], 'label': x[1]} for x in choices]

	if issubclass(syn.__class__, udm_syntax.LDAP_Search):
		options = options.get('options', {})
		try:
			syntax = udm_syntax.LDAP_Search(options['syntax'], options['filter'], options['attributes'], options['base'], options['value'], options['viewonly'], options['empty'], options['empty_end'])
		except KeyError:
			syntax = syn

		if '$dn$' in options:
			filter_mod = get_module(None, options['$dn$'], ldap_connection)
			if filter_mod:
				obj = filter_mod.get(options['$dn$'])
				syntax.filter = udm.pattern_replace(syntax.filter, obj)

		syntax._prepare(ldap_connection, syntax.filter)

		choices = []
		for item in syntax.values:
			if syntax.viewonly:
				dn, display_attr = item
			else:
				dn, store_pattern, display_attr = item

			if display_attr:
				# currently we just support one display attribute
				mod_display, display = split_module_attr(display_attr[0])
				module = get_module(mod_display, dn, ldap_connection)  # mod_display might be None
			else:
				module = get_module(None, dn, ldap_connection)
				display = None
			if not module:
				continue
			obj = module.get(dn)
			if not obj:
				continue

			# find the value to store
			if not syntax.viewonly:
				mod_store, store = split_module_attr(store_pattern)
				if store == 'dn':
					id = dn
				elif store in obj:
					id = obj[store]
				elif store in obj.oldattr and obj.oldattr[store]:
					id = obj.oldattr[store][0]
				else:
					# no valid store object, ignore
					MODULE.warn('LDAP_Search syntax %r: %r is no valid property for object %r - ignoring entry.' % (syntax.name, store, dn))
					continue

			# find the value to display
			if display == 'dn':
				label = dn
			elif display is None:  # if view-only and in case of error
				label = '%s: %s' % (module.title, obj[module.identifies])
			else:
				if display in obj:
					label = obj[display]
				elif display in obj.oldattr and obj.oldattr[display]:
					label = obj.oldattr[display][0]
				else:
					label = 'Unknown attribute %s' % display

			# create list entry
			if syntax.viewonly:
				choices.append({'module': 'udm', 'flavor': module.flavor or 'navigation', 'objectType': module.name, 'id': dn, 'label': label, 'icon': 'udm-%s' % module.name.replace('/', '-')})
			else:
				choices.append({'module': 'udm', 'flavor': module.flavor or 'navigation', 'objectType': module.name, 'id': id, 'label': label, 'icon': 'udm-%s' % module.name.replace('/', '-')})

	# sort choices before inserting / appending some special items
	choices = sorted(choices, key=lambda choice: choice['label'])

	if issubclass(syn.__class__, (udm_syntax.UDM_Objects, udm_syntax.UDM_Attribute)):
		if isinstance(syn.static_values, (tuple, list)):
			for value in syn.static_values:
				choices.insert(0, {'id': value[0], 'label': value[1]})
		if syn.empty_value:
			choices.insert(0, {'id': '', 'label': ''})
	elif issubclass(syn.__class__, udm_syntax.LDAP_Search):
		# then append empty value
		if syntax.addEmptyValue:
			choices.insert(0, {'id': '', 'label': ''})
		elif syntax.appendEmptyValue:
			choices.append({'id': '', 'label': ''})

	return choices


if __name__ == '__main__':
	set_bind_function(lambda lo: lo.bind('uid=Administrator,cn=users,%s' % (ucr['ldap/base'],), 'univention'))
