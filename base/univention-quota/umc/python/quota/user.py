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

from fnmatch import fnmatch
import notifier
import notifier.threads

import univention.management.console as umc
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

from univention.lib import fstab
import mtab
import tools

_ = umc.Translation('univention-management-console-module-quota').translate

class Commands(object):
	def getUsers(self, request):
		resultMessage = ''
		try:
			fs = fstab.File()
			mt = mtab.File()
		except IOError as error:
			MODULE.error('Could not open %s' % error.filename)
			resultMessage = _('Could not open %s' % error.filename)
			request.status = MODULE_ERR
			self.finished(request.id, resultMessage)
		else:
			partition = fs.find(spec = request.options['partitionDevice'])
			if partition:
				mounted = mt.get(partition.spec)
				if mounted and 'usrquota' in mounted.options:
					cb = notifier.Callback(self._getUsers, request.id,
										   request.options['partitionDevice'], request)
					tools.repquota(request.options['partitionDevice'], cb)
				else:
					request.status = MODULE_ERR
					resultMessage = _('This partition is currently not mounted')
					self.finished(request.id, resultMessage)
			else:
				request.status = MODULE_ERR
				resultMessage = _('No partition found')
				self.finished(request.id, resultMessage)

	def _getUsers(self, pid, status, result, id, partition,
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
		self.finished(request.id, erg)

	def setUser(self, request):
		def _thread(request):
			result = tools.setquota(request.options['partitionDevice'], request.options['user'],
						   tools.byte2block(request.options['sizeLimitSoft']),
						   tools.byte2block(request.options['sizeLimitHard']),
						   request.options['fileLimitSoft'], request.options['fileLimitHard'])
			return result
		thread = notifier.threads.Simple('Set', notifier.Callback(_thread, request),
		                                 notifier.Callback(self._setUser, request))
		thread.run()

	def _setUser(self, thread, result, request):
		if not isinstance(result, BaseException):
			request.status = SUCCESS
			self.finished(request.id, [])
		else:
			msg = str(result) + '\n' + '\n'.join(thread.trace)
			MODULE.error('An internal error occurred: %s' % msg)
			self.finished(request.id, msg)

	def removeUsers(self, request):
		def _thread(request):
			failed = []
			for userID in request.options: # TODO rename userID
				(user, partitionDevice) = userID.split('@')
				success = tools.setquota(partitionDevice, user, '0', '0', '0', '0')
				if not success:
					failed.append((user, partitionDevice))
			return failed
		thread = notifier.threads.Simple('Remove', notifier.Callback(_thread, request),
		                                 notifier.Callback(self._removeUsers, request))
		thread.run()

	def _removeUsers(self, thread, result, request):
		if not isinstance(result, BaseException):
			request.status = SUCCESS
			self.finished(request.id, result)
		else:
			msg = str(result) + '\n' + '\n'.join(thread.trace)
			MODULE.error('An internal error occurred: %s' % msg)
			self.finished(request.id, msg)
		# if not status:
		# 	if request.options['user']:
		# 		user = request.options['user'].pop(0)
		# 		tools.setquota(request.options['partitionDevice'], user,
		# 		               0, 0, 0, 0, notifier.Callback(self._removeUsers, request))
		# 		return
		# 	text = _('Successfully removed quota settings')
		# 	self.finished(request.id, [], report = text, success = True)
		# else:
		# 	text = _('Failed to remove quota settings for user %(user)s on partition %(partitionDevice)s') % \
		# 	         request.options
		# 	self.finished(request.id, [], report = text, success = False)
