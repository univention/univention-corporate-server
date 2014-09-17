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

from univention.management.console.modules import Base
from univention.management.console.modules.decorators import simple_response, sanitize
from univention.management.console.modules.sanitizers import PatternSanitizer
from univention.management.console.log import MODULE

from univention.management.console.modules.diagnostic import plugins

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate


class Plugins(object):

	PLUGIN_DIR = os.path.dirname(plugins.__file__)

	@property
	def plugins(self):
		for plugin in listdir(self.PLUGIN_DIR):
			if plugin.endswith('.py') and plugin != '__init__.py':
				yield plugin[:-3]

	def __init__(self):
		self.modules = {}
		self.load()

	def load(self):
		for plugin in self.plugins:
			try:
				self.modules[plugin] = Plugin(plugin)
			except ImportError:
				raise
				pass

	def get(self, plugin):
		return self.modules[plugin]

	def __iter__(self):
		return iter(self.modules.values())


class Plugin(object):

	@property
	def title(self):
		return getattr(self.module, 'title', '')

	@property
	def description(self):
		return getattr(self.module, 'description', '')

	@property
	def last_result(self):
		return self.log.load()

	@property
	def status(self):
		# TODO: rename last_status?
		return self.log.load(header_only=True)

	def __init__(self, plugin):
		self.plugin = plugin
		self.load()
		self.log = PluginLog(str(self))

	def load(self):
		self.module = __import__(
			'univention.management.console.modules.diagnostic.plugins.%s' % (self.plugin,),
			fromlist=['univention.management.console.modules.diagnostic'],
			level=0
		)

	def match(self, pattern):
		# TODO: maybe description, etc.
		return pattern.match(self.title)

	def __str__(self):
		return '%s' % (self.plugin,)

	def execute(self):
		try:
			success, stdout, stderr = self.module.run()
		except:
			success = False
			stdout = ''
			stderr = traceback.format_exc()

		self.log.update(success, stdout, stderr)


class PluginLog(object):

	OUTPUT_SEPERATOR = '===== OUTPUT ====='

	def __init__(self, plugin):
		self.path = '/var/log/univention/management-console-module-diagnostic-%s.log' % (plugin,)

	def load(self, header_only=False):
		'''
		Parse log file and return its content.
		Only return header information if "header_only"
		is true.
		'''

		result = {}
		if not exists(self.path):
			return result

		logLines = open(self.path).readlines()
		outputStart = 5
		result['timestamp'] = logLines[0].split('date: ')[1].strip()
		result['result'] = logLines[1].split('result: ')[1].strip()

		if len(logLines) > 3 and 'summary:' in logLines[3]:
			result['summary'] = logLines[3].split('summary:')[1].strip()
			outputStart += 2

		if not header_only and len(logLines) >= outputStart:
			result['output'] = ''.join(logLines[outputStart:])

		return result

	def update(self, result, output='', errorMsg=''):
		'''Rewrite log file with the given result information'''

		timestamp = strftime('%Y-%m-%d %H:%M:%S')
		output = output.strip()
		errorMsg = errorMsg.strip()

		with open(self.path, 'w') as log:
			log.write('date: %s\nresult: %s\n' % (timestamp, int(result)))
			if 'summary:' in output:
				split = output.split('summary:')
				output = ''.join(split[:-1])
				log.write('\nsummary: %s\n' % split[-1].strip())
			if output or errorMsg:
				log.write('\n\n%s\n' % PluginLog.OUTPUT_SEPERATOR)
			if output:
				log.write('%s\n' % output)
			if errorMsg:
				log.write('\n\nErrors:\n=======\n%s' % errorMsg)


class Instance(Base):

	def init(self):
		self.plugins = Plugins()

	@simple_response
	def run(self, plugin):
		plugin = self.plugins.get(plugin)
		return plugin.execute()

	@sanitize(pattern=PatternSanitizer())
	@simple_response
	def query(self, pattern):
		result = []
		for plugin in self.plugins:
			if not plugin.match(pattern):
				continue

			result.append(dict(
				plugin=str(plugin),
				title=plugin.title,
				description=plugin.description,
				**plugin.status
			))
		return result

	@simple_response
	def get(self, plugin):
		plugin = self.plugins.get(plugin)
		return dict(
			plugin=str(plugin),
			title=plugin.title,
			description=plugin.description,
			**plugin.last_result
		)
