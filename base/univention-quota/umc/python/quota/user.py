#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: show quota information for a user
#
# Copyright 2006-2019 Univention GmbH
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

from __future__ import absolute_import

import notifier
import notifier.threads

from univention.lib import fstab
from univention.management.console import Translation
from univention.management.console.log import MODULE
from univention.management.console.base import UMC_Error
from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import StringSanitizer, IntegerSanitizer, PatternSanitizer

from . import mtab
from . import tools

_ = Translation('univention-management-console-module-quota').translate


class LimitSanitizer(IntegerSanitizer):

	def _sanitize(self, value, name, further_arguments):
		if not value:
			return self.default
		return super(LimitSanitizer, self)._sanitize(value, name, further_arguments)


class Commands(object):

	@sanitize(
		partitionDevice=StringSanitizer(required=True),
		filter=PatternSanitizer(default='.*'),
	)
	def users_query(self, request):
		partitionDevice = request.options['partitionDevice']
		self._check_error(request, partitionDevice)

		callback = notifier.Callback(self._users_query, request.id, partitionDevice, request)
		tools.repquota(request.options['partitionDevice'], callback)

	def _users_query(self, pid, status, callbackResult, id, partition, request):
		'''This function is invoked when a repquota process has died and
		there is output to parse that is restructured as UMC Dialog'''
		# general information
		devs = fstab.File()
		devs.find(spec=partition)

		# skip header
		header = 0
		try:
			while not callbackResult[header].startswith('----'):
				header += 1
		except IndexError:
			pass
		quotas = tools.repquota_parse(partition, callbackResult[header + 1:])
		result = [q for q in quotas if request.options['filter'].match(q['user'])]
		self.finished(request.id, result)

	@sanitize(
		partitionDevice=StringSanitizer(required=True),
		user=StringSanitizer(required=True),
		sizeLimitSoft=LimitSanitizer(default=0, required=True),
		sizeLimitHard=LimitSanitizer(default=0, required=True),
		fileLimitSoft=LimitSanitizer(default=0, required=True),
		fileLimitHard=LimitSanitizer(default=0, required=True),
	)
	def users_set(self, request):
		def _thread(request):
			partition = request.options['partitionDevice']
			user = request.options['user']
			if isinstance(user, unicode):
				user = user.encode('utf-8')

			size_soft = request.options['sizeLimitSoft']
			size_hard = request.options['sizeLimitHard']
			file_soft = request.options['fileLimitSoft']
			file_hard = request.options['fileLimitHard']
			self._check_error(request, partition)

			if tools.setquota(partition, user, tools.byte2block(size_soft), tools.byte2block(size_hard), file_soft, file_hard):
				raise UMC_Error(_('Failed to modify quota settings for user %(user)s on partition %(partition)s.') % {'user': user, 'partition': partition})

			return {'objects': [], 'success': True}

		thread = notifier.threads.Simple('Set', notifier.Callback(_thread, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	def users_remove(self, request):
		def _thread(request):
			partitions = []
			success = True
			objects = []

			# Determine different partitions
			for obj in request.options:
				partitions.append(obj['object'].split('@')[-1])
			for partition in set(partitions):
				self._check_error(request, partition)

			# Remove user quota
			for obj in request.options:
				(unicode_user, partition) = obj['object'].split('@', 1)
				user = unicode_user.encode('utf-8')
				if tools.setquota(partition, user, 0, 0, 0, 0):
					objects.append({'id': obj['object'], 'success': False})
					success = False
				else:
					objects.append({'id': obj['object'], 'success': True})

			return {'objects': objects, 'success': success}

		thread = notifier.threads.Simple('Remove', notifier.Callback(_thread, request), notifier.Callback(self.thread_finished_callback, request))
		thread.run()

	def _check_error(self, request, partition_name):  # TODO
		try:
			fs = fstab.File()
			mt = mtab.File()
		except IOError as error:
			MODULE.error('Could not open %s' % error.filename)
			raise ValueError(_('Could not open %s') % error.filename)

		partition = fs.find(spec=partition_name)
		if partition:
			mounted_partition = mt.get(partition.spec)
			if mounted_partition:
				if 'usrquota' not in mounted_partition.options and 'usrjquota=aquota.user' not in mounted_partition.options:
					raise UMC_Error(_('The following partition is mounted without quota support: %s') % partition_name)
			else:
				raise UMC_Error(_('The following partition is currently not mounted: %s') % partition_name)
		else:
			raise UMC_Error(_('No partition found (%s)') % partition_name)
