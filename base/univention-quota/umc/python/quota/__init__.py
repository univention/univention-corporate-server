#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages quota support for locale hard drives
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

import univention.info_tools as uit
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

import df
import fstab
import mtab
import tools
import partition
import user

_ = umc.Translation('univention-management-console-modules-quota').translate

#TODO comments

class Instance(umcm.Base, partition.Commands, user.Commands):
	def __init__(self):
		umcm.Base.__init__(self)
		partition.Commands.__init__(self)
		user.Commands.__init__(self)

	def quota_list(self, request):
		result = ''
		message = ''
		try:
			fs = fstab.File()
			mt = mtab.File()

		except IOError as error:
			MODULE.error('Could not open {0}'.format(error.filename))
			message = _('Could not open {0}'.format(error.filename))
			request.status = MODULE_ERR

		#except InvalidEntry as error: #TODO
		#	pass

		else:
			partitions = fs.get(['xfs', 'ext3', 'ext2'], False) #TODO ext4?
			result = []
			for partition in partitions:
				listEntry = {}
				if partition.uuid:
					listEntry['partitionDevice'] = partition.uuid
				else:
					listEntry['partitionDevice'] = partition.spec
				listEntry['mountPoint'] = partition.mount_point
				listEntry['partitionSize'] = '-'
				listEntry['freeSpace'] = '-'
				listEntry['inUse'] = _('Deactivated')
				isMounted = mt.get(partition.spec)
				if isMounted:
					deviceInfo = df.DeviceInfo(partition.mount_point)
					listEntry['partitionSize'] = tools.block2byte(deviceInfo.size(), 1)
					listEntry['freeSpace'] = tools.block2byte(deviceInfo.free(), 1)
					if 'usrquota' in isMounted.options:
						listEntry['inUse'] = _('Activated')
				result.append(listEntry)
			request.status = SUCCESS

		self.finished(request.id, result, message)
