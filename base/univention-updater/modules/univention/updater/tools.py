#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages updates
#
# Copyright (C) 2008-2010 Univention GmbH
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

import univention.debug as ud

import sys
import re
import os
import copy
import httplib, base64, string
import socket
import univention.config_registry

HTTP_PROXY_DEFAULT_PORT = 3128

class UCS_Version( object ):
	'''Version object consisting of major-, minor-number and patch-level'''
	FORMAT = '%(major)d.%(minor)d'
	FULLFORMAT = '%(major)d.%(minor)d-%(patchlevel)d'
	# regular expression matching a UCS version X.Y-Z
	_regexp = re.compile( '(?P<major>[0-9]*)\.(?P<minor>[0-9]*)-(?P<patch>[0-9]*)' )

	def __init__( self, version ):
		'''version must a string matching the pattern X.Y-Z or a triple
		with major, minor and patchlevel.
		>>> v = UCS_Version((2,3,1))
		>>> v = UCS_Version([2,3,1])
		>>> v = UCS_Version("2.3-1")
		>>> v2 = UCS_Version(v)
		'''
		if isinstance( version, ( tuple, list ) ) and len( version ) == 3:
			self.major, self.minor, self.patchlevel = map(int, version)
		elif isinstance( version, str ):
			self.set( version )
		elif isinstance(version, UCS_Version):
			self.major, self.minor, self.patchlevel = version.major, version.minor, version.patchlevel
		else:
			raise TypeError("not a tuple, list or string")

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
		'''Parse string and set version.'''
		match = UCS_Version._regexp.match( version )
		if not match:
			raise AttributeError( 'string does not match UCS version pattern' )
		self.major, self.minor, self.patchlevel = map(int, match.groups())

	def __getitem__(self, k):
		'''Dual natured dictionary: retrieve value from attribute.'''
		return self.__dict__[k]
	def __str__(self):
		'''Return full version string.'''
		return UCS_Version.FULLFORMAT % self

class UCSRepo(UCS_Version):
	'''Debian repository.'''
	def __init__(self, **kw):
		kw.setdefault('patchlevel_reset', 0)
		for (k, v) in kw.items():
			if isinstance(v, str) and '%(' in v:
				setattr(self, k, UCSRepo._substitution(v, self.__dict__))
			else:
				setattr(self, k, v)
	def __repr__(self):
		return repr(self.__dict__)
	def _format(self, format):
		'''Format longest path for directory/file access.'''
		while format:
			try:
				return format % self
			except KeyError, (k,):
				# strip missing part
				i = format.index('%%(%s)' % k)
				format = format[:i]
				# strip partial part
				i = format.rindex('/') + 1
				format = format[:i]
	class _substitution:
		'''Helper to print dynamically substituted variable.
		>>> h={'major':2}
		>>> h['version'] = UCSRepo._substitution('%(major)d.%(minor)d', h)
		>>> h['minor'] = 3
		>>> '%(version)s' % h
		'2.3'
		'''
		def __init__(self, format, values):
			self.format = format
			self.values = values
		def __str__(self):
			try:
				return self.format % self.values
			except KeyError, e:
				for (k, v) in self.values.items():
					if self == v:
						raise KeyError(k)
				raise e
		def __repr__(self):
			return repr(self.format)

class UCSRepoPool(UCSRepo):
	'''Debian pool repository.'''
	def __init__(self, **kw):
		kw.setdefault('version', UCS_Version.FORMAT)
		kw.setdefault('patch', UCS_Version.FULLFORMAT)
		super(UCSRepoPool,self).__init__(**kw)
	def deb(self, type="deb"):
		'''Format for /etc/apt/sources.list.

		>>> r=UCSRepoPool(prefix='http://apt.univention.de/',major=2,minor=3,patchlevel=1,part='maintained',arch='i386')
		>>> r.deb()
		'deb http://apt.univention.de/2.3/maintained/ 2.3-1/i386/'
		'''
		fmt = "%(prefix)s%(version)s/%(part)s/ %(patch)s/%(arch)s/"
		return "%s %s" % (type, super(UCSRepoPool,self)._format(fmt))
	def path(self, file='Packages.gz'):
		'''Format pool for directory/file access.

		>>> UCSRepoPool(prefix='http://apt.univention.de/',major=2,minor=3).path()
		'/2.3/'
		>>> UCSRepoPool(major=2,minor=3,part='maintained').path()
		'/2.3/maintained/'
		>>> UCSRepoPool(major=2,minor=3,patchlevel=1,part='maintained').path()
		'/2.3/maintained/2.3-1/'
		>>> UCSRepoPool(major=2,minor=3,patchlevel=1,part='maintained',arch='i386').path()
		'/2.3/maintained/2.3-1/i386/Packages.gz'
		'''
		fmt = "/%(version)s/%(part)s/%(patch)s/%(arch)s/" + file
		return super(UCSRepoPool,self)._format(fmt)
	def clean(self):
		'''Format for /etc/apt/mirror.list'''
		fmt = "%(prefix)s%(version)s/%(part)s/%(patch)s/" # %(arch)s/
		return "clean %s" % super(UCSRepoPool,self)._format(fmt)

class UCSRepoDist(UCSRepo):
	'''Debian dists repository.'''
	def __init__(self, **kw):
		kw.setdefault('version', UCS_Version.FORMAT)
		kw.setdefault('patch', UCS_Version.FULLFORMAT)
		super(UCSRepoDist,self).__init__(**kw)
	def deb(self, type="deb"):
		'''Format for /etc/apt/sources.list.

		>>> r=UCSRepoDist(prefix='http://apt.univention.de/',major=2,minor=2,patchlevel=0,part='maintained',arch='i386')
		>>> r.deb()
		'deb http://apt.univention.de/2.2/maintained/2.2-0/ dists/univention/main/binary-i386/'
		'''
		fmt = "%(prefix)s%(version)s/%(part)s/%(patch)s/ dists/univention/main/binary-%(arch)s/"
		return "%s %s" % (type, super(UCSRepoDist,self)._format(fmt))
	def path(self, file='Packages.gz'):
		'''Format dist for directory/file access.

		>>> UCSRepoDist(prefix='http://apt.univention.de/',major=2,minor=2).path()
		'/2.2/'
		>>> UCSRepoDist(major=2,minor=2,part='maintained').path()
		'/2.2/maintained/'
		>>> UCSRepoDist(major=2,minor=2,patchlevel=0,part='maintained').path()
		'/2.2/maintained/2.2-0/dists/univention/main/'
		>>> UCSRepoDist(major=2,minor=2,patchlevel=0,part='maintained',arch='i386').path()
		'/2.2/maintained/2.2-0/dists/univention/main/binary-i386/Packages.gz'
		'''
		fmt = "/%(version)s/%(part)s/%(patch)s/dists/univention/main/binary-%(arch)s/" + file
		return super(UCSRepoDist,self)._format(fmt)

class UniventionUpdater:
	'''Handle Univention package repositories.'''
	def __init__(self):
		self.connection = None
		self.proxy_prefix = None
		self.proxy_username = None
		self.proxy_password = None
		self.proxy_server = None
		self.proxy_port = None
		self.architectures = [ os.popen('dpkg-architecture -qDEB_BUILD_ARCH 2>/dev/null').readline()[:-1] ]

		self.ucr_reinit()

	def config_repository( self ):
		'''Retrieve configuration to access repository. Overridden in UniventionMirror.'''
		self.online_repository = self.configRegistry.get('repository/online', 'True')
		if self.online_repository.lower() in ('yes', 'true', 'enabled', '1'):
			self.online_repository = True
		else:
			self.online_repository = False
		self.repository_server = self.configRegistry.get('repository/online/server', 'apt.univention.de')
		self.repository_port = self.configRegistry.get('repository/online/port', '80')
		self.repository_prefix = self.configRegistry.get('repository/online/prefix', '').strip('/')
		self.sources = self.configRegistry.get('repository/online/sources', 'no' ).lower() in ('yes', 'true', 'enabled', '1')
		self.http_method = self.configRegistry.get('repository/online/httpmethod', 'GET').upper()

	def open_connection(self, server=None, port=None):
		'''Open http-connection to server:port'''

		if not self.nameserver_available:
			raise socket.gaierror, (socket.EAI_NONAME, 'The repository server %s could not be resolved.' % server)
		if not server:
			server = self.repository_server
		if port in (None, ''):
			port = self.repository_port

		if self.proxy and self.proxy != '':
			self.proxy_prefix = "%s:%s" % (server, port)

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

			#print "# %s:%d %s" % (self.proxy_server, self.proxy_port, self.proxy_prefix)
			self.connection = httplib.HTTPConnection(self.proxy_server, self.proxy_port)
			proxy_headers = {}

			if self.proxy_username and self.proxy_password:
				#setup basic authentication
				user_pass = base64.encodestring('%s:%s' % (self.proxy_username, self.proxy_password))
				proxy_headers['Proxy-Authorization'] = string.strip ('Basic %s' % user_pass)
			return proxy_headers
		else:
			#print "# %s:%s" % (server, port)
			self.connection = httplib.HTTPConnection(server, int(port))

	def close_connection(self):
		'''Close http-connection'''
		self.connection.close()

	def ucr_reinit(self):
		'''Re-initialize settings'''
		self.configRegistry=univention.config_registry.ConfigRegistry()
		self.configRegistry.load()

		self.is_repository_server = self.configRegistry.get( 'local/repository', 'no' ) in ( 'yes', 'true' )

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
		if maintained.lower() in ('yes', 'true', 'enabled', '1'):
			self.parts.append('maintained')

		unmaintained = self.configRegistry.get('repository/online/unmaintained', 'False')
		if unmaintained.lower() in ('yes', 'true', 'enabled', '1'):
			self.parts.append('unmaintained')

		#UCS version
		self.ucs_version=self.configRegistry['version/version']
		self.patchlevel = int(self.configRegistry['version/patchlevel'])
		self.security_patchlevel = int(self.configRegistry['version/security-patchlevel'])
		self.version_major, self.version_minor = map(int, self.ucs_version.split('.'))

		# should hotfixes be used
		self.hotfixes = self.configRegistry.get('repository/online/hotfixes', 'no' ).lower() in ('yes', 'true', 'enabled', '1')

		# UniventionMirror needs to provide its own settings
		self.config_repository()

		# check availability of the repository server
		try:
			socket.gethostbyname(self.repository_server)
			self.nameserver_available=True
		except socket.gaierror:
			self.nameserver_available=False

		# check for prefix on repository server (if the repository server is reachable)
		try:
			if not self.repository_prefix and self.net_path_exists( '/univention-repository/' ):
				self.repository_prefix = 'univention-repository'
		except:
			self.repository_prefix = ''

	def net_path_exists (self, path, server='', port='', prefix='', username='', password='', debug=False):
		# path MUST NOT contain the schema and hostname
		proxy_headers = self.open_connection(server=server, port=port)
		if server: #if we use a different server we should also use a different prefix
			if prefix:
				site = '%s/%s/%s' % (self.proxy_prefix, prefix, path)
			else:
				site = '%s/%s' % (self.proxy_prefix, path)
		else:
			site = '%s/%s/%s' % (self.proxy_prefix, self.repository_prefix, path)

		replace_slash = re.compile ('[/]{2,}')
		site = replace_slash.sub ('/', site)
		if not site.startswith ('http://') and proxy_headers != None:
			site = 'http://%s' % site

		if proxy_headers != None:
			self.connection.putrequest(self.http_method, site, skip_accept_encoding=1)
		else:
			self.connection.putrequest(self.http_method, site)

		if username and password:
			auth = 'Basic ' + string.strip(base64.encodestring(username + ':' + password))
			self.connection.putheader('Authorization', auth)

		if proxy_headers != None:
			for k, v in proxy_headers.items ():
				self.connection.putheader (k, v)
		self.connection.endheaders ()
		response = self.connection.getresponse()
		response.read()
		ud.debug(ud.NETWORK, ud.ALL, "%d %s %s" % (response.status, self.http_method, site))
		#print "# %d %s %s" % (response.status, self.http_method, site) # TODO

		if response.status == httplib.OK: # 200
			self.close_connection()
			return True

		if response.status == httplib.NOT_IMPLEMENTED and self.http_method == 'HEAD': # 501
			# fall-back to GET if not implemented
			ud.debug(ud.NETWORK, ud.INFO, "HEAD not implemented at %s, switching to GET." % site)
			self.http_method = 'GET'
			self.close_connection()
			return self.net_path_exsists (self, path, server, port, prefix, username, password, debug)

		if debug:
			if response.status == httplib.NOT_FOUND: # 404
				print >>sys.stderr, '# The site http://%s:%s%s was not found' % (server, port, site)
			elif response.status == httplib.UNAUTHORIZED: # 401
				if username and password:
					print >>sys.stderr, '# Authentication failure for http://%s:%s@%s:%s%s' % (username, password, server, port, site)
				else:
					print >>sys.stderr, '# Username and password are requiered for http://%s:%s%s' % (server, port, site)
			else:
				print >>sys.stderr, '# The http error code (%d) was returned for the site http://%s:%s%s' % (response.status, server, port, site)

		self.close_connection()
		return False

	def get_next_version(self, version, components=[]):
		'''Check if a new patchlevel, minor or major release is available for the given version.
		Components must be available for the same major.minor version.
		'''
		for ver in [
			{'major':version.major  , 'minor':version.minor  , 'patchlevel':version.patchlevel+1},
			{'major':version.major  , 'minor':version.minor+1, 'patchlevel':0},
			{'major':version.major+1, 'minor':0              , 'patchlevel':0}
			]:
			if self.net_path_exists(UCSRepoPool(part='maintained', **ver).path()):
				for component in components:
					mm_version = UCS_Version.FORMAT % ver
					if not self.get_component_repositories(component, [mm_version], False):
						print >>sys.stderr, "# Required component '%s' not available for version %s" % (component, mm_version)
						return None
				else:
					return UCS_Version.FULLFORMAT % ver
		return None

	def release_update_available( self, ucs_version = None ):
		'''Check if an update is available for the ucs_version'''
		if not ucs_version:
			ucs_version = self.current_version

		components = filter(lambda c: 'current' in self.configRegistry.get('repository/online/component/%s/version' % c, '').split(','), self.get_components())

		return self.get_next_version(UCS_Version(ucs_version), components)

	def release_update_temporary_sources_list(self, version, components=None):
		'''Return list of Debian repository statements for the release update including blocking components.'''
		if components == None:
			components = self.get_components()

		mmp_version = UCS_Version(version)
		mm_version = UCS_Version.FORMAT % mmp_version
		archs = ['all', 'extern'] + self.architectures

		result = []
		for ver in self._iterate_versions(UCSRepoPool(), mmp_version, mmp_version, self.parts, archs):
			result.append(ver.deb())
		for component in components:
			result += self.get_component_repositories(component, [mm_version], False)
		return result

	def security_update_temporary_sources_list(self):
		'''Create a list of Debian repository statements for the next security update'''
		start = end = UCS_Version( (self.version_major, self.version_minor, self.security_patchlevel+1) )
		archs = ['all', 'extern'] + self.architectures

		sources_list = []
		for ver in self._iterate_versions(UCSRepoPool(patch="sec%(patchlevel)d"), start, end, self.parts, archs):
			sources_list.append( ver.deb() )
		return sources_list

	def security_update_available(self):
		'''Check for the security version for the current version'''
		start = end = UCS_Version( (self.version_major, self.version_minor, self.security_patchlevel+1) )
		archs = ['all', 'extern'] + self.architectures
		for ver in self._iterate_versions(UCSRepoPool(patch="sec%(patchlevel)d"), start, end, self.parts, archs):
			return 'sec%(patchlevel)s' % ver
		return False

	@property
	def current_version(self):
		'''Return current (major.minor-patchlevel) version.'''
		return UCS_Version((self.version_major, self.version_minor, self.patchlevel))

	def get_ucs_version(self):
		'''Return current (major.minor-patchlevel) version as string.'''
		return str(self.current_version)

	def get_components(self):
		'''Retrieve all enabled components from registry as list'''
		components = []
		for key in self.configRegistry.keys():
			if key.startswith('repository/online/component/'):
				component_part = key.split('repository/online/component/')[1]
				if component_part.find('/') == -1 and self.configRegistry[key].lower() in ('yes', 'true', 'enabled', '1'):
					components.append(component_part)
		return components

	def get_all_components(self):
		'''Retrieve all configured components from registry as list'''
		components = []
		for key in self.configRegistry.keys():
			if key.startswith('repository/online/component/'):
				component_part = key.split('repository/online/component/')[1]
				if component_part.find('/') == -1:
					components.append(component_part)
		return components

	def get_component(self, name):
		'''Retrieve named component from registry as hash'''
		component = {}
		for key in self.configRegistry.keys():
			component['activated'] = self.configRegistry['repository/online/component/%s' % name]
			component['name'] = name
			if key.startswith('repository/online/component/%s/' % name):
				var = key.split('repository/online/component/%s/' % name)[1]
				component[var] = self.configRegistry[key]
				pass
		return component

	def _iterate_versions(self, ver, start, end, parts, archs, **netConf):
		'''Iterate through all versions of repositories between start and end.'''
		(ver.major, ver.minor, ver.patchlevel) = (start.major, start.minor, start.patchlevel)
		# TODO: s/self.repository_XYZ/netConf[XYZ]/
		if self.repository_prefix:
			ver.prefix = 'http://%s:%s/%s/' % ( self.repository_server, self.repository_port, self.repository_prefix )
		else:
			ver.prefix = 'http://%s:%s/' % ( self.repository_server, self.repository_port )

		# Workaround version of start << first available repository version,
		# e.g. repository starts at 2.3-0, but called with start=2.0-0
		findFirst = True
		while ver <= end: # major
			while self.net_path_exists(ver.path(), **netConf): # minor
				findFirst = False
				# reset patchlevel for each nested part
				saved_patchlevel = ver.patchlevel
				for ver.part in parts: # part
					ver.patchlevel = saved_patchlevel
					while self.net_path_exists(ver.path(), **netConf): # patchlevel
						for ver.arch in archs: # architecture
							if self.net_path_exists(ver.path(), **netConf):
								yield ver
						del ver.arch
						if isinstance(ver.patch, str): # patchlevel not used
							break
						ver.patchlevel += 1
						if ver > end:
							break
				del ver.part
				ver.minor += 1
				ver.patchlevel = ver.patchlevel_reset
				if ver > end:
					break
			if findFirst and ver.minor < 99:
				ver.minor += 1
				ver.patchlevel = ver.patchlevel_reset
			else:
				ver.major += 1
				ver.minor = 0

	def print_version_repositories( self, clean = False, dists = False, start = None, end = None ):
		'''Return a string of Debian repository statements for all UCS versions
		between start and end.

		For dists=True, additional entries for the parts below dists/ are also added.
		With clean=True, online/repository/clean controls if additional clean statements for apt-mirror are added.
		Default for start: (major, 0, 0)
		Default for end: (major, minor, patchlevel)
		'''
		if not self.online_repository:
			return ''

		if clean:
			clean = self.configRegistry.get('online/repository/clean', 'False').lower() in ('yes', 'true', 'enabled', '1')

		if not start:
			start = UCS_Version( ( self.version_major, 0, 0 ) )

		if not end:
			end = UCS_Version( ( self.version_major, self.version_minor, self.patchlevel ) )

		archs = ['all', 'extern'] + self.architectures
		result = []

		if dists:
			for ver in self._iterate_versions(UCSRepoDist(), start, end, self.parts, self.architectures):
				result.append( ver.deb() )
		for ver in self._iterate_versions(UCSRepoPool(), start, end, self.parts, archs):
			result.append( ver.deb() )
			if ver.arch == archs[-1]: # after architectures but before next patch(level)
				if clean:
					result.append( ver.clean() )
				if self.sources:
					ver.arch = "source"
					if self.net_path_exists(ver.path("Sources.gz")):
						result.append( ver.deb("deb-src") )

		return '\n'.join(result)

	def print_security_repositories( self, clean = False, start = None, end = None, all_security_updates = False ):
		'''Return a string of Debian repository statements for all UCS security
		updates for UCS versions between start and end.

		Default for start: (major, minor)
		Default for end: (major, minor)
		With clean=True, online/repository/clean controls if additional clean statements for apt-mirror are added.
		For all_security_updates=True, all available instead of all needed statements for security updates are returned.
		'''
		# NOTE: Here "patchlevel" is used for the "security patchlevel"
		if not self.online_repository:
			return ''

		if clean:
			clean = self.configRegistry.get('online/repository/clean', 'False').lower() in ('yes', 'true', 'enabled', '1')

		if start:
			start = copy.copy(start)
			start.patchlevel = 1 # security updates start with 'sec1'
		else:
			start = UCS_Version( ( self.version_major, self.version_minor, 1 ) )

		# Hopefully never more than 99 security updates
		max = bool(all_security_updates) and 100 or self.security_patchlevel
		if end:
			end = copy.copy(end)
			end.patchlevel = max
		else:
			end = UCS_Version( (self.version_major, self.version_minor, max) )

		archs = ['all', 'extern'] + self.architectures
		result = []

		for ver in self._iterate_versions(UCSRepoPool(patch="sec%(patchlevel)d", patchlevel_reset=1), start, end, self.parts, archs):
			result.append( ver.deb() )
			if ver.arch == archs[-1]: # after architectures but before next patch(level)
				if clean:
					result.append( ver.clean() )
				if self.sources:
					ver.arch = "source"
					if self.net_path_exists(ver.path("Sources.gz")):
						result.append( ver.deb("deb-src") )

		if self.hotfixes:
			# hotfixes don't use patchlevel, but UCS_Version.__cmp__ uses them
			start.patchlevel = end.patchlevel = None
			for ver in self._iterate_versions(UCSRepoPool(patch="hotfixes"), start, end, self.parts, archs):
				result.append( ver.deb() )

		return '\n'.join(result)

	def get_component_repositories(self, component, versions, clean=False):
		'''Return array of Debian repository statements for requested component.
		With clean=True, additional clean statements for apt-mirror are added.
		'''
		archs = ['all', 'extern'] + self.architectures
		result = []

		repo = UCSRepoPool(patch=component)
		netConf = {'prefix':''}
		if not self.is_repository_server:
			netConf['server'] = self.configRegistry.get('repository/online/component/%s/server' % component, self.repository_server)
		else:
			netConf['server'] = self.repository_server
		netConf['port'] = self.configRegistry.get('repository/online/component/%s/port' % component, self.repository_port)
		repository_prefix = self.configRegistry.get( 'repository/online/component/%s/prefix' % component, '' )

		parts = self.configRegistry.get('repository/online/component/%s/parts' % component, 'maintained').split(',')
		netConf['username'] = self.configRegistry.get('repository/online/component/%s/username' % component, None)
		netConf['password'] = self.configRegistry.get('repository/online/component/%s/password' % component, None)
		cleanComponent = False
		if clean:
			cleanComponent = self.configRegistry.get('repository/online/component/%s/clean' % component, 'False').lower() in ('yes', 'true', 'enabled', '1')

		repo.prefix = "http://"
		if netConf['username'] and netConf['password']:
			from urllib import quote # rfc1738: unsafe characters
			# FIXME http://bugs.debian.org/500560: [@:/] don't work
			repo.prefix += "%s:%s@" % (quote(netConf['username'],''), quote(netConf['password'],''))
		repo.prefix += "%(server)s:%(port)s/" % netConf
		# allow None as a component prefix
		if not repository_prefix:
			# check for prefix on component repository server (if the repository server is reachable)
			try:
				if self.net_path_exists( '/univention-repository/', **netConf ):
					netConf['prefix'] = 'univention-repository'
					repo.prefix += 'univention-repository/'
				elif self.repository_prefix and self.net_path_exists('/%s/' % self.repository_prefix, **netConf):
					netConf['prefix'] = self.repository_prefix
					repo.prefix += '%s/' % self.repository_prefix
			except:
				pass
		elif repository_prefix.lower() != 'none':
			netConf['prefix'] = repository_prefix.strip('/')
			repo.prefix += '%s/' % repository_prefix.strip('/')
		netConf['debug'] = True

		for repo.version in versions:
			for repo.part in ["%s/component" % part for part in parts]:
				if not self.net_path_exists(repo.path(), **netConf):
					continue

				# support different repository format without architecture (e.g. used by OX)
				path = '/%(version)s/%(part)s/%(patch)s/Packages.gz' % repo
				if self.net_path_exists(path, **netConf):
					result.append('deb %(prefix)s%(version)s/%(part)s/%(patch)s/ ./' % repo)
					if cleanComponent:
						result.append('clean %(prefix)s%(version)s/%(part)s/%(patch)s/' % repo)
				else:
					for repo.arch in archs:
						if self.net_path_exists(repo.path(), **netConf):
							result.append( repo.deb() )
					if cleanComponent:
						result.append( repo.clean() )
					if self.sources:
						repo.arch = "source"
						if self.net_path_exists(repo.path("Sources.gz")):
							result.append( repo.deb("deb-src") )
					del repo.arch

		return result

	def print_component_repositories( self, clean = False ):
		'''Return a string of Debian repository statements for all enabled components.
		With clean=True, repository/online/component/%s/clean controls if additional clean statements for apt-mirror are added.
		'''
		if not self.online_repository:
			return ''

		if clean:
			clean = self.configRegistry.get('online/repository/clean', 'False').lower() in ('yes', 'true', 'enabled', '1')

		result = []

		for component in self.get_components():
			str = self.configRegistry.get('repository/online/component/%s/version' % component, '')
			versions = set()
			for version in str.split(','):
				if version in ('current', ''): # all from same major
					version = {'major': self.version_major}
					for version['minor'] in range(self.version_minor + 1):
						versions.add(UCS_Version.FORMAT % version)
				else:
					versions.add(version)
			result += self.get_component_repositories(component, versions, clean)

		return '\n'.join(result)

if __name__ == '__main__':
	import doctest
	doctest.testmod()
