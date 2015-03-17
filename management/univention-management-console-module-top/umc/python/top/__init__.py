#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: process overview
#
# Copyright 2011-2014 Univention GmbH
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

import time
import psutil

import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import SUCCESS, MODULE_ERR

from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import PatternSanitizer

_ = umc.Translation('univention-management-console-module-top').translate

class Instance(umcm.Base):
	@sanitize(pattern=PatternSanitizer(default='.*'))
	def query(self, request):
		category = request.options.get('category', 'all')
		pattern = request.options.get('pattern')
		processes = []
		for process in psutil.process_iter():
			listEntry = {}
			# Temporary variables; used to calculate cpu percentage
			listEntry['timestamp'] = []
			listEntry['cpu_time'] = []
			listEntry['timestamp'].append(time.time())
			(user_time, system_time, ) = process.get_cpu_times()
			listEntry['cpu_time'].append(user_time + system_time)
			try:
				username = process.username
			except KeyError:  # fixed in psutil 2.2.0
				username = str(process.uids.real)
			listEntry['user'] = username
			listEntry['pid'] = process.pid
			listEntry['cpu'] = 0.0
			listEntry['mem'] = process.get_memory_percent()
			listEntry['command'] = ' '.join(process.cmdline)
			if listEntry['command'] == '':
				listEntry['command'] = process.name
			if category == 'all':
				for value in listEntry.itervalues():
					if pattern.match(str(value)):
						processes.append(listEntry)
						break
			else:
				if pattern.match(str(listEntry[category])):
					processes.append(listEntry)

		# Calculate correct cpu percentage
		time.sleep(1)
		for process_entry in processes:
			try:
				process = psutil.Process(process_entry['pid'])
			except psutil.NoSuchProcess:
				pass
			else:
				process_entry['timestamp'].append(time.time())
				(user_time, system_time, ) = process.get_cpu_times()
				process_entry['cpu_time'].append(user_time + system_time)

				elapsed_time = process_entry['timestamp'][1] - process_entry['timestamp'][0]
				elapsed_cpu_time = process_entry['cpu_time'][1] - process_entry['cpu_time'][0]
				cpu_percent = (elapsed_cpu_time / elapsed_time) * 100
				process_entry['cpu'] = cpu_percent
				# Cleanup request result
				del process_entry['timestamp']
				del process_entry['cpu_time']

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
					process.terminate()
				elif signal == 'SIGKILL':
					process.kill()
			except psutil.NoSuchProcess, error:
				failed.append(pid)
				MODULE.error(str(error))
		if not failed:
			request.status = SUCCESS
			success = True
		else:
			request.status = MODULE_ERR
			failed = ', '.join(map(str, failed))
			message = _('No process found with PID %s') % (failed)
			success = False
		self.finished(request.id, success, message=message)
