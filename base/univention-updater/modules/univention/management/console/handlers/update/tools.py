#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages updates
#
# Copyright (C) 2008 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import re
import univention.management.console.locales as locales

_ = locales.Translation('univention.management.console.handlers.update').translate

import univention.debug as ud

import os
import httplib, base64, string
import univention.config_registry

HTTP_PROXY_DEFAULT_PORT = 3128

class UniventionUpdater:

	def __init__(self):
		self.connection = None
		self.proxy_prefix = None
		self.proxy_username = None
		self.proxy_password = None
		self.proxy_server = None
		self.proxy_port = None

		self.ucr_reinit()


	# TODO set default value of the variable port to "self.repository_port"
	def open_connection(self, server=None, port=None):
		if self.proxy and self.proxy != '':
			if server:
				self.proxy_prefix = server
			else:
				self.proxy_prefix = self.repository_server

			if port in (None, ''):
				port = int (self.repository_port)
			else:
				port = int (port)

			location = self.proxy
			if location.find ('@') != -1:
				user_pwd, location = location.split ('@')
				self.proxy_username, self.proxy_password = user_pwd.split(':')

			if location.find (':') != -1:
				location, pport = location.split (':')
				self.proxy_port = int (pport)
			else:
				self.proxy_port = HTTP_PROXY_DEFAULT_PORT
			self.proxy_server   = location

			self.connection = httplib.HTTPConnection('%s:%s' % (self.proxy_server, self.proxy_port))
			proxy_headers = {'Host': self.proxy_server}

			if self.proxy_username and self.proxy_password:
				#setup basic authentication
				user_pass = base64.encodestring('%s:%s' % (self.proxy_username, self.proxy_password))
				proxy_headers['Proxy-Authorization'] = string.strip ('Basic %s' % user_pass)
			return proxy_headers
		else:
			if server:
				self.connection = httplib.HTTPConnection(server)
			else:
				self.connection = httplib.HTTPConnection(self.repository_server)

	def close_connection(self):
		self.connection.close()
		

	def ucr_reinit(self):
		self.configRegistry=univention.config_registry.ConfigRegistry()
		self.configRegistry.load()

		self.architecture=os.popen('dpkg-architecture -qDEB_BUILD_ARCH 2>/dev/null').readline()[:-1]

		self.online_repository=self.configRegistry.get('repository/online', 'true')

		self.repository_server = self.configRegistry.get('repository/online/server', 'apt.univention.de')
		self.repository_port = self.configRegistry.get('repository/online/port', '80')
		self.repository_prefix = self.configRegistry.get('repository/online/prefix', '')

		if self.configRegistry.has_key('proxy/http') and self.configRegistry['proxy/http']:
			self.proxy = self.configRegistry['proxy/http'].lower().replace('http://','')
		elif os.environ.has_key('http_proxy') and os.environ['http_proxy']:
			self.proxy = os.environ['http_proxy'].lower().replace('http://','')
		else:
			self.proxy = None
		self.proxy_prefix = ''

		# check for maintained and unmaintained
		self.parts = []

		maintained = self.configRegistry.get('repository/online/maintained', 'True')
		if maintained.lower() in ['true', 'yes', '1']:
			self.parts.append('maintained')

		unmaintained = self.configRegistry.get('repository/online/unmaintained', 'False')
		if unmaintained.lower() in ['true', 'yes', '1']:
			self.parts.append('unmaintained')

		#UCS version
		self.ucs_version=self.configRegistry['version/version']
		self.patchlevel=self.configRegistry['version/patchlevel']
		self.security_patchlevel=self.configRegistry['version/security-patchlevel']
		self.version_major = self.ucs_version.split('.')[0]
		self.version_minor = self.ucs_version.split('.')[-1]

	def net_path_exists (self, path, server='', port='', prefix='', username='', password=''):
		proxy_headers = self.open_connection(server=server, port=port)
		if server: #if we use a diffrent server we should also use a diffrent prefix
			if prefix:
				site = '%s/%s/%s' % (self.proxy_prefix, prefix, path)
			else:
				site = '%s/%s' % (self.proxy_prefix, path)
		else:
			site = '%s/%s/%s' % (self.proxy_prefix, self.repository_prefix, path)

		replace_slash = re.compile ('[/]{2,}')
		site = replace_slash.sub ('/', site)
		if not site.startswith ('http://') and proxy_headers:
			site = 'http://%s' % site

		if proxy_headers:
			self.connection.putrequest('GET', site, skip_host=1, skip_accept_encoding=1)
		else:
			self.connection.putrequest('GET', site)

		if username and password:
			auth = 'Basic ' + string.strip(base64.encodestring(username + ':' + password))
			self.connection.putheader('Authorization', auth)

		if proxy_headers:
			for k, v in proxy_headers.items ():
				self.connection.putheader (k, v)
		try:
			self.connection.endheaders ()
			response = self.connection.getresponse()
			response.read()

			if response.status == 200:
				self.close_connection()
				return True
		except:
			import traceback
			print traceback.format_exc ()

		self.close_connection()
		return False

	def release_update_available(self):

		nextupdate = None

		if self.net_path_exists('%s/maintained/%s-%d/' % (self.ucs_version, self.ucs_version, int(self.patchlevel)+1)): #check for x.y-(z+1)
			nextupdate = '%s-%d' % (self.ucs_version, int(self.patchlevel)+1)
		elif self.net_path_exists('%s.%d/maintained/%s.%d-0/' % (self.version_major, int(self.version_minor)+1, self.version_major, int(self.version_minor)+1)): #check for x.y-(z+1)
			nextupdate = '%s.%d-0' % (self.version_major, int(self.version_minor)+1)
		elif self.net_path_exists('%d.0/maintained/%d.0-0/' % (int(self.version_major)+1, int(self.version_major)+1)): #check for x.y-(z+1)
			nextupdate = '%d.0-0' % (int(self.version_major)+1)

		return nextupdate

	def security_update_temporary_sources_list(self):
		sources_list = []
		for part in self.parts:
			# for example: http://apt.univention.de/2.0/maintained/
			path='/%s/%s/' % (self.ucs_version, part)
			if not self.net_path_exists(path):
				continue

			next_security_version = int(self.security_patchlevel) + 1
			path='/%s/%s/sec%s/' % (self.ucs_version, part, next_security_version)
			if self.net_path_exists(path):
				for arch in ['all', self.architecture, 'extern']:
					path='/%s/%s/sec%s/%s/' % (self.ucs_version, part, next_security_version, arch)
					if self.net_path_exists(path):
						sources_list.append('deb http://%s/%s/%s/%s/ sec%s/%s/' % (self.repository_server, self.repository_prefix, self.ucs_version, part, next_security_version, arch))
		return sources_list

	def security_update_available(self):
		# check for the security version for the current version
		for part in self.parts:
			# for example: http://apt.univention.de/2.0/maintained/
			path='/%s/%s/' % (self.ucs_version, part)
			if not self.net_path_exists(path):
				continue

			next_security_version = int(self.security_patchlevel) + 1
			path='/%s/%s/sec%s/' % (self.ucs_version, part, next_security_version)
			if self.net_path_exists(path):
				return 'sec%s' % next_security_version

		return False


	def get_ucs_version(self):
		return '%s-%s' % (self.ucs_version, self.patchlevel)

	def get_components(self):
		components = []
		for key in self.configRegistry.keys():
			if key.startswith('repository/online/component/'):
				component_part = key.split('repository/online/component/')[1]
				if component_part.find('/') == -1 and self.configRegistry[key].lower() in [ 'true', 'yes', 'enabled', '1']:
					components.append(component_part)
		return components

	def get_all_components(self):
		components = []
		for key in self.configRegistry.keys():
			if key.startswith('repository/online/component/'):
				component_part = key.split('repository/online/component/')[1]
				if component_part.find('/') == -1:
					components.append(component_part)
		return components

	def get_component(self, name):
		component = {}
		for key in self.configRegistry.keys():
			component['activated'] = self.configRegistry['repository/online/component/%s' % name]
			component['name'] = name
			if key.startswith('repository/online/component/%s/' % name):
				var = key.split('repository/online/component/%s/' % name)[1]
				component[var] = self.configRegistry[key]
				pass
		return component
		#ud.debug(ud.ADMIN, ud.INFO, 'get_component: name = %s' % name)
		#component = {}
		#for key in self.configRegistry.keys():
		#	ud.debug(ud.ADMIN, ud.INFO, 'get_component: key = %s' % key)
		#	if key.startswith('repository/online/component/%s/' % name):
		#		var = key.split('repository/online/component/%s/')[1]
		#		#if var.find('/') == -1:
		#		#	component[var] = self.configRegistry[key]
		#return component


