# vim:set ts=4 sw=4 noet fileencoding=UTF-8 :
"""Find maintainer scripts using wrong header."""
#
# Copyright (C) 2016-2020 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

import re
from glob import glob
from os import walk
from os.path import basename, dirname, isdir, join, normpath, relpath, splitext
from shlex import split
from typing import Callable, Dict, Iterator, List, Set, Tuple  # noqa F401

import univention.ucslint.base as uub


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	# https://www.debian.org/doc/debian-policy/ch-maintainerscripts.html#summary-of-ways-maintainer-scripts-are-called
	# https://wiki.debian.org/DpkgTriggers
	ACTIONS = {
		'preinst': {'install', 'upgrade', 'abort-upgrade'},
		'postinst': {'configure', 'abort-upgrade', 'abort-remove', 'abort-deconfigure', 'triggered'},
		'prerm': {'remove', 'upgrade', 'deconfigure', 'failed-upgrade'},
		'postrm': {'remove', 'purge', 'upgrade', 'disappear', 'failed-upgrade', 'abort-install', 'abort-upgrade'},
	}
	SCRIPTS = frozenset(ACTIONS)

	def getMsgIds(self):
		return {
			'0018-1': (uub.RESULT_STYLE, 'wrong script name in comment'),
			'0018-2': (uub.RESULT_STYLE, 'Unneeded entry in debian/dirs; the directory is implicitly created by another debhelper'),
			'0018-3': (uub.RESULT_WARN, 'Invalid action in Debian maintainer script'),
			'0018-4': (uub.RESULT_WARN, 'Use debian/*.pyinstall to install Python modules'),
		}

	def check(self, path):
		# type: (str) -> None
		self.check_scripts(path)
		self.check_dirs(path)

	def check_scripts(self, path):
		# type: (str) -> None
		debianpath = join(path, 'debian')
		for script_path in uub.FilteredDirWalkGenerator(debianpath, suffixes=self.SCRIPTS):
			package, suffix = self.split_pkg(script_path)

			other_scripts = self.SCRIPTS - {suffix}
			other_actions = set(action for actions in self.ACTIONS.values() for action in actions) - self.ACTIONS[suffix]
			self.debug('script=%s' % suffix)
			self.debug('actions=%s' % ' '.join(sorted(self.ACTIONS[suffix])))
			self.debug('other_script=%s' % ' '.join(sorted(other_scripts)))
			self.debug('other_actions=%s' % ' '.join(sorted(other_actions)))

			with open(script_path, 'r') as script_file:
				content = script_file.read()

			for nr, line in enumerate(content.splitlines(), start=1):
				if not line.startswith('#'):
					break
				for script_name in other_scripts:
					if script_name in line:
						self.addmsg(
							'0018-1',
							'wrong script name: %r' % (line.strip(),),
							filename=script_path,
							line=nr)

			for nr, line in enumerate(content.splitlines(), start=1):
				if line.startswith('#'):
					continue
				for match in self.RE_TEST.finditer(line):
					try:
						actions = self.parse_test(split(match.group('cond'))) & other_actions
					except ValueError as ex:
						self.debug('Failed %s:%d: %s in %s' % (script_path, nr, ex, line))
						continue
					if actions:
						self.addmsg(
							'0018-3',
							'Invalid actions "%s" in Debian maintainer script' % (','.join(actions),),
							filename=script_path,
							line=nr)

			nr = 1
			col = 1
			pos = 0
			for match in self.RE_CASE.finditer(content):
				for cases in match.group('cases').split(';;'):
					cases = cases.lstrip('\t\n\r (')
					cases = cases.split(')', 1)[0]
					actions = set(action for case in cases.split('|') for action in split(case)) & other_actions
					if actions:
						start, end = match.span()
						while pos < start:
							if match.string[pos] == "\n":
								col = 1
								nr += 1
							else:
								col += 1
							pos += 1

						self.addmsg(
							'0018-3',
							'Invalid actions "%s" in Debian maintainer script' % (','.join(actions),),
							filename=script_path, line=nr, pos=col)

	@classmethod
	def parse_test(cls, tokens):
		# type: (List[str]) -> Set[str]
		"""
		Parse test string and return action names

		:param tokens: `test` string tokens.
		:returns: Set containing the action names

		>>> UniventionPackageCheck.parse_test(['$1', '=', 'upgrade'])
		{'upgrade'}
		>>> UniventionPackageCheck.parse_test(['upgrade', '!=', '${1}'])
		{'upgrade'}
		>>> UniventionPackageCheck.parse_test(['(', '-n', '$1', ')'])
		set()
		>>> UniventionPackageCheck.parse_test(['-n', '$1'])
		set()
		>>> UniventionPackageCheck.parse_test(['-n', '$1', '-a', '-z', '$1'])
		set()
		>>> UniventionPackageCheck.parse_test(['1', '-le', '2'])
		set()
		>>> UniventionPackageCheck.parse_test(['$1'])
		set()
		"""
		COND = {'-a', '-o'}
		UNARY = {'-b', '-c', '-d', '-e', '-f', '-g', '-G', '-h', '-k', '-L', '-n', '-O', '-p', '-r', '-s', '-S', '-t', '-u', '-w', '-x', '-z'}
		COMP1 = {'-ot', '-nt', '-ef', '-ne', '-lt', '-le', '-gt', '-ge', '-eq'}
		COMP2 = {'=', '!=', '==', '=~'}
		result = set()
		while tokens:
			t = tokens.pop(0)
			if t == ')':
				break
			elif t == '(':
				result |= cls.parse_test(tokens)
			elif t == '!':
				pass
			elif t in COND:
				pass
			elif t in UNARY:
				tokens.pop(0)
			elif t.startswith('-'):
				raise ValueError(t)
			elif tokens:
				op = tokens.pop(0)
				if op in COMP1 | COMP2:
					arg = tokens.pop(0)
					if op in COMP2:
						if cls.RE_ARG1.match(t):
							result.add(arg)
						elif cls.RE_ARG1.match(arg):
							result.add(t)
				elif op in COND:
					pass  # [-n] t
				else:
					raise ValueError(op)
			else:
				pass  # [-n] t

		return result

	def check_dirs(self, path):
		# type: (str) -> None
		dirs = {}  # type: Dict[str, Set[str]]
		debianpath = join(path, 'debian')

		for fp in uub.FilteredDirWalkGenerator(debianpath, suffixes=['install']):
			package, suffix = self.split_pkg(fp)
			pkg = dirs.setdefault(package, Dirs(package))
			py_install = False
			# ~/doc/2018-04-11-ApiDoc/pymerge
			for lnr, line in self.lines(fp):
				dst = ''
				for src, dst in self.process_install(line):
					self.debug('%s:%d Installs %s to %s' % (fp, lnr, src, dst))
					pkg.add(dst)

				if self.RE_PYTHONPATHS.match(dst):
					self.addmsg(
						'0018-4',
						'Use debian/*.pyinstall to install Python modules',
						filename=fp,
						line=lnr)

		for fp in uub.FilteredDirWalkGenerator(debianpath, suffixes=['pyinstall']):
			package, suffix = self.split_pkg(fp)
			pkg = dirs.setdefault(package, Dirs(package))
			for lnr, line in self.lines(fp):
				for src, dst in self.process_pyinstall(line):
					self.debug('%s:%d Installs %s to %s' % (fp, lnr, src, dst))
					pkg.add(dst)

		for fp in uub.FilteredDirWalkGenerator(debianpath, suffixes=['dirs']):
			package, suffix = self.split_pkg(fp)
			pkg = dirs.setdefault(package, Dirs(package))
			for lnr, line in self.lines(fp):
				line = line.strip('/')
				if line in pkg:
					self.addmsg(
						'0018-2',
						'Unneeded directory %r' % (line,),
						filename=fp,
						line=lnr)

	@staticmethod
	def lines(name):
		# type: (str) -> Iterator[Tuple[int, str]]
		with open(name, 'r') as stream:
			for lnr, line in enumerate(stream, start=1):
				line = line.strip()
				if not line:
					continue
				if line.startswith('#'):
					continue
				yield (lnr, line)

	@staticmethod
	def split_pkg(name):
		# type: (str) -> Tuple[str, str]
		filename = basename(name)
		if '.' in filename:
			package, suffix = splitext(filename)
			suffix = suffix.lstrip('.')
		else:
			package = ''
			suffix = filename

		return (package, suffix)

	@staticmethod
	def process_install(line, glob=glob):
		# type: (str, Callable) -> Iterator[Tuple[str, str]]
		"""
		Parse :file:`debian/*.install` lines.

		>>> list(UniventionPackageCheck.process_install("usr"))
		[('usr', 'usr')]
		>>> list(UniventionPackageCheck.process_install("usr    prefix/"))
		[('usr', 'prefix/usr')]
		>>> fake_glob = lambda pat: ['src/__init__.py']
		>>> list(UniventionPackageCheck.process_install("src/*.py", glob=fake_glob))
		[('src/__init__.py', 'src/__init__.py')]
		>>> list(UniventionPackageCheck.process_install("src/*.py    prefix/", glob=fake_glob))
		[('src/__init__.py', 'prefix/__init__.py')]
		"""
		args = [_.strip('/') for _ in line.split()]
		dst = args.pop() if len(args) >= 2 else dirname(args[0])

		for src in args:
			for fn in glob(src) if ('*' in src or '?' in src or '[' in src) else [src]:
				if isdir(fn):
					for root, dirs, files in walk(fn):
						for name in files:
							src_path = join(root, name)
							dst_path = join(dst, relpath(src_path, dirname(fn)))
							yield (src_path, dst_path)
				else:
					yield (fn, join(dst, basename(fn)))

	@classmethod
	def process_pyinstall(cls, line, glob=glob):
		# type: (str, Callable) -> Iterator[Tuple[str, str]]
		"""
		Parse :file:`debian/*.pyinstall` lines.

		>>> list(UniventionPackageCheck.process_pyinstall("foo.py"))
		[('foo.py', 'foo.py')]
		>>> list(UniventionPackageCheck.process_pyinstall("foo/bar.py 2.6-"))
		[('foo/bar.py', 'foo/bar.py')]
		>>> list(UniventionPackageCheck.process_pyinstall("foo/bar.py spam"))
		[('foo/bar.py', 'spam/bar.py')]
		>>> list(UniventionPackageCheck.process_pyinstall("foo/bar.py spam.egg 2.5"))
		[('foo/bar.py', 'spam/egg/bar.py')]
		"""
		args = line.split()
		src = args.pop(0)
		if args and cls.RE_VERSION_RANGE.match(args[-1]):
			args.pop(-1)
		dst = args.pop(0).replace('.', '/') if args and cls.RE_NAMESPACE.match(args[0]) else dirname(src)
		assert not args, args

		for fn in glob(src) if ('*' in src or '?' in src or '[' in src) else [src]:
			yield (fn, join(dst, basename(fn)))

	RE_HASHBANG = re.compile(r'^#!\s*/bin/(?:[bd]?a)?sh\b')
	RE_TEST = re.compile(
		r'''
		(?:(?P<test>\[{1,2}) | \b test)
		\s+
		(?P<cond>.+?)
		(?(test)\s+\]{1,2} | (?:\s*(?:; | && | \|\| | $)))
		''', re.VERBOSE)
	RE_CASE = re.compile(
		r'''
		\b
		case
		\s+
		(?P<quot>"?)
		(?:\$(?:1|\{1[#%:?+=/-[^}]*\}))
		(?P=quot)
		\s+
		in
		\s+
		(?P<cases>.+?)
		\b
		esac
		\b
		''', re.VERBOSE | re.DOTALL)
	RE_ARG1 = re.compile(r'\$(?:1|\{1[#%:?+=/-[^}]*\})')
	# /usr/share/dh-python/dhpython/version.py # VERSION_RE
	RE_VERSION_RANGE = re.compile(
		r'''^
		\d+\.\d+
		(?:- (?:\d+\.\d+)? )?
		(?:,
		   \d+\.\d+
		   (?:- (?:\d+\.\d+)? )?
		)*
		$''', re.VERBOSE)
	# /usr/share/dh-python/dhpython/tools.py # INSTALL_RE
	RE_NAMESPACE = re.compile(
		r'''^
		(?![0-9])\w+
		(?:\. (?![0-9])\w+ )*
		$''', re.VERBOSE)
	RE_PYTHONPATHS = re.compile(
		r'''^/?
		(?:usr/lib/pymodules/python[0-9.]+/
		  |usr/lib/python[0-9.]+/
		  |usr/share/pyshared/
		)''', re.VERBOSE)


class Dirs(set):
	"""Set of directories."""

	DIRS = frozenset({
		'bin',
		'etc',
		'etc/cron.d',
		'etc/cron.hourly',
		'etc/cron.daily',
		'etc/cron.weekly',
		'etc/cron.monthly',
		'etc/default',
		'etc/init.d',
		'lib',
		'lib/security',
		'sbin',
		'usr',
		'usr/bin',
		'usr/lib',
		'usr/sbin',
		'var',
		'var/lib',
		'var/log',
		'var/www',
	})

	def __init__(self, package):  # type: (str) -> None
		set.__init__(self, {'usr/share/doc/' + package} | self.DIRS)

	def add(self, dst):  # type: (str) -> None
		path = dirname(normpath(dst.strip('/')))
		while path > '/':
			set.add(self, path)
			path = dirname(path)


if __name__ == '__main__':
	import doctest
	doctest.testmod()
