#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: handles partition related commands
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

import univention.management.console as umc
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import MODULE_ERR, SUCCESS

from . import df
from . import mtab
from . import tools

from univention.lib import fstab

_ = umc.Translation('univention-management-console-module-quota').translate


class Commands(object):

	def partitions_query(self, request):
		result = []
		message = None
		try:
			fs = fstab.File()
			mt = mtab.File()
		except IOError as error:
			MODULE.error('Could not open %s' % error.filename)
			message = _('Could not open %s') % error.filename
			request.status = MODULE_ERR
		else:
			partitions = fs.get(['xfs', 'ext4', 'ext3', 'ext2'], False)
			for partition in partitions:
				list_entry = {}
				list_entry['partitionDevice'] = partition.spec
				list_entry['mountPoint'] = partition.mount_point
				list_entry['partitionSize'] = None
				list_entry['freeSpace'] = None
				list_entry['inUse'] = tools.quota_is_enabled(partition)
				mounted_partition = mt.get(partition.spec)
				if mounted_partition:
					partition_info = df.DeviceInfo(partition.mount_point)
					list_entry['partitionSize'] = tools.block2byte(partition_info.size(), 'GB', 1)
					list_entry['freeSpace'] = tools.block2byte(partition_info.free(), 'GB', 1)
				result.append(list_entry)
			request.status = SUCCESS
		self.finished(request.id, result, message)

	def partitions_info(self, request):
		result = {}
		message = None
		try:
			fs = fstab.File()
			mt = mtab.File()
		except IOError as error:
			MODULE.error('Could not open %s' % error.filename)
			message = _('Could not open %s') % error.filename
			request.status = MODULE_ERR
		else:
			partition = fs.find(spec=request.options['partitionDevice'])
			if partition:
				mounted_partition = mt.get(partition.spec)
				if mounted_partition:
					result['mountPoint'] = mounted_partition.mount_point
					result['filesystem'] = mounted_partition.type
					result['options'] = mounted_partition.options
					request.status = SUCCESS
				else:
					request.status = MODULE_ERR
					message = _('This partition is currently not mounted')
			else:
				request.status = MODULE_ERR
				message = _('No partition found')
		self.finished(request.id, result, message)

	def partitions_activate(self, request):
		MODULE.info('quota/partitions/activate: %s' % request.options['partitionDevice'])
		callback = notifier.Callback(self._partitions_activate, request)
		tools.activate_quota(request.options['partitionDevice'], True, callback)

	def _partitions_activate(self, thread, result, request):
		message = None
		success = True
		for obj in result:
			if not obj['success']:
				success = False
		if success:
			message = _('Quota support successfully activated')
		request.status = SUCCESS
		self.finished(request.id, {'objects': result, 'success': success}, message)

	def partitions_deactivate(self, request):
		MODULE.info('quota/partitions/deactivate: %s' % request.options['partitionDevice'])
		callback = notifier.Callback(self._partitions_deactivate, request)
		tools.activate_quota(request.options['partitionDevice'], False, callback)

	def _partitions_deactivate(self, thread, result, request):
		message = None
		success = True
		for obj in result:
			if not obj['success']:
				success = False
		if success:
			message = _('Quota support successfully deactivated')
		request.status = SUCCESS
		self.finished(request.id, {'objects': result, 'success': success}, message)
