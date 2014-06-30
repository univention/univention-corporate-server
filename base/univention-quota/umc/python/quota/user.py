#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: show quota information for a user
#
# Copyright 2006-2014 Univention GmbH
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

import notifier
import notifier.threads
from fnmatch import fnmatch

import univention.management.console as umc
from univention.lib import fstab
from univention.management.console.log import MODULE
from univention.management.console.modules import UMC_CommandError, UMC_OptionMissing
from univention.management.console.protocol.definitions import MODULE_ERR, SUCCESS

import mtab
import tools

_ = umc.Translation('univention-management-console-module-quota').translate

class Commands(object):
	def _check_error(self, request, partition_name): # TODO
		message = None
		try:
			fs = fstab.File()
			mt = mtab.File()
		except IOError as error:
			MODULE.error('Could not open %s' % error.filename)
			message = _('Could not open %s') % error.filename
		partition = fs.find(spec = partition_name)
		if partition:
			mounted_partition = mt.get(partition.spec)
			if mounted_partition:
				if 'usrquota' not in mounted_partition.options:
					MODULE.error('The following partition is mounted '
					             'without quota support: %s' % partition_name)
					message = _('The following partition is mounted mounted '
					            'without quota support: %s') % partition_name
			else:
				MODULE.error('The following partition is '
				             'currently not mounted: %s' % partition_name)
				message = _('The following partition is currently '
				            'not mounted: %s') % partition_name
		else:
			MODULE.error('No partition found (%s)' % partition_name)
			message = _('No partition found (%s)') % partition_name
		if message:
			request.status = MODULE_ERR
			self.finished(request.id, None, message)

	def _thread_finished(self, thread, thread_result, request):
		if not isinstance(thread_result, BaseException):
			request.status = SUCCESS
			self.finished(request.id, {'objects': thread_result['result'],
			                           'success': thread_result['success']},
			              thread_result['message'])
		else:
			message = str(thread_result) + '\n' + '\n'.join(thread.trace)
			MODULE.error('An internal error occurred: %s' % message)
			request.status = MODULE_ERR
			self.finished(request.id, None, message)

	def users_query(self, request):
		self._check_error(request, request.options['partitionDevice'])
		callback = notifier.Callback(self._users_query, request.id,
		                       request.options['partitionDevice'], request)
		tools.repquota(request.options['partitionDevice'], callback)

	def _users_query(self, pid, status, callbackResult, id, partition, request):
		'''This function is invoked when a repquota process has died and
		there is output to parse that is restructured as UMC Dialog'''
		# general information
		devs = fstab.File()
		part = devs.find(spec = partition)

		# skip header
		try:
			header = 0
			while not callbackResult[header].startswith('----'):
				header += 1
		except:
			pass
		quotas = tools.repquota_parse(partition, callbackResult[header + 1 :])
		result = []
		for list_entry in quotas:
			if fnmatch(list_entry['user'], request.options['filter']):
				result.append(list_entry)
		request.status = SUCCESS
		self.finished(request.id, result)

	def users_set(self, request):
		def _thread(request):
			message = None
			success = True
			result = []

			partition = request.options['partitionDevice']
			unicode_user = request.options['user']
			user = unicode_user.encode('utf-8')
			size_soft = request.options['sizeLimitSoft']
			size_hard = request.options['sizeLimitHard']
			file_soft = request.options['fileLimitSoft']
			file_hard = request.options['fileLimitHard']
			self._check_error(request, partition)
			failed = tools.setquota(partition, user, tools.byte2block(size_soft),
			                        tools.byte2block(size_hard),
			                        file_soft, file_hard)
			if failed:
				MODULE.error('Failed to modify quota settings for user %s '
				             'on partition %s' % (user, partition))
				message = _('Failed to modify quota settings for user %s on '
				            'partition %s') % (user, partition)
				request.status = MODULE_ERR
				self.finished(request.id, None, message)
			message = _('Successfully set quota settings')
			return {'result': result, 'message': message, 'success': success}
		thread = notifier.threads.Simple('Set', notifier.Callback(_thread, request),
										 notifier.Callback(self._thread_finished, request))
		thread.run()

	def users_remove(self, request):
		def _thread(request):
			partitions = []
			message = None
			success = True
			result = []

			# Determine different partitions
			for obj in request.options:
				partitions.append(obj['object'].split('@')[-1])
			for partition in set(partitions):
				self._check_error(request, partition)

			# Remove user quota
			for obj in request.options:
				(unicode_user, partition) = obj['object'].split('@')
				user = unicode_user.encode('utf-8')
				failed = tools.setquota(partition, user, '0', '0', '0', '0')
				if failed:
					result.append({'id': obj['object'], 'success': False})
					success = False
				else:
					result.append({'id': obj['object'], 'success': True})
			if success:
				message = _('Successfully removed quota settings')
			return {'result': result, 'message': message, 'success': success}
		thread = notifier.threads.Simple('Remove', notifier.Callback(_thread, request),
										 notifier.Callback(self._thread_finished, request))
		thread.run()
