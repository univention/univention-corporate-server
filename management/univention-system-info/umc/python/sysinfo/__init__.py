#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: collecting system information
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2022 Univention GmbH
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

import os
import re
import subprocess

import requests
from six.moves.urllib_parse import urlencode, urlunparse

import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.log import MODULE
from univention.management.console.modules import UMC_Error
from univention.management.console.modules.decorators import simple_response, sanitize
from univention.management.console.modules.sanitizers import StringSanitizer

import univention.config_registry
ucr = univention.config_registry.ConfigRegistry()

_ = umc.Translation('univention-management-console-module-sysinfo').translate


class Instance(umcm.Base):

	def __init__(self):
		umcm.Base.__init__(self)
		self.mem_regex = re.compile('([0-9]*) kB')

	def _call(self, command):
		try:
			process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			(stdoutdata, stderrdata, ) = process.communicate()
			return (process.returncode, stdoutdata.decode('UTF-8'), stderrdata.decode('UTF-8'), )
		except OSError:
			return (True, None, None, )

	@simple_response
	def get_general_info(self):
		DMIDECODE = '/usr/sbin/dmidecode'
		MANUFACTURER_CMD = (DMIDECODE, '-s', 'system-manufacturer', )
		MODEL_CMD = (DMIDECODE, '-s', 'system-product-name', )

		stdout_list = []
		for command in (MANUFACTURER_CMD, MODEL_CMD, ):
			(exitcode, stdout, stderr, ) = self._call(command)
			if exitcode:
				MODULE.error('Command %r failed: %s %r %r' % (command, exitcode, stdout, stderr))
				raise UMC_Error(_('Failed to execute command'))
			else:
				stdout = stdout[:-1]  # remove newline character
				stdout_list.append(stdout)
		result = {}
		result['manufacturer'] = stdout_list[0]
		result['model'] = stdout_list[1]
		return result

	@sanitize(
		manufacturer=StringSanitizer(required=True),
		model=StringSanitizer(required=True),
		comment=StringSanitizer(required=True),
		ticket=StringSanitizer(required=False, default=''),
	)
	@simple_response
	def get_system_info(self, manufacturer, model, comment, ticket=''):
		SYSTEM_INFO_CMD = (
			'/usr/bin/univention-system-info',
			'-m', manufacturer,
			'-t', model,
			'-c', comment,
			'-s', ticket,
			'-u', )

		(exitcode, stdout, stderr, ) = self._call(SYSTEM_INFO_CMD)
		if exitcode:
			MODULE.error('Execution of univention-system-info failed: %s' % (stdout,))
			raise UMC_Error('Execution of univention-system-info failed')

		result = {}
		for line in stdout.splitlines():
			try:
				info, value = line.split(':', 1)
				result[info] = value
			except ValueError:
				pass
		if result.get('mem'):
			match = self.mem_regex.match(result['mem'])
			if match:
				try:
					converted_mem = (float(match.groups()[0]) / 1048576)
					result['mem'] = '%.2f GB' % converted_mem
					result['mem'] = result['mem'].replace('.', ',')
				except (IndexError, ValueError):
					pass
		result.pop('Temp', None)  # remove unnecessary entry
		return result

	@simple_response
	def get_mail_info(self):
		ucr.load()
		ADDRESS_VALUE = ucr.get('umc/sysinfo/mail/address', 'feedback@univention.de')
		SUBJECT_VALUE = ucr.get('umc/sysinfo/mail/subject', 'Univention System Info')

		url = urlunparse(('mailto', '', ADDRESS_VALUE, '', urlencode({'subject': SUBJECT_VALUE, }), ''))
		result = {}
		result['url'] = url.replace('+', '%20')
		return result

	@sanitize(archive=StringSanitizer(required=True))
	@simple_response
	def upload_archive(self, archive):
		ucr.load()
		url = ucr.get('umc/sysinfo/upload/url', 'https://forge.univention.org/cgi-bin/system-info-upload.py')

		SYSINFO_PATH = '/usr/share/univention-system-info/archives/'
		path = os.path.abspath(os.path.join(SYSINFO_PATH, archive))
		if not path.startswith(SYSINFO_PATH):
			raise UMC_Error('Archive path invalid.')

		with open(os.path.join(SYSINFO_PATH, archive), 'rb') as fd:
			try:
				response = requests.post(url, files={'filename': fd, })
				response.raise_for_status()
			except requests.exceptions.RequestException as exc:
				raise UMC_Error('Archive upload failed: %s' % (exc,))
			answer = response.text
		if answer.startswith('ERROR:'):
			raise UMC_Error(answer)

	@sanitize(traceback=StringSanitizer(), remark=StringSanitizer(), email=StringSanitizer())
	@simple_response
	def upload_traceback(self, traceback, remark, email):
		ucr.load()
		ucs_version = '%(version/version)s-%(version/patchlevel)s errata%(version/erratalevel)s' % ucr
		if ucr.get('appcenter/apps/ucsschool/version'):
			ucs_version = '%s - UCS@school %s' % (ucs_version, ucr['appcenter/apps/ucsschool/version'])
		# anonymised id of localhost
		uuid_system = ucr.get('uuid/system', '')
		url = ucr.get('umc/sysinfo/traceback/url', 'https://forge.univention.org/cgi-bin/system-info-traceback.py')
		MODULE.process('Sending %s to %s' % (traceback, url))
		request_data = {
			'traceback': traceback,
			'remark': remark,
			'email': email,
			'ucs_version': ucs_version,
			'uuid_system': uuid_system,
			'uuid_license': ucr.get('uuid/license', ''),
			'server_role': ucr.get('server/role'),
		}
		try:
			response = requests.post(url, data=request_data)
			response.raise_for_status()
		except requests.exceptions.RequestException as exc:
			raise UMC_Error('Sending traceback failed: %s' % (exc,))
