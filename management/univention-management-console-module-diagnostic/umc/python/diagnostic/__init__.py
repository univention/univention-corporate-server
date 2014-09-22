#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2014 Univention GmbH
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
# /usr/share/common-licenses/AGPL-3; if not, seGe
# <http://www.gnu.org/licenses/>.

from os import listdir
import os.path
import traceback
from time import strftime, gmtime

from univention.management.console.modules import Base
from univention.management.console.modules.decorators import simple_response, sanitize
from univention.management.console.modules.sanitizers import PatternSanitizer
from univention.management.console.modules.mixins import ProgressMixin
from univention.management.console.log import MODULE

from univention.management.console.modules.diagnostic import plugins

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate


class Problem(Exception):
	def __init__(self, message, **kwargs):
		super(Problem, self).__init__(message)
		self.kwargs = kwargs

class Conflict(Problem): pass
class Warning(Problem): pass
class Critical(Problem): pass


class Instance(Base, ProgressMixin):

	PLUGIN_DIR = os.path.dirname(plugins.__file__)

	def init(self):
		self.modules = {}
		self.load()

	@simple_response
	def run(self, plugin, **kwargs):
		plugin = self.get(plugin)
		return plugin.execute(**kwargs) # TODO: thread

	@sanitize(pattern=PatternSanitizer(default='.*'))
	@simple_response
	def query(self, pattern):
		return [plugin.dict for plugin in self if plugin.match(pattern)]

	@property
	def plugins(self):
		for plugin in listdir(self.PLUGIN_DIR):
			if plugin.endswith('.py') and plugin != '__init__.py':
				yield plugin[:-3]

	def load(self):
		for plugin in self.plugins:
			try:
				self.modules[plugin] = Plugin(plugin)
			except ImportError as exc:
				MODULE.error('Could not load plugin %r: %r' % (plugin, exc))
				raise

	def get(self, plugin):
		return self.modules[plugin]

	def __iter__(self):
		return iter(self.modules.values())


class Plugin(object):

	@property
	def title(self):
		u"""A title for the problem"""
		return getattr(self.module, 'title', '')

	@property
	def description(self):
		u"""A description of the problem and how to solve it"""
		return getattr(self.module, 'description', '')

	@property
	def buttons(self):
		u"""Buttons which are displayed e.g. to automatically solve the problem"""
		return getattr(self.module, 'buttons', [])

	@property
	def popups(self):
		u"""Buttons with pop ups"""
		return getattr(self.module, 'popups', [])

	@property
	def umc_modules(self):
		u"""References to UMC modules which can help solving the problem.
			(module, flavor, properties)
		"""
		return getattr(self.module, 'umc_modules', [])

	@property
	def links(self):
		u"""Links to e.g. related SDB articles
			(url, link_name)
		"""
		return getattr(self.module, 'links', [])

	def __init__(self, plugin):
		self.plugin = plugin
		self.load()

	def load(self):
		self.module = __import__(
			'univention.management.console.modules.diagnostic.plugins.%s' % (self.plugin,),
			fromlist=['univention.management.console.modules.diagnostic'],
			level=0
		)

	def execute(self, *args, **kwargs):
		success = True
		errors = {}
		try:
			try:
				result = self.module.run(*args, **kwargs)
				if isinstance(result, dict):
					errors.update(result)
			except Conflict:
				raise
			except:
				raise Conflict(traceback.format_exc())
		except Conflict as exc:
			success = False
			errors.update(exc.kwargs)

		result = dict(
			success=success
		)
		result.update(self.dict)
		result.update(errors)
		return result

	def match(self, pattern):
		return pattern.match(self.title) or pattern.match(self.description)

	def __str__(self):
		return '%s' % (self.plugin,)

	@property
	def dict(self):
		return dict(
			id=str(self),
			plugin=str(self),
			title=self.title,
			description=self.description,
			umc_modules=self.umc_modules,
			links=self.links,
			buttons=self.buttons,
			popups=self.popups,
		)


#class PluginLog(object):
#
#	@property
#	def last_result(self):
#		return self.load()
#
#	@property
#	def status(self):
#		return self.load(header_only=True)
#
#	def __init__(self, plugin):
#		self.path = '/var/log/univention/management-console-module-diagnostic-%s.log' % (plugin,)
#
#	def load(self, header_only=False):
#		if not os.path.exists(self.path):
#			return {}
#
#		s = os.stat(self.path)
#		timestamp = strftime('%Y-%m-%d %H:%M:%S', gmtime(s.st_mtime))
#
#		with open(self.path) as fd:
#			line = lambda x: fd.readline().rpartition(x)[2].strip()
#			result = int(line('result: '))
#			summary = line('summary: ')
#			output = None
#			if not header_only:
#				output = ''.join(fd.readlines())
#
#		return dict(
#			timestamp=timestamp,
#			result=result,
#			success=result==0,
#			output=output,
#			summary=summary,
#		)
#
#	def update(self, success, stdout='', stderr=''):
#		'''Rewrite log file with the given success information'''
#
#		stdout = stdout.strip()
#		stderr = stderr.strip()
#
#		with open(self.path, 'w') as log:
#			write = lambda l: log.write('%s\n' % (l,))
#
#			write('result: %s' % (int(not success)))
#
#			summary, _, stdout = stdout.partition('\n')
#			_, sep, summary = summary.rpartition('summary: ')
#			if not sep:
#				stdout = '%s%s' % (summary, stdout)
#				summary = ''
#
#			if summary:
#				write('\nsummary: %s' % (summary,))
#
#			if stdout:
#				write('\n\n===== OUTPUT =====')
#				write(stdout)
#
#			if stderr:
#				write('\n\n==== ERRORS =====')
#				write(stderr)
