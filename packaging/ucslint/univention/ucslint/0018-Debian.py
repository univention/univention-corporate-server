# vim:set ts=4 sw=4 noet fileencoding=UTF-8 :
"""Find maintainer scripts using wrong header."""
#
# Copyright (C) 2016-2022 Univention GmbH
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
from itertools import cycle
from os import walk
from os.path import basename, dirname, isdir, join, normpath, relpath, splitext
from shlex import split
from typing import Callable, Dict, Iterable, Iterator, List, Set, Tuple, Union  # noqa: F401

from debian.changelog import Changelog, ChangelogParseError  # Version

import univention.ucslint.base as uub
from univention.ucslint.common import RE_DEBIAN_PACKAGE_VERSION


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

	def getMsgIds(self) -> uub.MsgIds:
		return {
			'0018-1': (uub.RESULT_STYLE, 'wrong script name in comment'),
			'0018-2': (uub.RESULT_STYLE, 'Unneeded entry in debian/dirs; the directory is implicitly created by another debhelper'),
			'0018-3': (uub.RESULT_WARN, 'Invalid action in Debian maintainer script'),
			'0018-4': (uub.RESULT_WARN, 'Use debian/*.pyinstall to install Python modules'),
			'0018-5': (uub.RESULT_INFO, 'Maintainer script contains old upgrade code'),
		}

	def check(self, path: str) -> None:
		self.check_scripts(path)
		self.check_dirs(path)

	def get_debian_version(self, path: str) -> "Version":
		try:
			fn_changelog = join(path, 'debian', 'changelog')
			with open(fn_changelog, 'r') as fd:
				changelog = Changelog(fd)

			return Version(changelog.version.full_version)
		except (EnvironmentError, ChangelogParseError) as ex:
			self.debug('Failed open %r: %s' % (fn_changelog, ex))
			return Version('0')

	def check_scripts(self, path: str) -> None:
		debianpath = join(path, 'debian')
		version = self.get_debian_version(path)
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

			for row, line in enumerate(content.splitlines(), start=1):
				if not line.startswith('#'):
					break
				for script_name in other_scripts:
					if script_name in line:
						self.addmsg(
							'0018-1',
							'wrong script name: %r' % (line.strip(),),
							script_path, row, line=line)

			for row, line in enumerate(content.splitlines(), start=1):
				if line.startswith('#'):
					continue
				for match in self.RE_TEST.finditer(line):
					try:
						actions = self.parse_test(split(match.group('cond'))) & other_actions
					except ValueError as ex:
						self.debug('Failed %s:%d: %s in %s' % (script_path, row, ex, line))
						continue
					if actions:
						self.addmsg(
							'0018-3',
							'Invalid actions "%s" in Debian maintainer script' % (','.join(actions),),
							script_path, row, line=line)

				for match in self.RE_COMPARE_VERSIONS.finditer(line):
					ver_a, op, ver_b = match.groups()
					for arg in (ver_a, ver_b):
						if self.RE_ARG2.match(arg):
							continue
						if not RE_DEBIAN_PACKAGE_VERSION.match(arg):
							self.debug("%s:%d: Unknown argument %r" % (script_path, row, arg))
							continue

						ver = Version(arg)
						self.debug("%s << %s?" % (ver, version))
						if ver.numeric and version.numeric and ver.numeric[0] < version.numeric[0] - 1:
							self.addmsg(
								'0018-5',
								'Maintainer script contains old upgrade code for %s << %s' % (ver, version),
								script_path, row, match.start(0), line)

			for row, col, match in uub.line_regexp(content, self.RE_CASE):
				for cases in match.group('cases').split(';;'):
					cases = cases.lstrip('\t\n\r (')
					cases = cases.split(')', 1)[0]
					actions = set(action for case in cases.split('|') for action in split(case)) & other_actions
					if actions:
						self.addmsg(
							'0018-3',
							'Invalid actions "%s" in Debian maintainer script' % (','.join(actions),),
							script_path, row, col, line=line)

	@classmethod
	def parse_test(cls, tokens: List[str]) -> Set[str]:
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

	def check_dirs(self, path: str) -> None:
		dirs = {}  # type: Dict[str, Set[str]]
		debianpath = join(path, 'debian')

		for fp in uub.FilteredDirWalkGenerator(debianpath, suffixes=['install']):
			package, suffix = self.split_pkg(fp)
			pkg = dirs.setdefault(package, Dirs(package))
			# ~/doc/2018-04-11-ApiDoc/pymerge
			for row, line in self.lines(fp):
				dst = ''
				for src, dst in self.process_install(line):
					self.debug('%s:%d Installs %s to %s' % (fp, row, src, dst))
					pkg.add(dst)

				if self.RE_PYTHONPATHS.match(dst):
					self.addmsg(
						'0018-4',
						'Use debian/*.pyinstall to install Python modules',
						fp, row)

		for fp in uub.FilteredDirWalkGenerator(debianpath, suffixes=['pyinstall']):
			package, suffix = self.split_pkg(fp)
			pkg = dirs.setdefault(package, Dirs(package))
			for row, line in self.lines(fp):
				for src, dst in self.process_pyinstall(line):
					self.debug('%s:%d Installs %s to %s' % (fp, row, src, dst))
					pkg.add(dst)

		for fp in uub.FilteredDirWalkGenerator(debianpath, suffixes=['dirs']):
			package, suffix = self.split_pkg(fp)
			pkg = dirs.setdefault(package, Dirs(package))
			for row, line in self.lines(fp):
				line = line.strip('/')
				if line in pkg:
					self.addmsg(
						'0018-2',
						'Unneeded directory %r' % (line,),
						fp, row)

	@staticmethod
	def lines(name: str) -> Iterator[Tuple[int, str]]:
		with open(name, 'r') as stream:
			for row, line in enumerate(stream, start=1):
				line = line.strip()
				if not line:
					continue
				if line.startswith('#'):
					continue
				yield (row, line)

	@staticmethod
	def split_pkg(name: str) -> Tuple[str, str]:
		filename = basename(name)
		if '.' in filename:
			package, suffix = splitext(filename)
			suffix = suffix.lstrip('.')
		else:
			package = ''
			suffix = filename

		return (package, suffix)

	@staticmethod
	def process_install(line: str, glob: Callable[[str], Iterable[str]] = glob) -> Iterator[Tuple[str, str]]:
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
	def process_pyinstall(cls, line: str, glob: Callable[[str], Iterable[str]] = glob) -> Iterator[Tuple[str, str]]:
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
		$''', re.VERBOSE)  # noqa: E101
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
		)''', re.VERBOSE)  # noqa: E101
	RE_COMPARE_VERSIONS = re.compile(
		r'''
		\b dpkg \s+ --compare-versions
		\s+
		( (?: '[^']*' | "[^"]*" | \S )+ )
		\s+
		([lg][et](?:-nl)?|eq|ne|<[<=]?|=|>[>=]?)
		\s+
		( (?: '[^']*' | "[^"]*" | \S )+ )
		\s*(?: $ | ; | && | \|\| | \))
		''', re.VERBOSE)  # noqa: E101
	RE_ARG2 = re.compile(r'^("?)\$(?:2|\{2[#%:?+=/-[^}]*\})(\1)$')


class Dirs(Set[str]):
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

	def __init__(self, package: str) -> None:
		set.__init__(self, {'usr/share/doc/' + package} | self.DIRS)

	def add(self, dst: str) -> None:
		path = dirname(normpath(dst.strip('/')))
		while path > '/':
			set.add(self, path)
			path = dirname(path)


class Version(object):
	"""
	Version as a sqeunce of numeric and non-numeric parts.

	>>> str(Version('1'))
	'1'
	>>> str(Version('first'))
	'first'
	>>> str(Version("1:2.34alpha~5-6.7"))
	'1:2.34alpha~5-6.7'
	"""

	__slots__ = ('text', 'numeric')

	RE_VERSION = re.compile(r'([0-9]+)')

	def __init__(self, text: str) -> None:
		parts = self.RE_VERSION.split(text)
		self.text = parts[::2]
		self.numeric = [int(number) for number in parts[1::2]]

	def __iter__(self) -> Iterator[Union[str, int]]:
		try:
			for next in cycle(iter(part).__next__ for part in (self.text, self.numeric)):  # type: ignore
				yield next()
		except StopIteration:
			pass

	def __str__(self) -> str:
		return ''.join(str(part) for part in self)

	def __repr__(self) -> str:
		return '%s(%r)' % (self.__class__.__name__, self.__str__())


if __name__ == '__main__':
	import doctest
	doctest.testmod()
