# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
#  main configuration registry classes
#
# Copyright 2004-2012 Univention GmbH
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

import os
import sys
import re
import string
import cPickle
import copy
import subprocess
import fcntl
import pwd
import grp
import time
import errno
from debhelper import parseRfc822
from pipes import quote as escape_value

variable_pattern = re.compile('@%@([^@]+)@%@')
variable_token = re.compile('@%@')
execute_token = re.compile('@!@')
warning_pattern = re.compile('(UCRWARNING|BCWARNING|UCRWARNING_ASCII)=(.+)')
replog_file = '/var/log/univention/config-registry.replog'
file_dir = '/etc/univention/templates/files'
script_dir = '/etc/univention/templates/scripts'
module_dir = '/etc/univention/templates/modules'
info_dir = '/etc/univention/templates/info'

invalid_key_chars = re.compile('[\\r\\n\!\"\§\$\%\&\(\)\[\]\{\}\=\?\`\+\#\'\,\;\<\>\\\]')
invalid_value_chars = '\r\n'
shell_valid_key_chars = string.ascii_letters + string.digits + '_'

warning_text = '''Warning: This file is auto-generated and might be overwritten by
         univention-config-registry.
         Please edit the following file(s) instead:
Warnung: Diese Datei wurde automatisch generiert und kann durch
         univention-config-registry überschrieben werden.
         Bitte bearbeiten Sie an Stelle dessen die folgende(n) Datei(en):'''

class StrictModeException(Exception):
	pass

def warning_string(prefix='# ', width=80, srcfiles=set(), enforce_ascii=False):
	res = []

	for line in warning_text.split('\n'):
		if enforce_ascii:
			line = replaceUmlaut(line).encode('ascii', 'replace')
		res.append(prefix+line)
	res.append(prefix)

	for srcfile in srcfiles:
		if enforce_ascii:
			srcfile = srcfile.encode('ascii', 'replace')
		res.append(prefix+'\t%s' % srcfile)
	res.append(prefix)

	return "\n".join(res)

SCOPE = ['normal', 'ldap', 'schedule', 'forced', 'custom']
class ConfigRegistry( dict ):
	"""
	Merged persistent value store.
	This is a merged view of several sub-registries.
	"""
	NORMAL, LDAP, SCHEDULE, FORCED, CUSTOM = range( 5 )
	PREFIX = '/etc/univention'
	BASES = { NORMAL : 'base.conf', LDAP : 'base-ldap.conf', SCHEDULE : 'base-schedule.conf', FORCED : 'base-forced.conf' }

	def __init__( self, filename = None, write_registry = NORMAL ):
		if os.getenv( 'UNIVENTION_BASECONF' ):
			self.file = os.getenv( 'UNIVENTION_BASECONF' )
		elif filename:
			self.file = filename
		else:
			self.file = None
		if self.file:
			self._write_registry = ConfigRegistry.CUSTOM
		else:
			self._write_registry = write_registry
		self._registry = {}
		if not self.file:
			self._registry[ ConfigRegistry.NORMAL ] = self._create_registry( ConfigRegistry.NORMAL )
			self._registry[ ConfigRegistry.LDAP ] = self._create_registry( ConfigRegistry.LDAP )
			self._registry[ ConfigRegistry.SCHEDULE ] = self._create_registry( ConfigRegistry.SCHEDULE )
			self._registry[ ConfigRegistry.FORCED ] = self._create_registry( ConfigRegistry.FORCED )
			self._registry[ ConfigRegistry.CUSTOM ] = {}
		else:
			self._registry[ ConfigRegistry.NORMAL ] = {}
			self._registry[ ConfigRegistry.LDAP ] = {}
			self._registry[ ConfigRegistry.SCHEDULE ] = {}
			self._registry[ ConfigRegistry.FORCED ] = {}
			self._registry[ ConfigRegistry.CUSTOM ] = self._create_registry( ConfigRegistry.CUSTOM )

	def _create_registry( self, reg ):
		if reg == ConfigRegistry.CUSTOM:
			return _ConfigRegistry( file = self.file )
		else:
			return _ConfigRegistry( file = os.path.join( ConfigRegistry.PREFIX, ConfigRegistry.BASES[ reg ] ) )
	def load( self ):
		for reg in self._registry.values():
			if isinstance( reg, _ConfigRegistry ):
				reg.load()
		strict = self.is_true('ucr/encoding/strict')
		for reg in self._registry.values():
			if isinstance( reg, _ConfigRegistry ):
				reg.strict_encoding = strict

	def save( self ):
		registry = self._registry[self._write_registry]
		registry.save()

	def lock( self ):
		registry = self._registry[self._write_registry]
		registry.lock()

	def unlock( self ):
		registry = self._registry[self._write_registry]
		registry.unlock()

	def __delitem__( self, key ):
		registry = self._registry[self._write_registry]
		del registry[key]

	def __getitem__( self, key ):
		return self.get( key )

	def __setitem__( self, key, value ):
		registry = self._registry[self._write_registry]
		registry[key] = value

	def __contains__( self, key ):
		for reg in (ConfigRegistry.FORCED, ConfigRegistry.SCHEDULE, ConfigRegistry.LDAP, ConfigRegistry.NORMAL, ConfigRegistry.CUSTOM):
			registry = self._registry[reg]
			if key in registry:
				return True
		return False

	def iterkeys(self):
		merge = self._merge()
		for key in merge:
			yield key

	__iter__ = iterkeys

	def get( self, key, default = None, getscope = False ):
		for reg in (ConfigRegistry.FORCED, ConfigRegistry.SCHEDULE, ConfigRegistry.LDAP, ConfigRegistry.NORMAL, ConfigRegistry.CUSTOM):
			try:
				registry = self._registry[reg]
				if key not in registry: # BUG: _ConfigRegistry[key] does not raise a KeyError for unset keys, but returns ''
					continue
				value = registry[key]
				if getscope:
					return (reg, value)
				else:
					return value
			except KeyError:
				continue
		return default

	def has_key( self, key, write_registry_only = False ):
		if write_registry_only:
			registry = self._registry[self._write_registry]
			return key in registry
		else:
			return key in self

	def _merge( self, getscope=False ):
		merge = {}
		for reg in (ConfigRegistry.FORCED, ConfigRegistry.SCHEDULE, ConfigRegistry.LDAP, ConfigRegistry.NORMAL, ConfigRegistry.CUSTOM):
			registry = self._registry[reg]
			if not isinstance(registry, _ConfigRegistry):
				continue
			for key, value in registry.items():
				if key not in merge:
					if getscope:
						merge[key] = (reg, value)
					else:
						merge[key] = registry[key]
		return merge

	def items( self, getscope=False ):
		merge = self._merge(getscope=getscope)
		return merge.items()

	def keys( self ):
		merge = self._merge()
		return merge.keys()

	def values( self ):
		merge = self._merge()
		return merge.values()

	def __str__( self ):
		merge = self._merge()
		return '\n'.join(['%s: %s' % (key, val) for key, val in merge.items()])

	def is_true(self, key, default = False):
		"""Return if the strings value of key is considered as true."""
		if key in self:
			return self.get(key).lower() in ('yes', 'true', '1', 'enable', 'enabled', 'on')
		return default

	def is_false(self, key, default = False):
		"""Return if the strings value of key is considered as false."""
		if key in self:
			return self.get(key).lower() in ('no', 'false', '0', 'disable', 'disabled', 'off')
		return default

class _ConfigRegistry( dict ):
	"""
	Persistent value store.
	This is a single value store using a text file.
	"""
	def __init__(self, file = None):
		dict.__init__( self )
		if file:
			self.file = file
		else:
			self.file = '/etc/univention/base.conf'
		self.__create_base_conf()
		self.backup_file = self.file + '.bak'
		self.lock_filename = self.file + '.lock'
		self.strict_encoding = False # will be set by <ConfigRegistry> for each <_ConfigRegistry> - <True> means the backend files are valid UTF-8 and should stay that way --> only accept valid UTF-8

	def load(self):
		self.clear()
		import_failed = False
		try:
			fp = open(self.file, 'r')
		except EnvironmentError:
			import_failed = True

		if import_failed or len(fp.readlines()) < 3: # only comment or nothing
			import_failed = True # not set if file is to short
			try:
				fp = open(self.backup_file, 'r')
			except EnvironmentError:
				return

		fp.seek(0)
		for line in fp.readlines():
			line = re.sub(r'^[^:]*#.*$', "", line)
			if line == '':
				continue
			if line.find(': ') == -1:
				continue

			key, value = line.split(': ', 1)
			value = value.strip()
			if len(value) == 0: #if variable was set without an value
				value = ''

			self[key] = value
		fp.close()

		if import_failed:
			self.__save_file(self.file)

	def __create_base_conf( self ):
		if not os.path.exists( self.file ):
			try:
				fd = os.open( self.file, os.O_CREAT | os.O_RDONLY, 0644 )
				os.close( fd )
			except EnvironmentError:
				print >> sys.stderr, "E: the configuration file '%s' does not exist und could not be created" % (self.file,)
				exception_occured()

	def __save_file(self, filename):
		try:
			# open temporary file for writing
			fp = open(filename, 'w')
			# write data to file
			fp.write('# univention_ base.conf\n\n')
			fp.write(self.__str__())
			# flush (meta)data
			fp.flush()
			os.fsync(fp.fileno())
			# close fd
			fp.close()
		except EnvironmentError, ex:
			# suppress certain errors
			if ex.errno != errno.EACCES:
				raise

	def save(self):
		for filename in (self.backup_file, self.file):
			self.__save_file(filename)

	def lock(self):
		self.lock_file = open(self.lock_filename, "a+")
		fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)

	def unlock(self):
		self.lock_file.close()

	def __getitem__(self, key):
		try:
			return dict.__getitem__( self, key )
		except KeyError:
			return ''

	def __setitem__(self, key, value):
		if self.strict_encoding:
			try:
				key.decode('UTF-8') # only accept valid UTF-8 encoded bytes
			except UnicodeError:
				raise StrictModeException('variable name is not UTF-8 encoded')
			try:
				value.decode('UTF-8') # only accept valid UTF-8 encoded bytes
			except UnicodeError:
				raise StrictModeException('value is not UTF-8 encoded')
		return dict.__setitem__(self, key, value)

	def removeInvalidChars(self, seq):
		for letter in invalid_value_chars:
			seq = seq.replace(letter,'')
		return seq

	def __str__(self):
		return '\n'.join(['%s: %s' % (key, self.removeInvalidChars(val)) for
			key, val in sorted(self.items())])

def directoryFiles(dir):
	"""Return a list of all files below the given directory."""
	all = []
	def _walk(all, dirname, files):
		for file in files:
			f = os.path.join(dirname, file)
			if os.path.isfile(f):
				all.append(f)
	os.path.walk(dir, _walk, all)
	return all

# Bug #23202: For UCS-2.x use /usr/bin/python2.4, but after upgrade to UCS-3.x use /usr/bin/python2.6
if sys.version_info[0:2] < (2, 6):
	__python_executable = '/usr/bin/python2.6'
else:
	__python_executable = sys.executable
def filter(template, dir, srcfiles=set(), opts = {}):
	"""Process a template file: susbstitute variables."""
	while True:
		i = variable_token.finditer(template)
		try:
			start = i.next()
			end = i.next()
			name = template[start.end():end.start()]

			if name in dir:
				value = dir[name]
			else:
				match = warning_pattern.match(name)
				if match:
					mode, prefix = match.groups()
					if mode == "UCRWARNING_ASCII":
						value = warning_string(prefix, srcfiles=srcfiles, enforce_ascii=True)
					else:
						value = warning_string(prefix, srcfiles=srcfiles)
				else:
					value = ''

			if isinstance(value, (list, tuple)):
				value = value[0]
			template = template[:start.start()]+value+template[end.end():]
		except StopIteration:
			break

	while True:
		i = execute_token.finditer(template)
		try:
			start = i.next()
			end = i.next()

			p = subprocess.Popen((__python_executable, ), stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
			child_stdin, child_stdout = p.stdin, p.stdout
			child_stdin.write('# -*- coding: utf-8 -*-\n')
			child_stdin.write('import univention.config_registry\n')
			child_stdin.write('configRegistry = univention.config_registry.ConfigRegistry()\n')
			child_stdin.write('configRegistry.load()\n')
			# for compatibility
			child_stdin.write('baseConfig = configRegistry\n')
			child_stdin.write(template[start.end():end.start()])
			child_stdin.close()
			value = child_stdout.read()
			child_stdout.close()
			template = template[:start.start()] + value + template[end.end():]

		except StopIteration:
			break

	return template

def runScript(script, arg, changes):
	"""
	Execute script with command line arguments using a shell and pass changes on STDIN.
	For each changed variable a line with the 'name of the variable', the 'old value', and the 'new value' are passed seperated by '@%@'.
	"""
	diff = []
	for key, value in changes.items():
		if value and len(value) > 1 and value[0] and value[1]:
			diff.append('%s@%%@%s@%%@%s\n' % (key, value[0], value[1]))

	p = subprocess.Popen(script + " " + arg, shell=True, stdin=subprocess.PIPE, close_fds=True)
	p.communicate(''.join(diff))

def runModule(modpath, arg, ucr, changes):
	"""loads the python module that MUST be located in 'module_dir' or any subdirectory."""
	arg2meth = { 'generate': lambda obj: getattr(obj, 'handler'),
		     'preinst':  lambda obj: getattr(obj, 'preinst'),
		     'postinst': lambda obj: getattr(obj, 'postinst') }
	# temporarily prepend module_dir to load path
	sys.path.insert( 0, module_dir )
	module_name = os.path.splitext( modpath )[ 0 ]
	try:
		module = __import__( module_name.replace( os.path.sep, '.' ) )
		arg2meth[arg](module)(ucr, changes)
	except (AttributeError, ImportError), ex:
		print >> sys.stderr, ex
	del sys.path[ 0 ]

class configHandler(object):
	"""Base class of all config handlers."""
	variables = set()

class configHandlerDiverting(configHandler):
	"""File diverting config handler."""

	def __init__(self, to_file):
		self.to_file = os.path.join('/', to_file)
		self.user = None
		self.group = None
		self.mode = None

	def __hash__(self):
		return hash(self.to_file)

	def __cmp__(self, other):
		return cmp(self.to_file, other.to_file)

	def _set_perm(self, st):
		"""Set file permissions."""
		if self.user or self.group or self.mode:
			if self.mode:
				os.chmod(self.to_file, self.mode)
			if self.user and self.group:
				os.chown(self.to_file, self.user, self.group)
			elif self.user:
				os.chown(self.to_file, self.user, 0)
			elif self.group:
				os.chown(self.to_file, 0, self.group)
		elif st:
			os.chmod(self.to_file, st[0])

	def _call_silent(self, *cmd):
		"""Call command with stdin, stdout, and stderr redirected from/to devnull."""
		null = open(os.path.devnull, 'rw')
		try:
			# tell possibly wrapped dpkg-divert to really do the work
			env = dict(os.environ)
			env['DPKG_MAINTSCRIPT_PACKAGE'] = 'univention-config'
			return subprocess.call(cmd, stdin=null, stdout=null, stderr=null, env=env)
		finally:
			null.close()

	def need_divert(self):
		"""Check if diversion is needed."""
		return False

	def install_divert(self):
		"""Prepare file for diversion."""
		d = '%s.debian' % self.to_file
		self._call_silent('dpkg-divert', '--quiet', '--rename', '--divert', d, '--add', self.to_file)
		# Make sure a valid file still exists
		if os.path.exists(d) and not os.path.exists(self.to_file):
			# Don't use shutil.copy2(), which looses file ownership (Bug #22596)
			self._call_silent('cp', '-p', d, self.to_file)

	def uninstall_divert(self):
		"""Undo diversion of file."""
		try:
			os.unlink(self.to_file)
		except EnvironmentError:
			pass
		d = '%s.debian' % self.to_file
		self._call_silent('dpkg-divert', '--quiet', '--rename', '--divert', d, '--remove', self.to_file)

class configHandlerMultifile(configHandlerDiverting):

	def __init__(self, dummy_from_file, to_file):
		configHandlerDiverting.__init__(self, to_file)
		self.variables = set()
		self.from_files = set()
		self.dummy_from_file = dummy_from_file
		self.def_count = 1

	def __setstate__(self, state):
		"""Load state upon unpickling."""
		self.__dict__.update(state)
		self.def_count # may raise AttributeError, which forces UCR to rebuild the cache

	def addSubfiles(self, subfiles):
		for from_file, variables in subfiles:
			self.from_files.add(from_file)
			self.variables |= variables

	def remove_subfile(self, subfile):
		"""Remove subfile and return if set is now empty."""
		self.from_files.discard(subfile)
		if not self.need_divert():
			self.uninstall_divert()

	def __call__(self, args):
		ucr, changed = args
		print 'Multifile: %s' % self.to_file

		if self.def_count == 0 or not self.from_files:
			return

		to_dir = os.path.dirname(self.to_file)
		if not os.path.isdir(to_dir):
			os.makedirs(to_dir, 0755)

		if os.path.isfile(self.dummy_from_file):
			st = os.stat(self.dummy_from_file)
		else:
			st = None
		to_fp = open(self.to_file, 'w')

		filter_opts = {}

		for from_file in sorted(self.from_files, key=lambda x: os.path.basename(x)):
			try:
				from_fp = open(from_file, 'r')
			except EnvironmentError:
				continue
			to_fp.write(filter(from_fp.read(), ucr, srcfiles = self.from_files, opts = filter_opts))

		self._set_perm(st)
		to_fp.close()

		script_file = os.path.join(script_dir, self.to_file.strip("/"))
		if os.path.isfile(script_file):
			runScript(script_file, 'postinst', changed)

	def need_divert(self):
		"""Diversion is needed when at least one multifile and one subfile definition exists."""
		return self.def_count >= 1 and self.from_files

	def install_divert(self):
		"""Prepare file for diversion."""
		if self.need_divert():
			super(configHandlerMultifile, self).install_divert()

	def uninstall_divert(self):
		"""Undo diversion of file."""
		if not self.need_divert():
			super(configHandlerMultifile, self).uninstall_divert()

class configHandlerFile(configHandlerDiverting):

	def __init__(self, from_file, to_file):
		configHandlerDiverting.__init__(self, to_file)
		self.from_file = from_file
		self.preinst = None
		self.postinst = None

	def __call__(self, args):
		ucr, changed = args

		if hasattr( self, 'preinst') and self.preinst:
			runModule(self.preinst, 'preinst', ucr, changed)

		print 'File: %s' % self.to_file

		to_dir = os.path.dirname(self.to_file)
		if not os.path.isdir(to_dir):
			os.makedirs(to_dir, 0755)

		try:
			st = os.stat(self.from_file)
		except EnvironmentError:
			print >> sys.stderr, "The referenced template file does not exist"
			return None
		from_fp = open(self.from_file, 'r')
		to_fp = open(self.to_file, 'w')

		filter_opts = {}

		to_fp.write(filter(from_fp.read(), ucr, srcfiles = [self.from_file], opts = filter_opts))

		self._set_perm(st)
		from_fp.close()
		to_fp.close()

		if hasattr( self, 'postinst' ) and self.postinst:
			runModule(self.postinst, 'postinst', ucr, changed)

		script_file = self.from_file.replace(file_dir, script_dir)
		if os.path.isfile(script_file):
			runScript(script_file, 'postinst', changed)

	def need_divert(self):
		"""For simple files the diversion is always needed."""
		return True

class configHandlerScript(configHandler):

	def __init__(self, script):
		self.script = script

	def __call__(self, args):
		ucr, changed = args
		print 'Script: '+self.script
		if os.path.isfile(self.script):
			runScript(self.script, 'generate', changed)

class configHandlerModule(configHandler):

	def __init__(self, module):
		self.module = module

	def __call__(self, args):
		ucr, changed = args
		print 'Module: '+self.module
		runModule(self.module, 'generate', ucr, changed)


def grepVariables(f):
	"""Return set of all variables inside @%@ delimiters."""
	return set(variable_pattern.findall(f))

class configHandlers:
	"""Manage handlers for configuration variables."""
	CACHE_FILE = '/var/cache/univention-config/cache'
	# 0: without version
	# 1: with version header
	# 2: switch to handlers mapping to set, drop file, add multifile.def_count
	VERSION = 2
	VERSION_MIN = 0
	VERSION_MAX = 2
	VERSION_TEXT = 'univention-config cache, version'
	VERSION_NOTICE = '%s %s\n' % (VERSION_TEXT, VERSION)
	VERSION_RE = re.compile('^%s (?P<version>[0-9]+)$' % VERSION_TEXT)

	_handlers = {} # variable -> set(handlers)
	_multifiles = {} # multifile -> handler
	_subfiles = {} # multifile -> [(subfile, variables)] // pending

	def _get_cache_version(self, fp):
		line = fp.readline()	# IOError is propagated
		match = configHandlers.VERSION_RE.match(line)
		if match:
			version = int(match.group('version'))
		# "Old style" cache (version 0) doesn't contain version notice
		else:
			fp.seek(0)
			version = 0
		return version

	def load(self):
		"""Load cached .info data or force update."""
		try:
			fp = open(configHandlers.CACHE_FILE, 'r')
			try:
				version = self._get_cache_version(fp)
				if not configHandlers.VERSION_MIN <= version <= configHandlers.VERSION_MAX:
					raise TypeError("Invalid cache file version.")
				p = cPickle.Unpickler(fp)
				self._handlers = p.load()
				if version <= 1:
					# version <= 1: _handlers[multifile] -> [handlers]
					# version >= 2: _handlers[multifile] -> set([handlers])
					self._handlers = dict(((k, set(v)) for k, v in self._handlers.items()))
					# version <= 1: _files UNUSED
					_files = p.load()
				self._subfiles = p.load()
				self._multifiles = p.load()
			finally:
				fp.close()
		except (EnvironmentError, TypeError, ValueError, cPickle.UnpicklingError, EOFError, AttributeError):
			self.update()

	def stripBasepath(self, path, basepath):
		return path.replace(basepath, '')

	def getHandler(self, entry):
		"""Parse entry and return Handler instance."""
		try:
			typ = entry['Type'][0]
			m = getattr(self, '_get_handler_%s' % typ)
		except (LookupError, NameError):
			return None
		else:
			return m(entry)

	def _get_handler_file(self, entry):
			"""Parse file entry and return Handler instance."""
			try:
				name = entry['File'][0]
			except LookupError:
				return None
			from_path = os.path.join(file_dir, name)
			handler = configHandlerFile(from_path, name)
			if os.path.exists(from_path):
				handler.variables = grepVariables(open(from_path, 'r').read())

			try:
				handler.preinst = entry['Preinst'][0]
			except LookupError:
				pass

			try:
				handler.postinst = entry['Postinst'][0]
			except LookupError:
				pass

			handler.variables |= set(entry.get('Variables', set()))

			try:
				user = entry['User'][0]
			except LookupError:
				pass
			else:
				try:
					handler.user = pwd.getpwnam(user).pw_uid
				except LookupError:
					print >> sys.stderr, 'W: failed to convert the username %s to the uid' % (user,)

			try:
				group = entry['Group'][0]
			except LookupError:
				pass
			else:
				try:
					handler.group = grp.getgrnam(group).gr_gid
				except LookupError:
					print >> sys.stderr, 'W: failed to convert the groupname %s to the gid' % (group,)

			try:
				mode = entry['Mode'][0]
			except LookupError:
				pass
			else:
				try:
					handler.mode = int(mode, 8)
				except ValueError:
					print >> sys.stderr, 'W: failed to convert mode %s' % (mode,)

			return handler

	def _get_handler_script(self, entry):
			"""Parse script entry and return Handler instance."""
			try:
				script = entry['Script'][0]
				variables = entry['Variables']
			except LookupError:
				return None
			handler = configHandlerScript(os.path.join(script_dir, script))
			handler.variables = set(variables)
			return handler

	def _get_handler_module(self, entry):
			"""Parse module entry and return Handler instance."""
			try:
				module = entry['Module'][0]
				variables = entry['Variables']
			except LookupError:
				return None
			handler = configHandlerModule(os.path.splitext(module)[0])
			handler.variables = set(variables)
			return handler

	def _get_handler_multifile(self, entry):
			"""Parse multifile entry and return Handler instance."""
			try:
				mfile = entry['Multifile'][0]
			except LookupError:
				return None
			try:
				handler = self._multifiles[mfile]
				handler.def_count += 1
			except KeyError:
				from_path = os.path.join(file_dir, mfile)
				handler = configHandlerMultifile(from_path, mfile)

			handler.variables |= set(entry.get('Variables', set()))

			try:
				user = entry['User'][0]
			except LookupError:
				pass
			else:
				try:
					handler.user = pwd.getpwnam(user).pw_uid
				except LookupError:
					print >> sys.stderr, 'W: failed to convert the username %s to the uid' % (user,)

			try:
				group = entry['Group'][0]
			except LookupError:
				pass
			else:
				try:
					handler.group = grp.getgrnam(group).gr_gid
				except LookupError:
					print >> sys.stderr, 'W: failed to convert the groupname %s to the gid' % (group,)

			try:
				mode = entry['Mode'][0]
			except LookupError:
				pass
			else:
				try:
					handler.mode = int(mode, 8)
				except ValueError:
					print >> sys.stderr, 'W: failed to convert mode %s' % (mode,)


			# Add pending subfiles from earlier entries
			self._multifiles[mfile] = handler
			try:
				file_vars = self._subfiles.pop(mfile)
				handler.addSubfiles(file_vars)
			except KeyError:
				pass

			return handler

	def _get_handler_subfile(self, entry):
			"""Parse subfile entry and return Handler instance."""
			try:
				mfile = entry['Multifile'][0]
				subfile = entry['Subfile'][0]
			except LookupError:
				return None
			variables = set(entry.get('Variables', set()))
			name = os.path.join(file_dir, subfile)
			try:
				f = open(name, 'r')
				try:
					variables |= grepVariables(f.read())
				finally:
					f.close()
			except EnvironmentError:
				print >> sys.stderr, "Failed to process Subfile %s" % (name,)
				return None
			qentry = (name, variables)
			# if multifile handler does not yet exists, queue subfiles for later
			try:
				handler = self._multifiles[mfile]
				handler.addSubfiles([qentry])
			except KeyError:
				pending = self._subfiles.setdefault(mfile, [])
				pending.append(qentry)
				handler = None
			return handler

	def update(self):
		"""Parse all .info files to build list of handlers."""
		self._handlers.clear()
		self._multifiles.clear()
		self._subfiles.clear()

		handlers = set()
		for info in directoryFiles(info_dir):
			if not info.endswith('.info'):
				continue
			for section in parseRfc822(open(info, 'r').read()):
				handler = self.getHandler(section)
				if handler:
					handlers.add(handler)
		for handler in handlers:
			for variable in handler.variables:
				v2h = self._handlers.setdefault(variable, set())
				v2h.add(handler)

		self._save_cache()
		return handlers

	def update_divert(self, handlers):
		"""Synchronize diversions with handlers."""
		wanted = dict([(h.to_file, h) for h in handlers if isinstance(h, configHandlerDiverting) and h.need_divert()])
		to_remove = set()
		# Scan for diversions done by UCR
		f = open('/var/lib/dpkg/diversions', 'r') # from \n to \n package \n
		try:
			try:
				while True:
					path_from = f.next().rstrip()
					path_to = f.next().rstrip()
					diversion = f.next().rstrip()
					if path_from + '.debian' != path_to:
						continue
					if ':' != diversion: # local diversion
						continue
					assert path_from not in to_remove # no dulicates
					try:
						handler = wanted.pop(path_from)
					except KeyError:
						to_remove.add(path_from)
			except StopIteration:
				pass
		finally:
			f.close()
		# Remove existing diversion not wanted
		for path in to_remove:
			tmp_handler = configHandlerDiverting(path)
			tmp_handler.uninstall_divert()
		# Install missing diversions still wanted
		for path, handler in wanted.items():
			handler.install_divert()

	def _save_cache(self):
		"""Write cache file."""
		fp = open(configHandlers.CACHE_FILE, 'w')
		fp.write(configHandlers.VERSION_NOTICE)
		p = cPickle.Pickler(fp)
		p.dump(self._handlers)
		p.dump(self._subfiles)
		p.dump(self._multifiles)
		fp.close()

	def register(self, package, ucr):
		"""Register new info file for package."""
		handlers = set()
		file = os.path.join(info_dir, package+'.info')
		for section in parseRfc822(open(file, 'r').read()):
			handler = self.getHandler(section)
			if handler:
				handlers.add(handler)

		for handler in handlers:
			if isinstance(handler, configHandlerDiverting):
				handler.install_divert()
			values = {}
			for variable in handler.variables:
				v2h = self._handlers.setdefault(variable, set())
				v2h.add(handler)
				values[variable] = ucr[variable]
			handler((ucr, values))

		self._save_cache()
		return handlers

	def unregister(self, package, ucr):
		"""Un-register info file for package."""
		handlers = set()
		mf_handlers = set()
		file = os.path.join(info_dir, package+'.info')
		for section in parseRfc822(open(file, 'r').read()):
			try:
				typ = section['Type'][0]
			except LookupError:
				continue
			if typ == 'file':
				handler = self.getHandler(section)
			elif typ == 'subfile':
				mfile = section['Multifile'][0]
				sfile = section['Subfile'][0]
				try:
					handler = self._multifiles[mfile]
				except KeyError:
					continue # skip SubFile w/o MultiFile
				name = os.path.join(file_dir, sfile)
				handler.remove_subfile(name)
			elif typ == 'multifile':
				mfile = section['Multifile'][0]
				handler = self._multifiles[mfile]
				handler.def_count -= 1
			else:
				continue
			if not handler: # Bug #17913
				print >> sys.stderr, "Skipping internal error: no handler for %r in %s" % (section, package)
				continue
			handlers.add(handler)
			handler.uninstall_divert()
			# regenerate multifile from remaining parts
			if isinstance(handler, configHandlerMultifile):
				mf_handlers.add(handler)

		for handler in mf_handlers:
			self.call_handler(ucr, handler)

		try:
			# remove cache file to force rebuild of cache
			os.unlink(configHandlers.CACHE_FILE)
		except EnvironmentError:
			pass
		return handlers

	def __call__(self, variables, arg):
		"""Call handlers registered for changes in variables."""
		if not variables:
			return
		pending_handlers = set()

		for reg_var, handlers in self._handlers.items():
			_re = re.compile(reg_var)
			for variable in variables:
				if _re.match(variable):
					pending_handlers |= handlers
		for handler in pending_handlers:
			handler(arg)

	def commit(self, ucr, filelist=[]):
		"""Call handlers to (re-)generate files."""
		_filelist = []
		if filelist:
			cwd = os.getcwd()
			for _f in filelist:
				_f = os.path.normpath(os.path.expandvars(os.path.expanduser(os.path.normpath(_f))))
				if _f.startswith('/'):
					_filelist.append(_f)
				else:
					_filelist.append(os.path.normpath(os.path.join(cwd, _f)))
		# find handlers
		pending_handlers = set()
		for file in directoryFiles(info_dir):
			if not file.endswith('.info'):
				continue
			for section in parseRfc822(open(file, 'r').read()):
				if not section.get('Type'):
					continue
				handler = None
				if _filelist:
					files = section.get('File') or section.get('Multifile') or ()
					for f in files:
						if f[0] != '/':
							f = '/' + f
						if f in _filelist:
							handler = self.getHandler(section)
							break
					else:
						continue
				else:
					handler = self.getHandler(section)
				if handler:
					pending_handlers.add(handler)
		# call handlers
		for handler in pending_handlers:
			self.call_handler(ucr, handler)

	def call_handler(self, ucr, handler):
		"""Call handler passing current configuration variables."""
		values = {}
		for variable in handler.variables:
			if variable in self._handlers.keys():
				if ".*" in variable:
					for i in range(4):
						val = variable.replace(".*", "%s" % i)
						values[val] = ucr.get(val)
				else:
					values[variable] = ucr.get(variable)
		handler((ucr, values))

def randpw():
	"""Create random password."""
	valid = [ 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
		'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
		'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
		'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
		'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5',
		'6', '7', '8', '9' ]
	pw = ''
	fp = open('/dev/urandom', 'r')
	for i in range(0,8):
		o = fp.read(1)
		pw += valid[(ord(o) % len(valid))]
	fp.close()
	return pw

def replog(method, scope, ucr, var, value=None):
	"""
	This function writes a new entry to replication logfile if
	this feature has been enabled.
	"""
	if ucr.is_true('ucr/replog/enabled', False):
		if method == 'set':
			varvalue = "%s=%s" % (var, escape_value(value))
		else:
			varvalue = "'%s'" % var

		scope_arg = ''
		if scope == ConfigRegistry.LDAP:
			scope_arg = '--ldap-policy '
		elif scope == ConfigRegistry.FORCED:
			scope_arg = '--force '
		elif scope == ConfigRegistry.SCHEDULE:
			scope_arg = '--schedule '

		str = '%s: %s %s%s\n' % (time.strftime("%Y-%m-%d %H:%M:%S"), method, scope_arg, varvalue)
		try:
			if not os.path.isfile(replog_file):
				os.close(os.open(replog_file, os.O_CREAT, 0640))
			logfile = open(replog_file, "a+")
			logfile.write(str)
			logfile.close()
		except EnvironmentError, ex:
			print >> sys.stderr, "E: exception occurred while writing to replication log: %s" % (ex,)
			exception_occured()

def handler_set( args, opts = {}, quiet = False ):
	"""
	Set config registry variables in args.
	Args is an array of strings 'key=value' or 'key?value'.
	"""
	c = configHandlers()
	c.load()

	current_scope = ConfigRegistry.NORMAL
	reg = None
	if opts.get( 'ldap-policy', False ):
		current_scope = ConfigRegistry.LDAP
		reg = ConfigRegistry( write_registry = current_scope )
	elif opts.get( 'force', False ):
		current_scope = ConfigRegistry.FORCED
		reg = ConfigRegistry( write_registry = current_scope)
	elif opts.get( 'schedule', False ):
		current_scope = ConfigRegistry.SCHEDULE
		reg = ConfigRegistry( write_registry = current_scope)
	else:
		reg = ConfigRegistry()

	reg.lock()
	try:
		reg.load()

		changed = {}
		for arg in args:
			sep_set = arg.find('=') # set
			sep_def = arg.find('?') # set if not already set
			if sep_set == -1 and sep_def == -1:
				print >> sys.stderr, "W: Missing value for config registry variable '%s'" % (arg,)
				continue
			else:
				if sep_set > 0 and sep_def == -1:
					sep = sep_set
				elif sep_def > 0 and sep_set == -1:
					sep = sep_def
				else:
					sep = min(sep_set, sep_def)
			key = arg[0:sep]
			value = arg[sep+1:]
			old = reg.get(key)
			if (old is None or sep == sep_set) and validateKey(key):
				if not quiet:
					if reg.has_key( key, write_registry_only = True ):
						print 'Setting '+key
					else:
						print 'Create '+key
					k = reg.get(key, None, getscope=True)
					if k and k[0] > current_scope:
						print >> sys.stderr, 'W: %s is overridden by scope "%s"' % (key, SCOPE[k[0]])
				reg[key] = value
				changed[key] = (old, value)
				replog( 'set', current_scope, reg, key, value )
			else:
				if not quiet:
					if old is not None:
						print 'Not updating '+key
					else:
						print 'Not setting '+key

		reg.save()
	finally:
		reg.unlock()

	c( changed.keys(), ( reg, changed ) )

def handler_unset( args, opts = {} ):
	"""
	Unset config registry variables in args.
	"""
	current_scope = ConfigRegistry.NORMAL
	reg = None
	if opts.get( 'ldap-policy', False ):
		current_scope = ConfigRegistry.LDAP
		reg = ConfigRegistry( write_registry = current_scope )
	elif opts.get( 'force', False ):
		current_scope = ConfigRegistry.FORCED
		reg = ConfigRegistry( write_registry = current_scope)
	elif opts.get( 'schedule', False ):
		current_scope = ConfigRegistry.SCHEDULE
		reg = ConfigRegistry( write_registry = current_scope)
	else:
		reg = ConfigRegistry()
	reg.lock()
	try:
		reg.load()

		c = configHandlers()
		c.load()

		changed = {}
		for arg in args:
			if reg.has_key( arg, write_registry_only = True ):
				oldvalue = reg[arg]
				print 'Unsetting '+arg
				del reg[arg]
				changed[arg] = ( oldvalue, '' )
				k = reg.get(arg, None, getscope=True)
				replog( 'unset', current_scope, reg, arg )
				if k and k[0] > current_scope:
					print >> sys.stderr, 'W: %s is still set in scope "%s"' % (arg, SCOPE[k[0]])
			else:
				print >> sys.stderr, "W: The config registry variable '%s' does not exist" % arg
		reg.save()
	finally:
		reg.unlock()
	c( changed.keys(), ( reg, changed ) )

def handler_dump( args, opts = {} ):
	b = ConfigRegistry()
	b.load()
	for line in str(b).split('\n'):
		print line

def handler_update( args, opts = {} ):
	c = configHandlers()
	cur = c.update()
	c.update_divert(cur)

def handler_commit( args, opts = {} ):
	b = ConfigRegistry()
	b.load()

	c = configHandlers()
	c.load()
	c.commit(b, args)

def handler_register( args, opts = {} ):
	b = ConfigRegistry()
	b.load()

	c = configHandlers()
	c.update() # cache must be current
	# Bug #21263: by forcing an update here, the new .info file is already incorporated. Calling register for multifiles will increment the def_count a second time, which is not nice, but uncritical, since the diversion is (re-)done when >= 1.
	c.register(args[0], b)
	#c.commit((b, {}))

def handler_unregister( args, opts = {} ):
	b = ConfigRegistry()
	b.load()

	c = configHandlers()
	cur = c.update() # cache must be current
	obsolete = c.unregister(args[0], b)
	c.update_divert(cur - obsolete)

def handler_randpw( args, opts = {} ):
	print randpw()

def replaceDict(line, dict):
	''' Map any character from line to its value from dict '''
	return ''.join((dict.get(_, _) for _ in line))

def replaceUmlaut(line):
	umlauts = { 'Ä': 'Ae',
		    'ä': 'ae',
		    'Ö': 'Oe',
		    'ö': 'oe',
		    'Ü': 'Ue',
		    'ü': 'ue',
		    'ß': 'ss', }
	return replaceDict(line, umlauts)

def keyShellEscape(line):
	'''Escape variable name by substituting shell invalid characters by '_'.'''
	if not line:
		raise ValueError('got empty line')
	new_line = []
	if line[0] in string.digits:
		new_line.append('_')
	for letter in line:
		if letter in shell_valid_key_chars:
			new_line.append(letter)
		else:
			new_line.append('_')
	return ''.join(new_line)

def validateKey(k):
	"""Check if key consists of only shell valid characters."""
	old = k
	k = replaceUmlaut(k)

	if old != k:
		print >> sys.stderr, 'Please fix invalid umlaut in config variables key "%s" to %s' % (old, k)
		return 0

	if len(k) > 0:
		match = invalid_key_chars.search(k)

		if not match:
			return 1
		else:
			print >> sys.stderr, 'Please fix invalid char "%s" in config registry key "%s"' % (match.group(), k)
	return 0

def handler_filter( args, opts = {} ):
	"""Run filter on STDIN to STDOUT."""
	b = ConfigRegistry()
	b.load()
	sys.stdout.write(filter(sys.stdin.read(), b, opts = opts))

def handler_search( args, opts = {} ):
	global info_handler
	info_handler = None
	category = opts.get( 'category', None )
	non_empty = opts.get( 'non-empty', False )
	brief = opts.get( 'brief', False )
	search_keys = opts.get( 'key', False )
	search_values = opts.get( 'value', False )
	search_all = opts.get( 'all', False )
	verbose = opts.get( 'verbose', False )

	count_search = int(search_keys) + int(search_values) + int(search_all)
	if count_search > 1:
		print >> sys.stderr, 'E: at most one out of [--key|--value|--all] may be set'
		sys.exit( 1 )
	elif count_search == 0:
		search_keys = True
	search_values |= search_all
	search_keys |= search_all

	if not args:
		regex = [re.compile('')]
	else:
		try:
			regex = [re.compile(_) for _ in args]
		except re.error, ex:
			print >> sys.stderr, 'E: invalid regular expression: %s' % (ex,)
			sys.exit(1)

	#Import located here, because on module level, a circular import would be created
	import config_registry_info as cri
	cri.set_language('en')
	info = cri.ConfigRegistryInfo(install_mode=False)

	if category and not info.get_category(category):
		print >> sys.stderr, 'E: unknown category: "%s"' % (category,)
		sys.exit(1)

	b = ConfigRegistry()
	b.load()

	show_scope = b.is_true('ucr/output/scope', False)
	brief |= b.is_true('ucr/output/brief', False)

	all_vars = {}  # key: (value, vinfo, scope)
	for key, var in info.get_variables(category).items():
		all_vars[key] = (None, var, None)
	for key, (scope, value) in b.items(getscope=True):
		try:
			all_vars[key] = (value, all_vars[key][1], scope)
		except LookupError:
			all_vars[key] = (value, None, scope)

	for key, (value, vinfo, scope) in all_vars.items():
		for reg in regex:
			if (
					(search_keys and reg.search(key)) or
					(search_values and value and reg.search(value)) or
					(search_all and vinfo and reg.search(vinfo.get('description', '')))
					):
				print_variable_info_string(key, value, vinfo, scope, show_scope, brief, non_empty, verbose)
				break

def handler_get( args, opts = {} ):
	global opt_filters
	
	b = ConfigRegistry()
	b.load()

	if not args[ 0 ] in b:
		return
	if opt_filters[ 99 ][ 2 ]:
		print '%s: %s' % ( args[ 0 ], b.get( args[ 0 ], '' ) )
	else:
		print b.get( args[ 0 ], '' )

class UnknownKeyException(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

def print_variable_info_string( key, value, variable_info, scope=None, show_scope=False, brief=False, non_empty=False, verbose=False ):
	value_string = None
	if value is None and not variable_info:
		raise UnknownKeyException('W: unknown key: "%s"' % key)
	elif value in ( None, '' ) and non_empty:
		return
	elif value is None:
		# if not shell filter option is set
		if not opt_filters[ 99 ][ 2 ]:
			value_string = '<empty>'
		else:
			value_string = ''
	else:
		value_string = '%s' % value
	if not show_scope or scope in (None, 0) or scope > len(SCOPE):
		key_value = '%s: %s' % (key, value_string)
	else:
		if opt_filters[ 99 ][ 2 ]: # Do not display scope in shell export filter
			key_value = '%s: %s' % (key, value_string)
		else:
			key_value = '%s (%s): %s' % (key, SCOPE[scope], value_string)
			

	info_string = None
	if brief and not verbose or not variable_info:
		info_string = key_value
	else:
		info = [ key_value ]
#		info.append(' ' + variable_info.get('description', 'no description available'))
# https://forge.univention.org/bugzilla/show_bug.cgi?id=15556
# Workaround:
		description = variable_info.get( 'description' )
		if not description or not description.strip():
			description = 'no description available'
		info.append(' ' + description)
		if verbose or info_handler:
			info.append(' Categories: ' + variable_info.get('categories', 'none'))

		info_string = '\n'.join(info)

	if brief and not verbose:
		print info_string
	else:
		print info_string + '\n'

def handler_info( args, opts = {} ):
	global info_handler
	reg = ConfigRegistry()
	reg.load()
	#Import located here, because on module level, a circular import would be created
	import config_registry_info as cri
	cri.set_language('en')
	info = cri.ConfigRegistryInfo(install_mode=False)
	info_handler = True

	for arg in args:
		try:
			print_variable_info_string(arg, reg.get(arg, None), info.get_variable(arg))
		except UnknownKeyException, ex:
			print >> sys.stderr, ex

def handler_help(args, opts={}, out=sys.stdout):
	print >> out, '''
univention-config-registry: base configuration for UCS
copyright (c) 2001-2012 Univention GmbH, Germany

Syntax:
  univention-config-registry [options] <action> [options] [parameters]

Options:

  -h | --help | -?:
	print this usage message and exit program

  --version | -v:
	print version information and exit program

  --shell (valid actions: dump, search):
	convert key/value pair into shell compatible format, e.g.
	`version/version: 1.0` => `version_version="1.0"`

  --keys-only (valid actions: dump, search):
	print only the keys

Actions:
  set [--force|--schedule|--ldap-policy] <key>=<value> [... <key>=<value>]:
	set one or more keys to specified values; if a key is non-existent
	in the configuration registry it will be created

  get <key>:
	retrieve the value of the specified key from the configuration
	database

  unset [--force|--schedule|--ldap-policy] <key> [... <key>]:
	remove one or more keys (and its associated values) from
	configuration database

  dump:
	display all key/value pairs which are stored in the
	configuration database

  search [--key|--value|--all] [--category <category>] [--brief] [--non-empty] [... <regex>]:
	displays all key/value pairs and their descriptions that match at
	least one of the given regular expressions
	--key: only search the keys (default)
	--value: only search the values
	--all: search keys, values and descriptions
	--category: limit search to variables of <category>
	--brief: don\'t print descriptions (can be enabled by default via ucr/output/brief)
	--non-empty: only search in non-empty variables
	no <regex> given: display all variables
	--verbose: also print category for each variable

  info <key> [... <key>]:
	display verbose information for the specified variable(s)

  shell [key]:
	convert key/value pair into shell compatible format, e.g.
	`version/version: 1.0` => `version_version="1.0"`
	(deprecated: use --shell dump instead)

  commit [file1 ...]:
	rebuild configuration file from univention template; if
	no file is specified ALL configuration files are rebuilt

  filter [file]:
	evaluate a template file, expects python inline code in UTF-8 or US-ASCII

Description:
  univention-config-registry is a tool to handle the basic configuration for UCS
'''
	sys.exit(0)

def handler_version( args, opts = {} ):
	print 'univention-config-registry @%@package_version@%@'
	sys.exit(0)

def missing_parameter(action):
	print >> sys.stderr, 'E: too few arguments for command [%s]' % (action,)
	print >> sys.stderr, 'try `univention-config-registry --help` for more information'
	sys.exit(1)

def exception_occured():
	print >> sys.stderr, 'E: your request could not be fulfilled'
	print >> sys.stderr, 'try `univention-config-registry --help` for more information'
	sys.exit(1)

def filter_shell( args, text ):
	out = []
	for line in text:
		try:
			var, value = line.split( ': ', 1 )
		except ValueError:
			var = line
			value = ''
		out.append('%s=%s' % (keyShellEscape(var), escape_value(value)))
	return out

def filter_keys_only( args, text ):
	out = []
	for line in text:
		out.append( line.split( ': ', 1 )[ 0 ] )
	return out

def filter_sort( args, text ):
	text.sort()
	return text

class Output:
	def __init__(self):
		self.text = []

	def write(self, line):
		if line and line.strip():
			self.text.append(line)

	def writelines(self, lines):
		for l in lines:
			self.text.append(l)

handlers = {
	'set': (handler_set, 1),
	'unset': (handler_unset, 1),
	'dump': (handler_dump, 0),
	'update': (handler_update, 0),
	'commit': (handler_commit, 0),
	'register': (handler_register, 1),
	'unregister': (handler_unregister, 1),
	'randpw': (handler_randpw, 0),
	'shell': (None, 0),	# for compatibility only
	'filter': (handler_filter, 0),
	'search': (handler_search, 0),
	'get': (handler_get, 1),
	'info': (handler_info, 1),
	}
# action options: each of these options perform an action
opt_actions = {
	# name : ( function, state, ( alias list ) )
	'help': [handler_help, False, ('-h', '-?')],
	'version': [handler_version, False, ('-v',)],
	}
# filter options: these options define filter for the output
opt_filters = {
	# id : ( name, function, state, ( valid actions ) )
	0: ['keys-only', filter_keys_only, False, ('dump', 'search')],
	10: ['sort', filter_sort, False, ('dump', 'search', 'info')],
	99: ['shell', filter_shell, False, ('dump', 'search', 'shell', 'get')],
	}
BOOL, STRING = range(2)
opt_commands = {
	'set' : { 'force' : (BOOL, False), 'ldap-policy' : (BOOL, False), 'schedule' : (BOOL, False) },
	'unset' : { 'force' : (BOOL, False), 'ldap-policy' : (BOOL, False), 'schedule' : (BOOL, False) },
	'search' : { 'key' : (BOOL, False), 'value' : (BOOL, False), 'all' : (BOOL, False), \
				 'brief' : (BOOL, False), 'category' : (STRING, None), 'non-empty' : (BOOL, False), \
				 'verbose' : (BOOL, False) },
	'filter' : { 'encode-utf8' : (BOOL, False) }
	}

def main(args):
	global handlers, opt_actions, opt_filters, opt_commands

	try:
		# close your eyes ...
		if not args: args.append( '--help' )
		# search for options in command line arguments
		for arg in copy.copy( args ):
			if not arg[ 0 ] == '-': break

			# is action option?
			for key, opt in opt_actions.items():
				if arg[ 2 : ] == key or arg in opt[ 2 ]:
					opt_actions[ key ][ 1 ] = True
					break
			else:
				# not an action option; is a filter option?
				for id, opt in opt_filters.items():
					if arg[ 2 : ] == opt[ 0 ]:
						opt[ 2 ] = True
						break
				else:
					print >> sys.stderr, 'E: unknown option %s' % (arg,)
					handler_help(args, out=sys.stderr)
					sys.exit(1)

			# remove option from command line arguments
			args.pop( 0 )

		# is action already defined by global option?
		for k in opt_actions:
			if opt_actions[ k ][ 1 ]:
				opt_actions[ k ][ 0 ](args)

		# find action
		action = args[ 0 ]
		args.pop( 0 )
		# COMPAT: the 'shell' command is now an option and equivalent to --shell search
		if action == 'shell':
			action = 'search'
			# activate shell option
			opt_filters[ 99 ][ 2 ] = True
			# switch to old, brief output
			opt_commands[ 'search' ][ 'brief' ] = (BOOL, True)

			tmp = []
			if not args:
				tmp.append( '' )
			else:
				for arg in args:
					if not arg.startswith( '--' ):
						tmp.append( '^%s$' % arg )
					else:
						tmp.append( arg )
			args = tmp

		# set 'sort' option by default for dump and search
		if action in ['dump', 'search', 'info']:
			opt_filters[ 10 ][ 2 ] = True

		# set brief option when generating shell output
		if opt_filters[ 99 ][ 2 ] == True:
			opt_commands[ 'search' ][ 'brief' ] = (BOOL, True)

		# if a filter option is set: verify that a valid command is given
		filter = False
		for id, opt in opt_filters.items():
			if opt[ 2 ]:
				if not action in opt[ 3 ]:
					print >> sys.stderr, 'E: invalid option --%s for command %s' % (opt[0], action)
					sys.exit( 1 )
				else:
					filter = True

		# check command options
		cmd_opts = opt_commands.get( action, {} )
		skip_next_arg = False
		for arg in copy.copy( args ):
			if skip_next_arg:
				skip_next_arg = False
				args.pop( 0 )
				continue
			if not arg.startswith( '--' ): break
			cmd_opt = arg[ 2: ]
			if action in ('set', 'unset', ) and cmd_opt == 'forced':
				cmd_opt = 'force'
			if cmd_opt in cmd_opts.keys():
				cmd_opt_tuple = cmd_opts[ cmd_opt ]
				if cmd_opt_tuple[0] == BOOL:
					cmd_opts[ cmd_opt ] = (BOOL, True)
				else: #STRING
					if len(args) < 2:
						sys.stderr.write('E: Option %s for command %s expects an argument\n' % (arg, action))
						sys.exit(1)
					cmd_opts[ cmd_opt ] = (STRING, args[ 1 ])
					skip_next_arg = True
			else:
				opt_actions[ 'help' ][ 1 ] = True
				print >> sys.stderr, 'invalid option %s for command %s' % (arg, action)
				sys.exit( 1 )
			args.pop( 0 )

		for cmd_opt, opt_tuple in copy.copy(cmd_opts).items():
			cmd_opts[ cmd_opt ] = opt_tuple[ 1 ]

		# action!
		if action in handlers.keys():
			# enough arguments?
			if len( args ) < handlers[ action ][ 1 ]:
				missing_parameter( action )
			# if any filter option is set
			if filter:
				old_stdout = sys.stdout
				sys.stdout = Output()
			handlers[ action ][ 0 ]( args, cmd_opts )
			# let the filter options do their job
			if filter:
				out = sys.stdout
				text = out.text
				sys.stdout = old_stdout
				for id, opt in opt_filters.items():
					if opt[ 2 ]:
						text = opt[ 1 ]( args, text )
				for line in text:
					print line
		else:
			print >> sys.stderr, 'E: unknown action: %s' % (action,)
			handler_help(args, out=sys.stderr)
			sys.exit( 1 )

	except (EnvironmentError, TypeError):
		exception_occured()

if __name__ == '__main__':
	try:
		main(sys.argv[1:])
	except StrictModeException, ex2:
		print >> sys.stderr, 'E: UCR is running in strict mode and thus cannot accept the given input:'
		print >> sys.stderr, ex2
		sys.exit(1)
