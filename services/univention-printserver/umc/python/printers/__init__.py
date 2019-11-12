#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: updater
#
# Copyright 2011-2019 Univention GmbH
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
import lxml.html

from univention.lib.i18n import Translation

from univention.udm import UDM
from univention.config_registry import ConfigRegistry
from univention.management.console.base import Base
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.modules import UMC_Error
from univention.management.console.modules.decorators import simple_response, log, sanitize
from univention.management.console.modules.sanitizers import PatternSanitizer, ChoicesSanitizer

_ = Translation('univention-management-console-module-printers').translate


class Instance(Base):

	def init(self):
		self._hostname = ucr.get('hostname')

	@sanitize(pattern=PatternSanitizer(default='.*'), key=ChoicesSanitizer(choices=['printer', 'description', 'location'], required=True))
	@simple_response
	def list_printers(self, key, pattern):
		""" Lists the printers for the overview grid. """

		quota = self._quota_enabled()  # we need it later

		result = []
		plist = self._list_printers()
		for element in plist:
			printer = element['printer']
			data = self._printer_details(printer)
			for field in data:
				element[field] = data[field]
			# filter according to query
			if pattern.match(element[key]):
				if printer in quota:
					element['quota'] = quota[printer]
				else:
					element['quota'] = False
				result.append(element)

		return result

	@simple_response
	@log
	def get_printer(self, printer=''):
		""" gets detail data for one printer. """

		result = self._printer_details(printer)
		result['printer'] = printer
		result['status'] = self._printer_status(printer)
		result['quota'] = self._quota_enabled(printer)
		return result

	@simple_response
	def list_jobs(self, printer=''):
		""" returns list of jobs for one printer. """

		return self._job_list(printer)

	@simple_response
	def list_quota(self, printer=''):
		""" lists all quota entries related to this printer. """

		result = []
		status = None

		try:
			from pykota.tool import PyKotaTool
			from pykota import reporter
			from pykota.storages.pgstorage import PGError
		except ImportError:
			raise UMC_Error(_('The print quota settings are currently disabled. Please install the package univention-printquota to enable them.'))

		reportTool = PyKotaTool()
		try:
			reportTool.deferredInit()
			printers = reportTool.storage.getMatchingPrinters(printer)
			reportingtool = reporter.openReporter(reportTool, 'html', printers, '*', 0)
			status = reportingtool.generateReport()
		except PGError as exc:
			MODULE.error('Cannot connect to postgres: %s' % (exc,))
			raise UMC_Error(_('The connection to the print quota postgres database failed. Please make sure the postgres service is running and reachable.'))
		finally:
			reportTool.regainPriv()

		if status:
			tree = lxml.html.fromstring(status)
			table = tree.find_class('pykotatable')
			for i in table:
				for a in i.iterchildren(tag='tr'):
					data = list()
					for b in a.iterchildren(tag='td'):
						data.append(b.text_content().strip())
					if data and len(data) >= 11:
						user = data[0]
						# limitby = data[1]
						# overcharge = data[2]
						used = data[3]
						soft = data[4]
						hard = data[5]
						# balance = data[6]
						# grace = data[7]
						total = data[8]
						# paid = data[9]
						# warn = data[10]
						result.append(dict(
							user=user,
							used=used,
							soft=soft,
							hard=hard,
							total=total,
						))

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
		password = open('/etc/machine.secret').read().rstrip('\n')
		server = ucr.get('ldap/server/name')
		udm = UDM.credentials(identity, password, server=server).version(1)
		users = udm.get('users/user').search()
		return [user.props.username for user in users]

	@simple_response
	@log
	def enable_printer(self, printer='', on=False):
		""" can enable or disable a printer, depending on args.
			returns empty string on success, else error message.
		"""

		return self._enable_printer(printer, on)

	@simple_response
	@log
	def cancel_jobs(self, jobs, printer=''):
		""" cancels one or more print jobs. Job IDs are passed
			as an array that can be directly passed on to the
			_shell_command() method
		"""

		return self._cancel_jobs(printer, jobs)

	@simple_response
	@log
	def set_quota(self, printer='', user='', soft=0, hard=0):
		""" sets quota limits for a (printer, user) combination.
			optionally tries to create the corresponding user entry.
		"""

		if printer == '' or user == '':
			return "Required parameter missing"
		else:
			return self._set_quota(printer, user, soft, hard)

	@simple_response
	@log
	def reset_quota(self, printer='', users=None):
		""" resets quota for a (printer, user) combination."""
		users = users or []

		return self._reset_quota(printer, users)

	# ----------------------- Internal functions -------------------------

	def _job_list(self, printer):
		""" lists jobs for a given printer, directly suitable for the grid """

		# *** NOTE *** we don't set language to 'neutral' since it is useful
		#				to get localized date/time strings.

		result = []
		(stdout, stderr, status) = self._shell_command(['/usr/bin/lpstat', '-o', printer])
		expr = re.compile('\s*(\S+)\s+(\S+)\s+(\d+)\s*(.*?)$')
		if status == 0:
			for line in stdout.split("\n"):
				mobj = expr.match(line)
				if mobj:
					entry = {
						'job': mobj.group(1),
						'owner': mobj.group(2),
						'size': mobj.group(3),
						'date': mobj.group(4)
					}
					result.append(entry)
		return result

	def _list_printers(self):
		""" returns a list of printers, along with their 'enabled' status. """

		result = []
		expr = re.compile('printer\s+(\S+)\s.*?(\S+abled)')
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
		expr = re.compile('\s+([^\s\:]+)\:\s*(.*?)$')
		(stdout, stderr, status) = self._shell_command(['/usr/bin/lpstat', '-l', '-p', printer], {'LANG': 'C'})
		if status == 0:
			for line in stdout.split("\n"):
				mobj = expr.match(line)
				if mobj:
					result[mobj.group(1).lower()] = mobj.group(2)
		result['server'] = self._hostname
		return result

	def _enable_printer(self, printer, on):
		""" internal function that enables/disables a printer.
			returns empty string or error message.
		"""

		cmd = 'univention-cups-enable' if on else 'univention-cups-disable'
		(stdout, stderr, status) = self._shell_command([cmd, printer])

		if status:
			return stderr

		return ''

	def _set_quota(self, printer, user, soft, hard):
		""" sets a quota entry. Can also add a user """

		# Before we can set quota we have to ensure that the user is
		# already known to PyKota. Fortunately these tools don't complain
		# if we try to create a user that doesn't already exist.

		self._shell_command(['/usr/bin/pkusers', '--skipexisting', '--add', user], {'LANG': 'C'})

		# Caution! order of args is important!

		(stdout, stderr, status) = self._shell_command([
			'/usr/bin/edpykota',
			'--printer', printer,
			'--softlimit', str(soft),
			'--hardlimit', str(hard),
			'--add', user
		], {'LANG': 'C'})

		# not all errors are propagated in exit codes...
		# but at least they adhere to the general rule that
		# progress is printed to STDOUT and errors/warnings to STDERR
		if status or len(stderr):
			return stderr

		return ''

	def _reset_quota(self, printer, users):
		""" resets the 'used' counter on a quota entry. """

		cmd = [	'/usr/bin/edpykota', '--printer', printer, '--reset']
		# appending user names to the args array -> spaces in user names
		# don't confuse edpykota (In 2.4, this was a problem)
		for user in users:
			if user:
				cmd.append(user)
		(stdout, stderr, status) = self._shell_command(cmd, {'LANG': 'C'})

		if status or stderr:
			return stderr

		return ''

	def _quota_enabled(self, printer=None):
		""" returns a dictionary with printer names and their 'quota active' status.
			if printer is specified, returns only quota status for this printer.
		"""

		result = {}
		expr = re.compile('device for (\S+)\:\s*(\S+)$')
		(stdout, stderr, status) = self._shell_command(['/usr/bin/lpstat', '-v'], {'LANG': 'C'})
		if status == 0:
			for line in stdout.split("\n"):
				match = expr.match(line)
				if match:
					quota = False
					if match.group(2).startswith('cupspykota'):
						quota = True
					result[match.group(1)] = quota
		# No printer specified: return the whole list.
		if printer is None:
			return result

		# Printer specified: return its quota value or False if not found.
		return result.get(printer, False)

	def _cancel_jobs(self, printer, jobs):
		""" internal function that cancels a list of jobs.
			returns empty string or error message.
		"""

		args = ['/usr/bin/cancel', '-U', '%s$' % self._hostname]
		for job in jobs:
			args.append(job)
		args.append(printer)
		(stdout, stderr, status) = self._shell_command(args)

		if status:
			return stderr
		return ''

	def _shell_command(self, args, env=None):

		proc = subprocess.Popen(args=args, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
		outputs = proc.communicate()

		return (outputs[0], outputs[1], proc.returncode)
