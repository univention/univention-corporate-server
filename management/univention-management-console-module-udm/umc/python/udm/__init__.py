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

import copy
import re
import os
import shutil
import tempfile
import locale
import urllib
import urllib2
import traceback
import inspect

import notifier
import notifier.threads

from ldap import LDAPError, INVALID_CREDENTIALS
from univention.lib.i18n import Translation
from univention.management.console.config import ucr
from univention.management.console.modules import Base, UMC_OptionTypeError, UMC_OptionMissing, UMC_CommandError, UMC_Error
from univention.management.console.modules.decorators import simple_response, sanitize, multi_response, prevent_xsrf_check, allow_get_request
from univention.management.console.modules.sanitizers import (
	Sanitizer, LDAPSearchSanitizer, EmailSanitizer, ChoicesSanitizer,
	ListSanitizer, StringSanitizer, DictSanitizer, BooleanSanitizer,
	DNSanitizer
)
from univention.management.console.modules.mixins import ProgressMixin
from univention.management.console.log import MODULE
from univention.management.console.ldap import get_user_connection
from univention.management.console.protocol.session import TEMPUPLOADDIR

import univention.admin.syntax as udm_syntax
import univention.admin.modules as udm_modules
import univention.admin.objects as udm_objects
import univention.admin.uexceptions as udm_errors
import univention.admin.uldap as udm_uldap

from univention.config_registry import handler_set

import univention.directory.reports as udr

from .udm_ldap import (
	UDM_Error, UDM_Module,
	ldap_dn2path, get_module, read_syntax_choices, list_objects, _get_syntax,
	LDAP_Connection, set_bind_function, container_modules,
	info_syntax_choices, search_syntax_choices_by_key,
	UserWithoutDN, ObjectDoesNotExist, SuperordinateDoesNotExist, NoIpLeft,
	LDAP_AuthenticationFailed
)
from .tools import LicenseError, LicenseImport, install_opener, urlopen, dump_license, check_license

USE_ASTERISKS = ucr.is_true('directory/manager/web/allow_wildcard_search', True)
ADD_ASTERISKS = USE_ASTERISKS and ucr.is_true('directory/manager/web/auto_substring_search', True)

_ = Translation('univention-management-console-module-udm').translate


def sanitize_func(sanitizer_func):
	from univention.management.console.modules.decorators import copy_function_meta_data, sanitize

	def _decorated(function):
		def _response(self, request):
			sanitizer_parameters = sanitizer_func(self, request)
			if isinstance(sanitizer_parameters, dict):
				sanitizer = sanitize(**sanitizer_parameters)
			else:  # if isinstance(sanitizer_parameters, (list, tuple)):
				sanitizer = sanitize(*sanitizer_parameters)
			return sanitizer(function)(self, request)
		copy_function_meta_data(function, _response)
		return _response
	return _decorated


def module_from_request(func):
	def _decorated(self, request, *a, **kw):
		request.options['module'] = self._get_module_by_request(request)
		return func(self, request, *a, **kw)
	return _decorated


def bundled(func):
	def _decoarated(self, request):
		bundled = isinstance(request.options, (list, tuple))
		if not bundled:
			ret = func(self, request)
		else:
			options = request.options
			ret = [func(self, request) for request.options in options]
		self.finished(request.id, ret)
	return _decoarated


class ObjectPropertySanitizer(StringSanitizer):

	def __init__(self, **kwargs):
		"""A LDAP attribute name.
			must at least be 1 character long.

			This sanitizer prevents LDAP search filter injections in the attribute name.

			TODO: in theory we should only allow existing attributes for the request object(/object type)
		"""
		args = dict(
			minimum=1,
			regex_pattern=r'^[\w\d\-;]+$'
		)
		args.update(kwargs)
		StringSanitizer.__init__(self, **args)


class PropertySearchSanitizer(LDAPSearchSanitizer):

	def _sanitize(self, value, name, further_arguments):
		object_type = further_arguments.get('objectType')
		property_ = further_arguments.get('objectProperty')
		add_asterisks, use_asterisks = self.add_asterisks, self.use_asterisks
		if object_type and property_ and UDM_Module(object_type).module:
			prop = UDM_Module(object_type).module.property_descriptions.get(property_)
			# If the property is represented as a Checkbox in the frontend then
			# we get True/False as search value.
			# We need to make sure that the sanitizer rewrites this to the
			# correct thruthy/falsy string of the syntax class and not add asterisks.
			if prop and issubclass(prop.syntax if inspect.isclass(prop.syntax) else type(prop.syntax), (udm_syntax.IStates, udm_syntax.boolean)):
				self.use_asterisks = False
				self.add_asterisks = False
				value = prop.syntax.sanitize_property_search_value(value)
		try:
			return super(PropertySearchSanitizer, self)._sanitize(value, name, further_arguments)
		finally:
			self.add_asterisks, self.use_asterisks = add_asterisks, use_asterisks


class Instance(Base, ProgressMixin):

	def __init__(self):
		Base.__init__(self)
		self.reports_cfg = None
		self.modules_with_childs = []
		self.__license_checks = set()
		install_opener(ucr)

	def init(self):
		if not self.user_dn:
			raise UserWithoutDN(self._username)

		MODULE.info('Initializing module as user %r' % (self.user_dn,))
		set_bind_function(self.bind_user_connection)

		# read user settings and initial UDR
		self.reports_cfg = udr.Config()
		self.modules_with_childs = container_modules()

	def set_locale(self, _locale):
		super(Instance, self).set_locale(_locale)
		locale.setlocale(locale.LC_TIME, _locale)

	def error_handling(self, etype, exc, etraceback):
		super(Instance, self).error_handling(etype, exc, etraceback)
		if isinstance(exc, (udm_errors.authFail, INVALID_CREDENTIALS)):
			MODULE.warn('Authentication failed: %s' % (exc,))
			raise LDAP_AuthenticationFailed()
		if isinstance(exc, (udm_errors.base, LDAPError)):
			MODULE.error(''.join(traceback.format_exception(etype, exc, etraceback)))

	def bind_user_connection(self, lo):
		super(Instance, self).bind_user_connection(lo)
		self.require_license(lo)

	def require_license(self, lo):
		if id(lo) in self.__license_checks:
			return
		self.__license_checks.add(id(lo))
		try:
			import univention.admin.license  # noqa: F401
		except ImportError:
			return  # GPL Version
		try:
			check_license(lo, True)
		except LicenseError:
			lo.allow_modify = False
		lo.requireLicense()

	def get_ldap_connection(self):
		try:
			lo, po = get_user_connection(bind=self.bind_user_connection, write=True)
		except (LDAPError, udm_errors.ldapError):
			lo, po = get_user_connection(bind=self.bind_user_connection, write=True)
		return lo, udm_uldap.position(lo.base)

	def get_module(self, flavor, ldap_dn):
		return get_module(flavor, ldap_dn, self.get_ldap_connection()[0])

	def _get_module_by_request(self, request, object_type=None):
		"""Tries to determine the UDM module to use. If no specific
		object type is given the request option 'objectType' is used. In
		case none if this leads to a valid object type the request
		flavor is chosen. Failing all this will raise in
		UMC_OptionMissing exception. On success a UMC_Module object is
		returned."""
		if object_type is None:
			object_type = request.options.get('objectType')

		module_name = object_type
		if not module_name or 'all' == module_name:
			module_name = request.flavor

		if not module_name or module_name == 'navigation':
			raise UMC_OptionMissing(_('No flavor or valid UDM module name specified'))

		return UDM_Module(module_name)

	@LDAP_Connection
	def license(self, request, ldap_connection=None, ldap_position=None):
		message = None
		try:
			check_license(ldap_connection)
		except LicenseError as exc:
			message = str(exc)

		self.finished(request.id, {'message': message})

	@LDAP_Connection
	def license_info(self, request, ldap_connection=None, ldap_position=None):
		license_data = {}
		try:
			import univention.admin.license as udm_license
		except:
			license_data['licenseVersion'] = 'gpl'
		else:
			license_data['licenseVersion'] = udm_license._license.version
			if udm_license._license.version == '1':
				for item in ('licenses', 'real'):
					license_data[item] = {}
					for lic_type in ('CLIENT', 'ACCOUNT', 'DESKTOP', 'GROUPWARE'):
						count = getattr(udm_license._license, item)[udm_license._license.version][getattr(udm_license.License, lic_type)]
						if isinstance(count, basestring):
							try:
								count = int(count)
							except:
								count = None
						license_data[item][lic_type.lower()] = count

				if 'UGS' in udm_license._license.types:
					udm_license._license.types = [x for x in udm_license._license.types if x != 'UGS']
			elif udm_license._license.version == '2':
				for item in ('licenses', 'real'):
					license_data[item] = {}
					for lic_type in ('SERVERS', 'USERS', 'MANAGEDCLIENTS', 'CORPORATECLIENTS'):
						count = getattr(udm_license._license, item)[udm_license._license.version][getattr(udm_license.License, lic_type)]
						if isinstance(count, basestring):
							try:
								count = int(count)
							except:
								count = None
						license_data[item][lic_type.lower()] = count
				license_data['keyID'] = udm_license._license.licenseKeyID
				license_data['support'] = udm_license._license.licenseSupport
				license_data['premiumSupport'] = udm_license._license.licensePremiumSupport

			license_data['licenseTypes'] = udm_license._license.types
			license_data['oemProductTypes'] = udm_license._license.oemProductTypes
			license_data['endDate'] = udm_license._license.endDate
			license_data['baseDN'] = udm_license._license.licenseBase
			free_license = ''
			if license_data['baseDN'] == 'Free for personal use edition':
				free_license = 'ffpu'
			if license_data['baseDN'] == 'UCS Core Edition':
				free_license = 'core'
			if free_license:
				license_data['baseDN'] = ucr.get('ldap/base', '')
			license_data['freeLicense'] = free_license
			license_data['sysAccountsFound'] = udm_license._license.sysAccountsFound

		self.finished(request.id, license_data)

	@prevent_xsrf_check
	@LDAP_Connection
	def license_import(self, request, ldap_connection=None, ldap_position=None):
		filename = None
		if isinstance(request.options, (list, tuple)) and request.options:
			# file upload
			filename = request.options[0]['tmpfile']
			if not os.path.realpath(filename).startswith(TEMPUPLOADDIR):
				self.finished(request.id, [{'success': False, 'message': 'invalid file path'}])
				return
		else:
			self.required_options(request, 'license')
			lic = request.options['license']

			# Replace non-breaking space with a normal space
			# https://forge.univention.org/bugzilla/show_bug.cgi?id=30098
			lic = lic.replace(unichr(160), " ")

			lic_file = tempfile.NamedTemporaryFile(delete=False)
			lic_file.write(lic)
			lic_file.close()
			filename = lic_file.name

		def _error(msg=None):
			self.finished(request.id, [{
				'success': False, 'message': msg
			}])

		try:
			with open(filename, 'rb') as fd:
				# check license and write it to LDAP
				importer = LicenseImport(fd)
				importer.check(ucr.get('ldap/base', ''))
				importer.write(ldap_connection)
		except (ValueError, AttributeError, LDAPError) as exc:
			MODULE.error('License import failed (malformed LDIF): %r' % (exc, ))
			# AttributeError: missing univentionLicenseBaseDN
			# ValueError raised by ldif.LDIFParser when e.g. dn is duplicated
			# LDAPError e.g. LDIF contained non existing attributes
			if isinstance(exc, LDAPError) and len(exc.args) and isinstance(exc.args[0], dict) and exc.args[0].get('info'):
				_error(_('LDAP error: %s.') % exc.args[0].get('info'))
			else:
				_error()
			return
		except LicenseError as exc:
			MODULE.error('LicenseImport check failed: %r' % (exc, ))
			_error(str(exc))
			return
		finally:
			os.unlink(filename)

		self.finished(request.id, [{'success': True}])

	@multi_response(progress=[_('Moving %d object(s)'), _('%($dn$)s moved')])
	def move(self, iterator, object, options):
		for object, options in iterator:
			if 'container' not in options:
				yield {'$dn$': object, 'success': False, 'details': _('The destination is missing')}
				continue
			module = self.get_module(None, object)
			if not module:
				yield {'$dn$': object, 'success': False, 'details': _('Could not identify the given LDAP object')}
			elif 'move' not in module.operations:
				yield {'$dn$': object, 'success': False, 'details': _('This object can not be moved')}
			else:
				try:
					module.move(object, options['container'])
					yield {'$dn$': object, 'success': True}
				except UDM_Error as e:
					yield {'$dn$': object, 'success': False, 'details': str(e)}

	@sanitize(DictSanitizer(dict(
		object=DictSanitizer(dict(), required=True),
		options=DictSanitizer(dict(
			objectType=StringSanitizer(required=True)
		), required=True)
	), required=True))
	def add(self, request):
		"""Creates LDAP objects.

		requests.options = [ { 'options' : {}, 'object' : {} }, ... ]

		return: [ { '$dn$' : <LDAP DN>, 'success' : (True|False), 'details' : <message> }, ... ]
		"""

		def _thread(request):
			result = []
			for obj in request.options:
				options = obj.get('options', {})
				properties = obj.get('object', {})

				module = self._get_module_by_request(request, object_type=options.get('objectType'))
				if '$labelObjectType$' in properties:
					del properties['$labelObjectType$']
				try:
					dn = module.create(properties, container=options.get('container'), superordinate=options.get('superordinate'))
					result.append({'$dn$': dn, 'success': True})
				except UDM_Error as e:
					result.append({'$dn$': e.dn, 'success': False, 'details': str(e)})

			return result

		thread = notifier.threads.Simple('Get', notifier.Callback(_thread, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	@sanitize(DictSanitizer(dict(
		object=DictSanitizer({
			'$dn$': StringSanitizer(required=True)
		}, required=True),
	)), required=True)
	def put(self, request):
		"""Modifies the given list of LDAP objects.

		requests.options = [ { 'options' : {}, 'object' : {} }, ... ]

		return: [ { '$dn$' : <LDAP DN>, 'success' : (True|False), 'details' : <message> }, ... ]
		"""

		def _thread(request):
			result = []
			for obj in request.options:
				properties = obj.get('object') or {}
				ldap_dn = properties['$dn$']
				module = self.get_module(request.flavor, ldap_dn)
				if module is None:
					if len(request.options) == 1:
						raise ObjectDoesNotExist(ldap_dn)
					result.append({'$dn$': ldap_dn, 'success': False, 'details': _('LDAP object does not exist.')})
					continue
				MODULE.info('Modifying LDAP object %s' % (ldap_dn,))
				if '$labelObjectType$' in properties:
					del properties['$labelObjectType$']
				try:
					module.modify(properties)
					result.append({'$dn$': ldap_dn, 'success': True})
				except UDM_Error as exc:
					result.append({'$dn$': ldap_dn, 'success': False, 'details': str(exc)})
			return result

		thread = notifier.threads.Simple('Get', notifier.Callback(_thread, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	def remove(self, request):
		"""Removes the given list of LDAP objects.

		requests.options = [ { 'object' : <LDAP DN>, 'options' { 'cleanup' : (True|False), 'recursive' : (True|False) } }, ... ]

		return: [ { '$dn$' : <LDAP DN>, 'success' : (True|False), 'details' : <message> }, ... ]
		"""

		def _thread(request):
			result = []
			for item in request.options:
				ldap_dn = item.get('object')
				options = item.get('options', {})
				module = self.get_module(request.flavor, ldap_dn)
				if module is None:
					result.append({'$dn$': ldap_dn, 'success': False, 'details': _('LDAP object could not be identified')})
					continue
				try:
					module.remove(ldap_dn, options.get('cleanup', False), options.get('recursive', False))
					result.append({'$dn$': ldap_dn, 'success': True})
				except UDM_Error as e:
					result.append({'$dn$': ldap_dn, 'success': False, 'details': str(e)})

			return result

		thread = notifier.threads.Simple('Get', notifier.Callback(_thread, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	@simple_response
	def meta_info(self, objectType):
		module = UDM_Module(objectType)
		if module:
			return {
				'help_link': module.help_link,
				'help_text': module.help_text,
				'columns': module.columns,
				'has_tree': module.has_tree,
			}

	def get(self, request):
		"""Retrieves the given list of LDAP objects. Password property will be removed.

		requests.options = [ <LDAP DN>, ... ]

		return: [ { '$dn$' : <LDAP DN>, <object properties> }, ... ]
		"""

		MODULE.info('Starting thread for udm/get request')
		thread = notifier.threads.Simple('Get', notifier.Callback(self._get, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	def copy(self, request):
		thread = notifier.threads.Simple('Copy', notifier.Callback(self._get, request, True), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	def _get(self, request, copy=False):
		def _remove_uncopyable_properties(obj):
			if not copy:
				return
			for name, p in obj.descriptions.items():
				if not p.copyable:
					obj.info.pop(name, None)
		result = []
		for ldap_dn in request.options:
			if request.flavor == 'users/self':
				ldap_dn = self._user_dn
			module = self.get_module(request.flavor, ldap_dn)
			if module is None:
				raise ObjectDoesNotExist(ldap_dn)
			else:
				obj = module.get(ldap_dn)
				if obj:
					_remove_uncopyable_properties(obj)
					obj.set_defaults = True
					obj.set_default_values()
					_remove_uncopyable_properties(obj)
					props = obj.info
					empty_props_with_default_set = {}
					for key in obj.info.keys():
						if obj.hasChanged(key):
							empty_props_with_default_set[key] = {
								'default_value': obj.info[key],
								'prevent_umc_default_popup': obj.descriptions[key].prevent_umc_default_popup
							}
					props['$empty_props_with_default_set$'] = empty_props_with_default_set

					for passwd in module.password_properties:
						if passwd in props:
							del props[passwd]
					if not copy:
						props['$dn$'] = obj.dn
					props['$options$'] = {}
					for opt in module.get_options(udm_object=obj):
						props['$options$'][opt['id']] = opt['value']
					props['$policies$'] = {}
					for policy in obj.policies:
						pol_mod = self.get_module(None, policy)
						if pol_mod and pol_mod.name:
							props['$policies$'].setdefault(pol_mod.name, []).append(policy)
					props['$labelObjectType$'] = module.title
					props['$flags$'] = obj.oldattr.get('univentionObjectFlag', [])
					props['$operations$'] = module.operations
					props['$references$'] = module.get_policy_references(ldap_dn)
					result.append(props)
				else:
					MODULE.process('The LDAP object for the LDAP DN %s could not be found' % ldap_dn)
		return result

	@sanitize(
		objectPropertyValue=PropertySearchSanitizer(
			add_asterisks=ADD_ASTERISKS,
			use_asterisks=USE_ASTERISKS,
			further_arguments=['objectType', 'objectProperty'],
		),
		objectProperty=ObjectPropertySanitizer(required=True),
		fields=ListSanitizer(),
	)
	def query(self, request):
		"""Searches for LDAP objects and returns a few properties of the found objects

		requests.options = {}
			'objectType' -- the object type to search for (default: if not given the flavor is used)
			'objectProperty' -- the object property that should be scanned
			'objectPropertyValue' -- the filter that should be found in the property
			'fields' -- the properties which should be returned
			'container' -- the base container where the search should be started (default: LDAP base)
			'superordinate' -- the superordinate object for the search (default: None)
			'scope' -- the search scope (default: sub)

		return: [ { '$dn$' : <LDAP DN>, 'objectType' : <UDM module name>, 'path' : <location of object> }, ... ]
		"""

		def _thread(request):
			ucr.load()
			module = self._get_module_by_request(request)

			superordinate = request.options.get('superordinate')
			if superordinate == 'None':
				superordinate = None
			elif superordinate is not None:
				MODULE.info('Query defines a superordinate %s' % superordinate)
				mod = self.get_module(request.flavor, superordinate)
				if mod is not None:
					MODULE.info('Found UDM module %r for superordinate %s' % (mod.name, superordinate))
					superordinate = mod.get(superordinate)
					if not request.options.get('container'):
						request.options['container'] = superordinate.dn
				else:
					raise SuperordinateDoesNotExist(superordinate)

			container = request.options.get('container')
			objectProperty = request.options['objectProperty']
			objectPropertyValue = request.options['objectPropertyValue']
			scope = request.options.get('scope', 'sub')
			hidden = request.options.get('hidden')
			fields = (set(request.options.get('fields', []) or []) | set([objectProperty])) - set(['name', 'None'])
			result = module.search(container, objectProperty, objectPropertyValue, superordinate, scope=scope, hidden=hidden)
			if result is None:
				return []

			entries = []
			object_type = request.options.get('objectType', request.flavor)

			for obj in result:
				if obj is None:
					continue
				module = self.get_module(object_type, obj.dn)
				if module is None:
					# This happens when concurrent a object is removed between the module.search() and self.get_module() call
					MODULE.warn('LDAP object does not exists %s (flavor: %s). The object is ignored.' % (obj.dn, request.flavor))
					continue
				entry = {
					'$dn$': obj.dn,
					'$childs$': module.childs,
					'$flags$': obj.oldattr.get('univentionObjectFlag', []),
					'$operations$': module.operations,
					'objectType': module.name,
					'labelObjectType': module.subtitle,
					'name': module.obj_description(obj),
					'path': ldap_dn2path(obj.dn, include_rdn=False)
				}
				if '$value$' in fields:
					entry['$value$'] = [module.property_description(obj, column['name']) for column in module.columns]
				for field in fields - set(module.password_properties) - set(entry.keys()):
					entry[field] = module.property_description(obj, field)
				entries.append(entry)
			return entries

		thread = notifier.threads.Simple('Query', notifier.Callback(_thread, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	def reports_query(self, request):
		"""Returns a list of reports for the given object type"""
		# i18n: translattion for univention-directory-reports
		_('PDF Document')
		self.finished(request.id, [{'id': name, 'label': _(name)} for name in sorted(self.reports_cfg.get_report_names(request.flavor))])

	def sanitize_reports_create(self, request):
		choices = self.reports_cfg.get_report_names(request.flavor)
		return dict(
			report=ChoicesSanitizer(choices=choices, required=True),
			objects=ListSanitizer(DNSanitizer(minimum=1), required=True, min_elements=1)
		)

	@sanitize_func(sanitize_reports_create)
	def reports_create(self, request):
		"""Creates a report for the given LDAP DNs and returns the URL to access the file"""

		@LDAP_Connection
		def _thread(request, ldap_connection=None, ldap_position=None):
			report = udr.Report(ldap_connection)
			try:
				report_file = report.create(request.flavor, request.options['report'], request.options['objects'])
			except udr.ReportError as exc:
				raise UMC_Error(str(exc))

			path = '/usr/share/univention-management-console-module-udm/'
			filename = os.path.join(path, os.path.basename(report_file))

			shutil.move(report_file, path)
			os.chmod(filename, 0o600)
			url = '/univention/command/udm/reports/get?report=%s' % (urllib.quote(os.path.basename(report_file)),)
			return {'URL': url}

		thread = notifier.threads.Simple('ReportsCreate', notifier.Callback(_thread, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	@allow_get_request
	@sanitize(report=StringSanitizer(required=True))
	def reports_get(self, request):
		report = request.options['report']
		path = '/usr/share/univention-management-console-module-udm/'
		filename = os.path.join(path, os.path.basename(report))
		try:
			with open(filename) as fd:
				self.finished(request.id, fd.read(), mimetype='text/csv' if report.endswith('.csv') else 'application/pdf')
		except EnvironmentError:
			raise UMC_Error(_('The report does not exists. Please create a new one.'), status=404)

	def values(self, request):
		"""Returns the default search pattern/value for the given object property

		requests.options = {}
			'objectProperty' -- the object property that should be scanned

		return: <value>
		"""
		module = self._get_module_by_request(request)
		property_name = request.options.get('objectProperty')
		if property_name == 'None':
			result = None
		else:
			result = module.get_default_values(property_name)
		self.finished(request.id, result)

	@sanitize(
		networkDN=StringSanitizer(required=True),
		increaseCounter=BooleanSanitizer(default=False)
	)
	def network(self, request):
		"""Returns the next IP configuration based on the given network object

		requests.options = {}
			'networkDN' -- the LDAP DN of the network object
			'increaseCounter' -- if given and set to True, network object counter for IP addresses is increased

		return: {}
		"""
		module = UDM_Module('networks/network')
		obj = module.get(request.options['networkDN'])

		if not obj:
			raise ObjectDoesNotExist(request.options['networkDN'])
		try:
			obj.refreshNextIp()
		except udm_errors.nextFreeIp:
			raise NoIpLeft(request.options['networkDN'])

		result = {'ip': obj['nextIp'], 'dnsEntryZoneForward': obj['dnsEntryZoneForward'], 'dhcpEntryZone': obj['dhcpEntryZone'], 'dnsEntryZoneReverse': obj['dnsEntryZoneReverse']}
		self.finished(request.id, result)

		if request.options['increaseCounter']:
			# increase the next free IP address
			obj.stepIp()
			obj.modify()

	@module_from_request
	@simple_response()
	def containers(self, module):
		"""Returns the list of default containers for the given object
		type. Therefore the python module and the default object in the
		LDAP directory are searched.

		requests.options = {}
			'objectType' -- The UDM module name

		return: [ { 'id' : <LDAP DN of container>, 'label' : <name> }, ... ]
		"""
		containers = [{'id': x, 'label': ldap_dn2path(x)} for x in module.get_default_containers()]
		containers.sort(cmp=lambda x, y: cmp(x['label'].lower(), y['label'].lower()))
		return containers

	@module_from_request
	@simple_response
	def templates(self, module):
		"""Returns the list of template objects for the given object
		type.

		requests.options = {}
			'objectType' -- The UDM module name

		return: [ { 'id' : <LDAP DN of container or None>, 'label' : <name> }, ... ]
		"""

		result = []
		if module.template:
			template = UDM_Module(module.template)
			objects = template.search(ucr.get('ldap/base'))
			for obj in objects:
				obj.open()
				result.append({'id': obj.dn, 'label': obj[template.identifies]})

		return result

	@LDAP_Connection
	def types(self, request, ldap_connection=None, ldap_position=None):
		"""Returns the list of object types matching the given flavor or container.

		requests.options = {}
			'superordinate' -- if available only types for the given superordinate are returned (not for the navigation)
			'container' -- if available only types suitable for the given container are returned (only for the navigation)

		return: [ { 'id' : <LDAP DN of container or None>, 'label' : <name> }, ... ]
		"""
		superordinate = request.options.get('superordinate')
		if request.flavor != 'navigation':
			module = UDM_Module(request.flavor)
			if superordinate:
				module = self.get_module(request.flavor, superordinate) or module
			self.finished(request.id, module.child_modules)
			return

		container = request.options.get('container') or superordinate
		if not container:
			# no container is specified, return all existing object types
			MODULE.info('no container specified, returning all object types')
			self.finished(request.id, [{'id': name, 'label': getattr(mod, 'short_description', name)} for name, mod in udm_modules.modules.items()])
			return

		if 'None' == container:
			# if 'None' is given, use the LDAP base
			container = ucr.get('ldap/base')
			MODULE.info('no container == \'None\', set LDAP base as container')

		# create a list of modules that can be created
		# ... all container types except container/dc
		allowed_modules = set([m for m in udm_modules.containers if udm_modules.name(m) != 'container/dc'])

		# the container may be a superordinate or have one as its parent
		# (or grandparent, ....)
		superordinate = udm_modules.find_superordinate(container, None, ldap_connection)
		if superordinate:
			# there is a superordinate... add its subtypes to the list of allowed modules
			MODULE.info('container has a superordinate: %s' % superordinate)
			allowed_modules.update(udm_modules.subordinates(superordinate))
		else:
			# add all types that do not have a superordinate
			MODULE.info('container has no superordinate')
			allowed_modules.update(mod for mod in udm_modules.modules.values() if not udm_modules.superordinates(mod))

		# make sure that the object type can be created
		allowed_modules = [mod for mod in allowed_modules if udm_modules.supports(mod, 'add')]
		MODULE.info('all modules that are allowed: %s' % [udm_modules.name(mod) for mod in allowed_modules])

		# return the final list of object types
		self.finished(request.id, [{'id': udm_modules.name(_module), 'label': getattr(_module, 'short_description', udm_modules.name(_module))} for _module in allowed_modules])

	@bundled
	@sanitize(objectType=StringSanitizer())  # objectDN=StringSanitizer(allow_none=True),
	def layout(self, request):
		"""Returns the layout information for the given object type.

		requests.options = {}
			'objectType' -- The UDM module name. If not available the flavor is used

		return: <layout data structure (see UDM python modules)>
		"""
		module = self._get_module_by_request(request)
		module.load(force_reload=True)  # reload for instant extended attributes
		if request.flavor == 'users/self':
			object_dn = None
		else:
			object_dn = request.options.get('objectDN')
		return module.get_layout(object_dn)

	@bundled
	@sanitize(
		objectType=StringSanitizer(),
		objectDn=StringSanitizer(),
		searchable=BooleanSanitizer(default=False)
	)
	def properties(self, request):
		"""Returns the properties of the given object type.

		requests.options = {}
			'searchable' -- If given only properties that might be used for search filters are returned

		return: [ {}, ... ]
		"""
		module = self._get_module_by_request(request)
		module.load(force_reload=True)  # reload for instant extended attributes
		object_dn = request.options.get('objectDN')
		properties = module.get_properties(object_dn)
		if request.options.get('searchable', False):
			properties = [prop for prop in properties if prop.get('searchable', False)]
		return properties

	@module_from_request
	@simple_response
	def options(self, module):
		"""Returns the options specified for the given object type

		requests.options = {}
			'objectType' -- The UDM module name. If not available the flavor is used

		return: [ {}, ... ]
		"""
		return module.options

	@bundled
	@sanitize(
		objectType=StringSanitizer()
	)
	def policies(self, request):
		"""Returns a list of policy types that apply to the given object type"""
		module = self._get_module_by_request(request)
		return module.policies

	def validate(self, request):
		"""Validates the correctness of values for properties of the
		given object type. Therefore the syntax definition of the properties is used.

		requests.options = {}
			'objectType' -- The UDM module name. If not available the flavor is used

		return: [ { 'property' : <name>, 'valid' : (True|False), 'details' : <message> }, ... ]
		"""

		def _thread(request):
			module = self._get_module_by_request(request)

			result = []
			for property_name, value in request.options.get('properties').items():
				# ignore special properties named like $.*$, e.g. $options$
				if property_name.startswith('$') and property_name.endswith('$'):
					continue
				property_obj = module.get_property(property_name)

				if property_obj is None:
					raise UMC_OptionMissing(_('Property %s not found') % property_name)

				# check each element if 'value' is a list
				if isinstance(value, (tuple, list)) and property_obj.multivalue:
					subResults = []
					subDetails = []
					for ival in value:
						try:
							property_obj.syntax.parse(ival)
							subResults.append(True)
							subDetails.append('')
						except (udm_errors.valueInvalidSyntax, udm_errors.valueError, TypeError) as e:
							subResults.append(False)
							subDetails.append(str(e))
					result.append({'property': property_name, 'valid': subResults, 'details': subDetails})
				# otherwise we have a single value
				else:
					try:
						property_obj.syntax.parse(value)
						result.append({'property': property_name, 'valid': True})
					except (udm_errors.valueInvalidSyntax, udm_errors.valueError) as e:
						result.append({'property': property_name, 'valid': False, 'details': str(e)})

			return result

		thread = notifier.threads.Simple('Validate', notifier.Callback(_thread, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	@sanitize(
		syntax=StringSanitizer(required=True),
		key=LDAPSearchSanitizer(use_asterisks=False),
	)
	@simple_response
	def syntax_choices_key(self, syntax, key):
		lo, po = self.get_ldap_connection()
		syntax = _get_syntax(syntax)
		if syntax is None:
			return
		return search_syntax_choices_by_key(syntax, key, lo, po)

	@sanitize(syntax=StringSanitizer(required=True))
	@simple_response
	def syntax_choices_info(self, syntax):
		lo, po = self.get_ldap_connection()
		syntax = _get_syntax(syntax)
		if syntax is None:
			return
		return info_syntax_choices(syntax, ldap_connection=lo, ldap_position=po)

	@sanitize(
		objectPropertyValue=LDAPSearchSanitizer(),
		objectProperty=ObjectPropertySanitizer(),
		syntax=StringSanitizer(required=True)
	)
	def syntax_choices(self, request):
		"""Dynamically determine valid values for a given syntax class

		requests.options = {}
			'syntax' -- The UDM syntax class

		return: [ { 'id' : <name>, 'label' : <text> }, ... ]
		"""

		@LDAP_Connection
		def _thread(request, ldap_connection=None, ldap_position=None):
			syntax = _get_syntax(request.options['syntax'])
			if syntax is None:
				return
			return read_syntax_choices(syntax, request.options, ldap_connection=ldap_connection, ldap_position=ldap_position)

		thread = notifier.threads.Simple('SyntaxChoice', notifier.Callback(_thread, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	@sanitize(
		container=StringSanitizer(default='', allow_none=True)
	)
	def move_container_query(self, request):
		scope = 'one'
		modules = self.modules_with_childs
		container = request.options.get('container')
		if not container:
			scope = 'base'

		thread = notifier.threads.Simple('MoveContainerQuery', notifier.Callback(self._container_query, request, container, modules, scope), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	@sanitize(
		container=StringSanitizer(allow_none=True)
	)
	def nav_container_query(self, request):
		"""Returns a list of LDAP containers located under the given
		LDAP base (option 'container'). If no base container is
		specified the LDAP base object is returned."""

		ldap_base = ucr['ldap/base']
		container = request.options.get('container')

		modules = self.modules_with_childs
		scope = 'one'
		if not container:
			# get the tree root == the ldap base
			scope = 'base'
		elif request.flavor != 'navigation' and container and ldap_base.lower() == container.lower():
			# this is the tree root of DNS / DHCP, show all zones / services
			scope = 'sub'
			modules = [request.flavor]

		thread = notifier.threads.Simple('NavContainerQuery', notifier.Callback(self._container_query, request, container, modules, scope), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	@LDAP_Connection
	def _container_query(self, request, container, modules, scope, ldap_connection=None, ldap_position=None):
		"""Get a list of containers or child objects of the specified container."""

		if not container:
			container = ucr['ldap/base']
			defaults = {}
			if request.flavor != 'navigation':
				defaults['$operations$'] = ['search', ],  # disallow edit
			if request.flavor in ('dns/dns', 'dhcp/dhcp'):
				defaults.update({
					'label': UDM_Module(request.flavor).title,
					'icon': 'udm-%s' % (request.flavor.replace('/', '-'),),
				})
			return [dict({
				'id': container,
				'label': ldap_dn2path(container),
				'icon': 'udm-container-dc',
				'path': ldap_dn2path(container),
				'objectType': 'container/dc',
				'$operations$': UDM_Module('container/dc').operations,
				'$flags$': [],
				'$childs$': True,
				'$isSuperordinate$': False,
			}, **defaults)]

		result = []
		for xmodule in modules:
			xmodule = UDM_Module(xmodule)
			superordinate = udm_objects.get_superordinate(xmodule.module, None, ldap_connection, container)
			try:
				for item in xmodule.search(container, scope=scope, superordinate=superordinate):
					module = UDM_Module(item.module)
					result.append({
						'id': item.dn,
						'label': item[module.identifies],
						'icon': 'udm-%s' % (module.name.replace('/', '-')),
						'path': ldap_dn2path(item.dn),
						'objectType': module.name,
						'$operations$': module.operations,
						'$flags$': item.oldattr.get('univentionObjectFlag', []),
						'$childs$': module.childs,
						'$isSuperordinate$': udm_modules.isSuperordinate(module.module),
					})
			except UDM_Error as exc:
				raise UMC_Error(str(exc))

		return result

	@sanitize(
		container=StringSanitizer(required=True)
	)
	@LDAP_Connection
	def nav_object_query(self, request, ldap_connection=None, ldap_position=None):
		"""Returns a list of objects in a LDAP container (scope: one)

		requests.options = {}
			'container' -- the base container where the search should be started (default: LDAP base)
			'objectType' -- the object type that should be displayed (optional)
			'objectProperty' -- the object property that should be scanned (optional)
			'objectPropertyValue' -- the filter that should b found in the property (optional)

		return: [ { '$dn$' : <LDAP DN>, 'objectType' : <UDM module name>, 'path' : <location of object> }, ... ]
		"""
		object_type = request.options.get('objectType', '')
		if object_type not in ('None', '$containers$'):
			# we need to search for a specific objectType, then we should call the standard query
			# we also need to get the correct superordinate
			superordinate = udm_objects.get_superordinate(object_type, None, ldap_connection, request.options['container'])
			if superordinate and superordinate.module == 'settings/cn':
				# false positive detected superordinate; Bug #32843
				superordinate = None
			if superordinate:
				superordinate = superordinate.dn
			request.options['superordinate'] = superordinate
			request.options['scope'] = 'one'
			self.query(request)
			return

		def _thread(container):
			entries = []
			for module, obj in list_objects(container, object_type=object_type, ldap_connection=ldap_connection, ldap_position=ldap_position):
				if obj is None:
					continue
				if object_type != '$containers$' and module.childs:
					continue
				if object_type == '$containers$' and not module.childs:
					continue
				entries.append({
					'$dn$': obj.dn,
					'$childs$': module.childs,
					'objectType': module.name,
					'labelObjectType': module.subtitle,
					'name': udm_objects.description(obj),
					'path': ldap_dn2path(obj.dn, include_rdn=False),
					'$flags$': obj.oldattr.get('univentionObjectFlag', []),
					'$operations$': module.operations,
				})

			return entries

		thread = notifier.threads.Simple('NavObjectQuery', notifier.Callback(_thread, request.options['container']), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	@sanitize(DictSanitizer(dict(
		objectType=StringSanitizer(required=True),
		policies=ListSanitizer(),
		policyType=StringSanitizer(required=True),
		objectDN=Sanitizer(default=None),
		container=Sanitizer(default=None)
		# objectDN=StringSanitizer(default=None, allow_none=True),
		# container=StringSanitizer(default=None, allow_none=True)
	)))
	def object_policies(self, request):
		"""Returns a virtual policy object containing the values that
		the given object or container inherits"""
		def _thread(request):

			object_dn = None
			container_dn = None
			obj = None

			def _get_object(_dn, _module):
				'''Get existing UDM object and corresponding module. Verify user input.'''
				if _module is None or _module.module is None:
					raise UMC_OptionTypeError('The given object type is not valid')
				_obj = _module.get(_dn)
				if _obj is None or (_dn and not _obj.exists()):
					raise ObjectDoesNotExist(_dn)
				return _obj

			def _get_object_parts(_options):
				'''Get object related information and corresponding UDM object/module. Verify user input.'''

				_object_type = _options['objectType']
				_object_dn = _options['objectDN']
				_container_dn = _options['container']

				if (object_dn, container_dn) == (_object_dn, _container_dn):
					# nothing has changed w.r.t. last entry -> return last values
					return (object_dn, container_dn, obj)

				_obj = None
				_module = None
				if _object_dn:
					# editing an exiting UDM object -> use the object itself
					_module = UDM_Module(_object_type)
					_obj = _get_object(_object_dn, _module)
				elif _container_dn:
					# editing a new (i.e. non existing) object -> use the parent container
					_module = self.get_module(None, _container_dn)
					_obj = _get_object(_container_dn, _module)

				return (_object_dn, _container_dn, _obj)

			ret = []
			for ioptions in request.options:
				object_dn, container_dn, obj = _get_object_parts(ioptions)
				policy_dns = ioptions.get('policies', [])
				policy_module = UDM_Module(ioptions['policyType'])
				policy_obj = _get_object(policy_dns[0] if policy_dns else None, policy_module)

				if obj is None:
					ret.append({})
					continue

				policy_obj.clone(obj)

				# There are 2x2x2 (=8) cases that may occur (c.f., Bug #31916):
				# (1)
				#   [edit] editing existing UDM object
				#   -> the existing UDM object itself is loaded
				#   [new]  virtually edit non-existing UDM object (when a new object is being created)
				#   -> the parent container UDM object is loaded
				# (2)
				#   [w/pol]   UDM object has assigned policies in LDAP directory
				#   [w/o_pol] UDM object has no policies assigned in LDAP directory
				# (3)
				#   [inherit] user request to (virtually) change the policy to 'inherited'
				#   [set_pol] user request to (virtually) assign a particular policy
				faked_policy_reference = None
				if object_dn and not policy_dns:
					# case: [edit; w/pol; inherit]
					# -> current policy is (virtually) overwritten with 'None'
					faked_policy_reference = [None]
				elif not object_dn and policy_dns:
					# cases:
					# * [new; w/pol; inherit]
					# * [new; w/pol; set_pol]
					# -> old + temporary policy are both (virtually) set at the parent container
					faked_policy_reference = obj.policies + policy_dns
				else:
					# cases:
					# * [new; w/o_pol; inherit]
					# * [new; w/o_pol; set_pol]
					# * [edit; w/pol; set_pol]
					# * [edit; w/o_pol; inherit]
					# * [edit; w/o_pol; set_pol]
					faked_policy_reference = policy_dns

				policy_obj.policy_result(faked_policy_reference)
				infos = copy.copy(policy_obj.polinfo_more)
				for key, value in infos.items():
					if key in policy_obj.polinfo:
						if isinstance(infos[key], (tuple, list)):
							continue
						infos[key]['value'] = policy_obj.polinfo[key]

				ret.append(infos)
			return ret

		thread = notifier.threads.Simple('ObjectPolicies', notifier.Callback(_thread, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	def object_options(self, request):
		"""Returns the options known by the given objectType. If an LDAP
		DN is passed the current values for the options of this object
		are returned, otherwise the default values for the options are
		returned."""
		object_type = request.options.get('objectType')
		if not object_type:
			raise UMC_OptionMissing('The object type is missing')
		object_dn = request.options.get('objectDN')

		def _thread(object_type, object_dn):
			module = UDM_Module(object_type)
			if module.module is None:
				raise UMC_OptionTypeError('The given object type is not valid')

			return module.get_option(object_dn)

		thread = notifier.threads.Simple('ObjectOptions', notifier.Callback(_thread, object_type, object_dn), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	@sanitize(email=EmailSanitizer(required=True))
	@simple_response
	def request_new_license(self, email):
		license = dump_license()
		if license is None:
			raise UMC_CommandError(_('Cannot parse License from LDAP'))
		data = {}
		data['email'] = email
		data['licence'] = license
		data = urllib.urlencode(data)
		url = 'https://license.univention.de/keyid/conversion/submit'
		request = urllib2.Request(url, data=data, headers={'User-agent': 'UMC/AppCenter'})
		self._request_license(request)
		# creating a new ucr variable to prevent duplicated registration (Bug #35711)
		handler_set(['ucs/web/license/requested=true'])
		return True

	def _request_license(self, request):
		try:
			urlopen(request)
		except (urllib2.HTTPError, urllib2.URLError, IOError) as exc:
			strerror = ''
			if hasattr(exc, 'read'):  # try to parse an html error
				body = exc.read()
				match = re.search('<span id="details">(?P<details>.*?)</span>', body, flags=re.DOTALL)
				if match:
					strerror = match.group(1).replace('\n', '')
			if not strerror:
				if hasattr(exc, 'getcode') and exc.getcode() >= 400:
					strerror = _('This seems to be a problem with the license server. Please try again later.')
				while hasattr(exc, 'reason'):
					exc = exc.reason
				if hasattr(exc, 'errno'):
					version = ucr.get('version/version')
					errno = exc.errno
					strerror += getattr(exc, 'strerror', '') or ''
					if errno == 1:  # gaierror(1, something like 'SSL Unknown protocol')
						link_to_doc = _('https://docs.software-univention.de/manual-%s.html#ip-config:Web_proxy_for_caching_and_policy_management__virus_scan') % version
						strerror += '. ' + _('This may be a problem with the proxy of your system. You may find help at %s.') % link_to_doc
					if errno == -2:  # gaierror(-2, 'Name or service not known')
						link_to_doc = _('https://docs.software-univention.de/manual-%s.html#networks:dns') % version
						strerror += '. ' + _('This is probably due to the DNS settings of your server. You may find help at %s.') % link_to_doc
			if not strerror.strip():
				strerror = str(exc)
			raise UMC_Error(_('An error occurred while contacting the license server: %s') % (strerror,), status=500)
