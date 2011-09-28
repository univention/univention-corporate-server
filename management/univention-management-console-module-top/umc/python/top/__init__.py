#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: process overview
#
# Copyright 2011 Univention GmbH
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

import psutil
from fnmatch import fnmatch

import univention.info_tools as uit
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

_ = umc.Translation('univention-management-console-module-top').translate

class Instance(umcm.Base):
	def __init__(self):
		umcm.Base.__init__(self)

	def query(self, request):
		category = request.options.get('category', 'all')
		filter = request.options.get('filter', '*')
		processes = []
		for process in psutil.process_iter():
			listEntry = {}
			listEntry['user'] = process.username
			listEntry['pid'] = str(process.pid)
			listEntry['cpu'] = '%.1f' % process.get_cpu_percent()
			(vsize, rssize, ) = process.get_memory_info()
			listEntry['vsize'] = vsize / 1048576.0
			listEntry['rssize'] = rssize / 1048576.0
			listEntry['mem'] = '%.1f' % process.get_memory_percent()
			listEntry['command'] = ' '.join(process.cmdline)
			if listEntry['command'] == '':
				listEntry['command'] = process.name
			if category == 'all':
				for value in listEntry.itervalues():
					if fnmatch(str(value), filter):
						processes.append(listEntry)
						break
			else:
				if fnmatch(listEntry[category], filter):
					processes.append(listEntry)
		request.status = SUCCESS
		self.finished(request.id, processes)

	def kill(self, request):
		failed = []
		message = ''
		signal = request.options.get('signal', 'SIGTERM')
		pidList = request.options.get('pid', [])
		for pid in pidList:
			try:
				process = psutil.Process(int(pid))
				if signal == 'SIGTERM':
					process.kill(15)
				elif signal == 'SIGKILL':
					process.kill(9)
			except psutil.NoSuchProcess, error:
				failed.append(pid)
				MODULE.error(str(error))
		if not failed:
			request.status = SUCCESS
			success = True
		else:
			request.status = MODULE_ERR
			failed = ', '.join(failed)
			message = _('No process found with PID %s') % (failed)
			success = False
		self.finished(request.id, success, message=message)
