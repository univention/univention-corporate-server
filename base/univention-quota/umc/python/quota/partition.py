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

# external
import notifier

# univention
import univention.management.console as umc
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

# internal
import tools
import fstab
import mtab

_ = umc.Translation('univention-management-console-modules-quota').translate

class Commands(object):
	def quota_partition_show(self, request):
		fs = fstab.File()
		mt = mtab.File()
		part = fs.find(spec = request.options['partition'])
		mounted = mt.get(part.spec)

		if mounted and 'usrquota' in mounted.options:
			cb = notifier.Callback(self._quota_partition_show, request.id(),
			                       request.options['partition'])
			tools.repquota(request.options['partition'], cb)
		else:
			self.finished(request.id(), (part, []))

	def _quota_partition_show(self, pid, status, result, id, partition):
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

		self.finished(id, (part, quotas))

	def quota_partition_activate(self, request):
		cb = notifier.Callback(self._quota_partition_activate, request)
		tools.activate_quota(request.options['partitions'], True, cb)

	def _quota_partition_activate(self, thread, result, request):
		messages = []
		failed = False
		for dev, info in result.items():
			success, message = info
			if not success:
				messages.append(_('Activating quota for device %(device)s failed: %(message)s') % \
				                 {'device' : dev, 'message' : message})
				failed = True
			else:
				messages.append(_('Quota support successfully activated for device %s') % dev)
		report = '\n'.join(messages)
		request.status = SUCCESS # TODO
		self.finished(request.id, report, success = not failed)

	def quota_partition_deactivate(self, request):
		cb = notifier.Callback(self._quota_partition_deactivate, request)
		tools.activate_quota(request.options['partitions'], False, cb)

	def _quota_partition_deactivate(self, thread, result, request):
		messages = []
		failed = False
		for dev, info in result.items():
			success, message = info
			if not success:
				messages.append(_('Deactivating quota for device %(device)s failed: %(message)s') % \
				                 {'device' : dev, 'message' : message})
				failed = True
			else:
				messages.append(_('Quota support successfully deactivated for device %s') % dev)
		report = '\n'.join(messages)
		request.status = SUCCESS # TODO
		self.finished(request.id, report, success = not failed)
