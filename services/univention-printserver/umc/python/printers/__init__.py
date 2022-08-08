#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: updater
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

import re
import subprocess

from univention.lib.i18n import Translation

from univention.udm import UDM
from univention.config_registry import ConfigRegistry
from univention.management.console.error import UMC_Error
from univention.management.console.base import Base
from univention.management.console.config import ucr
from univention.management.console.modules.decorators import simple_response, log, sanitize
from univention.management.console.modules.sanitizers import PatternSanitizer, ChoicesSanitizer

_ = Translation('univention-management-console-module-printers').translate


class Instance(Base):

	@sanitize(pattern=PatternSanitizer(default='.*'), key=ChoicesSanitizer(choices=['printer', 'description', 'location'], required=True))
	@simple_response
	def list_printers(self, key, pattern):
		""" Lists the printers for the overview grid. """
		result = []
		plist = self._list_printers()
		for element in plist:
			printer = element['printer']
			data = self._printer_details(printer)
			for field in data:
				element[field] = data[field]
			# filter according to query
			if pattern.match(element[key]):
				result.append(element)

		return result

	@simple_response
	@log
	def get_printer(self, printer=''):
		""" gets detail data for one printer. """

		result = self._printer_details(printer)
		result['printer'] = printer
		result['status'] = self._printer_status(printer)
		return result

	@simple_response
	def list_users(self):
		""" convenience function for the username entry. Lists
			all user names. We don't return this as an array of {id, label}
			tuples because:

			(1) id and label are always the same here
			(2) at the frontend, we must do some postprocessing, and an array
				is easier to handle.
			(3)	the ComboBox is able to handle a plain array.
		"""

		ucr = ConfigRegistry()
		ucr.load()
		identity = ucr.get('ldap/hostdn')
		with open('/etc/machine.secret') as fd:
			password = fd.readline().strip()
		server = ucr.get('ldap/server/name')
		udm = UDM.credentials(identity, password, server=server).version(2)
		users = udm.get('users/user').search()
		return [user.props.username for user in users]

	@simple_response
	def list_jobs(self, printer=''):
		""" lists jobs for a given printer, directly suitable for the grid """

		# *** NOTE *** we don't set language to 'neutral' since it is useful
		#				to get localized date/time strings.

		result = []
		(stdout, stderr, status) = self._shell_command(['/usr/bin/lpstat', '-o', printer])
		expr = re.compile(r'\s*(\S+)\s+(\S+)\s+(\d+)\s*(.*?)$')
		if status == 0:
			for line in stdout.split("\n"):
				mobj = expr.match(line)
				if mobj:
					entry = {
						'job': mobj.group(1),
						'owner': mobj.group(2),
						'size': int(mobj.group(3)),
						'date': mobj.group(4)
					}
					result.append(entry)
		return result

	def _list_printers(self):
		""" returns a list of printers, along with their 'enabled' status. """

		result = []
		expr = re.compile(r'printer\s+(\S+)\s.*?(\S+abled)')
		(stdout, stderr, status) = self._shell_command(['/usr/bin/lpstat', '-p'], {'LANG': 'C'})
		if status == 0:
			for line in stdout.split("\n"):
				mobj = expr.match(line)
				if mobj:
					entry = {'printer': mobj.group(1), 'status': mobj.group(2)}
					result.append(entry)
		return result

	def _printer_status(self, printer):
		""" returns the 'enabled' status of a printer """

		(stdout, stderr, status) = self._shell_command(['/usr/bin/lpstat', '-p', printer], {'LANG': 'C'})
		if status == 0:
			if ' enabled ' in stdout:
				return 'enabled'
			if ' disabled ' in stdout:
				return 'disabled'
		return 'unknown'

	def _printer_details(self, printer):
		""" returns as much as possible details about a printer. """

		result = {}
		expr = re.compile(r'\s+([^\s\:]+)\:\s*(.*?)$')
		(stdout, stderr, status) = self._shell_command(['/usr/bin/lpstat', '-l', '-p', printer], {'LANG': 'C'})
		if status == 0:
			for line in stdout.split("\n"):
				mobj = expr.match(line)
				if mobj:
					result[mobj.group(1).lower()] = mobj.group(2)
		result['server'] = ucr.get('hostname')
		return result

	@simple_response
	@log
	def enable_printer(self, printer='', on=False):
		""" enable or disable a printer, depending on args. """
		cmd = 'univention-cups-enable' if on else 'univention-cups-disable'
		(stdout, stderr, status) = self._shell_command([cmd, printer])

		if status:
			raise UMC_Error(_('Could not %s printer: %s') % (_('activate') if on else _('deactivate'), stderr,))

	@simple_response
	@log
	def cancel_jobs(self, jobs, printer=''):
		""" cancels one or more print jobs. Job IDs are passed
			as an array that can be directly passed on to the
			_shell_command() method
		"""

		args = ['/usr/bin/cancel', '-U', '%s$' % ucr.get('hostname')]
		for job in jobs:
			args.append(job)
		args.append(printer)
		(stdout, stderr, status) = self._shell_command(args)
		if status:
			raise UMC_Error(_('Could not cancel job: %s') % (stderr,))

	def _shell_command(self, args, env=None):
		proc = subprocess.Popen(args=args, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
		stdout, stderr = proc.communicate()
		stdout, stderr = stdout.decode('UTF-8', 'replace'), stderr.decode('UTF-8', 'replace')
		return (stdout, stderr, proc.returncode)
