#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: collecting system information
#
# Copyright 2011-2012 Univention GmbH
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

import os
import re
import subprocess

import univention.info_tools as uit
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

from urllib import quote, urlencode
from urlparse import urlunparse

# locale module that overrides functions in urllib2
import upload
import urllib2

import univention.config_registry as ucr

_ = umc.Translation('univention-management-console-module-sysinfo').translate

class Instance(umcm.Base):
	def __init__(self):
		umcm.Base.__init__(self)
		self.mem_regex = re.compile('([0-9]*) kB')

	def _call(self, command):
		try:
			process = subprocess.Popen(command, stdout=subprocess.PIPE,
									   stderr=subprocess.PIPE)
			(stdoutdata, stderrdata, ) = process.communicate()
			return (process.returncode, stdoutdata, stderrdata, )
		except OSError:
			return (True, None, None, )

	def get_general_info(self, request):
		DMIDECODE = '/usr/sbin/dmidecode'
		MANUFACTURER_CMD = (DMIDECODE, '-s', 'system-manufacturer', )
		MODEL_CMD = (DMIDECODE, '-s', 'system-product-name', )

		stdout_list = []
		for command in (MANUFACTURER_CMD, MODEL_CMD, ):
			(exitcode, stdout, stderr, ) = self._call(command)
			if exitcode:
				message = _('Failed to execute command')
				request.status = MODULE_ERR
				self.finished(request.id, None, message)
				return
			else:
				stdout = stdout[:-1] # remove newline character
				stdout_list.append(stdout)
		result = {}
		result['manufacturer'] = stdout_list[0]
		result['model'] = stdout_list[1]

		request.status = SUCCESS
		self.finished(request.id, result)

	def get_system_info(self, request):
		MANUFACTURER = request.options['manufacturer'].encode( 'utf-8' )
		MODEL = request.options['model'].encode( 'utf-8' )
		COMMENT = request.options['comment'].encode( 'utf-8' )
		SYSTEM_INFO_CMD = ( '/usr/bin/univention-system-info',
							'-m', MANUFACTURER,
							'-t', MODEL,
							'-c', COMMENT,
							'-s', request.options.get('ticket', ''),
							'-u', )

		(exitcode, stdout, stderr, ) = self._call(SYSTEM_INFO_CMD)
		if exitcode:
			MODULE.error('Execution of univention-system-info failed: %s'
			             % stdout)
			result = None
			request.status = MODULE_ERR
		else:
			result = {}
			for line in stdout.splitlines():
				try:
					info, value = line.split(':')
					result[info] = value
				except:
					pass
			if result['mem']:
				match = self.mem_regex.match(result['mem'])
				if match:
					try:
						converted_mem = (float(match.groups()[0]) / 1048576)
						result['mem'] = '%.2f GB' % converted_mem
						result['mem'] = request['mem'].replace('.', ',')
					except:
						pass
			if result['Temp']:
				del result['Temp'] # remove unnecessary entry
			request.status = SUCCESS

		self.finished(request.id, result)

	def get_mail_info(self, request):
		ucr_reg = ucr.ConfigRegistry()
		ucr_reg.load()
		ADDRESS_KEY = 'umc/sysinfo/mail/address'
		SUBJECT_KEY = 'umc/sysinfo/mail/subject'
		ADDRESS_VALUE = ucr_reg.get(ADDRESS_KEY, 'feedback@univention.de')
		SUBJECT_VALUE = ucr_reg.get(SUBJECT_KEY, 'Univention System Info')

		url = urlunparse(('mailto', '', ADDRESS_VALUE, '',
		                  urlencode({'subject': SUBJECT_VALUE, }), ''))
		result = {}
		result['url'] = url.replace('+', '%20')
		request.status = SUCCESS
		self.finished(request.id, result)

	def upload_archive(self, request):
		UPLOAD_KEY = 'umc/sysinfo/upload/url'
		FALLBACK_UPLOAD_URL = 'https://forge.univention.de/cgi-bin/system-info-upload.py'
		ucr_reg = ucr.ConfigRegistry()
		ucr_reg.load()
		url = ucr_reg.get(UPLOAD_KEY, FALLBACK_UPLOAD_URL)

		SYSINFO_PATH = '/var/www/univention-management-console/system-info/'
		fd = open(os.path.join(SYSINFO_PATH, request.options['archive']), 'r')
		data = {'filename': fd, }
		req = urllib2.Request(url, data, {})
		try:
			u = urllib2.urlopen(req)
			answer = u.read()
			success = True
		except:
			success = False

		if not success or answer.startswith('ERROR:'):
			request.status = MODULE_ERR
		else:
			request.status = SUCCESS

		self.finished(request.id, None)
