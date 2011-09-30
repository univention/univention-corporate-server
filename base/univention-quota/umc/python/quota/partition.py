#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: handles partition related commands
#
# Copyright 2006-2011 Univention GmbH
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

from fnmatch import fnmatch
import notifier

from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *
import univention.management.console as umc

import fstab
import mtab
import tools

_ = umc.Translation('univention-management-console-module-quota').translate

class Commands(object):
	def quota_partition_info(self, request):
		message = ''
		fs = fstab.File()
		mt = mtab.File()
		part = fs.find(spec = request.options['partitionDevice'])
		mounted = mt.get(part.spec)
		result = {}
		if mounted:
			result['mountPoint'] = mounted.mount_point
			result['filesystem'] = mounted.type
			result['options'] = mounted.options
			request.status = SUCCESS
		else:
			request.status = MODULE_ERR
		self.finished(request.id, result, message)
	def quota_partition_show(self, request):
		message = ''
		fs = fstab.File()
		mt = mtab.File()
		part = fs.find(spec = request.options['partitionDevice'])
		mounted = mt.get(part.spec)
		if mounted and 'usrquota' in mounted.options:
			cb = notifier.Callback(self._quota_partition_show, request.id,
			                       request.options['partitionDevice'], request)
			tools.repquota(request.options['partitionDevice'], cb)
		else:
			request.status = MODULE_ERR
			MODULE.error('partition is not mounted') # TODO
			self.finished(request.id, message)

	def _quota_partition_show(self, pid, status, result, id, partition,
	                          request):
		'''This function is invoked when a repquota process has died and
		there is output to parse that is restructured as UMC Dialog'''

		# general information
		devs = fstab.File()
		part = devs.find(spec = partition)

		# skip header
		try:
			header = 0
			while not result[header].startswith('----'):
				header += 1
		except:
			pass
		quotas = tools.repquota_parse(partition, result[header + 1 :])
		erg = []
		for listEntry in quotas:
			if fnmatch(listEntry['user'], request.options['filter']):
				erg.append(listEntry)

		request.status = SUCCESS
		self.finished(id, erg)
		#self.finished(id, (part, quotas))

	def quota_partition_activate(self, request):
		cb = notifier.Callback(self._quota_partition_activate, request)
		tools.activate_quota(request.options['partitions'], True, cb)

	def quota_partition_deactivate(self, request):
		cb = notifier.Callback(self._quota_partition_activate, request)
		tools.activate_quota(request.options['partitions'], False, cb)

	def _quota_partition_activate(self, thread, cbResult, request):
		result = []
		failed = False
		for partitionDevice, partitionInfo in cbResult.items():
			(success, message, ) = partitionInfo
			if not success:
				failed = True
			result.append({'partitionDevice': partitionDevice,
			               'success': str(success),
			               'message': message,
			               })
		if failed:
			request.status = MODULE_ERR
		else:
			request.status = SUCCESS
		self.finished(request.id, result)
