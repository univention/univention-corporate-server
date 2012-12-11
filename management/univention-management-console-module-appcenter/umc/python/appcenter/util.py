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

# standard library
from contextlib import contextmanager
import urllib2

# univention
from univention.management.console.log import MODULE
import univention.config_registry

# local application
from constants import COMPONENT_BASE, COMP_PARTS, COMP_PARAMS, STATUS_ICONS, DEFAULT_ICON, PUT_SUCCESS, PUT_PROCESSING_ERROR

# TODO: this should probably go into univention-lib
# and hide urllib/urllib2 completely
# i.e. it should be unnecessary to import them directly
# in a module
def install_opener(ucr):
	proxy_http = ucr.get('proxy/http')
	if proxy_http:
		proxy = urllib2.ProxyHandler({'http': proxy_http, 'https': proxy_http})
		opener = urllib2.build_opener(proxy)
		urllib2.install_opener(opener)

def urlopen(request):
	# use this in __init__ and app_center
	# to have the proxy handler installed globally
	return urllib2.urlopen(request)

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
		yesno = ['no', 'yes']
		#truefalse = ['False', 'True']
		enabled = ['disabled', 'enabled']
		#enable = ['disable', 'enable']
		onoff = ['off', 'on']
		#onezero = ['0', '1']		# strings here! UCR doesn't know about integers

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

@contextmanager
def set_save_commit_load(ucr):
	ucr.load()
	changes = Changes(ucr)
	yield changes
	ucr.save()
	ucr.load()
	if changes.changed():
		changes.commit()

class ComponentManager(object):
	def __init__(self, ucr, updater):
		self.ucr = ucr
		self.uu = updater

	def component(self, component_id):
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

	def is_registered(self, component_id):
		return '%s/%s' % (COMPONENT_BASE, component_id) in self.ucr

	def put_app(self, app):
		# ATTENTION: changes made here have to be done
		# in univention-add-app
		app_data = {
			'server' : app.get_server(),
			'prefix' : '',
			'maintained' : True,
			'unmaintained' : False,
			'enabled' : True,
			'name' : app.component_id,
			'description' : app.get('description'),
			'username' : '',
			'password' : '',
			'version' : 'current',
			'localmirror' : 'false',
		}
		errata_data = app_data.copy()
		errata_data['name'] += '-errata'
		errata_data['description'] = '%s Errata' % app.name
		with set_save_commit_load(self.ucr) as super_ucr:
			self.put(app_data, super_ucr)
			self.put(errata_data, super_ucr)

	def remove_app(self, app):
		with set_save_commit_load(self.ucr) as super_ucr:
			self._remove(app.component_id, super_ucr)
			self._remove(app.component_id + '-errata', super_ucr)

	def put(self, data, super_ucr):
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

	def remove(self, component_id):
		""" Removes one component. Note that this does not remove
			entries below repository/online/component/<id> that
			are not part of a regular component definition.
		"""
		result = {}
		result['status'] = PUT_SUCCESS

		try:
			with set_save_commit_load(self.ucr) as super_ucr:
				self._remove(component_id, super_ucr)

		except Exception as e:
			result['status'] = PUT_PROCESSING_ERROR
			result['message'] = "Parameter error: %s" % str(e)

		return result

	def _remove(self, component_id, super_ucr):
		named_component_base = '%s/%s' % (COMPONENT_BASE, component_id)
		for var in COMP_PARAMS + ['parts']:
			# COMP_PARTS (maintained,unmaintained) are special
			# '' deletes this variable
			super_ucr.set_registry_var('%s/%s' % (named_component_base, var), '')

		super_ucr.set_registry_var(named_component_base, '')

