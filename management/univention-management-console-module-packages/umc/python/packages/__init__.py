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

import apt

import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.modules.decorators import simple_response, sanitize
from sanitizers import AptFunctionSanitizer, PatternSanitizer

from univention.lib.package_manager import PackageManager, LockError

from univention.management.console.log import MODULE

_ = umc.Translation('univention-management-console-module-packages').translate

class Instance(umcm.Base):
	def init(self):
		self.package_manager	= None

	@simple_response
	def sections(self):
		""" fills the 'sections' combobox in the search form """

		cache = apt.Cache()
		sections = set()
		for package in cache.keys():
			sections.add(cache[package].section)

		return [{'id' : section, 'label' : section} for section in sorted(sections)]

	@sanitize(pattern=PatternSanitizer())
	@simple_response
	def query(self, pattern, installed=False, section='all', key='package'):
		""" Query to fill the grid. Structure is fixed here.
		"""
		result = []
		cache = apt.Cache()
		for pkey in cache.keys():
			if (not installed) or cache[pkey].is_installed:
				pkg = cache[pkey]
				if section == 'all' or pkg.section == section:
					toshow = False
					if pattern.pattern == '.*':
						toshow = True
					elif key == 'package' and pattern.search(pkey):
						toshow = True
					elif key == 'description' and pattern.search(pkg.rawDescription):
						toshow = True
					if toshow:
						result.append(self._package_to_dict(pkg, full=False))
		return result
		
	@simple_response
	def get(self, package):
		""" retrieves full properties of one package """

		cache = apt.Cache()

		if package in cache:
			return self._package_to_dict(cache[package], full=True)
		else:
			# TODO: 404?
			return {}

	@sanitize(function=AptFunctionSanitizer(required=True, may_change_value=True))
	def invoke(self, request):
		""" executes an installer action """
		package = request.options.get('package')
		function = request.options.get('function')

		if self._pm_running():
			# this module instance already has a running package manager
			raise umcm.UMC_Error(_('Another package operation is in progress'))
		try:
			self.package_manager = PackageManager(
				info_handler=MODULE.process,
				step_handler=None,
				error_handler=MODULE.warn,
			)
		except LockError as e:
			# make it thread safe: another process started a package manager
			raise umcm.UMC_Error(str(e))
		else:
			package_found = bool(self.package_manager.get_package(package))
			self.finished(request.id, package_found)

			if package_found:
				def _thread(package_manager, function, package):
					with package_manager.noninteractive():
						if function == 'install':
							package_manager.install(package)
						else:
							package_manager.uninstall(package)
					package_manager.unlock()
				def _finished(thread, result):
					if isinstance(result, BaseException):
						MODULE.warn('Exception during %s %s: %s' % (function, package, str(result)))
				thread = notifier.threads.Simple('invoke', 
					notifier.Callback(_thread, self.package_manager, function, package), _finished)
				thread.run()

	@simple_response
	def progress(self):
		timeout = 5
		errors = []
		if self._pm_running(if_not_locked_free_him_and_save_errors_to=errors):
			return self.package_manager.poll(timeout)
		else:
			if errors:
				return {'errors' : errors}
		return None

	def _pm_running(self, if_not_locked_free_him_and_save_errors_to=None):
		if self.package_manager is None:
			return False
		locked = self.package_manager.is_locked()
		if locked:
			return True
		else:
			if if_not_locked_free_him_and_save_errors_to is not None:
				for error in self.package_manager.progress_state._errors:
					if_not_locked_free_him_and_save_errors_to.append(error)
				# free him
				del self.package_manager
				self.package_manager = None
		return False

	def _package_to_dict(self, package, full):
		""" Helper that extracts properties from a 'apt_pkg.Package' object
			and stores them into a dictionary. Depending on the 'full'
			switch, stores only limited (for grid display) or full
			(for detail view) set of properties.
		"""
		result = {
			'package':	package.name,
			'section':	package.section,
			'installed':	package.is_installed,
			'upgradable':	package.is_upgradable,
			'summary':	package.summary
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
			result['description']	= package.description
			result['priority']	= package.priority
			# Some fields differ depending on whether the package is installed or not:
			if package.is_installed:
				# If an upgrade is available the 'Packages' class returns zero in the
				# 'installedPackageSize' field... we work around this by silently returning
				# the upgrade candidate's size.
				if package.installedPackageSize:
					result['size'] = package.installedPackageSize
				else:
					MODULE.warn("Package '%s': is_installed=true but installedPackageSize=0: using packageSize instead" % package.name)
					result['size'] = package.packageSize
				result['installed_version'] = package.installedVersion
				if package.is_upgradable:
					result['candidate_version'] = package.candidateVersion
			else:
				del result['upgradable']	# not installed: don't show 'upgradable' at all
				result['size'] = package.packageSize
				result['candidate_version'] = package.candidateVersion
			# format size to handle bytes
			size = result['size']
			byte_mods = ['B', 'kB', 'MB']
			for byte_mod in byte_mods:
				if size < 10000:
					break
				size = float(size) / 1024
			else:
				size = size * 1024 # once too often
			if size == int(size):
				format_string = '%d %s'
			else:
				format_string = '%.2f %s'
			result['size'] = format_string % (size, byte_mod)

		return result
	
