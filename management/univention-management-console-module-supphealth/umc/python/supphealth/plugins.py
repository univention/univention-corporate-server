#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console module:
#   Support health UMC module
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
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

from os.path import exists
from subprocess import Popen, PIPE
from time import localtime, strftime

from univention.lib.i18n import Translation

_ = Translation('univention-management-console-module-supphealth').translate

# internal plugin cache
PLUGIN_CACHE = {}


def getPlugin(plugin_filename):
	if not plugin_filename in PLUGIN_CACHE:
		PLUGIN_CACHE[plugin_filename] = Plugin(plugin_filename)
	return PLUGIN_CACHE[plugin_filename]


class Plugin(object):
	ROOT_DIRECTORY = '/usr/share/univention-management-console-module-supphealth/plugins'
	TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

	def __init__(self, plugin_filename):
		self.fileName = plugin_filename
		self.path = '%s/%s' % (Plugin.ROOT_DIRECTORY, self.fileName)
		self.log = PluginLog(self.fileName)
		self.header = {'title':'', 'description':''}
		self.validHeader = True

		self.load()
		
	def load(self):
		'''Parse plugin file header'''

		if not exists(self.path):
			return

		with open(self.path) as pluginFile:
			for line in pluginFile:
				if line.startswith('##'): # all files beginning with "##" are considered part of the plugin header
					try:
						key, value = line[3:].split(':')
					except ValueError:
						continue
					if key.strip() in self.header:
						self.header[key.strip()] = value.strip()
				if not line.startswith('#'): # neither part of the plugin header nor hashbang
					break
		if not self.header.get('title').strip() or not self.header.get('description').strip():
			self.validHeader = False

	def execute(self):
		'''Execute the plugin as subprocess'''

		timestamp = strftime(Plugin.TIMESTAMP_FORMAT)
		try:
			pluginProcess = Popen(['%s/%s' % (Plugin.ROOT_DIRECTORY, self.fileName)], stdout=PIPE, stderr=PIPE)
		except OSError as ex:
			self.log.update(timestamp, -1, errorMsg=str(ex))
			return
		stdout, stderr = pluginProcess.communicate()
		self.log.update(timestamp, 0 if pluginProcess.returncode == 0 else 1, stdout, stderr)

	@property
	def lastResult(self):
		return self.log.load()

	@property
	def status(self):
		return self.log.load(headerOnly=True)


class PluginLog(object):
	ROOT_DIRECTORY = '/var/cache/univention-management-console-module-supphealth/logs'
	OUTPUT_SEPERATOR = '===== OUTPUT ====='

	def __init__(self, plugin_filename):
		self.path = '%s/%s.log' % (PluginLog.ROOT_DIRECTORY, plugin_filename)

	def load(self, headerOnly=False):
		'''
		Parse log file and return its content.
		Only return header information if "headerOnly"
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

		if not headerOnly and len(logLines) >= outputStart:
			result['output'] = ''.join(logLines[outputStart:])

		return result

	def update(self, timestamp, result, output='', errorMsg=''):
		'''Rewrite log file with the given result information'''

		output = output.strip()
		errorMsg = errorMsg.strip()

		with open(self.path, 'w') as log:
			log.write('date: %s\nresult: %s\n' % (timestamp, result))
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
