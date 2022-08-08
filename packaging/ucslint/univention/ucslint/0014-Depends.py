#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:set fileencoding=utf-8 sw=4 ts=4 et:
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2008-2022 Univention GmbH
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
from os import listdir
from os.path import curdir, exists, join, splitext
from typing import Dict, Iterable, Iterator, Set, Tuple  # noqa: F401

from apt import Cache  # type: ignore

import univention.ucslint.base as uub
from apt_pkg import Version  # noqa: F401


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
	RE_FIELD = re.compile(r"([a-z0-9_]+)[ \t]*(?:(<<|<=|=|>=|>>)[ \t]*([-a-zA-Z0-9.+~]+))?")
	RE_INIT = re.compile(r"^(?:File|Subfile): (etc/init.d/.+)$")
	RE_TRANSITIONAL = re.compile(r'\b[Tt]ransition(?:al)?(?: dummy)? [Pp]ackage\b')  # re.IGNORECASE
	DEPS = {
		'uicr': (re.compile(r"(?:/usr/bin/)?univention-install-(?:config-registry(?:-info)?|service-info)|\bdh\b.*--with\b.*\bucr\b"), set(('univention-config-dev',))),
		'umcb': (re.compile(r"(?:/usr/bin/)?dh-umc-module-build|\bdh\b.*--with\b.*\bumc\b"), set(('univention-management-console-dev',))),
		'ucr': (re.compile(r"""(?:^|(?<=['";& \t]))(?:/usr/sbin/)?(?:univention-config-registry|ucr)(?:(?=['";& \t])|$)"""), set(('univention-config', '${misc:Depends}'))),
		'ial': (re.compile(r"/usr/share/univention-config-registry/init-autostart\.lib"), set(('univention-base-files',))),
	}
	PRIORITIES = frozenset({'required', 'important'})

	def __init__(self) -> None:
		super(UniventionPackageCheck, self).__init__()
		self.apt = None
		self.path = ''  # updated in check()

	def getMsgIds(self) -> uub.MsgIds:
		return {
			'0014-0': (uub.RESULT_WARN, 'failed to open/read file'),
			'0014-1': (uub.RESULT_ERROR, 'parsing error in debian/control'),
			'0014-2': (uub.RESULT_ERROR, 'univention-install-... is used in debian/rules, but debian/control lacks a build-dependency on univention-config-dev.'),
			'0014-3': (uub.RESULT_ERROR, 'dh-umc-module-build is used in debian/rules, but debian/control lacks a build-dependency on univention-management-console-dev.'),
			'0014-4': (uub.RESULT_ERROR, 'univention-config-registry is used in a .preinst script, but the package lacks a pre-dependency on univention-config.'),
			'0014-5': (uub.RESULT_ERROR, 'univention-config-registry is used in a maintainer script, but the package lacks a dependency on univention-config.'),
			'0014-6': (uub.RESULT_WARN, 'init-autostart.lib is sourced by a script, but the package lacks an explicit dependency on univention-base-files.'),
			'0014-7': (uub.RESULT_WARN, 'The source package contains debian/*.univention- files, but the package is not found in debian/control.'),
			'0014-8': (uub.RESULT_WARN, 'unexpected UCR file'),
			'0014-9': (uub.RESULT_WARN, 'depends on transitional package'),
			'0014-10': (uub.RESULT_WARN, 'depends on "Essential:yes" package'),
			'0014-11': (uub.RESULT_STYLE, 'depends on "Priority:required/important" package'),
		}

	def postinit(self, path: str) -> None:
		"""Checks to be run before real check or to create pre-calculated data for several runs. Only called once!"""
		try:
			self.apt = Cache(memonly=True)
		except Exception as ex:
			self.debug('failed to load APT cache: %s' % (ex,))

	def _scan_script(self, fn: str) -> Set[str]:
		"""find calls to 'univention-install-', 'ucr' and use of 'init-autostart.lib' in file 'fn'."""
		need = set()
		self.debug('Reading %s' % (fn,))
		try:
			with open(fn, 'r') as f:
				for l in f:
					for (key, (regexp, pkgs)) in self.DEPS.items():
						if regexp.search(l):
							self.debug('Found %s in %s' % (key.upper(), fn))
							need.add(key)
		except EnvironmentError:
			self.addmsg('0014-0', 'failed to open and read file', fn)
			return need

		return need

	def check_source(self, source_section: uub.DebianControlSource) -> Set[str]:
		"""Check source package for dependencies."""
		src_deps = source_section.dep_all

		fn_rules = join(self.path, 'debian', 'rules')
		need = self._scan_script(fn_rules)
		uses_uicr = 'uicr' in need
		uses_umcb = 'umcb' in need

		# Assert packages using "univention-install-" build-depens on "univention-config-dev" and depend on "univention-config"
		if uses_uicr and not src_deps & self.DEPS['uicr'][1]:
			self.addmsg('0014-2', 'Missing Build-Depends: univention-config-dev', fn_rules)

		if uses_umcb and not src_deps & self.DEPS['umcb'][1]:
			self.addmsg('0014-3', 'Missing Build-Depends: univention-management-console-dev', fn_rules)

		return src_deps

	def check_package(self, section: uub.DebianControlBinary) -> Set[str]:
		"""Check binary package for dependencies."""
		pkg = section['Package']
		self.debug('Package: %s' % (pkg,))

		bin_pre_set = section.pre
		bin_deps = bin_pre_set | section.dep

		# Assert packages using "ucr" in preinst pre-depend on "univention-config"
		for ms in ('preinst',):
			fn = join(self.path, 'debian', '%s.%s' % (pkg, ms))
			if not exists(fn):
				continue
			need = self._scan_script(fn)
			if 'ucr' in need and not bin_pre_set & self.DEPS['ucr'][1]:
				self.addmsg('0014-4', 'Missing Pre-Depends: univention-config', fn)

		# Assert packages using "ucr" depend on "univention-config"
		for ms in ('postinst', 'prerm', 'postrm'):
			fn = join(self.path, 'debian', '%s.%s' % (pkg, ms))
			if not exists(fn):
				continue
			need = self._scan_script(fn)
			if 'ucr' in need and not bin_deps & self.DEPS['ucr'][1]:
				self.addmsg('0014-5', 'Missing Depends: univention-config, ${misc:Depends}', fn)

		p = join(self.path, '[0-9][0-9]%s.inst' % (pkg,))
		for fn in glob(p):
			need = self._scan_script(fn)
			if 'ucr' in need and not bin_deps & self.DEPS['ucr'][1]:
				self.addmsg('0014-4', 'Missing Depends: univention-config, ${misc:Depends}', fn)

		# FIXME: scan all other files for ucr as well?

		# Assert packages using "init-autostart.lib" depends on "univention-base-files"
		init_files = set()
		init_files.add(join(self.path, 'debian', '%s.init' % (pkg,)))
		init_files.add(join(self.path, 'debian', '%s.init.d' % (pkg,)))
		try:
			fn = join(self.path, 'debian', '%s.univention-config-registry' % (pkg,))
			if exists(fn):
				with open(fn, 'r') as f:
					for l in f:
						m = self.RE_INIT.match(l)
						if m:
							fn = join(self.path, 'conffiles', m.group(1))
							init_files.add(fn)
		except EnvironmentError:
			self.addmsg('0014-0', 'failed to open and read file', fn)

		for fn in init_files:
			if not exists(fn):
				continue
			need = self._scan_script(fn)
			if 'ial' in need and not bin_deps & self.DEPS['ial'][1]:
				self.addmsg('0014-6', 'Missing Depends: univention-base-files', fn)

		return bin_deps | section.rec | section.sug

	def check(self, path: str) -> None:
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		fn_control = join(path, 'debian', 'control')
		self.debug('Reading %s' % (fn_control,))
		try:
			parser = uub.ParserDebianControl(fn_control)
			self.path = path
		except uub.FailedToReadFile:
			self.addmsg('0014-0', 'failed to open and read file', fn_control)
			return
		except uub.UCSLintException:
			self.addmsg('0014-1', 'parsing error', fn_control)
			return

		deps = self.check_source(parser.source_section)
		for section in parser.binary_sections:
			deps |= self.check_package(section)

		self.check_unknown(path, parser)
		self.check_transitional(deps)
		self.check_essential(deps)

	def check_unknown(self, path: str, parser: uub.ParserDebianControl) -> None:
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
			self.addmsg('0014-8', 'unexpected UCR file', join(path, 'debian', unowned))

	def check_transitional(self, deps: Iterable[str]) -> None:
		fn_control = join(self.path, 'debian', 'control')
		for cand in self._cand(deps):
			if self.RE_TRANSITIONAL.search(cand.summary):
				self.addmsg('0014-8', 'depends on transitional package %s' % (cand.package.name,), fn_control)

	def check_essential(self, deps: Iterable[str]) -> None:
		fn_control = join(self.path, 'debian', 'control')
		for cand in self._cand(deps):
			if cand.package.essential:
				self.addmsg('0014-10', 'depends on "Essential:yes" package %s' % (cand.package.name,), fn_control)
			elif cand.priority in self.PRIORITIES:
				self.addmsg('0014-11', 'depends on "Priority:required/important" package %s' % (cand.package.name,), fn_control)

	def _cand(self, deps: Iterable[str]) -> Iterator[Version]:
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
			else:
				yield cand


if __name__ == '__main__':
	upc = UniventionPackageCheck()
	upc.check(curdir)
	msglist = upc.result()
	for msg in msglist:
		print(str(msg))
