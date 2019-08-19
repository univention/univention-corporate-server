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

import univention.ucslint.base as uub
from os import walk
from os.path import basename, dirname, isdir, join, normpath, relpath, splitext
from glob import glob
from typing import Callable, Dict, Iterator, List, Set, Tuple  # noqa F401


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def getMsgIds(self):
		return {
			'0018-1': (uub.RESULT_STYLE, 'wrong script name in comment'),
			'0018-2': (uub.RESULT_STYLE, 'Unneeded entry in debian/dirs; the directory is implicitly created by another debhelper'),
			'0018-3': (uub.RESULT_WARN, 'Invalid action in Debian maintainer script'),
		}

	def check(self, path):
		# type: (str) -> None
		self.check_scripts(path)
		self.check_dirs(path)

	def check_scripts(self, path):
		# type: (str) -> None
		SCRIPTS = frozenset(('preinst', 'postinst', 'prerm', 'postrm'))
		debianpath = join(path, 'debian')
		for script_path in uub.FilteredDirWalkGenerator(debianpath, suffixes=SCRIPTS):
			package, suffix = self.split_pkg(script_path)

			with open(script_path, 'r') as script_file:
				for nr, line in enumerate(script_file, start=1):
					if not line.startswith('#'):
						break
					for script_name in SCRIPTS - set((suffix,)):
						if script_name in line:
							self.addmsg(
								'0018-1',
								'wrong script name: %r' % (line.strip(),),
								filename=script_path,
								line=nr)

	def check_dirs(self, path):
		# type: (str) -> None
		DIRS = frozenset((
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
		))
		dirs = {}  # type: Dict[str, Set[str]]
		debianpath = join(path, 'debian')

		for fp in uub.FilteredDirWalkGenerator(debianpath, suffixes=['install']):
			package, suffix = self.split_pkg(fp)
			pkg = dirs.setdefault(package, {'usr/share/doc/' + package} | DIRS)
			# ~/doc/2018-04-11-ApiDoc/pymerge
			for lnr, line in self.lines(fp):
				for src, dst in self.process_install(line):
					self.debug('%s:%d Installs %s to %s' % (fp, lnr, src, dst))
					path = dirname(normpath(dst.strip('/')))
					while path > '/':
						pkg.add(path)
						path = dirname(path)

		for fp in uub.FilteredDirWalkGenerator(debianpath, suffixes=['dirs']):
			package, suffix = self.split_pkg(fp)
			pkg = dirs.setdefault(package, {'usr/share/doc/' + package} | DIRS)
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
