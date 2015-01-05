#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages UDM modules
#
# Copyright 2011-2014 Univention GmbH
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

import copy
import re
import grp
import os
import shutil
import notifier
import notifier.threads
import pwd
import tempfile
import urllib
import urllib2

from ldap import LDAPError
from univention.lib.i18n import Translation
from univention.management.console.config import ucr
from univention.management.console.modules import Base, UMC_OptionTypeError, UMC_OptionMissing, UMC_CommandError, error_handling
from univention.management.console.modules.decorators import simple_response, sanitize, multi_response
from univention.management.console.modules.sanitizers import (
	LDAPSearchSanitizer, EmailSanitizer, ChoicesSanitizer,
	ListSanitizer, StringSanitizer, DictSanitizer, BooleanSanitizer
)
from univention.management.console.modules.mixins import ProgressMixin
from univention.management.console.log import MODULE
from univention.management.console.protocol.session import TEMPUPLOADDIR

import univention.admin.modules as udm_modules
import univention.admin.objects as udm_objects
import univention.admin.uexceptions as udm_errors

from univention.config_registry import handler_set

import univention.directory.reports as udr

from univention.management.console.protocol.definitions import MODULE_ERR_COMMAND_FAILED

from .udm_ldap import (
	UDM_Error, UDM_Module, UDM_Settings, check_license,
	ldap_dn2path, get_module, read_syntax_choices, list_objects,
	LDAP_Connection, set_credentials, container_modules,
	info_syntax_choices, search_syntax_choices_by_key,
	UserWithoutDN, ObjectDoesNotExists, SuperordinateDoesNotExists, NoIpLeft
)
from .tools import LicenseError, LicenseImport, install_opener, urlopen, dump_license

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


class Instance(Base, ProgressMixin):

	def __init__(self):
		Base.__init__(self)
		self.settings = None
		self.reports_cfg = None
		self.modules_with_childs = []
		install_opener(ucr)

	@Base.password.setter
	def password(self, password):
		super(Instance, Instance).password.fset(self, password)
		set_credentials(self._user_dn, self._password)

	def init(self):
		'''Initialize the module. Invoked when ACLs, commands and
		credentials are available'''
		if not self._user_dn:
			raise UserWithoutDN(self._username)

		set_credentials(self._user_dn, self._password)

		# read user settings and initial UDR
		self.settings = UDM_Settings()
		self.settings.user(self._user_dn)
		self.reports_cfg = udr.Config()
		self.modules_with_childs = container_modules()

	def _get_module(self, object_type, flavor=None):
		"""Tries to determine to UDM module to use. If no specific
		object type is given or is 'all', the request
		flavor is chosen. Failing all this will raise in
		UMC_OptionMissing exception. On success a UMC_Module object is
		returned."""
		module_name = object_type
		if not module_name or 'all' == module_name:
			module_name = flavor

		if not module_name:
			raise UMC_OptionMissing(_('No flavor or valid UDM module name specified'))

		return UDM_Module(module_name)

	def _get_module_by_request(self, request, object_type=None):
		"""Tries to determine the UDM module to use. If no specific
		object type is given the request option 'objectType' is used. In
		case none if this leads to a valid object type the request
		flavor is chosen. Failing all this will raise in
		UMC_OptionMissing exception. On success a UMC_Module object is
		returned."""
		if object_type is None:
			object_type = request.options.get('objectType')
		return self._get_module(object_type, request.flavor)

	def _thread_finished(self, thread, result, request):
		if not isinstance(result, BaseException):
			self.finished(request.id, result)
			return

		if isinstance(result, (udm_errors.ldapSizelimitExceeded, udm_errors.ldapTimeout)):
			self.finished(request.id, None, result.args[0], status=MODULE_ERR_COMMAND_FAILED)
			return

		def fake_func(self, request):
			raise thread.exc_info[0], thread.exc_info[1], thread.exc_info[2]
		fake_func.__name__ = 'thread %s' % (request.arguments[0],)
		error_handling(fake_func)(self, request)

	@LDAP_Connection
	def license(self, request, ldap_connection=None, ldap_position=None):
		message = None
		try:
			# call the check_license method, handle the different exceptions, and
			# return a user friendly message
			check_license(ldap_connection)
		except udm_errors.licenseNotFound:
			message = _('License not found. During this session add and modify are disabled.')
		except udm_errors.licenseAccounts:  # UCS license v1
			message = _('You have too many user accounts for your license. During this session add and modify are disabled.')
		except udm_errors.licenseUsers:  # UCS license v2
			message = _('You have too many user accounts for your license. During this session add and modify are disabled.')
		except udm_errors.licenseClients:  # UCS license v1
			message = _('You have too many client accounts for your license. During this session add and modify are disabled.')
		except udm_errors.licenseServers:  # UCS license v2
			message = _('You have too many server accounts for your license. During this session add and modify are disabled.')
		except udm_errors.licenseManagedClients:  # UCS license v2
			message = _('You have too many managed client accounts for your license. During this session add and modify are disabled.')
		except udm_errors.licenseCorporateClients:  # UCS license v2
			message = _('You have too many corporate client accounts for your license. During this session add and modify are disabled.')
		except udm_errors.licenseDesktops:  # UCS license v1
			message = _('You have too many desktop accounts for your license. During this session add and modify are disabled.')
		except udm_errors.licenseGroupware:  # UCS license v1
			message = _('You have too many groupware accounts for your license. During this session add and modify are disabled.')
		except udm_errors.licenseDVSUsers:  # UCS license v2
			message = _('You have too many DVS user accounts for your license. During this session add and modify are disabled.')
		except udm_errors.licenseDVSClients:  # UCS license v2
			message = _('You have too many DVS client accounts for your license. During this session add and modify are disabled.')
		except udm_errors.licenseExpired:
			message = _('Your license is expired. During this session add and modify are disabled.')
		except udm_errors.licenseWrongBaseDn:
			message = _('Your license is not valid for your LDAP-Base. During this session add and modify are disabled.')
		except udm_errors.licenseInvalid:
			message = _('Your license is not valid. During this session add and modify are disabled.')
		except udm_errors.licenseDisableModify:
			message = _('Your license does not allow modifications. During this session add and modify are disabled.')
		except udm_errors.freeForPersonalUse:
			message = _('You are currently using the "Free for personal use" edition of Univention Corporate Server.')
		except udm_errors.licenseGPLversion:
			message = _('Your license status could not be validated. Thus, you are not eligible to support and maintenance. If you have bought a license, please contact Univention or your Univention partner.')

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
					udm_license._license.types = filter(lambda x: x != 'UGS', udm_license._license.types)
			elif udm_license._license.version == '2':
				for item in ('licenses', 'real'):
					license_data[item] = {}
					for lic_type in ('SERVERS', 'USERS', 'MANAGEDCLIENTS', 'CORPORATECLIENTS', 'VIRTUALDESKTOPUSERS', 'VIRTUALDESKTOPCLIENTS'):
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
			license_data['ffpu'] = False
			if license_data['baseDN'] == 'Free for personal use edition':
				license_data['baseDN'] = ucr.get('ldap/base', '')
				license_data['ffpu'] = True
			license_data['sysAccountsFound'] = udm_license._license.sysAccountsFound

		self.finished(request.id, license_data)

	def license_import(self, request):
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
				importer.write(self._user_dn, self._password)
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
			module = get_module(None, object)
			if 'container' not in options:
				yield {'$dn$': object, 'success': False, 'details': _('The destination is missing')}
			elif not module:
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

		thread = notifier.threads.Simple('Get', notifier.Callback(_thread, request), notifier.Callback(self._thread_finished, request))
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
				module = get_module(request.flavor, ldap_dn)
				if module is None:
					result.append({'$dn$': ldap_dn, 'success': False, 'details': _('LDAP object could not be found.')})
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

		thread = notifier.threads.Simple('Get', notifier.Callback(_thread, request), notifier.Callback(self._thread_finished, request))
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
				module = get_module(request.flavor, ldap_dn)
				if module is None:
					result.append({'$dn$': ldap_dn, 'success': False, 'details': _('LDAP object could not be identified')})
					continue
				try:
					module.remove(ldap_dn, options.get('cleanup', False), options.get('recursive', False))
					result.append({'$dn$': ldap_dn, 'success': True})
				except UDM_Error as e:
					result.append({'$dn$': ldap_dn, 'success': False, 'details': str(e)})

			return result

		thread = notifier.threads.Simple('Get', notifier.Callback(_thread, request), notifier.Callback(self._thread_finished, request))
		thread.run()

	@simple_response
	def meta_info(self, objectType):
		module = UDM_Module(objectType)
		if module:
			return {
				'help_link': module.help_link,
				'help_text': module.help_text,
			}

	def get(self, request):
		"""Retrieves the given list of LDAP objects. Password property will be removed.

		requests.options = [ <LDAP DN>, ... ]

		return: [ { '$dn$' : <LDAP DN>, <object properties> }, ... ]
		"""

		def _thread(request):
			result = []
			for ldap_dn in request.options:
				if request.flavor == 'users/self':
					ldap_dn = self._user_dn
				module = get_module(request.flavor, ldap_dn)
				if module is None:
					raise ObjectDoesNotExists(ldap_dn)
				else:
					obj = module.get(ldap_dn)
					if obj:
						props = obj.info
						for passwd in module.password_properties:
							if passwd in props:
								del props[passwd]
						props['$dn$'] = obj.dn
						props['$options$'] = {}
						for opt in module.get_options(udm_object=obj):
							props['$options$'][opt['id']] = opt['value']
						props['$policies$'] = {}
						for policy in obj.policies:
							pol_mod = get_module(None, policy)
							if pol_mod and pol_mod.name:
								props['$policies$'][pol_mod.name] = policy
						props['$labelObjectType$'] = module.title
						props['$flags$'] = obj.oldattr.get('univentionObjectFlag', []),
						result.append(props)
					else:
						MODULE.process('The LDAP object for the LDAP DN %s could not be found' % ldap_dn)
			return result

		MODULE.info('Starting thread for udm/get request')
		thread = notifier.threads.Simple('Get', notifier.Callback(_thread, request), notifier.Callback(self._thread_finished, request))
		thread.run()

	@sanitize(
		objectPropertyValue=LDAPSearchSanitizer(),
		objectProperty=ObjectPropertySanitizer(required=True)
	)
	def query(self, request):
		"""Searches for LDAP objects and returns a few properties of the found objects

		requests.options = {}
			'objectType' -- the object type to search for (default: if not given the flavor is used)
			'objectProperty' -- the object property that should be scaned
			'objectPropertyValue' -- the filter that should be found in the property
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
				mod = get_module(request.flavor, superordinate)
				if mod is not None:
					MODULE.info('Found UDM module for superordinate')
					superordinate = mod.get(superordinate)
					request.options['container'] = superordinate.dn
				else:
					raise SuperordinateDoesNotExists(superordinate)

			container = request.options.get('container')
			objectProperty = request.options['objectProperty']
			objectPropertyValue = request.options['objectPropertyValue']
			scope = request.options.get('scope', 'sub')
			hidden = request.options.get('hidden')
			result = module.search(container, objectProperty, objectPropertyValue, superordinate, scope=scope, hidden=hidden)

			entries = []
			object_type = request.options.get('objectType', request.flavor)
			if result:
				for obj in result:
					if obj is None:
						continue
					module = get_module(object_type, obj.dn)
					if module is None:
						# This happens when concurrent a object is removed between the module.search() and get_module() call
						MODULE.warn('LDAP object does not exists %s (flavor: %s). The object is ignored.' % (obj.dn, request.flavor))
						continue
					if module.module is None:
						MODULE.warn('Could not identify LDAP object %s (flavor: %s). The object is ignored.' % (obj.dn, request.flavor))
						continue
					entry = {
						'$dn$': obj.dn,
						'$childs$': module.childs,
						'$flags$': obj.oldattr.get('univentionObjectFlag', []),
						'objectType': module.name,
						'labelObjectType': module.subtitle,
						'name': module.obj_description(obj) or udm_objects.description(obj),
						'path': ldap_dn2path(obj.dn, include_rdn=False)
					}
					if request.options['objectProperty'] not in ('name', 'None'):
						entry[request.options['objectProperty']] = obj[request.options['objectProperty']]
					entries.append(entry)
				return entries

		thread = notifier.threads.Simple('Query', notifier.Callback(_thread, request), notifier.Callback(self._thread_finished, request))
		thread.run()

	def reports_query(self, request):
		"""Returns a list of reports for the given object type"""
		self.finished(request.id, self.reports_cfg.get_report_names(request.flavor))

	def sanitize_reports_create(self, request):
		choices = self.reports_cfg.get_report_names(request.flavor)
		return dict(
			report=ChoicesSanitizer(choices=choices, required=True),
			objects=ListSanitizer(StringSanitizer(minimum=1), required=True, min_elements=1)
		)

	@sanitize_func(sanitize_reports_create)
	def reports_create(self, request):
		"""Creates a report for the given LDAP DNs and returns the file

		requests.options = {}
			'report' -- name of the report
			'objects' -- list of LDAP DNs to include in the report

		return: report file
		"""

		@LDAP_Connection
		def _thread(request, ldap_connection=None, ldap_position=None):
			udr.admin.connect(access=ldap_connection)
			udr.admin.clear_cache()
			cfg = udr.Config()
			template = cfg.get_report(request.flavor, request.options['report'])
			doc = udr.Document(template, header=cfg.get_header(request.flavor, request.options['report']), footer=cfg.get_footer(request.flavor, request.options['report']))
			tmpfile = doc.create_source(request.options['objects'])
			if doc._type == udr.Document.TYPE_LATEX:
				doc_type = _('PDF document')
				pdffile = doc.create_pdf(tmpfile)
				os.unlink(tmpfile)
			else:
				doc_type = _('text file')
				pdffile = tmpfile
			try:
				os.unlink(tmpfile[: -4] + 'aux')
				os.unlink(tmpfile[: -4] + 'log')
			except:
				pass
			if pdffile:
				path = '/var/www/univention-directory-reports'
				shutil.copy(pdffile, path)
				os.unlink(pdffile)

				www_data_user = pwd.getpwnam('www-data')
				www_data_grp = grp.getgrnam('www-data')
				filename = os.path.join(path, os.path.basename(pdffile))
				os.chown(filename, www_data_user.pw_uid, www_data_grp.gr_gid)
				os.chmod(filename, 0o644)
				url = '/univention-directory-reports/%s' % os.path.basename(pdffile)
				# link = '<a target="_blank" href="%s">%s (%s)</a>' % ( url, module.name, request.options[ 'report' ] )

				return {'success': True, 'count': len(request.options['objects']), 'URL': url, 'docType': doc_type}
			else:
				return {'success': False, 'count': 0, 'URL': None, 'docType': doc_type}

		thread = notifier.threads.Simple('ReportsCreate', notifier.Callback(_thread, request), notifier.Callback(self._thread_finished, request))
		thread.run()

	def values(self, request):
		"""Returns the default search pattern/value for the given object property

		requests.options = {}
			'objectProperty' -- the object property that should be scaned

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
		module = self._get_module('networks/network')
		obj = module.get(request.options['networkDN'])

		if not obj:
			raise ObjectDoesNotExists(request.options['networkDN'])
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

	@simple_response(with_flavor=True)
	def containers(self, flavor, objectType=None):
		"""Returns the list of default containers for the given object
		type. Therefor the python module and the default object in the
		LDAP directory are searched.

		requests.options = {}
			'objectType' -- The UDM module name

		return: [ { 'id' : <LDAP DN of container>, 'label' : <name> }, ... ]
		"""
		module = self._get_module(objectType, flavor)

		containers = module.containers

		if self.settings is not None:
			containers += self.settings.containers(flavor)

		containers.sort(cmp=lambda x, y: cmp(x['label'].lower(), y['label'].lower()))
		return containers

	def superordinates(self, request):
		"""Returns the list of superordinate containers for the given
		object type.

		requests.options = {}
			'objectType' -- The UDM module name

		return: [ { 'id' : <LDAP DN of container or None>, 'label' : <name> }, ... ]
		"""
		module = self._get_module_by_request(request)
		self.finished(request.id, module.superordinates)

	def templates(self, request):
		"""Returns the list of template objects for the given object
		type.

		requests.options = {}
			'objectType' -- The UDM module name

		return: [ { 'id' : <LDAP DN of container or None>, 'label' : <name> }, ... ]
		"""
		module = self._get_module_by_request(request)

		result = []
		if module.template:
			template = UDM_Module(module.template)
			objects = template.search(ucr.get('ldap/base'))
			for obj in objects:
				obj.open()
				result.append({'id': obj.dn, 'label': obj[template.identifies]})

		self.finished(request.id, result)

	@LDAP_Connection
	def types(self, request, ldap_connection=None, ldap_position=None):
		"""Returns the list of object types matching the given flavor or container.

		requests.options = {}
			'superordinate' -- if available only types for the given superordinate are returned (not for the navigation)
			'container' -- if available only types suitable for the given container are returned (only for the navigation)

		return: [ { 'id' : <LDAP DN of container or None>, 'label' : <name> }, ... ]
		"""
		if request.flavor != 'navigation':
			module = UDM_Module(request.flavor)
			superordinate = request.options.get('superordinate')
			if superordinate:
				self.finished(request.id, module.types4superordinate(request.flavor, superordinate))
			else:
				self.finished(request.id, module.child_modules)
		else:
			container = request.options.get('container')
			if not container:
				# no container is specified, return all existing object types
				MODULE.info('no container specified, returning all object types')
				self.finished(request.id, map(lambda module: {'id': module[0], 'label': getattr(module[1], 'short_description', module[0])}, udm_modules.modules.items()))
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
				allowed_modules.update(filter(lambda mod: not udm_modules.superordinate(mod), udm_modules.modules.values()))

			# make sure that the object type can be created
			allowed_modules = filter(lambda mod: udm_modules.supports(mod, 'add'), allowed_modules)
			MODULE.info('all modules that are allowed: %s' % [udm_modules.name(mod) for mod in allowed_modules])

			# return the final list of object types
			self.finished(request.id, map(lambda module: {'id': udm_modules.name(module), 'label': getattr(module, 'short_description', udm_modules.name(module))}, allowed_modules))

	def layout(self, request):
		"""Returns the layout information for the given object type.

		requests.options = {}
			'objectType' -- The UDM module name. If not available the flavor is used

		return: <layout data structure (see UDM python modules)>
		"""
		ret = []
		for options in request.options:
			module = self._get_module_by_request(request, options.get('objectType'))
			module.load(force_reload=True)  # reload for instant extended attributes
			if request.flavor == 'users/self':
				object_dn = None
			else:
				object_dn = options.get('objectDN', None)
			ret.append(module.get_layout(object_dn))
		self.finished(request.id, ret)

	def properties(self, request):
		"""Returns the properties of the given object type.

		requests.options = {}
			'searchable' -- If given only properties that might be used for search filters are returned

		return: [ {}, ... ]
		"""
		ret = []
		bundled = False
		if isinstance(request.options, list):
			all_options = request.options
			bundled = True
		else:
			all_options = [request.options]
		for options in all_options:
			module = self._get_module_by_request(request, options.get('objectType'))
			module.load(force_reload=True)  # reload for instant extended attributes
			object_dn = options.get('objectDN')
			properties = module.get_properties(object_dn)
			if options.get('searchable', False):
				properties = filter(lambda prop: prop.get('searchable', False), properties)
			ret.append(properties)
		if not bundled:
			ret = ret[0]
		self.finished(request.id, ret)

	def options(self, request):
		"""Returns the options specified for the given object type

		requests.options = {}
			'objectType' -- The UDM module name. If not available the flavor is used

		return: [ {}, ... ]
		"""
		module = self._get_module_by_request(request)
		self.finished(request.id, module.options)

	def policies(self, request):
		"""Returns a list of policy types that apply to the given object type"""
		bundled = True
		all_options = request.options
		if not isinstance(request.options, list):
			all_options = [request.options]
			bundled = False

		result = []
		for options in all_options:
			module = self._get_module_by_request(request, options.get('objectType'))
			result.append(module.policies)

		if not bundled:
			result = result[0]
		self.finished(request.id, result)

	def validate(self, request):
		"""Validates the correctness of values for properties of the
		given object type. Therefor the syntax definition of the properties is used.

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

		thread = notifier.threads.Simple('Validate', notifier.Callback(_thread, request), notifier.Callback(self._thread_finished, request))
		thread.run()

	@sanitize(key=LDAPSearchSanitizer(use_asterisks=False))
	@simple_response
	def syntax_choices_key(self, syntax, key):
		return search_syntax_choices_by_key(syntax, key)

	@simple_response
	def syntax_choices_info(self, syntax):
		return info_syntax_choices(syntax)

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

		def _thread(request):
			return read_syntax_choices(request.options['syntax'], request.options)

		thread = notifier.threads.Simple('SyntaxChoice', notifier.Callback(_thread, request), notifier.Callback(self._thread_finished, request))
		thread.run()

	def nav_container_query(self, request):
		"""Returns a list of LDAP containers located under the given
		LDAP base (option 'container'). If no base container is
		specified the LDAP base object is returned."""

		if not request.options.get('container'):
			ldap_base = ucr.get('ldap/base')
			self.finished(request.id, [{'id': ldap_base, 'label': ldap_dn2path(ldap_base), 'icon': 'udm-container-dc', 'objectType': 'container/dc', 'operations': ['edit']}])
			return

		def _thread(container):
			success = True
			message = None
			superordinate = None
			result = []
			for base, typ in map(lambda x: x.split('/'), self.modules_with_childs):
				module = UDM_Module('%s/%s' % (base, typ))
				if module.superordinate:
					if superordinate is None:
						try:
							so_module = UDM_Module(module.superordinate)
							so_obj = so_module.get(request.options.get('container'))
							superordinate = so_obj
						except UDM_Error:  # superordinate object could not be load -> ignore module
							continue
					else:
						so_obj = superordinate
				else:
					so_obj = None
				try:
					for item in module.search(container, scope='one', superordinate=so_obj):
						result.append({
							'id': item.dn,
							'label': item[module.identifies],
							'icon': 'udm-%s-%s' % (base, typ),
							'path': ldap_dn2path(item.dn),
							'objectType': '%s/%s' % (base, typ),
							'operations': module.operations,
							'$flags$': item.oldattr.get('univentionObjectFlag', []),
						})
				except UDM_Error as e:
					success = False
					result = None
					message = str(e)

			return result, message, success

		def _finish(thread, result, request):
			if not isinstance(result, BaseException):
				result, message, success = result
				self.finished(request.id, result, message, success)
			else:
				self.finished(request.id, None, str(result), False)

		thread = notifier.threads.Simple('NavContainerQuery', notifier.Callback(_thread, request.options['container']), notifier.Callback(_finish, request))
		thread.run()

	@sanitize(
		container=StringSanitizer(required=True)
	)
	@LDAP_Connection
	def nav_object_query(self, request, ldap_connection=None, ldap_position=None):
		"""Returns a list of objects in a LDAP container (scope: one)

		requests.options = {}
			'container' -- the base container where the search should be started (default: LDAP base)
			'objectType' -- the object type that should be displayed (optional)
			'objectProperty' -- the object property that should be scaned (optional)
			'objectPropertyValue' -- the filter that should b found in the property (optional)

		return: [ { '$dn$' : <LDAP DN>, 'objectType' : <UDM module name>, 'path' : <location of object> }, ... ]
		"""
		object_type = request.options.get('objectType', '')
		if object_type not in ('None', '$containers$'):
			# we need to search for a specific objectType, then we should call the standard query
			# we also need to get the correct superordinate
			superordinate = udm_objects.get_superordinate(object_type, None, ldap_connection, request.options['container'])
			if superordinate:
				superordinate = superordinate.dn
			request.options['superordinate'] = superordinate
			request.options['scope'] = 'one'
			self.query(request)
			return

		def _thread(container):
			entries = []
			for module, obj in list_objects(container, object_type=object_type):
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
				})

			return entries

		thread = notifier.threads.Simple('NavObjectQuery', notifier.Callback(_thread, request.options['container']), notifier.Callback(self._thread_finished, request))
		thread.run()

	def object_policies(self, request):
		"""Returns a virtual policy object containing the values that
		the given object or container inherits"""
		def _thread(request):

			object_dn = None
			container_dn = None
			obj = None

			def _get_object(_dn, _module):
				'''Get existing UDM object and corresponding module. Verify user input.'''
				if _module.module is None:
					raise UMC_OptionTypeError('The given object type is not valid')
				_obj = _module.get(_dn)
				if _obj is None:
					raise UMC_OptionTypeError('The object could not be found')
				return _obj, _module

			def _get_object_parts(_options):
				'''Get object related information and corresponding UDM object/module. Verify user input.'''
				try:
					_object_type = _options.get('objectType')
					_object_dn = _options.get('objectDN')
					_container_dn = _options.get('container')
				except IndexError:
					raise UMC_OptionTypeError('The given object type is not valid')

				if (object_dn, container_dn) == (_object_dn, _container_dn):
					# nothing has changed w.r.t. last entry -> return last values
					return (object_dn, container_dn, obj)

				_obj = None
				_module = None
				if _object_dn:
					# editing an exiting UDM object -> use the object itself
					_obj, _module = _get_object(_object_dn, UDM_Module(_object_type))
				elif _container_dn:
					# editing a new (i.e. non existing) object -> use the parent container
					_obj, _module = _get_object(_container_dn, get_module(None, _container_dn))

				return (_object_dn, _container_dn, _obj)

			def _get_policy_parts(_options):
				'''Get policy related UDM object and DN. Verify user input.'''
				_policy_type = _options.get('policyType')
				_policy_dn = _options.get('policyDN')

				_policy_obj, _policy_module = _get_object(_policy_dn, UDM_Module(_policy_type))

				return (_policy_obj, _policy_dn)

			ret = []
			for ioptions in request.options:
				object_dn, container_dn, obj = _get_object_parts(ioptions)
				policy_obj, policy_dn = _get_policy_parts(ioptions)
				policy_obj.clone(obj)

				# There are 2x2x2 (=8) cases that may occur (c.f., Bug #31916):
				# (1)
				#   [edit] editing existing UDM object
				#   -> the existing UDM object itself is loaded
				#   [new]  virtually edit non-existing UDM object (when a new object is being created)
				#   -> the parent container UDM object is loaded
				# (2)
				#   [w/pol]   UDM object has assigend policies in LDAP directory
				#   [w/o_pol] UDM object has no policies assigend in LDAP directory
				# (3)
				#   [inherit] user request to (virtually) change the policy to 'inherited'
				#   [set_pol] user request to (virtually) assign a particular policy
				faked_policy_reference = None
				if object_dn and not policy_dn:
					# case: [edit; w/pol; inherit]
					# -> current policy is (virtually) overwritten with 'None'
					faked_policy_reference = [None]
				elif not object_dn and policy_dn:
					# cases:
					# * [new; w/pol; inherit]
					# * [new; w/pol; set_pol]
					# -> old + temporary policy are both (virtually) set at the parent container
					faked_policy_reference = obj.policies + [policy_dn]
				else:
					# cases:
					# * [new; w/o_pol; inherit]
					# * [new; w/o_pol; set_pol]
					# * [edit; w/pol; set_pol]
					# * [edit; w/o_pol; inherit]
					# * [edit; w/o_pol; set_pol]
					faked_policy_reference = policy_dn

				policy_obj.policy_result(faked_policy_reference)
				infos = copy.copy(policy_obj.polinfo_more)
				for key, value in infos.items():
					if key in policy_obj.polinfo:
						if isinstance(infos[key], (tuple, list)):
							continue
						infos[key]['value'] = policy_obj.polinfo[key]

				ret.append(infos)
			return ret

		thread = notifier.threads.Simple('ObjectPolicies', notifier.Callback(_thread, request), notifier.Callback(self._thread_finished, request))
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

		thread = notifier.threads.Simple('ObjectOptions', notifier.Callback(_thread, object_type, object_dn), notifier.Callback(self._thread_finished, request))
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
		try:
			urlopen(request)
		except Exception as e:
			try:
				# try to parse an html error
				body = e.read()
				detail = re.search('<span id="details">(?P<details>.*?)</span>', body).group(1)
			except:
				detail = str(e)
			raise UMC_CommandError(_('An error occurred while sending the request: %s') % detail)
		else:
			# creating a new ucr variable to prevent double registration (Bug #35711)
			handler_set(['ucs/web/license/requested=true'])
			return True
