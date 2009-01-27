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

import univention.management.console.locales as locales

_ = locales.Translation('univention.management.console.handlers.update').translate

import univention.debug as ud

import re
import os
import httplib, base64, string
import univention.config_registry

HTTP_PROXY_DEFAULT_PORT = 3128

class UCS_Version( object ):
	# regular expression matching a UCS version X.Y-Z
	_regexp = re.compile( '(?P<major>[0-9]*)\.(?P<minor>[0-9]*)-(?P<patch>[0-9]*)' )

	def __init__( self, version ):
		'''version must a string matching the pattern X.Y-Z or a triple
		with major, minor and patchlevel'''

		if isinstance( version, ( tuple, list ) ) and len( version ) == 3:
			self.major = int( version[ 0 ] )
			self.minor = int( version[ 1 ] )
			self.patchlevel = int( version[ 2 ] )
		elif isinstance( version, str ):
			self.set( version )

	def __cmp__( self, right ):
		'''Compare to UCS versions. The method returns 0 if the versions
		are equal, -1 if the left is less than the right and 1 of the
		left is greater than the right'''
		# major version differ
		if self.major < right.major:
			return -1
		if self.major > right.major:
			return 1
		# major is equal, check minor
		if self.minor < right.minor:
			return -1
		if self.minor > right.minor:
			return 1
		# minor is equal, check patchlevel
		if self.patchlevel < right.patchlevel:
			return -1
		if self.patchlevel > right.patchlevel:
			return 1

		return 0

	def set( self, version ):
		match = UCS_Version._regexp.match( version )
		if not match:
			raise AttributeError( 'string does not match UCS version pattern' )

		v = match.groupdict()
		self.major = int( v[ 'major' ] )
		self.minor = int( v[ 'minor' ] )
		self.patchlevel = int( v[ 'patch' ] )

	def __str__( self ):
		return '%d.%d-%d' % ( self.major, self.minor, self.patchlevel )

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

		self.architectures = [ os.popen('dpkg-architecture -qDEB_BUILD_ARCH 2>/dev/null').readline()[:-1] ]

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
		# path MUST NOT contain the schema and hostname
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

	def get_next_version( self, version ):
		if self.net_path_exists( '%d.%d/maintained/%d.%d-%d/' % ( version.major, version.minor, version.major, version.minor, version.patchlevel + 1 ) ): #check for x.y-(z+1)
			return '%d.%d-%d' % ( version.major, version.minor, version.patchlevel + 1 )
		elif self.net_path_exists( '%d.%d/maintained/%d.%d-0/' % ( version.major, version.minor + 1, version.major, version.minor + 1 ) ): #check for x.y-(z+1)
			return '%d.%d-0' % ( version.major, version.minor + 1 )
		elif self.net_path_exists('%d.0/maintained/%d.0-0/' % ( version.major + 1, version.major + 1 ) ): #check for x.y-(z+1)
			return '%d.0-0' % version.major + 1

		return None

	def release_update_available(self):
		return self.get_next_version( UCS_Version( self.version_major, self.version_minor, self.patchlevel ) )

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
				for arch in ['all', 'extern'] + self.architectures:
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

	def print_version_repositories( self, clean = False, dists = False, start = None, end = None ):
		repos = ''
		if not start:
			start = UCS_Version( ( self.version_major, 0, 0 ) )

		if not end:
			end = UCS_Version( ( self.version_major, self.version_minor, self.patchlevel ) )

		if clean:
			clean = self.configRegistry.get( 'online/repository/clean', False )

		while start <= end:
			# for example: http://apt.univention.de/2.0/
			path='/%s.%s/' % (start.major, start.minor)
			if not self.net_path_exists( path ):
				start.minor += 1
				continue
			if dists:
				path_base = '/%s.%s/maintained/%s.%s-0' % ( start.major, start.minor, start.major, start.minor )
				if self.net_path_exists( '%s/dists/' %  path_base ):
					for arch in self.architectures:
						path = '%s/dists/univention/main/binary-%s/' % ( path_base, arch )
						if self.net_path_exists( path ):
							if self.repository_prefix:
								repos += 'deb http://%s%s/%s dists/univention/main/binary-%s/\n' % ( self.repository_server, self.repository_prefix, path_base, arch )
							else:
								repos += 'deb http://%s%s dists/univention/main/binary-%s/\n' % ( self.repository_server, path_base, arch )
			for part in self.parts:
				# for example: http://apt.univention.de/2.0/maintained/
				path='/%s.%s/%s/' % (start.major, start.minor, part)
				if not self.net_path_exists(path):
					continue
				patch_inc = UCS_Version( ( start.major, start.minor, 0 ) )
				# as long as we do just increase the patch level ...
				while patch_inc.major == start.major and patch_inc.minor == start.minor:
					path='/%s.%s/%s/%s.%s-%s/' % ( patch_inc.major, patch_inc.minor, part, patch_inc.major, patch_inc.minor, patch_inc.patchlevel )
					if not self.net_path_exists(path):
						break

					# the helper variable printed is to be used to print a blank line at the end of a block
					printed = False
					for arch in ['all', 'extern'] + self.architectures:
						# for example: http://apt.univention.de/2.0/maintained/2.0-1
						path='/%s.%s/%s/%s.%s-%s/%s/' % ( patch_inc.major, patch_inc.minor, part, patch_inc.major, patch_inc.minor, patch_inc.patchlevel, arch )
						if not self.net_path_exists(path):
							continue
						printed = True
						if self.repository_prefix:
							path = 'http://%s/%s/%s.%s/%s/' % ( self.repository_server, self.repository_prefix, patch_inc.major, patch_inc.minor, part )
						else:
							path = 'http://%s/%s.%s/%s/' % ( self.repository_server, patch_inc.major, patch_inc.minor, part )
						repos += 'deb %s %s.%s-%s/%s/\n' % ( path, patch_inc.major, patch_inc.minor , patch_inc.patchlevel, arch)

					if clean:
						if self.repository_prefix:
							path = 'http://%s/%s/%s.%s/%s/' % ( self.repository_server, self.repository_prefix, patch_inc.major, patch_inc.minor, part )
						else:
							path = 'http://%s/%s.%s/%s/' % ( self.repository_server, patch_inc.major, patch_inc.minor, part )
						repos += 'clean %s/%s.%s-%s/\n' % ( path, patch_inc.major, patch_inc.minor , patch_inc.patchlevel )

					if printed:
						repos += '\n'
						printed = False
					next_version = self.get_next_version( patch_inc )
					if next_version:
						patch_inc.set( next_version )
						if patch_inc > end:
							break
					else:
						break

			start = patch_inc

		return repos

	def print_security_repositories( self, clean = False, start = None, end = None ):
		repos = ''
		if not start:
			start = UCS_Version( ( self.version_major, self.version_minor, 0 ) )

		if not end:
			end = UCS_Version( ( self.version_major, self.version_minor, 0 ) )

		if clean:
			clean = self.configRegistry.get( 'online/repository/clean', False )

		while start <=end:
			# check for the security version for the current version
			for part in self.parts:
				# for example: http://apt.univention.de/2.0/maintained/
				path='/%d.%d/%s/' % ( start.major, start.minor, part)
				if not self.net_path_exists(path):
					continue
				# I think we won't release more than 100 security releases for one UCS release ...
				for p in range(1, 100):
					if start.major == int( self.version_major ) and start.minor == int( self.version_minor )  and p > int( self.security_patchlevel ):
						break

					path='/%d.%d/%s/sec%s/' % ( start.major, start.minor, part, p )
					if not self.net_path_exists(path):
						break

					printed =  False
					for arch in ['all', 'extern'] + self.architectures:
						# for example: http://apt.univention.de/2.0/maintained/sec1
						path='/%s/%s/sec%s/%s/' % (self.ucs_version, part, p, arch )
						if not self.net_path_exists(path):
							continue
						printed = True
						repos += 'deb http://%s/%d.%d/%s/ sec%s/%s/\n' % ( self.repository_server, start.major, start.minor, part, p, arch)
					if clean:
						repos += 'clean http://%s/%d.%d/%s/sec%s/%s/\n' % ( self.repository_server, start.major, start.minor, part, p )
					if printed:
						repos += '\n'
						printed = False
			start.minor += 1
			# is there a minor version update
			path='/%d.%d/%s/' % ( start.major, start.minor, 'maintained' )
			if self.net_path_exists(path):
				continue
			start.major += 1
			start.minor = 0
			# is there a next major version update
			path='/%d.%d/%s/' % ( start.major, start.minor, 'maintained' )
			if not self.net_path_exists(path):
				break

		return repos

	def print_component_repositories( self, clean = False ):
		repos = ''
		version_part_left = int( self.version_major )
		version_part_right = int( self.version_minor )
		if clean:
			clean = self.configRegistry.get( 'online/repository/clean', False )

		components = []
		for key in self.configRegistry.keys():
			if key.startswith('repository/online/component/'):
				component_part = key.split('repository/online/component/')[1]
				if component_part.find('/') == -1 and self.configRegistry[key].lower() in [ 'true', 'yes', 'enabled', '1']:
					components.append(component_part)

		for component in components:
			repository_server = self.configRegistry.get('repository/online/component/%s/server' % component, self.repository_server)
			repository_port = self.configRegistry.get('repository/online/component/%s/port' % component, self.repository_port)
			prefix_var = 'repository/online/component/%s/prefix' % component
			if self.configRegistry.has_key( prefix_var ):
				repository_prefix = self.configRegistry.get( 'repository/online/component/%s/prefix' % component )
			else:
				repository_prefix = self.configRegistry.get( 'repository/online/component/%s/prefix' % component, self.repository_prefix )
			versions = self.configRegistry.get('repository/online/component/%s/version' % component, self.ucs_version).split(',')
			parts = self.configRegistry.get('repository/online/component/%s/parts' % component, 'maintained').split(',')
			username = self.configRegistry.get('repository/online/component/%s/username' % component, None)
			password = self.configRegistry.get('repository/online/component/%s/password' % component, None)
			if clean:
				clean = self.configRegistry.get( 'repository/online/component/%s/clean' % component, False )

			for version in versions:
				if version == 'current':
					version = self.ucs_version
				for part in parts:
					auth_string = ''
					if username and password:
						auth_string = '%s:%s@' % (username, password)
					#2.0/maintained/component/
					path = '/%s/%s/component/%s/' % ( version, part, component )
					if not self.net_path_exists(path, server=repository_server, port=repository_port, prefix=repository_prefix, username=username, password=password):
						continue
					printed = False

					# support a diffrent repository
					path = '/%s/%s/component/%s/Packages.gz' % ( version, part, component )
					if self.net_path_exists(path, server=repository_server, port=repository_port, prefix=repository_prefix, username=username, password=password):
						if repository_prefix:
							path = 'http://%s%s/%s/%s/%s/component/%s/' % ( auth_string, repository_server, repository_prefix, version, part, component)
						else:
							path = 'http://%s%s/%s/%s/component/%s/' % ( auth_string, repository_server, version, part, component)
						repos += 'deb %s ./ \n' % path
						if clean:
							repos += 'clean %s\n' % path
						printed = True
					else:
						for arch in ['all', 'extern'] + self.architectures:
							path = '/%s/%s/component/%s/%s/' % ( version, part, component, arch )
							if not self.net_path_exists(path, server=repository_server, port=repository_port, prefix=repository_prefix, username=username, password=password):
								continue
							printed = True
							if repository_prefix:
								path = 'http://%s%s/%s/%s/%s/' % ( auth_string, repository_server, repository_prefix, version, part )
							else:
								path = 'http://%s%s/%s/%s/' % ( auth_string, repository_server, version, part )
							repos += 'deb %scomponent %s/%s/\n' % ( path, component, arch )
					if clean:
						if repository_prefix:
							path = 'http://%s%s/%s/%s/%s/' % ( auth_string, repository_server, repository_prefix, version, part )
							repos += 'clean %s/component/%s/\n' % ( path, component )
						else:
							path = 'http://%s%s/%s/%s/' % ( auth_string, repository_server, version, part )
							repos += 'clean %s/component/%s/\n' % ( path, component )
					if printed:
						repos += '\n'
						printed = False

		return repos
