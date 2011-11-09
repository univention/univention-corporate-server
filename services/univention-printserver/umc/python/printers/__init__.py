#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: updater
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

import pprint
import subprocess
import univention.management.console as umc
import univention.management.console.modules as umcm
import univention.config_registry

from fnmatch import *
import re
import string
import subprocess

from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

_ = umc.Translation('univention-management-console-module-printers').translate

class Instance(umcm.Base):
	
	def init(self):
		
		self.ucr = univention.config_registry.ConfigRegistry()
		self.ucr.load()
		
		self._hostname = self.ucr.get('hostname')
		

	def list_printers(self,request):
		""" Lists the printers for the overview grid. """
		
		# ----------- DEBUG -----------------
		MODULE.info("printers/query invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------
		
		key = request.options.get('key','printer')
		pattern = request.options.get('pattern','*')
		
		quota = self._quota_enabled()		# we need it later
		
		result = []
		plist = self._list_printers()
		for element in plist:
			try:
				printer = element['printer']
				data = self._printer_details(printer)
				for field in data:
					element[field] = data[field]
				# filter according to query
				if fnmatch(element[key],pattern):
					if printer in quota:
						element['quota'] = quota[printer]
					else:
						element['quota'] = False
					result.append(element)
			except:
				pass
				
		# ---------- DEBUG --------------
		MODULE.info("printers/query returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = ''
		if len(result) > 5:
			tmp = result[0:5]
			MODULE.info("   >> %d entries, first 5 are:" % len(result))
			st = pp.pformat(tmp).split("\n")
		else:
			st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id,result)

	def get(self,request):
		""" gets detail data for one printer. """
		
		# ----------- DEBUG -----------------
		MODULE.info("printers/get invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------

		printer = request.options.get('printer','')
		result = self._printer_details(printer)
		result['printer'] = printer
		result['status'] = self._printer_status(printer)
		result['quota'] = self._quota_enabled(printer)
		
		# ---------- DEBUG --------------
		MODULE.info("printers/get returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id,result)

	def list_jobs(self,request):
		""" returns list of jobs for one printer. """
		
		# ----------- DEBUG -----------------
		MODULE.info("printers/jobs/query invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------
		
		result = self._job_list(request.options.get('printer',''))
		
		# ---------- DEBUG --------------
		MODULE.info("printers/jobs/query returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = ''
		if len(result) > 5:
			tmp = result[0:5]
			MODULE.info("   >> %d entries, first 5 are:" % len(result))
			st = pp.pformat(tmp).split("\n")
		else:
			st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id,result)
		
	def list_quota(self,request):
		""" lists all quota entries related to this printer. """
		
		# fill a dummy result table.
		printer = request.options.get('printer','')
		result = []
		
		self.finished(request.id,result)
		
	def enable(self,request):
		""" can enable or disable a printer, depending on args.
			returns empty string on success, else error message. 
		"""
		
		# ----------- DEBUG -----------------
		MODULE.info("printers/enable invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------
		
		printer = request.options.get('printer','')
		on = request.options.get('on',False)
		
		result = self._enable_printer(printer,on)
		
		# ---------- DEBUG --------------
		MODULE.info("printers/enable returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id, result)
		
	def cancel(self,request):
		""" cancels one or more print jobs. Job IDs are passed
			as an array that can be directly passed on to the
			_shell_command() method
		"""

		# ----------- DEBUG -----------------
		MODULE.info("printers/jobs/cancel invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------
		
		jobs = request.options['jobs']
		printer = request.options.get('printer','')
		result = self._cancel_jobs(printer,jobs)
		
		# ---------- DEBUG --------------
		MODULE.info("printers/jobs/cancel returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id, result)
		
		
		
	# ----------------------- Internal functions -------------------------

	def _job_list(self,printer):
		""" lists jobs for a given printer, directly suitable for the grid """
		
		# *** NOTE *** we don't set language to 'neutral' since it is useful
		#				to get localized date/time strings.
		
		result = []
		(stdout,stderr,status) = self._shell_command(['/usr/bin/lpstat','-o',printer])
		expr = re.compile('\s*(\S+)\s+(\S+)\s+(\d+)\s*(.*?)$')
		if status == 0:
			for line in stdout.split("\n"):
				mobj = expr.match(line)
				if mobj:
					entry = {
						'job':		mobj.group(1),
						'owner':	mobj.group(2),
						'size':		mobj.group(3),
						'date':		mobj.group(4)
					}
					result.append(entry)
		return result
	
	def _list_printers(self):
		""" returns a list of printers, along with their 'enabled' status. """
		
		result = []
		expr = re.compile('printer\s+(\S+)\s.*?(\S+abled)')
		(stdout,stderr,status) = self._shell_command(['/usr/bin/lpstat','-p'],{'LANG':'C'})
		if status == 0:
			for line in stdout.split("\n"):
				mobj = expr.match(line)
				if mobj:
					entry = { 'printer' : mobj.group(1), 'status': mobj.group(2) }
					result.append(entry)
		return result
	
	def _printer_status(self,printer):
		""" returns the 'enabled' status of a printer """
		
		(stdout,stderr,status) = self._shell_command(['/usr/bin/lpstat','-p',printer],{'LANG':'C'})
		if status == 0:
			if ' enabled ' in stdout:
				return 'enabled'
			if ' disabled ' in stdout:
				return 'disabled'
		return 'unknown'
	
	def _printer_details(self,printer):
		""" returns as much as possible details about a printer. """
		
		result = {}
		expr = re.compile('\s+([^\s\:]+)\:\s*(.*?)$')
		(stdout,stderr,status) = self._shell_command(['/usr/bin/lpstat','-l','-p',printer],{'LANG':'C'})
		if status == 0:
			for line in stdout.split("\n"):
				mobj = expr.match(line)
				if mobj:
					result[mobj.group(1).lower()] = mobj.group(2)
		result['server'] = self._hostname
		return result
	
	def _enable_printer(self,printer,on):
		""" internal function that enables/disables a printer.
			returns empty string or error message.
		"""
		
		cmd = 'univention-cups-enable' if on else 'univention-cups-disable'
		(stdout,stderr,status) = self._shell_command([cmd,printer])
		
		if status:
			return stderr
		
		# Q: What do these tools return if the cups command being called returns with error?
		# A: They return zero, the exit code meant for success.
		#
		# Q: Which is the channel where these tools print the ERROR message?
		# A: On STDOUT, as the name suggests.
		#
		# Q: What do these tools print on success?
		# A: Two newlines, instead of nothing.
		if re.search('\S',stdout):
			return stdout
		
		return ''
	
	def _quota_enabled(self,printer=None):
		""" returns a dictionary with printer names and their 'quota active' status.
			if printer is specified, returns only quota status for this printer.
		"""
		
		result = {}
		expr = re.compile('device for (\S+)\:\s*(\S+)$')
		(stdout,stderr,status) = self._shell_command(['/usr/bin/lpstat','-v'],{'LANG':'C'})
		if status == 0:
			for line in stdout.split("\n"):
				match = expr.match(line)
				if match:
					quota = False
					if match.group(2).startswith('cupspykota'):
						quota = True
					result[match.group(1)] = quota
		# No printer specified: return the whole list.
		if printer == None:
			return result
		
		# Printer specified: return its quota value or False if not found.
		if printer in result:
			return result[printer]
		return False
	
	def _cancel_jobs(self,printer,jobs):
		""" internal function that cancels a list of jobs.
			returns empty string or error message.
		"""
		
		args = ['/usr/bin/cancel','-U','%s$' % self._hostname]
		for job in jobs:
			args.append(job)
		args.append(printer)
		(stdout,stderr,status) = self._shell_command(args)
		
		if status:
			return stderr
		return ''
		
	def _shell_command(self,args,env=None):
		
		proc = subprocess.Popen(args=args, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
		outputs = proc.communicate()
		
		return (outputs[0],outputs[1],proc.returncode)
			