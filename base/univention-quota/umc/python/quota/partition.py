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

import df
from univention.lib import fstab
import mtab
import tools

_ = umc.Translation('univention-management-console-module-quota').translate

class Commands(object):
	def getPartitions(self, request):
		result = []
		resultMessage = ''
		try:
			fs = fstab.File()
			mt = mtab.File()
		except IOError as error:
			MODULE.error('Could not open %s' % error.filename)
			resultMessage = _('Could not open %s' % error.filename)
			request.status = MODULE_ERR
		else:
			partitions = fs.get(['xfs', 'ext3', 'ext2'], False) # TODO ext4?
			for partition in partitions:
				listEntry = {}
				if partition.uuid:
					listEntry['partitionDevice'] = partition.uuid
				else:
					listEntry['partitionDevice'] = partition.spec
				listEntry['mountPoint'] = partition.mount_point
				listEntry['partitionSize'] = None
				listEntry['freeSpace'] = None
				listEntry['inUse'] = False
				mountedPartition = mt.get(partition.spec)
				if mountedPartition:
					infoPartition = df.DeviceInfo(partition.mount_point) # TODO rename?
					listEntry['partitionSize'] = tools.block2byte(infoPartition.size(), 'GB', 1)
					listEntry['freeSpace'] = tools.block2byte(infoPartition.free(), 'GB', 1)
					if 'usrquota' in mountedPartition.options:
						listEntry['inUse'] = True
				result.append(listEntry)
			request.status = SUCCESS
		self.finished(request.id, result, resultMessage)

	def getPartitionInfo(self, request):
		result = {}
		resultMessage = ''
		try:
			fs = fstab.File()
			mt = mtab.File()
		except IOError as error:
			MODULE.error('Could not open %s' % error.filename)
			resultMessage = _('Could not open %s' % error.filename)
			request.status = MODULE_ERR
		else:
			partition = fs.find(spec = request.options['partitionDevice'])
			if partition:
				mounted = mt.get(partition.spec)
				if mounted:
					result['mountPoint'] = mounted.mount_point
					result['filesystem'] = mounted.type
					result['options'] = mounted.options
					request.status = SUCCESS
				else:
					request.status = MODULE_ERR
					resultMessage = _('This partition is currently not mounted')
			else:
				request.status = MODULE_ERR
				resultMessage = _('No partition found')
		self.finished(request.id, result, resultMessage)

	def activatePartitions(self, request):
		cb = notifier.Callback(self._activatePartitions, request)
		tools.activate_quota(request.options['partitions'], True, cb)

	def deactivatePartitions(self, request):
		cb = notifier.Callback(self._activatePartitions, request)
		tools.activate_quota(request.options['partitions'], False, cb)

	def _activatePartitions(self, thread, cbResult, request):
		message = '<tr><th>%s</th><th>%s</th><th>%s</th></tr>' % (_('Partition'), _('State'), _('Message'))
		failed = False
		for partitionDevice, partitionInfo in cbResult.items():
			(success, message, ) = partitionInfo
			if not success:
				failed = True
			message = '%s<tr><th>%s</th><th>%s</th><th>%s</th></tr>' % (message, partitionDevice, _(str(success)), _(message))
		message = '<table>%s</table>' % message
		request.status = SUCCESS
		self.finished(request.id, {'message': message, 'failed': failed})
