#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: show quota information for a user
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

import notifier

import tools
import fstab

import univention.management.console as umc

_ = umc.Translation('univention-management-console-module-quota').translate

class Commands(object):
	def quota_user_show(self, request):
		if request.options.has_key('partition') and \
		   request.options.has_key('user'):
			tools.repquota(request.options['partition'],
			               notifier.Callback(self._quota_user_show, request),
			               request.options['user'])
		else:
			self._quota_user_show(0, 0, None, request)

	def _quota_user_show(self, pid, status, result, request):
		devs = fstab.File()
		lst = umcd.List()

		# check user and partition option for existance
		username = None
		if request.options.has_key('user') and request.options['user']:
			username = request.options['user']
		device = None
		if request.options.has_key('partition') and request.options['partition']:
			device = devs.find(spec = request.options['partition'])

		# quota options
		result = tools.repquota_parse(device, result)
		if not result:
			user_quota = tools.UserQuota(device, username, '0', '0', '0', None,
			                            '0', '0', '0', None)
		else:
			user_quota = result[0]

		self.finished(request.id(), user_quota)

	def quota_user_set(self, request):
		tools.setquota(request.options['partition'], request.options['user'],
		               tools.byte2block(request.options['block_soft']),
		               tools.byte2block(request.options['block_hard']),
		               request.options['file_soft'], request.options['file_hard'],
		               notifier.Callback(self._quota_user_set, request))

	def _quota_user_set(self, pid, status, result, request):
		if not status:
			text = _('Successfully set quota settings')
			self.finished(request.id(), [], report = text, success = True)
		else:
			text = _('Failed to modify quota settings for user %(user)s on partition %(partition)s') % \
			         request.options
			self.finished(request.id(), [], report = text, success = False)

	def quota_user_remove(self, request):
		if request.options['user']:
			user = request.options['user'].pop(0)
			tools.setquota(request.options['partition'], user, 0, 0, 0, 0,
			               notifier.Callback(self._quota_user_remove, request))
		else:
			self.finished(request.id(), [])

	def _quota_user_remove(self, pid, status, result, request):
		if not status:
			if request.options['user']:
				user = request.options['user'].pop(0)
				tools.setquota(request.options['partition'], user,
				               0, 0, 0, 0, notifier.Callback(self._quota_user_remove, request))
				return
			text = _('Successfully removed quota settings')
			self.finished(request.id(), [], report = text, success = True)
		else:
			text = _('Failed to remove quota settings for user %(user)s on partition %(partition)s') % \
			         request.options
			self.finished(request.id(), [], report = text, success = False)
