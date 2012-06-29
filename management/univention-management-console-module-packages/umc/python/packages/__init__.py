#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software management
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
import re
import time
from os import stat,listdir,chmod,unlink,path
from subprocess import Popen

import apt

import univention.management.console as umc
import univention.management.console.modules as umcm
import univention.config_registry


from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

_ = umc.Translation('univention-management-console-module-packages').translate

class Instance(umcm.Base):
	def init(self):
		MODULE.warn("Initializing 'packages' module with LANG = '%s'" % self.locale)
		
		self._counter		= 0											# sane start value
		self._tempscript	= '/tmp/umc_packages_runscripts.sh'				# temp script name for invoking scripts
		self._logname		= '/tmp/umc_packages_logfile.tmp'				# holds log output

	def sections(self,request):
		""" fills the 'sections' combobox in the search form """
		# ----------- DEBUG -----------------
		MODULE.warn("packages/sections invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.warn("   << %s" % s)
		# -----------------------------------
		
		sections = []
		result = []
		cache = apt.Cache()
		for package in cache.keys():
			section = cache[package].section
			if not section in sections:
				sections.append(section)
		for section in sections:
			result.append({
				'id':		section,
				'label':	section
			})
			
		# ---------- DEBUG --------------
		MODULE.warn("packages/sections returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = ''
		if len(result) > 5:
			tmp = result[0:5]
			MODULE.warn("   >> %d entries, first 5 are:" % len(result))
			st = pp.pformat(tmp).split("\n")
		else:
			st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.warn("   >> %s" % s)
		# --------------------------------
		self.finished(request.id,result)

	def query(self,request):
		""" Query to fill the grid. Structure is fixed here.
		"""
		# ----------- DEBUG -----------------
		MODULE.warn("packages/query invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.warn("   << %s" % s)
		# -----------------------------------
		
		installed	= request.options.get('installed',False)
		section		= request.options.get('section','all')
		key			= request.options.get('key','')
		pattern		= request.options.get('pattern','')
		
		result = []
		cache = apt.Cache()
		if  key == 'package':
			_re=re.compile( '^%s$' % pattern.replace('*','.*') )
		elif key == 'description':
			_re=re.compile( '%s' % pattern.replace('*','.*').lower() )
		for pkey in cache.keys():
			if (not installed) or cache[pkey].is_installed:
				if section == 'all' or cache[pkey].section == section:
					toshow = False
					if pattern == '*':
						toshow = True
					elif key == 'package' and _re.search(pkey):
						toshow = True
					elif key == 'description' and _re.search(cache[pkey].rawDescription.lower()):
						toshow = True
					if toshow:
						result.append(self._package_to_dict(cache[pkey],False))

		# ---------- DEBUG --------------
		MODULE.warn("packages/query returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = ''
		if len(result) > 5:
			tmp = result[0:5]
			MODULE.warn("   >> %d entries, first 5 are:" % len(result))
			st = pp.pformat(tmp).split("\n")
		else:
			st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.warn("   >> %s" % s)
		# --------------------------------

		self.finished(request.id,result)
		
	def get(self,request):
		""" retrieves full properties of one package """
		# ----------- DEBUG -----------------
		MODULE.warn("packages/get invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.warn("   << %s" % s)
		# -----------------------------------
		
		pkg = request.options.get('package','')
		cache = apt.Cache()
		
		result = {}
		if pkg in cache:
			result = self._package_to_dict(cache[pkg], True)
		
		# ---------- DEBUG --------------
		MODULE.warn("packages/get returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.warn("   >> %s" % s)
		# --------------------------------
		
		self.finished(request.id,result)
		
	def invoke(self,request):
		""" executes an installer action """
		# ----------- DEBUG -----------------
		MODULE.warn("packages/invoke invoked with:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.warn("   << %s" % s)
		# -----------------------------------
		
		pkg = request.options.get('package','')
		fnc = request.options.get('function','')
		
		fncarg = {
			'install':		'install',
			'upgrade':		'install',
			'uninstall':	'remove',
		}
		
		self._counter = 20
		result = {}
		
		# tool to call, command, args, package name
		args = [
			'apt-get',
			fncarg[fnc],
			 "-o", "DPkg::Options::=--force-confold", "-y", "--force-yes",
			 pkg
		]
		
		# Can't do without asynchronous job. The module management would
		# happily kill a module, returning a 502 and leaving a crashed
		# dpkg state... 
		cmds = [
			'#!/bin/bash',
			'trap "rm -f %s" EXIT' % self._tempscript,
			'(',
			'  echo "`date`: Starting to %s %s"' % (fnc,pkg),
			'  /usr/share/univention-updater/disable-apache2-umc',  # disable UMC server components restart
			'  %s' % (' '.join(args)),
			'  ret=$?',
			'  /usr/share/univention-updater/enable-apache2-umc --no-restart',  # enable UMC server components restart
			'  echo "`date`: finished with ${ret}"',
			') >%s 2>&1' % self._logname
		]
		result = self._run_shell_script(cmds)

		
		# ---------- DEBUG --------------
		MODULE.warn("packages/invoke returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.warn("   >> %s" % s)
		# --------------------------------
		
		self.finished(request.id,result)
		
	def logview(self,request):
		""" Frontend to the _logview() function: returns
			either the timestamp of the log file or
			some log lines.
		"""
		# ----------- DEBUG -----------------
		MODULE.info("packages/logview invoked with:")
		MODULE.info("   << LANG = '%s'" % self.locale)
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(request.options).split("\n")
		for s in st:
			MODULE.info("   << %s" % s)
		# -----------------------------------
		
		result = self._logview(int(request.options.get('count',10)))
		request.status = SUCCESS
		
		# ---------- DEBUG --------------
		# TODO: We should not repeat the whole log into
		# the module log file!
		MODULE.info("packages/logview returns:")
		pp = pprint.PrettyPrinter(indent=4)
		st = pp.pformat(result).split("\n")
		for s in st:
			MODULE.info("   >> %s" % s)
		# --------------------------------

		self.finished(request.id,result)
		
	def running(self,request):
		""" returns true while a job is running, simply by checking
			that the script file exists. """
		result = path.exists(self._tempscript)
		self.finished(request.id,result)
		
	def _package_to_dict(self,package,full):
		""" Helper that extracts properties from a 'apt_pkg.Package' object
			and stores them into a dictionary. Depending on the 'full'
			switch, stores only limited (for grid display) or full
			(for detail view) set of properties.
		"""
		result = {
			'package':		package.name,
			'section':		package.section,
			'installed':	package.is_installed,
			'upgradable':	package.is_upgradable,
			'summary':		package.summary
		}
		
		# add (and translate) a combined status field
		# *** NOTE *** we translate it here: if we would use the Custom Formatter
		#				of the grid then clicking on the sort header would not work.
		if package.is_installed:
			if package.is_upgradable:
				result['status'] = _("upgradeable")
			else:
				result['status'] = _("installed")
		else:
			result['status'] = _("not installed")

		# additional fields needed for detail view
		if full:
			result['description']	= package.description
			result['priority']		= package.priority
			# Some fields differ depending on whether the package is installed or not:
			if package.is_installed:
				# If an upgrade is available the 'Packages' class returns zero in the
				# 'installedPackageSize' field... we work around this by silently returning
				# the upgrade candidate's size.
				if package.installedPackageSize:
					result['size'] = package.installedPackageSize
				else:
					MODULE.warn("Package '%s': is_installed=true but installedPackageSize=0: using packageSize instead" % package.name)
					result['size'] = package.packageSize
				result['installed_version'] = package.installedVersion
			else:
				del result['upgradable']	# not installed: don't show 'upgradable' at all
				result['size'] = package.packageSize
			
		return result
	
	def _run_shell_script(self,cmds):
		"""internal helper for running a script:
		 -	arg is a list of lines to write into a temporary shell script
		 -	create that script, flag it executable
		 -	create process, store in self._process
		 -	on any error, returns error text, else empty string"""
		if path.exists(self._tempscript):
			# this is shown at the frontend, so we have to translate it.
			return _("Another package operation is in progress")
		file = None
		try:
			MODULE.info("Creating temporary script:")
			file = open(self._tempscript,'w')
			for line in cmds:
				MODULE.info("   ++ %s" % line)
				file.write("%s\n" % line)
			file.close()
			chmod(self._tempscript,0700)
			self._process = Popen(self._tempscript)
		except Exception, ex:
			self._process = None
			if file != None:
				file.close()
			if path.exists(self._tempscript):
				unlink(self._tempscript)
			MODULE.warn("ERROR: %s" % str(ex))		# print to module log
			return str(ex)
		return ''

	def _logview(self,count):
		"""Contains all functions needed to view or 'tail' the join log.
		Argument 'count' can have different values:
		< 0 ... return Unix timestamp of log file, to avoid fetching unchanged file.
		0 ..... return the whole file, splitted into lines.
		> 0 ... return the last 'count' lines of the file. (a.k.a. tail)"""
		lines = []
		if count < 0:
			try:
				st = stat(self._logname)
				if st:
					MODULE.info("   >> log file stamp = '%s'" % st[9])
					return st[9]
				return 0
			except:
				return 0
		try:
			file = open(self._logname,'r')
			for line in file:
				l = line.rstrip()
				lines.append(l)
				if (count) and (len(lines) > count):
					lines.pop(0)
		finally:
			if file != None:
				file.close()
		return lines

