# -*- coding: utf-8 -*-
#
"""Univention Configuration Registry handlers."""
#  main configuration registry classes
#
# Copyright 2004-2014 Univention GmbH
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

# API stability :pylint: disable-msg=R0201,W0613,R0903
# Too pedantic  :pylint: disable-msg=W0704
# Rewrite       :pylint: disable-msg=R0912

import sys
import os
import random
import re
import subprocess
import cPickle
import errno
from pwd import getpwnam
from grp import getgrnam
from univention.config_registry.misc import replace_umlaut, directory_files
from univention.debhelper import parseRfc822  # pylint: disable-msg=W0403

__all__ = ['ConfigHandlers']

VARIABLE_PATTERN = re.compile('@%@([^@]+)@%@')
VARIABLE_TOKEN = re.compile('@%@')
EXECUTE_TOKEN = re.compile('@!@')
WARNING_PATTERN = re.compile('(UCRWARNING|BCWARNING|UCRWARNING_ASCII)=(.+)')

INFO_DIR = '/etc/univention/templates/info'
FILE_DIR = '/etc/univention/templates/files'
SCRIPT_DIR = '/etc/univention/templates/scripts'
MODULE_DIR = '/etc/univention/templates/modules'
WARNING_TEXT = '''\
Warning: This file is auto-generated and might be overwritten by
         univention-config-registry.
         Please edit the following file(s) instead:
Warnung: Diese Datei wurde automatisch generiert und kann durch
         univention-config-registry überschrieben werden.
         Bitte bearbeiten Sie an Stelle dessen die folgende(n) Datei(en):

'''

def run_filter(template, directory, srcfiles=set(), opts=dict()):
	"""Process a template file: substitute variables."""
	while True:
		i = VARIABLE_TOKEN.finditer(template)
		try:
			start = i.next()
			end = i.next()
			name = template[start.end():end.start()]

			if name in directory:
				value = directory[name]
			else:
				match = WARNING_PATTERN.match(name)
				if match:
					mode, prefix = match.groups()
					if mode == "UCRWARNING_ASCII":
						value = warning_string(prefix, srcfiles=srcfiles,
								enforce_ascii=True)
					else:
						value = warning_string(prefix, srcfiles=srcfiles)
				else:
					value = ''

			if isinstance(value, (list, tuple)):
				value = value[0]
			template = template[:start.start()] + value + template[end.end():]
		except StopIteration:
			break

	while True:
		i = EXECUTE_TOKEN.finditer(template)
		try:
			start = i.next()
			end = i.next()

			proc = subprocess.Popen((sys.executable,),
					stdin=subprocess.PIPE, stdout=subprocess.PIPE,
					close_fds=True)
			value = proc.communicate('''\
# -*- coding: utf-8 -*-
import univention.config_registry
configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()
# for compatibility
baseConfig = configRegistry
%s
''' % template[start.end():end.start()])[0]
			template = template[:start.start()] + value + template[end.end():]

		except StopIteration:
			break

	return template


def run_script(script, arg, changes):
	"""
	Execute script with command line arguments using a shell and pass changes
	on STDIN.
	For each changed variable a line with the 'name of the variable', the 'old
	value', and the 'new value' are passed separated by '@%@'.
	"""
	diff = []
	for key, value in changes.items():
		if value and len(value) > 1 and value[0] and value[1]:
			diff.append('%s@%%@%s@%%@%s\n' % (key, value[0], value[1]))

	cmd = script + " " + arg
	proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
			close_fds=True)
	proc.communicate(''.join(diff))


def run_module(modpath, arg, ucr, changes):
	"""loads the python module that MUST be located in 'module_dir' or any
	subdirectory."""
	arg2meth = {
			'generate': lambda obj: getattr(obj, 'handler'),
			'preinst':  lambda obj: getattr(obj, 'preinst'),
			'postinst': lambda obj: getattr(obj, 'postinst'),
			}
	# temporarily prepend MODULE_DIR to load path
	sys.path.insert(0, MODULE_DIR)
	module_name = os.path.splitext(modpath)[0]
	try:
		module = __import__(module_name.replace(os.path.sep, '.'))
		arg2meth[arg](module)(ucr, changes)
	except (AttributeError, ImportError), ex:
		print >> sys.stderr, ex
	del sys.path[0]


def warning_string(prefix='# ', width=80, srcfiles=set(), enforce_ascii=False):
	"""Generate UCR warning text."""
	res = []

	for line in WARNING_TEXT.splitlines():
		if enforce_ascii:
			line = replace_umlaut(line).encode('ascii', 'replace')
		res.append('%s%s' % (prefix, line))

	for srcfile in sorted(srcfiles):
		if enforce_ascii:
			srcfile = srcfile.encode('ascii', 'replace')
		res.append('%s\t%s' % (prefix, srcfile))
	res.append(prefix)

	return "\n".join(res)


class ConfigHandler(object):
	"""Base class of all config handlers."""
	variables = set()


class ConfigHandlerDiverting(ConfigHandler):
	"""File diverting config handler."""

	def __init__(self, to_file):
		super(ConfigHandlerDiverting, self).__init__()
		self.to_file = os.path.join('/', to_file)
		self.user = None
		self.group = None
		self.mode = None
		self.preinst = None
		self.postinst = None

	def __hash__(self):
		"""Return unique hash."""
		return hash(self.to_file)

	def __cmp__(self, other):
		"""Compare this to other handler."""
		return cmp(self.to_file, other.to_file)

	def _set_perm(self, stat, to_file = None):
		"""Set file permissions."""
		if not to_file:
			to_file = self.to_file
		elif self.to_file != to_file:
			try:
				old_stat = os.stat(self.to_file)
				os.chmod(to_file, old_stat.st_mode)
				os.chown(to_file, old_stat.st_uid, old_stat.st_gid)
			except EnvironmentError:
				pass

		if self.user or self.group or self.mode:
			if self.mode:
				os.chmod(to_file, self.mode)

			if self.user and self.group:
				os.chown(to_file, self.user, self.group)
			elif self.user:
				os.chown(to_file, self.user, 0)
			elif self.group:
				os.chown(to_file, 0, self.group)
		elif stat:
			os.chmod(to_file, stat.st_mode)

	def _call_silent(self, *cmd):
		"""Call command with stdin, stdout, and stderr redirected from/to
		devnull."""
		null = open(os.path.devnull, 'rw')
		try:
			# tell possibly wrapped dpkg-divert to really do the work
			env = dict(os.environ)
			env['DPKG_MAINTSCRIPT_PACKAGE'] = 'univention-config'
			return subprocess.call(cmd, stdin=null, stdout=null, stderr=null,
					env=env)
		finally:
			null.close()

	def need_divert(self):
		"""Check if diversion is needed."""
		return False

	def install_divert(self):
		"""Prepare file for diversion."""
		deb = '%s.debian' % self.to_file
		self._call_silent('dpkg-divert', '--quiet', '--rename', '--local',
				'--divert', deb,
				'--add', self.to_file)
		# Make sure a valid file still exists
		if os.path.exists(deb) and not os.path.exists(self.to_file):
			# Don't use shutil.copy2() which looses file ownership (Bug #22596)
			self._call_silent('cp', '-p', deb, self.to_file)

	def uninstall_divert(self):
		"""Undo diversion of file.
		Returns True because the diversion was removed."""
		try:
			os.unlink(self.to_file)
		except EnvironmentError:
			pass
		deb = '%s.debian' % self.to_file
		self._call_silent('dpkg-divert', '--quiet', '--rename', '--local',
				'--divert', deb,
				'--remove', self.to_file)
		return True

	def _temp_file_name(self):
		dirname, basename = os.path.split(self.to_file)
		filename = '.%s__ucr__commit__%s' % (basename, random.random())
		return os.path.join(dirname, filename)


class ConfigHandlerMultifile(ConfigHandlerDiverting):
	"""Handler for multifile."""

	def __init__(self, dummy_from_file, to_file):
		super(ConfigHandlerMultifile, self).__init__(to_file)
		self.variables = set()
		self.from_files = set()
		self.dummy_from_file = dummy_from_file
		self.def_count = 1

	def __setstate__(self, state):
		"""Load state upon unpickling."""
		self.__dict__.update(state)
		# may raise AttributeError, which forces UCR to rebuild the cache
		self.def_count  # :pylint: disable-msg=W0104

	def add_subfiles(self, subfiles):
		"""Add subfile to multifile."""
		for from_file, variables in subfiles:
			self.from_files.add(from_file)
			self.variables |= variables

	def remove_subfile(self, subfile):
		"""Remove subfile and return if set is now empty."""
		self.from_files.discard(subfile)
		if not self.need_divert():
			self.uninstall_divert()

	def __call__(self, args):
		"""Generate multfile from subfile templates."""
		ucr, changed = args
		print 'Multifile: %s' % self.to_file


		if hasattr(self, 'preinst') and self.preinst:
			run_module(self.preinst, 'preinst', ucr, changed)

		if self.def_count == 0 or not self.from_files:
			return

		to_dir = os.path.dirname(self.to_file)
		if not os.path.isdir(to_dir):
			os.makedirs(to_dir, 0755)

		if os.path.isfile(self.dummy_from_file):
			stat = os.stat(self.dummy_from_file)
		elif os.path.isfile(self.to_file):
			stat = os.stat(self.to_file)
		else:
			stat = None

		tmp_to_file = self._temp_file_name()
		try:
			to_fp = open(tmp_to_file, 'w')

			filter_opts = {}

			for from_file in sorted(self.from_files, key=os.path.basename):
				try:
					from_fp = open(from_file, 'r')
				except EnvironmentError:
					continue
				to_fp.write(run_filter(from_fp.read(), ucr,
					srcfiles=self.from_files, opts=filter_opts))

			self._set_perm(stat, tmp_to_file)
			to_fp.close()

			os.rename(tmp_to_file, self.to_file)
		except:
			if os.path.exists(tmp_to_file):
				os.unlink(tmp_to_file)
			raise


		if hasattr(self, 'postinst') and self.postinst:
			run_module(self.postinst, 'postinst', ucr, changed)

		script_file = os.path.join(SCRIPT_DIR, self.to_file.strip("/"))
		if os.path.isfile(script_file):
			run_script(script_file, 'postinst', changed)

	def need_divert(self):
		"""Diversion is needed when at least one multifile and one subfile
		definition exists."""
		return self.def_count >= 1 and self.from_files

	def install_divert(self):
		"""Prepare file for diversion."""
		if self.need_divert():
			super(ConfigHandlerMultifile, self).install_divert()

	def uninstall_divert(self):
		"""Undo diversion of file.
		Returns True when the diversion is removed, False when the diversion is
		still needed."""
		if self.need_divert():
			return False
		return super(ConfigHandlerMultifile, self).uninstall_divert()


class ConfigHandlerFile(ConfigHandlerDiverting):
	"""Handler for (single)file."""

	def __init__(self, from_file, to_file):
		super(ConfigHandlerFile, self).__init__(to_file)
		self.from_file = from_file

	def __call__(self, args):
		"""Generate file from template."""
		ucr, changed = args

		if hasattr(self, 'preinst') and self.preinst:
			run_module(self.preinst, 'preinst', ucr, changed)

		print 'File: %s' % self.to_file

		to_dir = os.path.dirname(self.to_file)
		if not os.path.isdir(to_dir):
			os.makedirs(to_dir, 0755)

		try:
			stat = os.stat(self.from_file)
		except EnvironmentError:
			print >> sys.stderr, "The referenced template file does not exist"
			return None

		tmp_to_file = self._temp_file_name()
		try:
			from_fp = open(self.from_file, 'r')
			to_fp = open(tmp_to_file, 'w')

			filter_opts = {}

			to_fp.write(run_filter(from_fp.read(), ucr,
				srcfiles=[self.from_file], opts=filter_opts))

			self._set_perm(stat, tmp_to_file)
			from_fp.close()
			to_fp.close()

			os.rename(tmp_to_file, self.to_file)
		except:
			if os.path.exists(tmp_to_file):
				os.unlink(tmp_to_file)
			raise

		if hasattr(self, 'postinst') and self.postinst:
			run_module(self.postinst, 'postinst', ucr, changed)

		script_file = self.from_file.replace(FILE_DIR, SCRIPT_DIR)
		if os.path.isfile(script_file):
			run_script(script_file, 'postinst', changed)

	def need_divert(self):
		"""For simple files the diversion is always needed."""
		return True


class ConfigHandlerScript(ConfigHandler):
	"""Handler for scripts."""

	def __init__(self, script):
		super(ConfigHandlerScript, self).__init__()
		self.script = script

	def __call__(self, args):
		"""Call external programm after change."""
		_ucr, changed = args
		print 'Script: %s' % self.script
		if os.path.isfile(self.script):
			run_script(self.script, 'generate', changed)


class ConfigHandlerModule(ConfigHandler):
	"""Handler for module."""

	def __init__(self, module):
		super(ConfigHandlerModule, self).__init__()
		self.module = module

	def __call__(self, args):
		"""Call python module after change."""
		ucr, changed = args
		print 'Module: %s' % self.module
		run_module(self.module, 'generate', ucr, changed)


def grep_variables(text):
	"""Return set of all variables inside @%@ delimiters."""
	return set(VARIABLE_PATTERN.findall(text))


class ConfigHandlers:
	"""Manage handlers for configuration variables."""
	CACHE_FILE = '/var/cache/univention-config/cache'
	# 0: without version
	# 1: with version header
	# 2: switch to handlers mapping to set, drop file, add multifile.def_count
	# 3: split config_registry into sub modules
	VERSION = 3
	VERSION_MIN = 3
	VERSION_MAX = 3
	VERSION_TEXT = 'univention-config cache, version'
	VERSION_NOTICE = '%s %s\n' % (VERSION_TEXT, VERSION)
	VERSION_RE = re.compile('^%s (?P<version>[0-9]+)$' % VERSION_TEXT)

	_handlers = {}    # variable -> set(handlers)
	_multifiles = {}  # multifile -> handler
	_subfiles = {}    # multifile -> [(subfile, variables)] // pending

	def __init__(self):
		pass

	def _get_cache_version(self, cache_file):
		"""Read cached .info data."""
		line = cache_file.readline()    # IOError is propagated
		match = ConfigHandlers.VERSION_RE.match(line)
		if match:
			version = int(match.group('version'))
		# "Old style" cache (version 0) doesn't contain version notice
		else:
			cache_file.seek(0)
			version = 0
		return version

	def load(self):
		"""Load cached .info data or force update."""
		try:
			cache_file = open(ConfigHandlers.CACHE_FILE, 'r')
			try:
				version = self._get_cache_version(cache_file)
				chv = ConfigHandlers
				if not chv.VERSION_MIN <= version <= chv.VERSION_MAX:
					raise TypeError("Invalid cache file version.")
				pickler = cPickle.Unpickler(cache_file)
				self._handlers = pickler.load()
				if version <= 1:
					# version <= 1: _handlers[multifile] -> [handlers]
					# version >= 2: _handlers[multifile] -> set([handlers])
					self._handlers = dict(((k, set(v)) for k, v in
						self._handlers.items()))
					# version <= 1: _files UNUSED
					_files = pickler.load()
				self._subfiles = pickler.load()
				self._multifiles = pickler.load()
			finally:
				cache_file.close()
		except (StandardError, cPickle.UnpicklingError):
			self.update()

	def strip_basepath(self, path, basepath):
		"""Strip basepath prefix from path."""
		return path.replace(basepath, '')

	def get_handler(self, entry):
		"""Parse entry and return Handler instance."""
		try:
			typ = entry['Type'][0]
			handler = getattr(self, '_get_handler_%s' % typ)
		except (LookupError, NameError):
			return None
		else:
			return handler(entry)

	def _parse_common_file_handler(self, handler, entry):
		"""Parse common file and multifile entries."""
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
				handler.user = getpwnam(user).pw_uid
			except LookupError:
				print >> sys.stderr, ('W: failed to convert the username ' +
						'%s to the uid' % (user,))

		try:
			group = entry['Group'][0]
		except LookupError:
			pass
		else:
			try:
				handler.group = getgrnam(group).gr_gid
			except LookupError:
				print >> sys.stderr, ('W: failed to convert the groupname ' +
						'%s to the gid' % (group,))

		try:
			mode = entry['Mode'][0]
		except LookupError:
			pass
		else:
			try:
				handler.mode = int(mode, 8)
			except ValueError:
				print >> sys.stderr, 'W: failed to convert mode %s' % (mode,)

	def _get_handler_file(self, entry):
		"""Parse file entry and return Handler instance."""
		try:
			name = entry['File'][0]
		except LookupError:
			return None
		from_path = os.path.join(FILE_DIR, name)
		handler = ConfigHandlerFile(from_path, name)
		if os.path.exists(from_path):
			handler.variables = grep_variables(open(from_path, 'r').read())

		self._parse_common_file_handler(handler, entry)

		return handler

	def _get_handler_script(self, entry):
		"""Parse script entry and return Handler instance."""
		try:
			script = entry['Script'][0]
			variables = entry['Variables']
		except LookupError:
			return None
		handler = ConfigHandlerScript(os.path.join(SCRIPT_DIR, script))
		handler.variables = set(variables)
		return handler

	def _get_handler_module(self, entry):
		"""Parse module entry and return Handler instance."""
		try:
			module = entry['Module'][0]
			variables = entry['Variables']
		except LookupError:
			return None
		handler = ConfigHandlerModule(os.path.splitext(module)[0])
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
			from_path = os.path.join(FILE_DIR, mfile)
			handler = ConfigHandlerMultifile(from_path, mfile)

		self._parse_common_file_handler(handler, entry)

		# Add pending subfiles from earlier entries
		self._multifiles[mfile] = handler
		try:
			file_vars = self._subfiles.pop(mfile)
			handler.add_subfiles(file_vars)
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
		name = os.path.join(FILE_DIR, subfile)
		try:
			temp_file = open(name, 'r')
			try:
				variables |= grep_variables(temp_file.read())
			finally:
				temp_file.close()
		except EnvironmentError:
			print >> sys.stderr, "Failed to process Subfile %s" % (name,)
			return None
		qentry = (name, variables)
		# if multifile handler does not yet exists, queue subfiles for later
		try:
			handler = self._multifiles[mfile]
			handler.add_subfiles([qentry])
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
		for info in directory_files(INFO_DIR):
			if not info.endswith('.info'):
				continue
			for section in parseRfc822(open(info, 'r').read()):
				handler = self.get_handler(section)
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
		wanted = dict([(h.to_file, h) for h in handlers if \
				isinstance(h, ConfigHandlerDiverting) and h.need_divert()])
		to_remove = set()
		# Scan for diversions done by UCR
		div_file = open('/var/lib/dpkg/diversions', 'r')
		# from \n to \n package \n
		try:
			try:
				while True:
					path_from = div_file.next().rstrip()
					path_to = div_file.next().rstrip()
					diversion = div_file.next().rstrip()
					if path_from + '.debian' != path_to:
						continue
					if ':' != diversion:  # local diversion
						continue
					assert path_from not in to_remove  # no duplicates
					try:
						handler = wanted.pop(path_from)
					except KeyError:
						to_remove.add(path_from)
			except StopIteration:
				pass
		finally:
			div_file.close()
		# Remove existing diversion not wanted
		for path in to_remove:
			tmp_handler = ConfigHandlerDiverting(path)
			tmp_handler.uninstall_divert()
		# Install missing diversions still wanted
		for path, handler in wanted.items():
			handler.install_divert()

	def _save_cache(self):
		"""Write cache file."""
		try:
			with open(ConfigHandlers.CACHE_FILE, 'w') as cache_file:
				cache_file.write(ConfigHandlers.VERSION_NOTICE)
				pickler = cPickle.Pickler(cache_file)
				pickler.dump(self._handlers)
				pickler.dump(self._subfiles)
				pickler.dump(self._multifiles)
		except IOError as ex:
			if ex.errno != errno.EACCES:
				raise

	def register(self, package, ucr):
		"""Register new info file for package."""
		handlers = set()
		fname = os.path.join(INFO_DIR, '%s.info' % package)
		for section in parseRfc822(open(fname, 'r').read()):
			handler = self.get_handler(section)
			if handler:
				handlers.add(handler)

		for handler in handlers:
			if isinstance(handler, ConfigHandlerDiverting):
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
		"""Un-register info file for package.
		Returns set of (then obsolete) handlers."""
		obsolete_handlers = set()  # Obsolete handlers
		mf_handlers = set()  # Remaining Multifile handlers
		fname = os.path.join(INFO_DIR, '%s.info' % package)
		for section in parseRfc822(open(fname, 'r').read()):
			try:
				typ = section['Type'][0]
			except LookupError:
				continue
			if typ == 'file':
				handler = self.get_handler(section)
			elif typ == 'subfile':
				mfile = section['Multifile'][0]
				sfile = section['Subfile'][0]
				try:
					handler = self._multifiles[mfile]
				except KeyError:
					continue  # skip SubFile w/o MultiFile
				name = os.path.join(FILE_DIR, sfile)
				handler.remove_subfile(name)
				mf_handlers.add(handler)
			elif typ == 'multifile':
				mfile = section['Multifile'][0]
				handler = self._multifiles[mfile]
				handler.def_count -= 1
				mf_handlers.add(handler)
			else:
				continue
			if not handler:  # Bug #17913
				print >> sys.stderr, ("Skipping internal error: no handler " +
						"for %r in %s" % (section, package))
				continue
			if handler.uninstall_divert():
				obsolete_handlers.add(handler)

		for handler in mf_handlers - obsolete_handlers:
			self.call_handler(ucr, handler)

		try:
			# remove cache file to force rebuild of cache
			os.unlink(ConfigHandlers.CACHE_FILE)
		except EnvironmentError:
			pass
		return obsolete_handlers

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

	def commit(self, ucr, filelist=list()):
		"""Call handlers to (re-)generate files."""
		_filelist = []
		for fname in filelist:
			fname = os.path.expanduser(fname)
			fname = os.path.expandvars(fname)
			fname = os.path.abspath(fname)
			_filelist.append(fname)
		# find handlers
		pending_handlers = set()
		for fname in directory_files(INFO_DIR):
			if not fname.endswith('.info'):
				continue
			for section in parseRfc822(open(fname, 'r').read()):
				if not section.get('Type'):
					continue
				handler = None
				if _filelist:
					files = section.get('File') or \
							section.get('Multifile') or ()
					for filename in files:
						if not os.path.isabs(filename):
							filename = '/%s' % filename
						if filename in _filelist:
							handler = self.get_handler(section)
							break
					else:
						continue
				else:
					handler = self.get_handler(section)
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

# vim:set sw=4 ts=4 noet:
