#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software management
#
# Copyright 2011-2012 Univention GmbH
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

import re
import notifier
import notifier.threads
from contextlib import contextmanager
import subprocess
import shlex

import apt

import univention.config_registry
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.modules.decorators import simple_response, sanitize, log, sanitize_list, multi_response
from univention.management.console.modules.sanitizers import PatternSanitizer, MappingSanitizer, DictSanitizer, StringSanitizer, ChoicesSanitizer, ListSanitizer
from sanitizers import basic_components_sanitizer, advanced_components_sanitizer, add_components_sanitizer
from app_center import Application

from univention.lib.package_manager import PackageManager, LockError

from univention.management.console.log import MODULE

from univention.updater import UniventionUpdater
from univention.updater.commands import cmd_update
from univention.updater.errors import ConfigurationError

_ = umc.Translation('univention-management-console-module-packages').translate

from constants import *

class Changes(object):
	def __init__(self, ucr):
		self.ucr = ucr
		self._changes = {}

	def changed(self):
		return bool(self._changes)

	def _bool_string(self, variable, value):
		"""Returns a boolean string representation for a boolean UCR variable. We need
			this as long as we don't really know that all consumers of our variables
			transparently use the ucr.is_true() method to process the values. So we
			write the strings that we think are most suitable for the given variable.

			*** NOTE *** I would like to see such function in the UCR base class
				so we could call

								ucr.set_bool(variable, boolvalue)

				and the ucr itself would know which string representation to write.
		"""
		yesno		= ['no', 'yes']
		truefalse	= ['False', 'True']
		enabled		= ['disabled', 'enabled']
		enable		= ['disable', 'enable']
		onoff		= ['off', 'on']
		onezero		= ['0', '1']		# strings here! UCR doesn't know about integers

		# array of strings to match against the variable name, associated with the
		# corresponding bool representation to use. The first match is used.
		# 'yesno' is default if nothing matches.
		#
		# *** NOTE *** Currently these strings are matched as substrings, not regexp.

		setup = [
			['repository/online/component', enabled],
			['repository/online', onoff]
		]

		intval = int(bool(value))			# speak C:  intval = value ? 1 : 0;

		for s in setup:
			if s[0] in variable:
				return s[1][intval]
		return yesno[intval]

	def set_registry_var(self, name, value):
		""" Sets a registry variable and tracks changedness in a private variable.
			This enables the set_save_commit_load() method to commit the files being affected
			by the changes we have made.

			Function handles boolean values properly.
		"""
		try:
			oldval = self.ucr.get(name, '')
			if isinstance(value, bool):
				value = self._bool_string(name, value)

			# Don't do anything if the value being set is the same as
			# the value already found.
			if value == oldval:
				return

			# Possibly useful: if the value is the empty string -> try to unset this variable.
			# FIXME Someone please confirm that there are no UCR variables that need
			#		to be set to an empty string!
			if value == '':
				if name in self.ucr:
					MODULE.info("Deleting registry variable '%s'" % name)
					del self.ucr[name]
			else:
				MODULE.info("Setting registry variable '%s' = '%s'" % (name, value))
				self.ucr[name] = value
			if value != '' or oldval != '':
				self._changes[name] = (oldval, value)
		except Exception as e:
			MODULE.warn("set_registry_var('%s', '%s') ERROR %s" % (name, value, str(e)))

	def commit(self):
		handler = univention.config_registry.configHandlers()
		handler.load()
		handler(self._changes.keys(), (self.ucr, self._changes))

class Instance(umcm.Base):
	def init(self):
		self.package_manager = PackageManager(
			info_handler=MODULE.process,
			step_handler=None,
			error_handler=MODULE.warn,
			lock=False,
			always_noninteractive=True,
		)
		self.uu = UniventionUpdater(False)
		self.ucr = univention.config_registry.ConfigRegistry()
		self.ucr.load()

	@contextmanager
	def set_save_commit_load(self):
		changes = Changes(self.ucr)
		yield changes
		self.ucr.save()
		self.ucr.load()
		if changes.changed():
			changes.commit()


	@sanitize(pattern=PatternSanitizer(default='.*'))
	@simple_response
	def app_center_query(self, pattern):
		applications = Application.all()
		result = []
		for application in applications:
			if pattern.match(application.name):
				result.append(application.to_dict_overwiew())
		return result

	@sanitize(application=StringSanitizer(minimum=1, required=True))
	@simple_response
	def app_center_get(self, application):
		application = Application.find(application)
		return application.to_dict_detail(self)

	@sanitize(function=ChoicesSanitizer(['install', 'uninstall'], required=True),
		application=StringSanitizer(minimum=1, required=True)
		)
	def app_center_invoke(self, request):
		function = request.options.get('function')
		application_id = request.options.get('application')
		application = Application.find(application_id)
		try:
			with self.package_manager.locked(reset_status=True):
				application_found = application is not None
				self.finished(request.id, application_found)
				if application_found:
					def _thread(module, application, function):
						with module.package_manager.locked(set_finished=True):
							if function == 'install':
								return application.install(module)
							else:
								return application.uninstall(module)
					def _finished(thread, result):
						if isinstance(result, BaseException):
							MODULE.warn('Exception during %s %s: %s' % (function, application_id, str(result)))
					thread = notifier.threads.Simple('app_center_invoke', 
						notifier.Callback(_thread, self, application, function), _finished)
					thread.run()
		except LockError:
			# make it thread safe: another process started a package manager
			# this module instance already has a running package manager
			raise umcm.UMC_Error(_('Another package operation is in progress'))

	@simple_response
	def sections(self):
		""" fills the 'sections' combobox in the search form """

		sections = set()
		for package in self.package_manager.packages():
			sections.add(package.section)

		return sorted(sections)

	@sanitize(pattern=PatternSanitizer(required=True))
	@simple_response
	def query(self, pattern, installed=False, section='all', key='package'):
		""" Query to fill the grid. Structure is fixed here.
		"""
		result = []
		for package in self.package_manager.packages():
			if (not installed) or package.is_installed:
				if section == 'all' or package.section == section:
					toshow = False
					if pattern.pattern == '.*':
						toshow = True
					elif key == 'package' and pattern.search(package.name):
						toshow = True
					elif key == 'description' and pattern.search(package.candidate.raw_description):
						toshow = True
					if toshow:
						result.append(self._package_to_dict(package, full=False))
		return result

	@simple_response
	def get(self, package):
		""" retrieves full properties of one package """

		package = self.package_manager.get_package(package)
		if package is not None:
			return self._package_to_dict(package, full=True)
		else:
			# TODO: 404?
			return {}

	@sanitize(function=MappingSanitizer({
				'install' : 'install',
				'upgrade' : 'install',
				'uninstall' : 'remove',
			}, required=True),
		packages=ListSanitizer(StringSanitizer(minimum=1), required=True)
		)
	@simple_response
	def invoke_dry_run(self, packages, function):
		packages = self.package_manager.get_packages(packages)
		kwargs = {'install' : [], 'remove' : [], 'dry_run' : True}
		if function == 'install':
			kwargs['install'] = packages
		else:
			kwargs['remove'] = packages
		return dict(zip(['install', 'remove', 'broken'], self.package_manager.mark(**kwargs)))

	@sanitize(function=MappingSanitizer({
				'install' : 'install',
				'upgrade' : 'install',
				'uninstall' : 'remove',
			}, required=True),
		packages=ListSanitizer(StringSanitizer(minimum=1), required=True)
		)
	def invoke(self, request):
		""" executes an installer action """
		packages = request.options.get('packages')
		function = request.options.get('function')

		try:
			with self.package_manager.locked(reset_status=True):
				not_found = [pkg_name for pkg_name in packages if self.package_manager.get_package(pkg_name) is None]
				self.finished(request.id, {'not_found' : not_found})

				if not not_found:
					def _thread(package_manager, function, packages):
						with package_manager.locked(set_finished=True):
							if function == 'install':
								package_manager.install(*packages)
							else:
								package_manager.uninstall(*packages)
					def _finished(thread, result):
						if isinstance(result, BaseException):
							MODULE.warn('Exception during %s %s: %r' % (function, packages, str(result)))
					thread = notifier.threads.Simple('invoke', 
						notifier.Callback(_thread, self.package_manager, function, packages), _finished)
					thread.run()
		except LockError:
			# make it thread safe: another process started a package manager
			# this module instance already has a running package manager
			raise umcm.UMC_Error(_('Another package operation is in progress'))

	@simple_response
	def progress(self):
		timeout = 5
		return self.package_manager.poll(timeout)

	def _package_to_dict(self, package, full):
		""" Helper that extracts properties from a 'apt_pkg.Package' object
			and stores them into a dictionary. Depending on the 'full'
			switch, stores only limited (for grid display) or full
			(for detail view) set of properties.
		"""
		installed = package.installed # may be None
		candidate = package.candidate

		result = {
			'package': package.name,
			'installed': package.is_installed,
			'upgradable': package.is_upgradable,
			'summary': candidate.summary,
		}
		
		# add (and translate) a combined status field
		# *** NOTE *** we translate it here: if we would use the Custom Formatter
		#		of the grid then clicking on the sort header would not work.
		if package.is_installed:
			if package.is_upgradable:
				result['status'] = _('upgradable')
			else:
				result['status'] = _('installed')
		else:
			result['status'] = _('not installed')

		# additional fields needed for detail view
		if full:
			result['section'] = package.section
			result['priority'] = package.priority
			# Some fields differ depending on whether the package is installed or not:
			if package.is_installed:
				result['summary'] = installed.summary # take the current one
				result['description'] = installed.description
				result['installed_version'] = installed.version
				result['size'] = installed.installed_size
				if package.is_upgradable:
					result['candidate_version'] = candidate.version
			else:
				del result['upgradable'] # not installed: don't show 'upgradable' at all
				result['description'] = candidate.description
				result['size'] = candidate.installed_size
				result['candidate_version'] = candidate.version
			# format size to handle bytes
			size = result['size']
			byte_mods = ['B', 'kB', 'MB']
			for byte_mod in byte_mods:
				if size < 10000:
					break
				size = float(size) / 1000 # MB, not MiB
			else:
				size = size * 1000 # once too often
			if size == int(size):
				format_string = '%d %s'
			else:
				format_string = '%.2f %s'
			result['size'] = format_string % (size, byte_mod)

		return result

	@simple_response
	def query_components(self):
		"""	Returns components list for the grid in the ComponentsPage.
		"""
		# be as current as possible.
		self.uu.ucr_reinit()
		self.ucr.load()

		result = []
		for comp in self.uu.get_all_components():
			result.append(self._component(comp))
		return result

	@sanitize_list(StringSanitizer())
	@simple_response
	def get_components(self, *component_ids):
		# be as current as possible.
		self.uu.ucr_reinit()
		self.ucr.load()
		result = []
		for component_id in component_ids:
			result.append(self._component(component_id))
		return result

	@sanitize_list(DictSanitizer({'object' : advanced_components_sanitizer}))
	@simple_response
	def put_components(self, *objects):
		"""Writes back one or more component definitions.
		"""
		# umc.widgets.Form wraps the real data into an array:
		#
		#	[
		#		{
		#			'object' : { ... a dict with the real data .. },
		#			'options': None
		#		},
		#		... more such entries ...
		#	]
		#
		# Current approach is to return a similarly structured array,
		# filled with elements, each one corresponding to one array
		# element of the request:
		#
		#	[
		#		{
		#			'status'	:	a number where 0 stands for success, anything else
		#							is an error code
		#			'message'	:	a result message
		#			'object'	:	a dict of field -> error message mapping, allows
		#							the form to show detailed error information
		#		},
		#		... more such entries ...
		#	]

		result = []
		with self.set_save_commit_load() as super_ucr:
			for data in objects:
				result.append(self._put_component(data['object'], super_ucr))
			try:
				with open('/dev/null') as devnull:
					subprocess.call(shlex.split(cmd_update), stdout=devnull, stderr=devnull)
			except OSError as e:
				MODULE.error('Execution of "%s" failed: %s' % (cmd_update, str(e)))

		return result

	# do the same as put_components (update)
	# but dont allow adding an already existing entry
	add_components = sanitize_list(DictSanitizer({'object' : add_components_sanitizer}))(put_components)
	add_components.__name__ = 'add_components'

	@sanitize_list(StringSanitizer())
	@simple_response
	def del_components(self, *component_ids):
		result = []
		for component_id in component_ids:
			result.append(self._del_component(component_id))
		return result

	def _component(self, component_id):
		"""Returns a dict of properties for the component with this id.
		"""
		entry = {}
		entry['name'] = component_id
		for part in COMP_PARTS:
			entry[part] = False
		# ensure a proper bool
		entry['enabled'] = self.ucr.is_true('%s/%s' % (COMPONENT_BASE, component_id), False)
		# Most values that can be fetched unchanged
		for attr in COMP_PARAMS:
			regstr = '%s/%s/%s' % (COMPONENT_BASE, component_id, attr)
			entry[attr] = self.ucr.get(regstr, '')
		# Get default packages (can be named either defaultpackage or defaultpackages)
		entry['defaultpackages'] = list(self.uu.get_component_defaultpackage(component_id))  # method returns a set
		# Parts value (if present) must be splitted into words and added as bools.
		# For parts not contained here we have set 'False' default values.
		parts = self.ucr.get('%s/%s/parts' % (COMPONENT_BASE, component_id), '').split(',')
		for part in parts:
			p = part.strip()
			if len(p):
				entry[p] = True
		# Component status as a symbolic string
		entry['status'] = self.uu.get_current_component_status(component_id)
		entry['installed'] = self.uu.is_component_defaultpackage_installed(component_id)

		# correct the status to 'installed' if (1) status is 'available' and (2) installed is true
		if entry['status'] == 'available' and entry['installed']:
			entry['status'] = 'installed'

		# Possibly this makes sense? add an 'icon' column so the 'status' column can decorated...
		entry['icon'] = STATUS_ICONS.get(entry['status'], DEFAULT_ICON)

		# Allowance for an 'install' button: if a package is available, not installed, and there's a default package specified
		entry['installable'] = entry['status'] == 'available' and bool(entry['defaultpackages']) and not entry['installed']

		return entry

	def _put_component(self, data, super_ucr):
		"""	Does the real work of writing one component definition back.
			Will be called for each element in the request array of
			a 'put' call, returns one element that has to go into
			the result of the 'put' call.
			Function does not throw exceptions or print log messages.
		"""
		result = {
			'status': PUT_SUCCESS,
			'message': '',
			'object': {},
		}
		try:
			parts = set()
			name = data.pop('name')
			named_component_base = '%s/%s' % (COMPONENT_BASE, name)
			old_parts = self.ucr.get('%s/parts' % named_component_base, '')
			if old_parts:
				for part in old_parts.split(','):
					parts.add(part)
			for key, val in data.iteritems():
				if val is None:
					# was not given, so dont update
					continue
				if key in COMP_PARAMS:
					super_ucr.set_registry_var('%s/%s' % (named_component_base, key), val)
				elif key == 'enabled':
					super_ucr.set_registry_var(named_component_base, val)
				elif key in COMP_PARTS:
					if val:
						parts.add(key)
					else:
						parts.discard(key)
			super_ucr.set_registry_var('%s/parts' % named_component_base, ','.join(sorted(parts)))
		except Exception as e:
			result['status'] = PUT_PROCESSING_ERROR
			result['message'] = "Parameter error: %s" % str(e)

		# Saving the registry and invoking all commit handlers is deferred until
		# the end of the loop over all request elements.

		return result

	def _del_component(self, component_id):
		""" Removes one component. Note that this does not remove
			entries below repository/online/component/<id> that
			are not part of a regular component definition.
		"""
		result = {}
		result['status'] = PUT_SUCCESS

		try:
			with self.set_save_commit_load() as super_ucr:
				named_component_base = '%s/%s' % (COMPONENT_BASE, component_id)
				for var in COMP_PARAMS + ['parts']:
					# COMP_PARTS (maintained,unmaintained) are special
					# '' deletes this variable
					super_ucr.set_registry_var('%s/%s' % (named_component_base, var), '')

				super_ucr.set_registry_var(named_component_base, '')

		except Exception as e:
			result['status'] = PUT_PROCESSING_ERROR
			result['message'] = "Parameter error: %s" % str(e)

		return result

	@multi_response
	def get_settings(self):
		# *** IMPORTANT *** Our UCR copy must always be current. This is not only
		#	to catch up changes made via other channels (ucr command line etc),
		#	but also to reflect the changes we have made ourselves!
		self.ucr.load()

		return {
			'maintained' : self.ucr.is_true('repository/online/maintained', False),
			'unmaintained' : self.ucr.is_true('repository/online/unmaintained', False),
			'server' : self.ucr.get('repository/online/server', ''),
			'prefix' : self.ucr.get('repository/online/prefix', ''),
		}

	@sanitize_list(DictSanitizer({'object' : basic_components_sanitizer}),
		min_elements=1, max_elements=1 # moduleStore with one element...
	)
	@multi_response
	def put_settings(self, object):
		changed = False
		#		errors['server'] = _("Empty server name not allowed")
		#		estr = _("At least one out of %s must be selected.") % '(maintained, unmaintained)'
		#		errors['maintained'] = estr
		#		errors['unmaintained'] = estr

		# Set values into our UCR copy.
		try:
			with self.set_save_commit_load() as super_ucr:
				for key, value in object.iteritems():
					MODULE.info("   ++ Setting new value for '%s' to '%s'" % (key, value))
					super_ucr.set_registry_var('%s/%s' % (ONLINE_BASE, key), value)
				changed = super_ucr.changed()
		except Exception as e:
			MODULE.warn("   !! Writing UCR failed: %s" % str(e))
			return {'message' : str(e), 'status' : PUT_WRITE_ERROR}
		try:
			with open('/dev/null') as devnull:
				subprocess.call(shlex.split(cmd_update), stdout=devnull, stderr=devnull)
		except OSError as e:
			MODULE.error('Execution of "%s" failed: %s' % (cmd_update, str(e)))

		# Bug #24878: emit a warning if repository is not reachable
		try:
			updater = UniventionUpdater()
			for line in updater.print_version_repositories().split('\n'):
				if line.strip():
					break
			else:
				raise ConfigurationError()
		except ConfigurationError:
			msg = _("There is no repository at this server (or at least none for the current UCS version)")
			MODULE.warn("   !! Updater error: %s" % msg)
			response = {'message' : msg, 'status' : PUT_UPDATER_ERROR}
			# if nothing was committed, we want a different type of error code,
			# just to appropriately inform the user
			if changed:
				response['status'] = PUT_UPDATER_NOREPOS
			return response
		except:
			info = sys.exc_info()
			emsg = '%s: %s' % info[:2]
			MODULE.warn("   !! Updater error [%s]: %s" % (emsg))
			return {'message' : str(info[1]), 'status' : PUT_UPDATER_ERROR}
		return {'status' : PUT_SUCCESS}

