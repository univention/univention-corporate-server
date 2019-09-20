#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:set fileencoding=utf-8 sw=4 ts=4 et:
#
# Copyright (C) 2008-2019 Univention GmbH
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

from __future__ import print_function
from os import listdir
from os.path import join, exists, curdir, splitext
import re
from glob import glob
try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub
from apt import Cache


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
	RE_FIELD = re.compile("([a-z0-9_]+)[ \t]*(?:(<<|<=|=|>=|>>)[ \t]*([-a-zA-Z0-9.+~]+))?")
	RE_INIT = re.compile("^(?:File|Subfile): (etc/init.d/.+)$")
	RE_TRANSITIONAL = re.compile(r'\b[Tt]ransition(?:al)?(?: dummy)? [Pp]ackage\b')  # re.IGNORECASE
	DEPS = {
		'uicr': (re.compile("(?:/usr/bin/)?univention-install-(?:config-registry(?:-info)?|service-info)"), set(('univention-config-dev',))),
		'umcb': (re.compile("(?:/usr/bin/)?dh-umc-module-build"), set(('univention-management-console-dev',))),
		'ucr': (re.compile("""(?:^|(?<=['";& \t]))(?:/usr/sbin/)?(?:univention-config-registry|ucr)(?:(?=['";& \t])|$)"""), set(('univention-config', '${misc:Depends}'))),
		'ial': (re.compile("/usr/share/univention-config-registry/init-autostart\.lib"), set(('univention-base-files',))),
	}

	def __init__(self):
		super(UniventionPackageCheck, self).__init__()
		self.apt = None

	def getMsgIds(self):
		return {
			'0014-0': [uub.RESULT_WARN, 'failed to open/read file'],
			'0014-1': [uub.RESULT_ERROR, 'parsing error in debian/control'],
			'0014-2': [uub.RESULT_ERROR, 'univention-install-... is used in debian/rules, but debian/control lacks a build-dependency on univention-config-dev.'],
			'0014-3': [uub.RESULT_ERROR, 'dh-umc-module-build is used in debian/rules, but debian/control lacks a build-dependency on univention-management-console-dev.'],
			'0014-4': [uub.RESULT_ERROR, 'univention-config-registry is used in a .preinst script, but the package lacks a pre-dependency on univention-config.'],
			'0014-5': [uub.RESULT_ERROR, 'univention-config-registry is used in a maintainer script, but the package lacks a dependency on univention-config.'],
			'0014-6': [uub.RESULT_WARN, 'init-autostart.lib is sourced by a script, but the package lacks an explicit dependency on univention-base-files.'],
			'0014-7': [uub.RESULT_WARN, 'The source package contains debian/*.univention- files, but the package is not found in debian/control.'],
			'0014-8': [uub.RESULT_WARN, 'unexpected UCR file'],
			'0014-9': [uub.RESULT_WARN, 'depends on transitional package'],
		}

	def postinit(self, path):
		"""Checks to be run before real check or to create pre-calculated data for several runs. Only called once!"""
		try:
			self.apt = Cache(memonly=True)
		except Exception as ex:
			self.debug('failed to load APT cache: %s' % (ex,))

	def _split_field(self, s):
		"""Split control field into parts. Returns generator."""
		for con in s.split(','):
			con = con.strip()
			for dis in con.split('|'):
				i = dis.find('(')
				if i >= 0:
					dis = dis[:i]

				pkg = dis.strip()
				if pkg:
					yield pkg

	def _scan_script(self, fn):
		"""find calls to 'univention-install-', 'ucr' and use of 'init-autostart.lib' in file 'fn'."""
		need = set()
		self.debug('Reading %s' % (fn,))
		try:
			f = open(fn, 'r')
		except (OSError, IOError):
			self.addmsg('0014-0', 'failed to open and read file', filename=fn)
			return need
		try:
			for l in f:
				for (key, (regexp, pkgs)) in UniventionPackageCheck.DEPS.items():
					if regexp.search(l):
						self.debug('Found %s in %s' % (key.upper(), fn))
						need.add(key)
		finally:
			f.close()

		return need

	def check_source(self, source_section):
		"""Check source package for dependencies."""
		src_arch = source_section.get('Build-Depends', '')
		src_arch = self._split_field(src_arch)
		src_arch = set(src_arch)
		self.debug('Build-Depends: %s' % (src_arch,))
		src_indep = source_section.get('Build-Depends-Indep', '')
		src_indep = self._split_field(src_indep)
		src_indep = set(src_indep)
		self.debug('Build-Depends-Indep: %s' % (src_indep,))
		src_deps = src_arch | src_indep

		fn = join(self.path, 'debian', 'rules')
		need = self._scan_script(fn)
		uses_uicr = 'uicr' in need
		uses_umcb = 'umcb' in need

		# Assert packages using "univention-install-" build-depens on "univention-config-dev" and depend on "univention-config"
		if uses_uicr and not src_deps & UniventionPackageCheck.DEPS['uicr'][1]:
			self.addmsg('0014-2', 'Missing Build-Depends: univention-config-dev', filename=fn)

		if uses_umcb and not src_deps & UniventionPackageCheck.DEPS['umcb'][1]:
			self.addmsg('0014-3', 'Missing Build-Depends: univention-management-console-dev', filename=fn)

		return src_deps

	def check_package(self, section):
		"""Check binary package for dependencies."""
		pkg = section['Package']
		self.debug('Package: %s' % (pkg,))

		bin_pre = section.get('Pre-Depends', '')
		bin_pre = self._split_field(bin_pre)
		bin_pre = set(bin_pre)
		self.debug('Pre-Depends: %s' % (bin_pre,))
		bin_dep = section.get('Depends', '')
		bin_dep = self._split_field(bin_dep)
		bin_dep = set(bin_dep)
		self.debug('Depends: %s' % (bin_dep,))
		bin_rec = section.get('Recommends', '')
		bin_rec = self._split_field(bin_rec)
		bin_rec = set(bin_rec)
		self.debug('Recommends: %s' % (bin_rec,))
		bin_sug = section.get('Suggests', '')
		bin_sug = self._split_field(bin_sug)
		bin_sug = set(bin_sug)
		self.debug('Suggests: %s' % (bin_sug,))
		bin_deps = bin_pre | bin_dep

		# Assert packages using "ucr" in preinst pre-depend on "univention-config"
		for ms in ('preinst',):
			fn = join(self.path, 'debian', '%s.%s' % (pkg, ms))
			if not exists(fn):
				continue
			need = self._scan_script(fn)
			if 'ucr' in need and not bin_pre & UniventionPackageCheck.DEPS['ucr'][1]:
				self.addmsg('0014-4', 'Missing Pre-Depends: univention-config', filename=fn)

		# Assert packages using "ucr" depend on "univention-config"
		for ms in ('postinst', 'prerm', 'postrm'):
			fn = join(self.path, 'debian', '%s.%s' % (pkg, ms))
			if not exists(fn):
				continue
			need = self._scan_script(fn)
			if 'ucr' in need and not bin_deps & UniventionPackageCheck.DEPS['ucr'][1]:
				self.addmsg('0014-5', 'Missing Depends: univention-config, ${misc:Depends}', filename=fn)

		p = join(self.path, '[0-9][0-9]%s.inst' % (pkg,))
		for fn in glob(p):
			need = self._scan_script(fn)
			if 'ucr' in need and not bin_deps & UniventionPackageCheck.DEPS['ucr'][1]:
				self.addmsg('0014-4', 'Missing Depends: univention-config, ${misc:Depends}', filename=fn)

		# FIXME: scan all other files for ucr as well?

		# Assert packages using "init-autostart.lib" depends on "univention-base-files"
		init_files = set()
		init_files.add(join(self.path, 'debian', '%s.init' % (pkg,)))
		init_files.add(join(self.path, 'debian', '%s.init.d' % (pkg,)))
		try:
			fn = join(self.path, 'debian', '%s.univention-config-registry' % (pkg,))
			if exists(fn):
				f = open(fn, 'r')
				try:
					for l in f:
						m = UniventionPackageCheck.RE_INIT.match(l)
						if m:
							fn = join(self.path, 'conffiles', m.group(1))
							init_files.add(fn)
				finally:
					f.close()
		except (IOError, OSError):
			self.addmsg('0014-0', 'failed to open and read file', filename=fn)

		for fn in init_files:
			if not exists(fn):
				continue
			need = self._scan_script(fn)
			if 'ial' in need and not bin_deps & UniventionPackageCheck.DEPS['ial'][1]:
				self.addmsg('0014-6', 'Missing Depends: univention-base-files', filename=fn)

		return bin_deps | bin_rec | bin_sug

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		fn = join(path, 'debian', 'control')
		self.debug('Reading %s' % (fn,))
		try:
			parser = uub.ParserDebianControl(fn)
			self.path = path
		except uub.FailedToReadFile:
			self.addmsg('0014-0', 'failed to open and read file', filename=fn)
			return
		except uub.UCSLintException:
			self.addmsg('0014-1', 'parsing error', filename=fn)
			return

		deps = self.check_source(parser.source_section)
		for section in parser.binary_sections:
			deps |= self.check_package(section)

		self.check_unknown(path, parser)
		self.check_transitional(path, deps)

	def check_unknown(self, path, parser):
		# Assert all files debian/$pkg.$suffix belong to a package $pkg declared in debian/control
		SUFFIXES = (
			'.univention-config-registry',
			'.univention-config-registry-variables',
			'.univention-config-registry-categories',
			'.univention-service',
		)
		exists = set(
			filename
			for filename in listdir(join(path, 'debian'))
			if splitext(filename)[1] in SUFFIXES
		)
		known = set(
			section['Package'] + suffix
			for section in parser.binary_sections
			for suffix in SUFFIXES
		)
		for unowned in exists - known:
			self.addmsg('0014-8', 'unexpected UCR file', filename=join(path, 'debian', unowned))

	def check_transitional(self, path, deps):
		if not self.apt:
			return

		for dep in deps:
			if dep.startswith('${'):
				continue
			try:
				pkg = self.apt[dep]
				cand = pkg.candidate
				if not cand:
					raise LookupError(dep)
			except LookupError as ex:
				self.debug('not found %s: %s' % (dep, ex))
				continue
			if self.RE_TRANSITIONAL.search(cand.summary):
				self.addmsg('0014-8', 'depends on transitional package %s' % (dep,), filename=join(path, 'debian', 'control'))


if __name__ == '__main__':
	upc = UniventionPackageCheck()
	upc.check(curdir)
	msglist = upc.result()
	for msg in msglist:
		print(str(msg))
