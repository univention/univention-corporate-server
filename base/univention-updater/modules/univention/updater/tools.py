#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages updates
#
# Copyright 2008-2014 Univention GmbH
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

try:
	import univention.debug as ud
except ImportError:
	import univention.debug2 as ud

# TODO: Convert to absolute imports only AFTER the unit test has been adopted
from commands import cmd_update, cmd_dist_upgrade_sim, cmd_dist_upgrade
from errors import *

import errno
import time
import sys
import re
import os
import copy
import httplib
import socket
import univention.config_registry
import traceback
import urllib2
from urllib import quote
import subprocess
from operator import attrgetter, itemgetter
import new
import tempfile
import shutil
import logging
import atexit

RE_ALLOWED_DEBIAN_PKGNAMES = re.compile('^[a-z0-9][a-z0-9.+-]+$')
RE_SPLIT_MULTI = re.compile('[ ,]+')
RE_COMPONENT = re.compile(r'^repository/online/component/([^/]+)$')

MIN_GZIP = 100  # size of non-empty gzip file

try:
	NullHandler = logging.NullHandler
except AttributeError:
	class NullHandler(logging.Handler):
		"""Returns a new instance of the NullHandler class."""
		def emit(self, record):
			"""This method does nothing."""
			pass


def verify_script(script, signature):
	"""
	Verify detached signature of script.
	> gpg -a -u 2CBDA4B0 --passphrase-file /etc/archive-keys/ucs3.0.txt -o script.sh.gpg -b script.sh
	> verify_script(open("script.sh", "r").read(), open("script.sh.gpg", "r").read())
	"""
	# write signature to temporary file
	sig_fd, sig_name = tempfile.mkstemp()
	os.write(sig_fd, signature)
	os.close(sig_fd)

	# collect trusted keys of apt-key
	keys = [os.path.join(verify_script.APT, "trusted.gpg")]
	apt = os.path.join(verify_script.APT, "trusted.gpg.d")
	keys += [os.path.join(apt, key) for key in os.listdir(apt) if key.endswith('.gpg')]

	# build command line
	cmd = ["/usr/bin/gpgv"]
	for key in keys:
			cmd += ["--keyring", key]
	cmd += [sig_name, "-"]

	# verify script
	proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT, close_fds=True)
	stdout, _stderr = proc.communicate(script)
	ret = proc.wait()
	return stdout if ret != 0 else None
verify_script.APT = "/etc/apt"


class UCS_Version( object ):
	'''Version object consisting of major-, minor-number and patch-level'''
	FORMAT = '%(major)d.%(minor)d'
	FULLFORMAT = '%(major)d.%(minor)d-%(patchlevel)d'
	# regular expression matching a UCS version X.Y-Z
	_regexp = re.compile( '(?P<major>[0-9]+)\.(?P<minor>[0-9]+)-(?P<patch>[0-9]+)' )

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
			raise ValueError( 'string does not match UCS version pattern' )
		self.major, self.minor, self.patchlevel = map(int, match.groups())

	def __getitem__(self, k):
		'''Dual natured dictionary: retrieve value from attribute.'''
		return self.__dict__[k]
	def __str__(self):
		'''Return full version string.'''
		return UCS_Version.FULLFORMAT % self

	def __hash__(self):
		return hash((self.major, self.minor, self.patchlevel))

	def __eq__(self, other):
		return (self.major, self.minor, self.patchlevel) == (other.major, other.minor, other.patchlevel)

	def __repr__(self):
		'''Return canonical string representation.'''
		return 'UCS_Version((%d,%d,%r))' % (self.major, self.minor, self.patchlevel)

class UCSRepo(UCS_Version):
	'''Debian repository.'''
	def __init__(self, **kw):
		kw.setdefault('patchlevel_reset', 0)
		kw.setdefault('patchlevel_max', 99)
		for (k, v) in kw.items():
			if isinstance(v, str) and '%(' in v:
				setattr(self, k, UCSRepo._substitution(v, self.__dict__))
			else:
				setattr(self, k, v)
	def __repr__(self):
		return '%s(**%r)' % (self.__class__.__name__, self.__dict__)
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
				try:
					i = format.rindex('/') + 1
				except ValueError:
					i = 0
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

		>>> r=UCSRepoPool(prefix='http://updates.software-univention.de/',major=2,minor=3,patchlevel=1,part='maintained',arch='i386')
		>>> r.deb()
		'deb http://updates.software-univention.de/2.3/maintained/ 2.3-1/i386/'
		'''
		fmt = "%(prefix)s%(version)s/%(part)s/ %(patch)s/%(arch)s/"
		return "%s %s" % (type, super(UCSRepoPool,self)._format(fmt))
	def path(self, file='Packages.gz'):
		'''Format pool for directory/file access. Returns relative path.

		>>> UCSRepoPool(prefix='http://updates.software-univention.de/',major=2,minor=3).path()
		'2.3/'
		>>> UCSRepoPool(major=2,minor=3,part='maintained').path()
		'2.3/maintained/'
		>>> UCSRepoPool(major=2,minor=3,patchlevel=1,part='maintained').path()
		'2.3/maintained/2.3-1/'
		>>> UCSRepoPool(major=2,minor=3,patchlevel=1,part='maintained',arch='i386').path()
		'2.3/maintained/2.3-1/i386/Packages.gz'
		'''
		fmt = "%(version)s/%(part)s/%(patch)s/%(arch)s/" + file
		return super(UCSRepoPool,self)._format(fmt)
	def clean(self):
		'''Format for /etc/apt/mirror.list'''
		fmt = "%(prefix)s%(version)s/%(part)s/%(patch)s/" # %(arch)s/
		return "clean %s" % super(UCSRepoPool,self)._format(fmt)


class UCSRepoPoolNoArch(UCSRepo):
	'''Debian pool repository without explicit architecture subdirectory.'''
	def __init__(self, **kw):
		kw.setdefault('version', UCS_Version.FORMAT)
		kw.setdefault('patch', UCS_Version.FULLFORMAT)
		super(UCSRepoPoolNoArch,self).__init__(**kw)
	def deb(self, type="deb"):
		'''Format for /etc/apt/sources.list.

		>>> r=UCSRepoPoolNoArch(prefix='http://updates.software-univention.de/',major=2,minor=3,patch='comp',part='maintained/component',arch='all')
		>>> r.deb()
		'deb http://updates.software-univention.de/2.3/maintained/component/comp/ ./'
		'''
		fmt = "%(prefix)s%(version)s/%(part)s/%(patch)s/ ./"
		return "%s %s" % (type, super(UCSRepoPoolNoArch,self)._format(fmt))
	def path(self, file='Packages.gz'):
		'''Format pool for directory/file access. Returns relative path.

		>>> UCSRepoPoolNoArch(prefix='http://updates.software-univention.de/',major=2,minor=3).path()
		'2.3/'
		>>> UCSRepoPoolNoArch(major=2,minor=3,part='maintained/component').path()
		'2.3/maintained/component/'
		>>> UCSRepoPoolNoArch(major=2,minor=3,part='maintained/component',patch='comp').path()
		'2.3/maintained/component/comp/Packages.gz'
		>>> UCSRepoPoolNoArch(major=2,minor=3,part='maintained/component',patch='comp',arch='all').path()
		'2.3/maintained/component/comp/Packages.gz'
		'''
		fmt = "%(version)s/%(part)s/%(patch)s/" + file
		return super(UCSRepoPoolNoArch,self)._format(fmt)
	def clean(self):
		'''Format for /etc/apt/mirror.list'''
		fmt = "%(prefix)s%(version)s/%(part)s/%(patch)s/"
		return "clean %s" % super(UCSRepoPoolNoArch,self)._format(fmt)


class UCSRepoDist(UCSRepo):
	'''Debian dists repository.'''
	def __init__(self, **kw):
		kw.setdefault('version', UCS_Version.FORMAT)
		kw.setdefault('patch', UCS_Version.FULLFORMAT)
		super(UCSRepoDist,self).__init__(**kw)
	def deb(self, type="deb"):
		'''Format for /etc/apt/sources.list.

		>>> r=UCSRepoDist(prefix='http://updates.software-univention.de/',major=2,minor=2,patchlevel=0,part='maintained',arch='i386')
		>>> r.deb()
		'deb http://updates.software-univention.de/2.2/maintained/2.2-0/ dists/univention/main/binary-i386/'
		'''
		fmt = "%(prefix)s%(version)s/%(part)s/%(patch)s/ dists/univention/main/binary-%(arch)s/"
		return "%s %s" % (type, super(UCSRepoDist,self)._format(fmt))
	def path(self, file='Packages.gz'):
		'''Format dist for directory/file access. Returns relative path.

		>>> UCSRepoDist(prefix='http://updates.software-univention.de/',major=2,minor=2).path()
		'2.2/'
		>>> UCSRepoDist(major=2,minor=2,part='maintained').path()
		'2.2/maintained/'
		>>> UCSRepoDist(major=2,minor=2,patchlevel=0,part='maintained').path()
		'2.2/maintained/2.2-0/dists/univention/main/'
		>>> UCSRepoDist(major=2,minor=2,patchlevel=0,part='maintained',arch='i386').path()
		'2.2/maintained/2.2-0/dists/univention/main/binary-i386/Packages.gz'
		'''
		fmt = "%(version)s/%(part)s/%(patch)s/dists/univention/main/binary-%(arch)s/" + file
		return super(UCSRepoDist,self)._format(fmt)

class UCSHttpServer(object):
	'''Access to UCS compatible remote update server.'''

	class HTTPHeadHandler(urllib2.BaseHandler):
		'''Handle fallback from HEAD to GET if unimplemented.'''
		def http_error_501(self, req, fp, code, msg, headers): # httplib.NOT_IMPLEMENTED
			m = req.get_method()
			if m == 'HEAD' == UCSHttpServer.http_method:
				ud.debug(ud.NETWORK, ud.INFO, "HEAD not implemented at %s, switching to GET." % req)
				UCSHttpServer.http_method = 'GET'
				return self.parent.open(req)
			else:
				return None

	def __init__(self, server, port=80, prefix='', username=None, password=None, user_agent=None):
		self.log = logging.getLogger('updater.UCSHttp')
		self.log.addHandler(NullHandler())
		self.server = server
		self.port = int(port)
		prefix = str(prefix).strip('/')
		if prefix:
			self.prefix = '%s/' % prefix
		else:
			self.prefix = ''
		self.username = username
		self.password = password
		self.user_agent = user_agent

	http_method = 'HEAD'
	head_handler = HTTPHeadHandler()
	pass_handler = urllib2.HTTPPasswordMgrWithDefaultRealm()
	auth_handler = urllib2.HTTPBasicAuthHandler(pass_handler)
	proxy_handler = urllib2.ProxyHandler()
	# No need for ProxyBasicAuthHandler, since ProxyHandler parses netloc for @
	opener = urllib2.build_opener(head_handler, auth_handler, proxy_handler)
	failed_hosts = set()

	@classmethod
	def reinit(self):
		'''Reload proxy settings and reset failed hosts.'''
		self.proxy_handler = urllib2.ProxyHandler()
		self.opener = urllib2.build_opener(self.head_handler, self.auth_handler, self.proxy_handler)
		self.failed_hosts = set()

	def __getitem__(self, item):
		'''Convert attributes to dict.'''
		if item == 'server':
			return self.server
		elif item == 'prefix':
			return quote(self.prefix)
		elif item == 'port':
			if self.port == 80:
				return ''
			else:
				return ':%d' % self.port
		elif item == 'cred':
			if self.username:
				# FIXME http://bugs.debian.org/500560: [@:/] don't work
				return "%s:%s@" % (quote(self.username), quote(self.password))
			else:
				return ''
		else:
			raise KeyError(item)

	def __str__(self):
		'''URI with credentials.'''
		return 'http://%(cred)s%(server)s%(port)s/%(prefix)s' % self

	def __repr__(self):
		'''Return canonical string representation.'''
		return 'UCSHttpServer(%r, port=%d, prefix=%r, username=%r, password=%r)' % (self.server, self.port, self.prefix, self.username, self.password)

	def __add__(self, rel):
		'''Append relative URI.'''
		uri = copy.copy(self)
		uri.prefix += '%s/' % str(rel).strip('/')
		return uri

	def join(self, rel):
		'''Return joind URI without credential.'''
		uri = 'http://%(server)s%(port)s/%(prefix)s' % self
		uri += quote(str(rel).lstrip('/'))
		return uri

	def access(self, rel, get=False):
		'''Access URI and optionally get data. Return None on errors.'''
		if self.user_agent:
			UCSHttpServer.opener.addheaders = [('User-agent', self.user_agent)]
		uri = self.join(rel)
		if self.username:
			UCSHttpServer.auth_handler.add_password(realm=None, uri=uri, user=self.username, passwd=self.password)
		req = urllib2.Request(uri)
		if req.get_host() in self.failed_hosts:
			self.log.error('Already failed %s', req.get_host())
			raise DownloadError(uri, -1)
		if not get and UCSHttpServer.http_method != 'GET':
			# Overwrite get_method() to return "HEAD"
			def get_method(self, orig=req.get_method):
				method = orig()
				if method == 'GET':
					return UCSHttpServer.http_method
				else:
					return method
			req.get_method = new.instancemethod(get_method, req, urllib2.Request)

		self.log.info('Requesting %s', req.get_full_url())
		ud.debug(ud.NETWORK, ud.ALL, "updater: %s %s" % (req.get_method(), req.get_full_url()))
		try:
			res = UCSHttpServer.opener.open(req)
			try:
				code = res.code
				size = int(res.headers.get('content-length', 0))
				content = res.read()
				self.log.info("Got %s %s: %d %d", req.get_method(), req.get_full_url(), code, size)
				return (code, size, content)
			finally:
				res.close()
		# direct   | proxy                                        | Error cause
		#          | valid     closed   filter   DNS     auth     |
		# HTTP:200 | HTTP:200  URL:111  URL:110  GAI:-2  HTTP:407 | OK
		# HTTP:404 | HTTP:404  URL:111  URL:110  GAI:-2  HTTP:407 | Path unknown
		# ---------+----------------------------------------------+----------------------
		# URL:111  | HTTP:404  URL:111  URL:110  GAI:-2  HTTP:407 | Port closed
		# URL:110  | HTTP:404  URL:111  URL:110  GAI:-2  HTTP:407 | Port filtered
		# GAI:-2   | HTTP:502/4URL:111  URL:110  GAI:-2  HTTP:407 | Host name unknown
		# HTTP:401 | HTTP:401  URL:111  URL:110  GAI:-2  HTTP:407 | Authorization required
		except urllib2.HTTPError, res:
			self.log.exception("Failed %s %s: %s", req.get_method(), req.get_full_url(), res)
			if res.code == httplib.UNAUTHORIZED: # 401
				raise ConfigurationError(uri, 'credentials not accepted')
			if res.code == httplib.PROXY_AUTHENTICATION_REQUIRED: # 407
				raise ProxyError(uri, 'credentials not accepted')
			if res.code in (httplib.BAD_GATEWAY, httplib.GATEWAY_TIMEOUT): # 502 504
				self.failed_hosts.add(req.get_host())
				raise ConfigurationError(uri, 'host is unresolvable')
			raise DownloadError(uri, res.code)
		except urllib2.URLError, e:
			self.log.exception("Failed %s %s: %s", req.get_method(), req.get_full_url(), e)
			if isinstance(e.reason, basestring):
				reason = e.reason
			else:
				reason = e.reason.args[1] # default value for error message
				if isinstance(e.reason, socket.gaierror):
					if e.reason.args[0] == socket.EAI_NONAME: # -2
						reason = 'host is unresolvable'
				else:
					if e.reason.args[0] == errno.ETIMEDOUT: # 110
						reason = 'port is blocked'
					elif e.reason.args[0] == errno.ECONNREFUSED: # 111
						reason = 'port is closed'
			if '/' == req.get_selector()[0]: # direct
				self.failed_hosts.add(req.get_host())
				raise ConfigurationError(uri, reason)
			else: # proxy
				raise ProxyError(uri, reason)

class UCSLocalServer(object):
	'''Access to UCS compatible local update server.'''
	def __init__(self, prefix):
		self.log = logging.getLogger('updater.UCSFile')
		self.log.addHandler(NullHandler())
		prefix = str(prefix).strip('/')
		if prefix:
			self.prefix = '%s/' % prefix
		else:
			self.prefix = ''

	def __str__(self):
		'''Absolute file-URI.'''
		return 'file:///%s' % self.prefix

	def __repr__(self):
		'''Return canonical string representation.'''
		return 'UCSLocalServer(prefix=%r)' % (self.prefix,)

	def __add__(self, rel):
		'''Append relative URI.'''
		uri = copy.copy(self)
		uri.prefix += str(rel).lstrip('/')
		return uri

	def join(self, rel):
		'''Return joind URI without credential.'''
		uri = self.__str__()
		uri += str(rel).lstrip('/')
		return uri

	def access(self, rel, get=False):
		'''Access URI and optionally get data. Return None on errors.'''
		uri = self.join(rel)
		ud.debug(ud.NETWORK, ud.ALL, "updater: %s" % (uri,))
		# urllib2.urlopen() doesn't work for directories
		assert uri.startswith('file://')
		path = uri[len('file://'):]
		if os.path.exists(path):
			if os.path.isdir(path):
				self.log.info("Got %s", path)
				return (httplib.OK, 0, '')  # 200
			elif os.path.isfile(path):
				f = open(path, 'r')
				try:
					data = f.read()
				finally:
					f.close()
				self.log.info("Got %s: %d", path, len(data))
				return (httplib.OK, len(data), data)  # 200
		self.log.error("Failed %", path)
		raise DownloadError(uri, -1)

class UniventionUpdater:
	'''Handle Univention package repositories.'''
	COMPONENT_AVAILABLE = 'available'
	COMPONENT_NOT_FOUND = 'not_found'
	COMPONENT_DISABLED = 'disabled'
	COMPONENT_UNKNOWN = 'unknown'
	COMPONENT_PERMISSION_DENIED = 'permission_denied'
	FN_UPDATER_APTSOURCES_COMPONENT = '/etc/apt/sources.list.d/20_ucs-online-component.list'

	def __init__(self, check_access=True):
		"""Create new updater with settings from UCS.
		Throws ConfigurationError when configured server is not available immediately."""
		self.log = logging.getLogger('updater.Updater')
		self.log.addHandler(NullHandler())
		self.check_access = check_access
		self.connection = None
		self.architectures = [ os.popen('dpkg --print-architecture 2>/dev/null').readline()[:-1] ]

		self.ucr_reinit()

	def config_repository( self ):
		'''Retrieve configuration to access repository. Overridden in UniventionMirror.'''
		self.online_repository = self.configRegistry.is_true('repository/online', True)
		self.repository_server = self.configRegistry.get('repository/online/server', 'updates.software-univention.de')
		self.repository_port = self.configRegistry.get('repository/online/port', '80')
		self.repository_prefix = self.configRegistry.get('repository/online/prefix', '').strip('/')
		self.sources = self.configRegistry.is_true('repository/online/sources', False)
		UCSHttpServer.http_method = self.configRegistry.get('repository/online/httpmethod', 'HEAD').upper()

	def ucr_reinit(self):
		'''Re-initialize settings'''
		self.configRegistry=univention.config_registry.ConfigRegistry()
		self.configRegistry.load()

		self.is_repository_server = self.configRegistry.is_true('local/repository', False)

		if 'proxy/http' in self.configRegistry and self.configRegistry['proxy/http']:
			os.environ['http_proxy'] = self.configRegistry['proxy/http']
			UCSHttpServer.reinit()
		if 'proxy/no_proxy' in self.configRegistry and self.configRegistry['proxy/no_proxy']:
			os.environ['no_proxy'] = self.configRegistry['proxy/no_proxy']

		# check for maintained and unmaintained
		self.parts = ['maintained']
		if self.configRegistry.is_true('repository/online/unmaintained', False):
			self.parts.append('unmaintained')

		#UCS version
		self.ucs_version=self.configRegistry['version/version']
		self.patchlevel = int(self.configRegistry['version/patchlevel'])
		self.security_patchlevel = int(self.configRegistry.get('version/security-patchlevel', 0))
		self.erratalevel = int(self.configRegistry.get('version/erratalevel', 0))
		self.version_major, self.version_minor = map(int, self.ucs_version.split('.', 1))

		# should hotfixes be used
		self.hotfixes = self.configRegistry.is_true('repository/online/hotfixes', False)

		# override automatically detected architecture by UCR variable repository/online/architectures (comma or space separated)
		archlist = self.configRegistry.get('repository/online/architectures', '')
		if archlist:
			self.architectures = RE_SPLIT_MULTI.split(archlist)

		# UniventionMirror needs to provide its own settings
		self.config_repository()

		# generate user agent string
		user_agent = self._get_user_agent_string()

		# Auto-detect prefix
		self.server = UCSHttpServer(server=self.repository_server, port=self.repository_port, prefix=self.repository_prefix, user_agent = user_agent)
		try:
			if not self.repository_prefix:
				try:
					assert self.server.access('/univention-repository/')
					self.server += '/univention-repository/'
					self.log.info('Using detected prefix /univention-repository/')
				except DownloadError, e:
					self.log.info('No prefix /univention-repository/ detected, using /')
					ud.debug(ud.NETWORK, ud.ALL, "%s" % e)
				return # already validated or implicit /
			# Validate server settings
			try:
				assert self.server.access('')
				self.log.info('Using configured prefix %s', self.repository_prefix)
			except DownloadError, e:
				self.log.exception('Failed configured prefix %s', self.repository_prefix)
				uri, code = e
				raise ConfigurationError(uri, 'non-existing prefix "%s": %s' % (self.repository_prefix, uri))
		except ConfigurationError, e:
			if self.check_access:
				self.log.exception('Failed server detection: %s' % (e,))
				raise

	def get_next_version(self, version, components=[], errorsto='stderr'):
		'''Check if a new patchlevel, minor or major release is available for the given version.
		   Components must be available for the same major.minor version.
		   errorsto: stderr|exception|none
		'''
		debug = (errorsto == 'stderr')

		def versions(major, minor, patchlevel):
			"""Generate next valid version numbers as hash."""
			if patchlevel < 99:
				yield {'major':major,   'minor':minor,   'patchlevel':patchlevel+1}
			if minor < 99:
				yield {'major':major,   'minor':minor+1, 'patchlevel':0}
			if major < 99:
				yield {'major':major+1, 'minor':0,       'patchlevel':0}

		for ver in versions(version.major, version.minor, version.patchlevel):
			repo = UCSRepoPool(prefix=self.server, part='maintained', **ver)
			self.log.info('Checking for version %s', repo)
			try:
				assert self.server.access(repo.path())
				self.log.info('Found version %s', repo.path())
				failed = set()
				for component in components:
					self.log.info('Checking for component %s', component)
					mm_version = UCS_Version.FORMAT % ver
					if not self.get_component_repositories(component, [mm_version], clean=False, debug=debug):
						self.log.error('Missing component %s', component)
						if errorsto == 'stderr':
							print >> sys.stderr, RequiredComponentError(mm_version, [component])
						elif errorsto == 'exception':
							failed.add(component)
						else:
							return None
				if failed:
					raise RequiredComponentError(mm_version, failed)
				else:
					self.log.info('Going for version %s', ver)
					return UCS_Version.FULLFORMAT % ver
			except DownloadError, e:
				ud.debug(ud.NETWORK, ud.ALL, "%s" % e)
		return None

	def get_all_available_release_updates( self, ucs_version = None ):
		'''Returns a list of all available release updates - the function takes required components into account
		   and stops if a required component is missing
		   Arguments:
		     ucs_version: starts travelling through available version from version 'ucs_version'
		   Return value: tuple(versions, blocking component)
		     versions: available UCS versions (list of strings)
		     blocking component: None or name of update blocking component
		 '''

		if not ucs_version:
			ucs_version = self.current_version

		components = self.get_current_components()

		result = []
		while ucs_version:
			try:
				ucs_version = self.get_next_version(UCS_Version(ucs_version), components, errorsto='exception')
			except RequiredComponentError as ex:
				self.log.warn('Update blocked by components %s', ', '.join(ex.components))
				# ex.components blocks update to next version ==> return current list and blocking component
				return result, ex.components

			if ucs_version:
				result.append(ucs_version)
		self.log.info('Found release updates %r', result)
		return result, None

	def release_update_available( self, ucs_version = None, errorsto='stderr' ):
		'''Check if an update is available for the ucs_version'''
		if not ucs_version:
			ucs_version = self.current_version

		components = self.get_current_components()

		return self.get_next_version(UCS_Version(ucs_version), components, errorsto)

	def release_update_temporary_sources_list(self, version, components=None):
		'''Return list of Debian repository statements for the release update including all enabled components.'''
		if components is None:
			components = self.get_components()

		mmp_version = UCS_Version(version)
		current_components = self.get_current_components()
		archs = ['all'] + self.architectures

		result = []
		for server, ver in self._iterate_version_repositories(mmp_version, mmp_version, self.parts, archs):
			result.append(ver.deb())
		for component in components:
			repos = []
			try:
				repos = self.get_component_repositories(component, [mmp_version], False)
			except (ConfigurationError, ProxyError), e:
				# if component is marked as required (UCR variable "version" contains "current")
				# then raise error, otherwise ignore it
				if component in current_components:
					raise
			if not repos and component in current_components:
				server = self._get_component_server(component)
				uri = server.join('%s/component/%s/' % (version, component))
				raise ConfigurationError(uri, 'component not found')
			result += repos
		return result

	def security_update_temporary_sources_list(self):
		'''Create a list of Debian repository statements for the next security update'''
		start = end = UCS_Version( (self.version_major, self.version_minor, self.security_patchlevel+1) )
		archs = ['all'] + self.architectures

		sources_list = []
		for server, ver in self._iterate_security_repositories(start, end, self.parts, archs):
			sources_list.append( ver.deb() )
		return sources_list

	def errata_update_temporary_sources_list(self):
		'''Create a list of Debian repository statements for the next errata update'''
		start = end = UCS_Version( (self.version_major, self.version_minor, self.erratalevel+1) )
		archs = ['all'] + self.architectures

		sources_list = []
		for server, ver in self._iterate_errata_repositories(start, end, self.parts, archs):
			sources_list.append( ver.deb() )
		return sources_list

	def get_all_available_security_updates(self):
		'''Returns a list of all available security updates for current major.minor version
		   as integer
		   > updater.get_all_available_security_updates()
		   [3, 4, 5]
		'''
		result = []
		archs = ['all'] + self.architectures
		for sp in xrange(self.security_patchlevel + 1, 100):
			version = UCS_Version( (self.version_major, self.version_minor, sp) )
			secver = self.security_update_available(version)
			if secver:
				result.append( secver )
			else:
				break
		self.log.info('Found security updates %r', result)
		return result

	def get_all_available_errata_updates(self):
		'''
		Returns a list of all available errata updates for current major.minor version
		as integer
		> updater.get_all_available_errata_updates()
		[3, 4, 5]
		'''
		result = []
		archs = ['all'] + self.architectures
		for el in xrange(self.erratalevel + 1, 1000):
			version = UCS_Version( (self.version_major, self.version_minor, el) )
			secver = self.errata_update_available(version)
			if secver:
				result.append( secver )
			else:
				break
		self.log.info('Found errata updates %r', result)
		return result

	def get_component_erratalevel(self, component, version=None):
		'''
		Returns the errata level for a component and UCS-version
		installed on the system.
		If no version is given, the current_version is taken.
		'''
		if version is None:
			version = self.current_version
		version = UCS_Version(version)
		return int(self.configRegistry.get('repository/online/component/%s/%s.%s/erratalevel' % (component, version.major, version.minor), 0))

	def get_all_available_errata_component_updates(self):
		'''
		Returns a list of all available errata updates for current major.minor version
		as integer
		> updater.get_all_available_errata_component_updates()
		[
			('component1', {'2.3': [2, 3], '2.4': [5]}),
			('component2', {'3.0': [1], '3.1': []}),
			('component3', {'3.0': [1]}),
		]
		'''
		result = []
		archs = ['all'] + self.architectures
		for component in self.get_all_components():
			# get configured versions for component; default: this major
			versions = self._get_component_versions(component, None, None)
			component_versions = {}
			for version in versions:
				version_str = UCS_Version.FORMAT % version
				current_level = self.get_component_erratalevel(component, version)
				component_versions[version_str] = []
				for el in xrange(current_level + 1, 1000):
					if self.get_component_repositories(component, [version], errata_level=el):
						component_versions[version_str].append(el)
					else:
						break
			if component_versions:
				result.append( (component, component_versions) )

		self.log.info('Found component errata updates %r', result)
		return result

	def security_update_available(self, version=None):
		'''Check for the security version for the current version.
		   Returns next available security update number (integer) or False if no security update is available.
		'''
		if version:
			start = end = version
		else:
			start = end = UCS_Version( (self.version_major, self.version_minor, self.security_patchlevel+1) )
		archs = ['all'] + self.architectures
		for server, ver in self._iterate_security_repositories(start, end, self.parts, archs):
			return ver.patchlevel
		return False

	def errata_update_available(self, version=None):
		'''Check for the errata version for the current version.
		   Returns next available security update number (integer) or False if no security update is available.
		'''
		if version:
			start = end = version
		else:
			start = end = UCS_Version( (self.version_major, self.version_minor, self.erratalevel+1) )
		archs = ['all'] + self.architectures
		for server, ver in self._iterate_errata_repositories(start, end, self.parts, archs):
			return ver.patchlevel
		return False

	@property
	def current_version(self):
		'''Return current (major.minor-patchlevel) version.'''
		return UCS_Version((self.version_major, self.version_minor, self.patchlevel))

	def get_ucs_version(self):
		'''Return current (major.minor-patchlevel) version as string.'''
		return str(self.current_version)

	def get_components(self, only_localmirror_enabled=False):
		'''
			Retrieve all enabled components from registry as set().
			By default, only "enabled" components will be returned (repository/online/component/%s=$TRUE).
			If only_localmirror_enabled is True, then all components with
			repository/online/component/%s/localmirror=$TRUE will be returned.

			If repository/online/component/%s/localmirror is not set, then the value of
			repository/online/component/%s is used (backward compatibility).
		'''
		components = set()
		for key, value in self.configRegistry.items():
			match = RE_COMPONENT.match(key)
			if not match:
				continue
			component, = match.groups()
			enabled = self.configRegistry.is_true(value=value)
			if only_localmirror_enabled:
				enabled = self.configRegistry.is_true(key + '/localmirror', enabled)
			if enabled:
				components.add(component)
		return components

	def get_current_components(self):
		'''Return set() of all components marked as current.'''
		all_components = self.get_components()
		components = set()
		for component in all_components:
			key = 'repository/online/component/%s/version' % component
			value = self.configRegistry.get(key, '')
			versions = RE_SPLIT_MULTI.split(value)
			if 'current' in versions:
				components.add(component)
		return components

	def get_all_components(self):
		'''Retrieve all configured components from registry as set().'''
		components = set()
		for key in self.configRegistry.keys():
			if key.startswith('repository/online/component/'):
				component_part = key[len('repository/online/component/'):]
				if component_part.find('/') == -1:
					components.add(component_part)
		return components

	def get_component(self, name):
		'''Retrieve named component from registry as hash'''
		component = {
				'name': name,
				'activated': self.configRegistry.is_true('repository/online/component/%s' % name, False)
				}
		PREFIX = 'repository/online/component/%s/' % (name,)
		for key, value in self.configRegistry.items():
			if key.startswith(PREFIX):
				var = key[len(PREFIX):]
				component[var] = value
		return component

	def get_current_component_status(self, name):
		"""
		returns the current status of specified component based on /etc/apt/sources.list.d/20_ucs-online-component.list
		return value: <string>
		      COMPONENT_DISABLED              component has been disabled via UCR
			  COMPONENT_AVAILABLE             component is enabled and at least one valid repo string has been found in .list file
			  COMPONENT_NOT_FOUND             component is enabled but no valid repo string has been found in .list file
			  COMPONENT_PERMISSION_DENIED     component is enabled but authentication failed
			  COMPONENT_UNKNOWN				  component's status is unknown
		"""
		if name not in self.get_components():
			return self.COMPONENT_DISABLED

		try:
			comp_file = open(self.FN_UPDATER_APTSOURCES_COMPONENT, 'r')
		except IOError, e:
			return self.COMPONENT_UNKNOWN
		rePath = re.compile('(un)?maintained/component/ ?%s/' % name)
		reDenied = re.compile('credentials not accepted: %s$' % name)
		try:
			# default: file contains no valid repo entry
			result = self.COMPONENT_NOT_FOUND
			for line in comp_file:
				if line.startswith('deb ') and rePath.search(line):
					# at least one repo has been found
					result = self.COMPONENT_AVAILABLE
				elif reDenied.search(line):
					# stop immediately if at least one repo has authentication problems
					return self.COMPONENT_PERMISSION_DENIED
			# return result
			return result
		finally:
			comp_file.close()

	def get_component_defaultpackage(self, componentname):
		"""
		returns a set of (meta) package names to be installed for this component
		return value:
			set([ <string>, ... ])
		"""
		lst = set()
		for var in ('defaultpackages', 'defaultpackage'):
			if componentname and self.configRegistry.get('repository/online/component/%s/%s' % (componentname, var)):
				val = self.configRegistry.get('repository/online/component/%s/%s' % (componentname, var), '')
				# split at " " and "," and remove empty items
				lst |= set(RE_SPLIT_MULTI.split(val))
		lst.discard('')
		return lst

	def is_component_defaultpackage_installed(self, componentname, ignore_invalid_package_names=True):
		"""
		returns installation status of component's default packages
		return value:
		    None  ==> no default packages are defined
			True  ==> all default packages are installed
			False ==> at least one package is not installed
		function raises an ValueError exception if UCR variable contains invalid package names if ignore_invalid_package_names=False
		"""
		pkglist = self.get_component_defaultpackage(componentname)
		if not pkglist:
			return None

		# check package names
		for pkg in pkglist:
			match = RE_ALLOWED_DEBIAN_PKGNAMES.search(pkg)
			if not match:
				if ignore_invalid_package_names:
					continue
				raise ValueError('invalid package name (%s)' % pkg)

		cmd = ['/usr/bin/dpkg-query', '-W', '-f', '${Status}\\n']
		cmd.extend( pkglist )
		p = subprocess.Popen( cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
		stdout, stderr = p.communicate()
		# count number of "Status: install ok installed" lines
		installed_correctly = len([x for x in stdout.splitlines() if x.endswith(' ok installed')])
		# if pkg count and number of counted lines match, all packages are installed
		return len(pkglist) == installed_correctly

	def component_update_available(self):
		"""Check if any component has new or upgradeable packages available."""
		new, upgrade, removed = self.component_update_get_packages()
		return bool(new + upgrade + removed)

	def component_update_get_packages(self):
		"""Return tuple with list of (new, upgradeable) packages."""
		p1 = subprocess.Popen(['univention-config-registry commit /etc/apt/sources.list.d/20_ucs-online-component.list; LC_ALL=C %s >/dev/null; LC_ALL=C %s' % (cmd_update, cmd_dist_upgrade_sim)],
							  stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		(stdout,stderr) = p1.communicate()
		ud.debug(ud.NETWORK, ud.PROCESS, 'check for updates with "dist-upgrade -s", the returncode is %d' % p1.returncode)
		ud.debug(ud.NETWORK, ud.PROCESS, 'stderr=%s' % stderr)
		ud.debug(ud.NETWORK, ud.INFO, 'stdout=%s' % stdout)

		new_packages = []
		upgraded_packages = []
		removed_packages = []
		for line in stdout.splitlines():
			line_split = line.split(' ')
			if line.startswith('Inst '):
				# upgrade:
				#	Inst univention-updater [3.1.1-5] (3.1.1-6.408.200810311159 192.168.0.10)
				# inst:
				#	Inst mc (1:4.6.1-6.12.200710211124 oxae-update.open-xchange.com)
				if len(line_split) > 3:
					if line_split[2].startswith('[') and line_split[2].endswith(']'):
						ud.debug(ud.NETWORK, ud.PROCESS, 'Added %s to the list of upgraded packages' % line_split[1])
						upgraded_packages.append((line_split[1], line_split[2].replace('[','').replace(']',''), line_split[3].replace('(','')))
					else:
						ud.debug(ud.NETWORK, ud.PROCESS, 'Added %s to the list of new packages' % line_split[1])
						new_packages.append((line_split[1], line_split[2].replace('(','')))
				else:
					ud.debug(ud.NETWORK, ud.WARN, 'unable to parse the update line: %s' % line)
					continue
			elif line.startswith('Remv '):
				if len(line_split) > 3:
					ud.debug(ud.NETWORK, ud.PROCESS, 'Added %s to the list of removed packages' % line_split[1])
					removed_packages.append((line_split[1], line_split[2].replace('(','')))
				elif len(line_split) > 2:
					ud.debug(ud.NETWORK, ud.PROCESS, 'Added %s to the list of removed packages' % line_split[1])
					removed_packages.append((line_split[1], 'unknown'))
				else:
					ud.debug(ud.NETWORK, ud.WARN, 'unable to parse the update line: %s' % line)
					continue

		return ( new_packages, upgraded_packages, removed_packages )

	def run_dist_upgrade( self ):
		cmd = 'export DEBIAN_FRONTEND=noninteractive;%s >>/var/log/univention/updater.log 2>&1' % cmd_dist_upgrade
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		stdout, stderr = p.communicate()
		return p.returncode, stdout, stderr


	def _iterate_versions(self, ver, start, end, parts, archs, server):
		'''Iterate through all versions of repositories between start and end.'''
		self.log.info('Searching %s:%r [%s..%s) in %s and %s', server, ver, start, end, parts, archs)
		(ver.major, ver.minor, ver.patchlevel) = (start.major, start.minor, start.patchlevel)

		# Workaround version of start << first available repository version,
		# e.g. repository starts at 2.3-0, but called with start=2.0-0
		findFirst = True
		while ver <= end and ver.major <= 99: # major
			try:
				while ver.minor <= 99:
					self.log.info('Checking version %s', ver.path())
					assert server.access(ver.path()) # minor
					findFirst = False
					found_patchlevel = True
					while found_patchlevel and ver.patchlevel <= ver.patchlevel_max:
						found_patchlevel = False
						for ver.part in parts: # part
							try:
								self.log.info('Checking version %s', ver.path())
								assert server.access(ver.path()) # patchlevel
								found_patchlevel = True
								for ver.arch in archs: # architecture
									try:
										code, size, content = server.access(ver.path())
										self.log.info('Found content: code=%d size=%d', code, size)
										if size >= MIN_GZIP:
											yield ver
									except DownloadError, e:
										ud.debug(ud.NETWORK, ud.ALL, "%s" % e)
								del ver.arch
							except DownloadError, e:
								ud.debug(ud.NETWORK, ud.ALL, "%s" % e)
						del ver.part

						if isinstance(ver.patch, basestring): # patchlevel not used
							break
						ver.patchlevel += 1
						if ver > end:
							break
					ver.minor += 1
					ver.patchlevel = ver.patchlevel_reset
					if ver > end:
						break
			except DownloadError, e:
				ud.debug(ud.NETWORK, ud.ALL, "%s" % e)
			if findFirst and ver.minor < 99:
				ver.minor += 1
				ver.patchlevel = ver.patchlevel_reset
			else:
				ver.major += 1
				ver.minor = 0

	def _iterate_version_repositories(self, start, end, parts, archs, dists=False):
		'''Iterate over all releases and return (server, version).'''
		self.log.info('Searching releases [%s..%s), dists=%s', start, end, dists)
		server = self.server
		if dists:
			struct = UCSRepoDist(prefix=self.server)
			for ver in self._iterate_versions(struct, start, end, parts, archs, server):
				yield server, ver
		struct = UCSRepoPool(prefix=self.server)
		for ver in self._iterate_versions(struct, start, end, parts, archs, server):
			yield server, ver

	def _iterate_security_repositories(self, start, end, parts, archs, hotfixes=False):
		'''Iterate over all security releases and return (server, version).'''
		self.log.info('Searching security [%s..%s), hotfix=%s', start, end, hotfixes)
		server = self.server
		struct = UCSRepoPool(prefix=self.server, patch="sec%(patchlevel)d", patchlevel_reset=1)
		for ver in self._iterate_versions(struct, start, end, parts, archs, server):
			yield server, ver
		if hotfixes:
			# hotfixes don't use patchlevel, but UCS_Version.__cmp__ uses them
			start.patchlevel = end.patchlevel = None
			struct = UCSRepoPool(prefix=self.server, patch="hotfixes", patchlevel_reset=None)
			for ver in self._iterate_versions(struct, start, end, parts, archs, server):
				yield server, ver

	def _iterate_errata_repositories(self, start, end, parts, archs):
		'''Iterate over all errata releases and return (server, version).'''
		self.log.info('Searching errata [%s..%s)', start, end)
		server = self.server
		struct = UCSRepoPool(prefix=self.server, patch="errata%(patchlevel)d", patchlevel_reset=1, patchlevel_max=999)
		for ver in self._iterate_versions(struct, start, end, parts, archs, server):
			yield server, ver


	def _iterate_component_repositories(self, components, start, end, archs, for_mirror_list=False, errata_level=None, iterate_errata=True):
		'''
		Iterate over all components and return (server, version).
		for_mirror_list shall be True if the code shall iterate over component
		repositories for mirror.list.
		'''

		self.log.info('Searching components %r [%s..%s)', components, start, end)
		# Components are ... different:
		for component in components:
			# server, port, prefix
			server = self._get_component_server(component, for_mirror_list=for_mirror_list)
			# parts
			parts = set(self.parts)
			if self.configRegistry.is_true('repository/online/component/%s/unmaintained' % (component)):
				parts.add("unmaintained")
			parts = ['%s/component' % (part,) for part in parts]
			# versions
			if start == end:
				versions = (start,)
			else:
				versions = self._get_component_versions(component, start, end)

			self.log.info('Component %s from %s versions %r', component, server, versions)
			for version in versions:
				# Get a list of all availble errata updates for this component and version

				# The errata level for components is bound to the minor version
				patch_names = [component]
				if iterate_errata:
					if errata_level:
						patch_names = ['%s-errata%s' % (component, errata_level)]
					elif not for_mirror_list:
						# see below for mirror.list handling
						errata_level = self.get_component_erratalevel(component, version)
						patch_names += ['%s-errata%d' % (component, x) for x in range(1, errata_level + 1)]

				for patch_name in patch_names:
					try:
						for (UCSRepoPoolVariant, subarchs) in ((UCSRepoPool, archs), (UCSRepoPoolNoArch, ('all',))):
							struct = UCSRepoPoolVariant(prefix=server, patch=patch_name)
							for ver in self._iterate_versions(struct, version, version, parts, subarchs, server):
								yield server, ver
					except (ConfigurationError, ProxyError), e:
						# if component is marked as required (UCR variable "version" contains "current")
						# then raise error, otherwise ignore it
						if component in self.get_current_components():
							raise

				# Go through all errata level for this component and break if the first errata level is missing
				if for_mirror_list:
					for i in xrange(1, 1000):
						valid = False
						patch_name = '%s-errata%s' % (component, i)
						for (UCSRepoPoolVariant, subarchs) in ((UCSRepoPool, archs), (UCSRepoPoolNoArch, ('all',))):
							struct = UCSRepoPoolVariant(prefix=server, patch=patch_name)
							for ver in self._iterate_versions(struct, version, version, parts, subarchs, server):
								yield server, ver
								valid = True
						if not valid:
							break


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
			clean = self.configRegistry.is_true('online/repository/clean', False)

		if not start:
			start = UCS_Version( ( self.version_major, 0, 0 ) )

		if not end:
			end = UCS_Version( ( self.version_major, self.version_minor, self.patchlevel ) )

		archs = ['all'] + self.architectures
		result = []

		for server, ver in self._iterate_version_repositories(start, end, self.parts, archs, dists):
			result.append( ver.deb() )
			if isinstance(ver, UCSRepoPool) and ver.arch == archs[-1]: # after architectures but before next patch(level)
				if clean:
					result.append( ver.clean() )
				if self.sources:
					ver.arch = "source"
					try:
						code, size, content = server.access(ver.path("Sources.gz"))
						if size >= MIN_GZIP:
							result.append(ver.deb("deb-src"))
					except DownloadError, e:
						ud.debug(ud.NETWORK, ud.ALL, "%s" % e)

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
			clean = self.configRegistry.is_true('online/repository/clean', False)

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

		archs = ['all'] + self.architectures
		result = []

		for server, ver in self._iterate_security_repositories(start, end, self.parts, archs, self.hotfixes):
			result.append( ver.deb() )
			if ver.arch == archs[-1]: # after architectures but before next patch(level)
				if clean:
					result.append( ver.clean() )
				if self.sources:
					ver.arch = "source"
					try:
						code, size, content = server.access(ver.path("Sources.gz"))
						if size >= MIN_GZIP:
							result.append(ver.deb("deb-src"))
					except DownloadError, e:
						ud.debug(ud.NETWORK, ud.ALL, "%s" % e)

		return '\n'.join(result)

	def print_errata_repositories( self, clean = False, start = None, end = None, all_errata_updates = False ):
		'''Return a string of Debian repository statements for all UCS errata
		updates for UCS versions between start and end.

		Default for start: (major, minor)
		Default for end: (major, minor)
		With clean=True, online/repository/clean controls if additional clean statements for apt-mirror are added.
		For all_errata_updates=True, all available instead of all needed statements for errata updates are returned.
		'''
		# NOTE: Here "patchlevel" is used for the "erratalevel"
		if not self.online_repository:
			return ''

		if clean:
			clean = self.configRegistry.is_true('online/repository/clean', False)

		if start:
			start = copy.copy(start)
			start.patchlevel = 1 # errata updates start with 'errata1'
		else:
			start = UCS_Version( ( self.version_major, self.version_minor, 1 ) )
		# Explicit override of start for point updates (Bug #25616)
		if not all_errata_updates:
			try:
				skip = self.configRegistry['repository/online/errata/start']
				start.patchlevel = int(skip)
			except (KeyError, TypeError, ValueError), e:
				pass

		# Hopefully never more than 999 errata updates
		max = bool(all_errata_updates) and 1000 or self.erratalevel
		if end:
			end = copy.copy(end)
			end.patchlevel = max
		else:
			end = UCS_Version( (self.version_major, self.version_minor, max) )

		archs = ['all'] + self.architectures
		result = []

		for server, ver in self._iterate_errata_repositories(start, end, self.parts, archs):
			result.append( ver.deb() )
			if ver.arch == archs[-1]: # after architectures but before next patch(level)
				if clean:
					result.append( ver.clean() )
				if self.sources:
					ver.arch = "source"
					try:
						code, size, content = server.access(ver.path("Sources.gz"))
						if size >= MIN_GZIP:
							result.append(ver.deb("deb-src"))
					except DownloadError, e:
						ud.debug(ud.NETWORK, ud.ALL, "%s" % e)

		return '\n'.join(result)

	def _get_component_server(self, component, for_mirror_list=False):
		'''
        Return UCSServer as configures via UCR.
        If for_repo_server=True then the

        CS = value of repository/online/component/%s/server
        MS = value of repository/mirror/server
        RS = value of repository/online/server
        Y = value is "True"
        N = value is "False"
        - = value is unset or no entry
        ? = value is irrelevant

                     component  component    component |        R E S U L T
        isRepoServer enabled    localmirror  server    | sources.list  mirror.list
        ===============================================|==========================
            N           N          N           -       |      -             -
            N           Y          ?           -       |      RS            -
            N           Y          ?           CS      |      CS            -
        --------------------------------------------------------------------------
            Y           N          N           ?       |      -             -
            Y           N          Y           -       |      -             MS
            Y           N          Y           CS      |      -             CS
            Y           Y          N           -       |      MS            -
            Y           Y          N           CS      |      CS            -
            Y           Y          Y           -       |      RS            MS
            Y           Y          Y           CS      |      RS            CS
        --------------------------------------------------------------------------
            Y           N =======>(-)          -       |      -             -
            Y           Y =======>(-)          -       |      RS            MS
            Y           Y =======>(-)          CS      |      RS            CS

        if repository/online/component/%s/localmirror is unset, then the value of
        repository/online/component/%s will be used to achieve backward compatibility.
		'''

		if not self.is_repository_server:
			server = self.configRegistry.get('repository/online/component/%s/server' % component, self.repository_server)
			port = self.configRegistry.get('repository/online/component/%s/port' % component, self.repository_port)
		else:
			m_server = self.configRegistry.get('repository/mirror/server', None)
			m_port = self.configRegistry.get('repository/mirror/port', self.repository_port)
			c_enabled = self.configRegistry.is_true('repository/online/component/%s' % component, False)
			c_localmirror = self.configRegistry.is_true('repository/online/component/%s/localmirror' % component, c_enabled)

			if not for_mirror_list:
				# server/port for sources.list

				if c_enabled and c_localmirror:
					server = self.repository_server
					port   = self.repository_port

				elif c_enabled and not c_localmirror:
					server = self.configRegistry.get('repository/online/component/%s/server' % component, m_server)
					port   = self.configRegistry.get('repository/online/component/%s/port' % component,   m_port)

				else:
					# if component is not enabled, then why is this method called?
					raise CannotResolveComponentServerError(component, for_mirror_list)

			else:
				# server/port for mirror.list

				if c_localmirror:
					server = self.configRegistry.get('repository/online/component/%s/server' % component, m_server)
					port   = self.configRegistry.get('repository/online/component/%s/port' % component,   m_port)

				else:
					# if component is not enabled for mirroring, then why is this method called?
					raise CannotResolveComponentServerError(component, for_mirror_list)

		prefix = self.configRegistry.get('repository/online/component/%s/prefix' % component, '')
		username = self.configRegistry.get('repository/online/component/%s/username' % component, None)
		password = self.configRegistry.get('repository/online/component/%s/password' % component, None)

		user_agent = self._get_user_agent_string()

		server = UCSHttpServer(server=server, port=port, prefix='', username=username, password=password, user_agent=user_agent)
		try:
			# if prefix.lower() == 'none' ==> use no prefix
			if prefix and prefix.lower() == 'none':
				try:
					assert server.access('')
				except DownloadError, e:
					uri, code = e
					raise ConfigurationError(uri, 'absent prefix forced - component %s not found: %s' % (str(component), str(uri)))
			else:
				# build list of possible repository prefixes
				test_server_list = []
				test_server_list.append( server + '/univention-repository/' )    # first test
				if self.repository_prefix:
					test_server_list.append( server + self.repository_prefix )   # second test (only if repository_prefix is defined)
				test_server_list.append( server )                                # last guess :-)

				for testserver in test_server_list:
					if prefix:
						testserver = testserver + prefix  # append prefix if defined

					try:
						assert testserver.access('')
						server = testserver               # testserver is valid ==> save it
						break                             # server is valid ==> stop loop here; "else" statement will not match
					except DownloadError, e:
						ud.debug(ud.NETWORK, ud.ALL, "%s" % e)
						uri, code = e
				else:
					raise ConfigurationError(uri, 'non-existing component prefix: %s' % (str(uri)))

		except ConfigurationError, e:
			if self.check_access:
				raise
		return server

	def _get_component_versions(self, component, start, end):
		'''
		Return configured versions for component.
		 'current'=required component; must exist for requested version.
		 ''=optional component; used when exists for requested version.
		 'major.minor'=use exactly this version.
		Can be a space/comma separated combination of above.
		'''
		str = self.configRegistry.get('repository/online/component/%s/version' % component, '')
		versions = set()
		for version in RE_SPLIT_MULTI.split(str):
			if version in ('current', ''): # all from start to end, defaults to same major
				# Cache releases because it is network expensive
				try: mm_versions
				except NameError:
					mm_versions = self._releases_in_range(start, end)
				versions |= set(mm_versions)
			else:
				if '-' in version:
					version = UCS_Version(version)
				else:
					version = UCS_Version('%s-0' % version)
				versions.add(version)
		return versions

	def get_component_repositories(self, component, versions, clean=False, debug=True, for_mirror_list=False, errata_level=None):
		'''Return array of Debian repository statements for requested component.
		   With clean=True, additional clean statements for apt-mirror are added.
		   Component repositories for mirror.list are returned if for_mirror_list=True.
		'''
		archs = ['all'] + self.architectures
		result = []

		if errata_level > 999:
			return result

		cleanComponent = False
		if clean:
			cleanComponent = self.configRegistry.is_true('repository/online/component/%s/clean' % component, False)

		# Sanitize versions: UCS_Version() and Major.Minor
		versions_mmp = set()
		for version in versions:
			if isinstance(version, basestring):
				if '-' in version:
					version = UCS_Version(version)
				else:
					version = UCS_Version('%s-0' % version)
			elif isinstance(version, UCS_Version):
				version = copy.copy(version)
			else:
				raise TypeError('Not a UCS Version', version)
			version.patchlevel = 0 # component dont use the patchlevel
			versions_mmp.add(version)

		for version in versions_mmp:
			# Show errata updates for latest version only
			iterate_errata = version == max(versions_mmp)

			for server, ver in self._iterate_component_repositories([component], version, version, archs, for_mirror_list=for_mirror_list, errata_level=errata_level, iterate_errata=iterate_errata):
				result.append( ver.deb() )
				if ver.arch == archs[-1]: # after architectures but before next patch(level)
					if clean:
						result.append( ver.clean() )
					if self.sources:
						ver.arch = "source"
						try:
							code, size, content = server.access(ver.path("Sources.gz"))
							if size >= MIN_GZIP:
								result.append(ver.deb("deb-src"))
						except DownloadError, e:
							ud.debug(ud.NETWORK, ud.ALL, "%s" % e)

		return result

	def _releases_in_range(self, start=None, end=None):
		'''Find all $major.$minor releases between start [$major.0] and end [$major.$minor] including.'''
		if not start:
			start = UCS_Version((self.version_major, 0, 0))

		if not end:
			end = UCS_Version((self.version_major, self.version_minor, self.patchlevel))

		result = []

		version = UCSRepoPool(prefix=self.server)
		version.minor = start.minor
		version.patchlevel = 0
		foundFirst = False
		for version.major in range(start.major, min(99, end.major + 1)):
			while version <= end:
				try:
					assert self.server.access(version.path())
					foundFirst = True
					result.append(UCS_Version(version))
				except DownloadError:
					if foundFirst or version.minor > 99:
						break
				version.minor += 1
			version.minor = 0

		self.log.info('Releases [%s..%s) are %r', start, end, result)
		return result

	def print_component_repositories(self, clean=False, start=None, end=None, for_mirror_list=False):
		'''Return a string of Debian repository statements for all enabled components.
		With clean=True, repository/online/component/%s/clean controls if additional clean statements for apt-mirror are added.
		With for_mirror_list=True, component entries for mirror.list will be returned, otherwise component entries for local sources.list.
		'''
		if not self.online_repository:
			return ''

		if clean:
			clean = self.configRegistry.is_true('online/repository/clean', False)

		result = []
		for component in self.get_components(only_localmirror_enabled=for_mirror_list):
			try:
				versions = self._get_component_versions(component, start, end)
				repos = self.get_component_repositories(component, versions, clean, for_mirror_list=for_mirror_list)
				if versions and not repos:
					server = self._get_component_server(component)
					version = ','.join(map(str, versions))
					uri = server.join('%s/component/%s/' % (version, component))
					raise ConfigurationError(uri, 'component not found')
				result += repos
			except ConfigurationError, e:
				# just log configuration errors and continue
				result.append('# %s: %s' % (e, component))
		return '\n'.join(result)

	def _get_user_agent_string(self):
		# USER_AGENT='updater/identify - version/version-version/patchlevel errata version/erratalevel - uuid/system - uuid/license'
		# USER_AGENT='UCS upater - 3.1-0 errata28 - 77e6406d-7a3e-40b3-a398-81cf119c9ef7 - 4c52d2da-d04d-4b05-a593-1974ee851fc8'
		# USER_AGENT='UCS upater - 3.1-0 errata28 - 77e6406d-7a3e-40b3-a398-81cf119c9ef7 - 00000000-0000-0000-0000-000000000000'
		return '%s - %s-%s errata%s - %s - %s - %s' % ( self.configRegistry.get('updater/identify', 'UCS'),
								self.configRegistry.get('version/version'), self.configRegistry.get('version/patchlevel'),
								self.configRegistry.get('version/erratalevel'),
								self.configRegistry.get('uuid/system', '00000000-0000-0000-0000-000000000000'),
								self.configRegistry.get('uuid/license', '00000000-0000-0000-0000-000000000000'),
								','.join(self.configRegistry.get('repository/app_center/installed', '').split('-')) )

	@staticmethod
	def call_sh_files(scripts, logname, *args):
		'''Get pre- and postup.sh files and call them in the right order.
		> u = UniventionUpdater()
		> ver = u.current_version
		> struct = u._iterate_version_repositories(ver, ver, u.parts, u.architectures)
		> struct = u._iterate_component_repositories(['ucd'], ver, ver, u.architectures)
		> sec_ver = UCS_Version((u.version_major, u.version_minor, 1))
		> struct = u._iterate_security_repositories(sec_ver, sec_ver, u.parts, u.architectures)
		> scripts = u.get_sh_files(struct)
		> next_ver = u.get_next_version(u.current_version)
		> for phase, order in u.call_sh_files(scripts, '/var/log/univention/updater.log', next_ver):
		>   if (phase, order) == ('update', 'main'):
		>     ...
		'''
		# create temporary directory for scripts
		tempdir = tempfile.mkdtemp()
		atexit.register(shutil.rmtree, tempdir, ignore_errors=True)

		def call(*cmd):
			"""Execute script."""
			commandline = ' '.join(["'%s'" % a.replace("'", "'\\''") for a in cmd])
			ud.debug(ud.PROCESS, ud.INFO, "Calling %s" % commandline)
			p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
			tee = subprocess.Popen(('tee', '-a', logname), stdin=p.stdout)
			# Order is important! See bug #16454
			tee.wait()
			p.wait()
			return p.returncode

		# download scripts
		yield "update", "pre"
		main = {'preup': [], 'postup': []}
		comp = {'preup': [], 'postup': []}
		# save scripts to temporary files
		for server, struct, phase, path, script in scripts:
			if phase is None:
				continue
			assert script is not None
			uri = server.join(path)
			fd, name = tempfile.mkstemp(suffix='.sh', prefix=phase, dir=tempdir)
			try:
				size = os.write(fd, script)
				os.chmod(name, 0744)
				if size == len(script):
					ud.debug(ud.NETWORK, ud.INFO, "%s saved to %s" % (uri, name))
					if struct.part.endswith('/component'):
						comp[phase].append((name, str(struct.patch)))
					else:
						main[phase].append((name, str(struct.patch)))
					continue
			finally:
				os.close(fd)
			ud.debug(ud.NETWORK, ud.ERROR, "Error saving %s to %s" % (uri, name))

		# call component/preup.sh pre $args
		yield "preup", "pre"
		for (script, patch) in comp['preup']:
			if call(script, 'pre', *args) != 0:
				raise PreconditionError('preup', 'pre', patch, script)

		# call $next_version/preup.sh
		yield "preup", "main"
		for (script, patch) in main['preup']:
			if call(script, *args) != 0:
				raise PreconditionError('preup', 'main', patch, script)

		# call component/preup.sh post $args
		yield "preup", "post"
		for (script, patch) in comp['preup']:
			if call(script, 'post', *args) != 0:
				raise PreconditionError('preup', 'post', patch, script)

		# call $update/commands/distupgrade or $update/commands/upgrade
		yield "update", "main"

		# call component/postup.sh pos $args
		yield "postup", "pre"
		for (script, patch) in comp['postup']:
			if call(script, 'pre', *args) != 0:
				raise PreconditionError('postup', 'pre', patch, script)

		# call $next_version/postup.sh
		yield "postup", "main"
		for (script, patch) in main['postup']:
			if call(script, *args) != 0:
				raise PreconditionError('postup', 'main', patch, script)

		# call component/postup.sh post $args
		yield "postup", "post"
		for (script, patch) in comp['postup']:
			if call(script, 'post', *args) != 0:
				raise PreconditionError('postup', 'post', patch, script)

		# clean up
		yield "update", "post"

	@staticmethod
	def get_sh_files(repositories, verify=False):
		'''Return all preup- and postup-scripts of repositories.
		repositories: iteratable (server, struct)s
		Returns: iteratable (server, struct, phase, path, script)
		'''
		for server, struct in repositories:
			for phase in ('preup', 'postup'):
				name = '%s.sh' % phase
				path = struct.path(name)
				ud.debug(ud.ADMIN, ud.ALL, "Accessing %s" % path)
				try:
					_code, _size, script = server.access(path, get=True)
					# Bug #37031: dansguarding is lying and returns 200 even for blocked content
					if not script.startswith('#!'):
						raise ProxyError("Failed to fetch '%s' - maybe blocked by a proxy?")
					if verify and struct >= UCS_Version((3, 2, 0)):
						path_gpg = path + '.gpg'
						try:
							_code, _size, signature = server.access(path_gpg, get=True)
							if not signature.startswith("-----BEGIN PGP SIGNATURE-----"):
								raise ProxyError("Failed to fetch '%s' - maybe blocked by a proxy?")
						except DownloadError:
							raise VerificationError(path_gpg, "Signature download failed")
						error = verify_script(script, signature)
						if error is not None:
							raise VerificationError(path, "Invalid signature: %s" % error)
						yield server, struct, None, path_gpg, signature
					yield server, struct, phase, path, script
				except DownloadError, e:
					ud.debug(ud.NETWORK, ud.ALL, "%s" % e)

class LocalUpdater(UniventionUpdater):
	"""Direct file access to local repository."""
	def __init__(self):
		UniventionUpdater.__init__(self)
		self.log = logging.getLogger('updater.LocalUpdater')
		self.log.addHandler(NullHandler())
		repository_path = self.configRegistry.get('repository/mirror/basepath', '/var/lib/univention-repository')
		self.server = UCSLocalServer("%s/mirror/" % repository_path)

__UPDATER_LOCK_FILE_NAME='/var/lock/univention-updater'
def updater_lock_acquire(timeout=0):
	'''Acquire the updater-lock.
	Returns 0 if it could be acquired within <timeout> seconds.
	Returns a value >= 1 if locked by parent.
	Returns LockingError otherwise.'''
	deadline = time.time() + timeout
	my_pid = "%d\n" % os.getpid()
	parent_pid = "%d\n" % os.getppid()
	while True:
		try:
			lock_fd = os.open(__UPDATER_LOCK_FILE_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0644)
			bytes_written = os.write(lock_fd, my_pid)
			assert bytes_written == len(my_pid)
			os.close(lock_fd)
			return 0
		except OSError, error:
			if error.errno == errno.EEXIST:
				try:
					lock_fd = os.open(__UPDATER_LOCK_FILE_NAME, os.O_RDONLY | os.O_EXCL)
					try:
						lock_pid = os.read(lock_fd, 11) # sizeof(s32) + len('\n')
					finally:
						os.close(lock_fd)
					if my_pid == lock_pid:
						return 0
					if parent_pid == lock_pid: # u-repository-* called from u-updater
						return 1
					try:
						lock_pid = lock_pid.strip() or '?'
						lock_pid = int(lock_pid)
						os.kill(lock_pid, 0)
					except ValueError, e:
						msg = 'Invalid PID %s in lockfile %s.' % (lock_pid, __UPDATER_LOCK_FILE_NAME)
						raise LockingError(msg)
					except OSError, error:
						if error.errno == errno.ESRCH:
							print >>sys.stderr, 'Stale PID %s in lockfile %s, removing.' % (lock_pid, __UPDATER_LOCK_FILE_NAME)
							os.remove(__UPDATER_LOCK_FILE_NAME)
							continue # redo acquire
					# PID is valid and process is still alive...
				except OSError, error:
					pass
				if time.time() > deadline:
					if timeout > 0:
						msg = 'Timeout: still locked by PID %s. Check lockfile %s' % (lock_pid, __UPDATER_LOCK_FILE_NAME)
					else:
						msg = 'Locked by PID %s. Check lockfile %s' % (lock_pid or '?', __UPDATER_LOCK_FILE_NAME)
					raise LockingError(msg)
				else:
					time.sleep(1)
			else:
				raise

def updater_lock_release(lock):
	'''Release the updater-lock.
	Returns True if it has been unlocked (or decremented when nested).
	Returns False if it was already unlocked.'''
	if lock > 0:
		# parent process still owns the lock, do nothing and just return success
		return True
	try:
		os.remove(__UPDATER_LOCK_FILE_NAME)
		return True
	except OSError, error:
		if error.errno == errno.ENOENT:
			return False
		else:
			raise

if __name__ == '__main__':
	import doctest
	doctest.testmod()
