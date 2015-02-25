#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages system services
#
# Copyright 2011-2015 Univention GmbH
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

import subprocess
import notifier
import notifier.threads

import univention.info_tools as uit
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import simple_response, sanitize
from univention.management.console.modules.sanitizers import PatternSanitizer
from univention.management.console.protocol.definitions import *

import univention.service_info as usi
import univention.config_registry

_ = umc.Translation('univention-management-console-module-services').translate

class Instance(umcm.Base):
	def _run_it(self, services, action):
		failed = []
		for srv in services:
			if subprocess.call(('/usr/sbin/invoke-rc.d', srv, action)):
				failed.append(srv)
		return failed

	@sanitize(pattern=PatternSanitizer(default='.*'))
	@simple_response
	def query(self, pattern):
		srvs = usi.ServiceInfo()
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

		result = []
		for name, srv in srvs.services.items():
			entry = {}
			entry['service'] = name
			if 'description' in srv:
				try:
					lang = _.im_self.locale.language
					if lang in (None, 'C'):
						lang = 'en'
					entry['description'] = srv['description[%s]' % lang]
				except KeyError:
					entry['description'] = srv['description']
			else:
				entry['description'] = None
			key = '%s/autostart' % name
			if 'start_type' in srv:
				key = srv['start_type']
			# default: autostart=yes
			if not ucr.get(key):
				entry['autostart'] = 'yes'
			elif ucr.get(key).lower() in ('no'):
				entry['autostart']  = 'no'
			elif ucr.get(key).lower() in ('manually'):
				entry['autostart']  = 'manually'
			else:
				entry['autostart'] = 'yes'
			# Check if service is running
			if srv.running:
				entry['isRunning'] = True
			else:
				entry['isRunning'] = False
			for value in entry.values():
				if pattern.match(str(value)):
					result.append(entry)
					break

		return result

	def start(self, request):
		if self.permitted('services/start', request.options):
			message = {}
			message['success'] = _('Successfully started')
			message['failed'] = _('Starting the following services failed:')
			cb = notifier.Callback(self._service_changed, request, message)
			func = notifier.Callback(self._run_it, request.options, 'start')
			thread = notifier.threads.Simple('services', func, cb)
			thread.run()
		else:
			message = _('You are not permitted to run this command.')
			request.status = MODULE_ERR
			self.finished(request.id, None, message)

	def stop(self, request):
		if self.permitted('services/stop', request.options):
			message = {}
			message['success'] = _('Successfully stopped')
			message['failed'] = _('Stopping the following services failed:')
			cb = notifier.Callback(self._service_changed, request, message)
			func = notifier.Callback(self._run_it, request.options, 'stop')
			thread = notifier.threads.Simple('services', func, cb)
			thread.run()
		else:
			message = _('You are not permitted to run this command.')
			request.status = MODULE_ERR
			self.finished(request.id, None, message)

	def restart(self, request):
		MODULE.error(str(request.arguments))
		if self.permitted('services/restart', request.options):
			message = {}
			message['success'] = _('Successfully restarted')
			message['failed'] = _('Restarting the following services failed:')
			cb = notifier.Callback(self._service_changed, request, message)
			func = notifier.Callback(self._run_it, request.options, 'restart')
			thread = notifier.threads.Simple('services', func, cb)
			thread.run()
		else:
			message = _('You are not permitted to run this command.')
			request.status = MODULE_ERR
			self.finished(request.id, None, message)

	def _service_changed(self, thread, result, request, message):
		if result:
			if len(request.options) == 1:
				error_message = '%s %s' % (message['failed'], result[0])
				request.status = MODULE_ERR
				self.finished(request.id, {'success': False}, error_message)
			else:
				request.status = SUCCESS
				self.finished(request.id, {'objects': result, 'success': False})
		else:
			request.status = SUCCESS
			self.finished(request.id, {'success': True}, message['success'])

	def start_type(self, request):
		message = None
		srvs = usi.ServiceInfo()

		failed = []
		for name in request.options:
			srv = srvs.services.get(name, None)
			if srv:
				key = '%s/autostart' % name
				if 'start_type' in srv:
					key = srv['start_type']

				value = 'yes'
				if request.arguments[0] == 'services/start_auto':
					value = 'yes'
				if request.arguments[0] == 'services/start_manual':
					value = 'manually'
				if request.arguments[0] == 'services/start_never':
					value = 'no'
				univention.config_registry.handler_set(['%s=%s' % (key, value)])
			else:
				failed.append(name)

		if failed:
			if len(request.options) == 1:
				message = _('Could not change start type')
				request.status = MODULE_ERR
				self.finished(request.id, {'success': False}, message)
			else:
				request.status = SUCCESS
				self.finished(request.id, {'objects': failed, 'success': False})
		else:
			message = _('Successfully changed start type')
			request.status = SUCCESS
			self.finished(request.id, {'success': True}, message)
