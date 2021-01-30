# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2021 Univention GmbH
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

import os
import re

import univention.ucslint.base as uub
from univention.ucslint.common import RE_DEBIAN_CHANGELOG

RE_DEP = re.compile(
	r'''
	(?P<name>[0-9a-z][+.0-9a-z-]+)
	(?:\s*
		(?:
			\((?P<version>\s*(?P<vcomp><<|<=|=|>=|>>)\s*(?P<vstr>[^)]*))\)|
			\[(?P<arch>[^]]*)\]|
			<(?P<spec>[^>]*)>
		)
	)*''', re.VERBOSE
)


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def getMsgIds(self) -> uub.MsgIds:
		return {
			'0011-1': (uub.RESULT_WARN, 'failed to open/read file'),
			'0011-2': (uub.RESULT_ERROR, 'source package name differs in debian/control and debian/changelog'),
			'0011-3': (uub.RESULT_WARN, 'wrong section - should be "Univention"'),
			'0011-4': (uub.RESULT_WARN, 'wrong priority - should be "optional"'),
			'0011-5': (uub.RESULT_ERROR, 'wrong maintainer - should be "Univention GmbH <packages@univention.de>"'),
			'0011-6': (uub.RESULT_ERROR, 'XS-Python-Version without python-central in build-dependencies'),
			'0011-7': (uub.RESULT_ERROR, 'XS-Python-Version without XB-Python-Version in binary package entries'),
			'0011-8': (uub.RESULT_WARN, 'XS-Python-Version should be "2.7"'),
			'0011-9': (uub.RESULT_ERROR, 'cannot determine source package name'),
			'0011-10': (uub.RESULT_ERROR, 'parsing error in debian/control'),
			'0011-11': (uub.RESULT_WARN, 'debian/control: XS-Python-Version is not required any longer'),
			'0011-12': (uub.RESULT_ERROR, 'debian/control: please use python-support instead of python-central in Build-Depends'),
			'0011-13': (uub.RESULT_WARN, 'debian/control: ucslint is missing in Build-Depends'),
			'0011-14': (uub.RESULT_WARN, 'no matching package in debian/control'),
			'0011-15': (uub.RESULT_WARN, 'non-prefixed debhelper file'),
			'0011-16': (uub.RESULT_INFO, 'unknown debhelper file'),
			'0011-17': (uub.RESULT_WARN, 'debian/control: please use dh-python instead of python-support in Build-Depends'),
			'0011-18': (uub.RESULT_WARN, 'debian/rules: please use --with python2,python3 instead of python_support'),
			'0011-19': (uub.RESULT_WARN, 'parsing error in debian/compat'),
			'0011-20': (uub.RESULT_WARN, 'debian/compat and debian/control disagree on the version for debhelper'),
		}

	def check(self, path: str) -> None:
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		fn_changelog = os.path.join(path, 'debian', 'changelog')
		try:
			content_changelog = open(fn_changelog, 'r').read(1024)
		except EnvironmentError:
			self.addmsg('0011-1', 'failed to open and read file', fn_changelog)
			return

		fn_control = os.path.join(path, 'debian', 'control')
		try:
			parser = uub.ParserDebianControl(fn_control)
		except uub.FailedToReadFile:
			self.addmsg('0011-1', 'failed to open and read file', fn_control)
			return
		except uub.UCSLintException:
			self.addmsg('0011-11', 'parsing error', fn_control)
			return

		compat_version = 0
		fn_compat = os.path.join(path, 'debian', 'compat')
		try:
			content_compat = open(fn_compat, 'r').read()
			compat_version = int(content_compat)
		except EnvironmentError:
			# self.addmsg('0011-1', 'failed to open and read file', fn_compat)
			pass
		except ValueError:
			self.addmsg('0011-19', 'parsing error', fn_compat)

		# compare package name
		match = RE_DEBIAN_CHANGELOG.match(content_changelog)
		if match:
			srcpkgname = match.group(1)
		else:
			srcpkgname = ''
			self.addmsg('0011-9', 'cannot determine source package name', fn_changelog)

		controlpkgname = parser.source_section.get('Source')
		if not controlpkgname:
			self.addmsg('0011-9', 'cannot determine source package name', fn_control)

		if srcpkgname and controlpkgname:
			if srcpkgname != controlpkgname:
				self.addmsg('0011-2', 'source package name differs in debian/changelog and debian/control', fn_changelog)

		# parse source section of debian/control
		if not parser.source_section.get('Section', '') in ('univention'):
			self.addmsg('0011-3', 'wrong Section entry - should be "univention"', fn_control)

		if not parser.source_section.get('Priority', '') in ('optional'):
			self.addmsg('0011-4', 'wrong Priority entry - should be "optional"', fn_control)

		if not parser.source_section.get('Maintainer', '') in ('Univention GmbH <packages@univention.de>'):
			self.addmsg('0011-5', 'wrong Maintainer entry - should be "Univention GmbH <packages@univention.de>"', fn_control)

		if parser.source_section.get('XS-Python-Version', ''):
			self.addmsg('0011-11', 'XS-Python-Version is not required any longer', fn_control)

		build_depends = dict(
			(m.group(1), m.groupdict()) for m in (
				RE_DEP.match(dep) for dep in (
					alt.strip()
					for dep in parser.source_section.get('Build-Depends', '').split(',')
					for alt in dep.split('|')
				) if dep
			) if m
		)

		if 'python-central' in build_depends:
			self.addmsg('0011-12', 'please use python-support instead of python-central in Build-Depends', fn_control)

		if 'python-support' in build_depends:
			self.addmsg('0011-17', 'please use dh-python instead of python-support in Build-Depends', fn_control)

		try:
			dep = build_depends['debhelper']
			vstr = dep['vstr']
			vint = int(vstr.split('.')[0]) if vstr else 0
		except LookupError:
			pass
		except ValueError:
			self.addmsg('0011-10', 'failed parsing debhelper version', fn_control)
		else:
			if not compat_version:
				pass
			elif not vint:
				pass
			elif compat_version > vint:
				self.addmsg('0011-20', 'debian/compat=%d > debian/control=%d disagree on the version for debhelper' % (compat_version, vint), fn_control)
			elif compat_version < vint:
				self.addmsg('0011-20', 'debian/compat=%d < debian/control=%d disagree on the version for debhelper' % (compat_version, vint), fn_compat)
			else:
				pass

		self.check_debhelper(path, parser)

		try:
			fn_rules = os.path.join(path, 'debian', 'rules')
			with open(fn_rules, 'r') as fd:
				rules = fd.read()
				if re.search('--with[ =]*["\']?python_support', rules):
					self.addmsg('0011-18', 'please use --with python2,python3 instead of python_support', fn_rules)
		except EnvironmentError:
			pass

	EXCEPTION_FILES = {
		'changelog',  # dh_installchangelogs default
		'clean',  # dh_clean
		'compat',  # dh
		'control',
		'copyright',  # dh_installdocs default
		'debhelper-build-stamp',  # dh
		'files',  # dh_builddeb
		'NEWS',  # dh_installchangelogs default
		'not-installed',  # dh_install
		'pybuild.testfiles',  # pybuild
		'pybuild_python2.testfiles',  # pybuild
		'pybuild_python2.7.testfiles',  # pybuild
		'pybuild_python3.testfiles',  # pybuild
		'pybuild_python3.5.testfiles',  # pybuild
		'pybuild_python3.7.testfiles',  # pybuild
		'pydist-overrides',  # dh_python2
		'py3dist-overrides',  # dh_python3
		'rules',
		'source.lintian-overrides',  # dh_lintian
		'ucslint.overrides',
		'watch',  # uscan
	}

	KNOWN_DH_FILES = {
		'bash-completion',  # dh_bash-completion
		'bcep',  # dh_python3
		'bug-control',  # dh_bugfiles
		'bug-presubj',  # dh_bugfiles
		'bug-script',  # dh_bugfiles
		'changelog',  # dh_installchangelogs
		'compress',  # dh_compress
		'conffiles',  # dh_installdeb
		'config',  # dh_installdebconf
		'copyright',  # dh_installdocs
		'debhelper.log',  # dh
		'dirs',  # dh_installdirs
		'doc-base',  # dh_installdocs
		'docs',  # dh_installdocs
		'emacsen-install',  # dh_installemacsen
		'emacsen-remove',  # dh_installemacsen
		'emacsen-startup',  # dh_installemacsen
		'examples',  # dh_installexamples
		'files',  # dh_movefiles
		'gconf-defaults',  # dh_gconf
		'gconf-mandatory',  # dh_gconf
		'info',  # dh_installinfo
		'install',  # dh_install
		'links',  # dh_link
		'lintian-overrides',  # dh_lintian
		'maintscript',  # dh_installdeb
		'manpages',  # dh_installman
		'menu',  # dh_installmenu
		'menu-method',  # dh_installmenu
		'mine',  # dh_installmime
		'NEWS',  # dh_installchangelogs
		'postinst',  # dh_installdeb
		'postinst.debhelper',  # dh_installdeb
		'postrm',  # dh_installdeb
		'postrm.debhelper',  # dh_installdeb
		'preinst',  # dh_installdeb
		'preinst.debhelper',  # dh_installdeb
		'prerm',  # dh_installdeb
		'prerm.debhelper',  # dh_installdeb
		'README.Debian',  # dh_installdocs
		'mount',  # dh_systemd_enable
		'path',  # dh_systemd_enable
		'pydist',  # dh_python2 dh_python3
		'pyinstall',  # dh_python2 dh_python3
		'pyremove',  # dh_python2 dh_python3
		'service',  # dh_systemd_enable
		'sgmlcatalogs',  # dh_installcatalogs
		'sharedmimeinfo',  # dh_installmime
		'shlibs',  # dh_installdeb
		'socket',  # dh_systemd_enable
		'substvars',  # dh_gencontrol
		'symbols',  # dh_makeshlibs
		'symbols.i386',  # dh_makeshlibs
		'target',  # dh_systemd_enable
		'templates',  # dh_installdebconf
		'timer',  # dh_systemd_enable
		'tmpfile',  # dh_systemd_enable
		'TODO',  # dh_installdocs
		'triggers',  # dh_installdeb
		'umc-modules',  # dh-umc-modules-install
		'univention-config-registry-categories',  # univention-install-config-registry-info
		'univention-config-registry-mapping',  # univention-install-config-registry-info
		'univention-config-registry',  # univention-install-config-registry
		'univention-config-registry-variables',  # univention-install-config-registry-info
		'univention-l10n',  # univention-l10n-build / univention-l10n-install
		'univention-service',  # univention-install-service-info
		'wm',  # dh_installwm
	}

	NAMED_DH_FILES = {
		'cron.daily',  # dh_installcron
		'cron.d',  # dh_installcron
		'cron.hourly',  # dh_installcron
		'cron.monthly',  # dh_installcron
		'cron.weekly',  # dh_installcron
		'default',  # dh_installinit
		'if-down',  # dh_installifupdown
		'if-pre-down',  # dh_installifupdown
		'if-pre-up',  # dh_installifupdown
		'if-up',  # dh_installifupdown
		'init',  # dh_installinit
		'init.d',  # dh_installinit
		'isinstallable',  # Debian Installer
		'logcheck.cracking',  # dh_installlogcheck
		'logcheck.ignore.paranoid',  # dh_installlogcheck
		'logcheck.ignore.server',  # dh_installlogcheck
		'logcheck.ignore.workstation',  # dh_installlogcheck
		'logcheck.violations',  # dh_installlogcheck
		'logcheck.violations.ignore',  # dh_installlogcheck
		'logrotate',  # dh_installlogrotate
		'modprobe',  # dh_installmodules
		'modules',  # dh_installmodules
		'pam',  # dh_installpam
		'ppp.ip-down',  # dh_installppp
		'ppp.ip-up',  # dh_installppp
		'udev',  # dh_installudev
		'upstart',  # dh_installinit
	}

	def check_debhelper(self, path: str, parser: uub.ParserDebianControl) -> None:
		"""Check for debhelper package files."""
		if len(parser.binary_sections) == 1:
			# If there is only one binary package, accept the non-prefixed files ... for now
			return

		pkgs = [pkg['Package'] for pkg in parser.binary_sections]

		debianpath = os.path.join(path, 'debian')
		files = os.listdir(debianpath)

		regexp = re.compile(
			r'^(?:%s)[.](?:%s|.+[.](?:%s))$' % (
				'|'.join(re.escape(pkg) for pkg in pkgs),
				'|'.join(re.escape(suffix) for suffix in self.KNOWN_DH_FILES | self.NAMED_DH_FILES),
				'|'.join(re.escape(suffix) for suffix in self.NAMED_DH_FILES),
			))

		for rel_name in files:
			fn = os.path.join(debianpath, rel_name)

			if rel_name in self.EXCEPTION_FILES:
				continue

			if not os.path.isfile(fn):
				continue

			if regexp.match(rel_name):
				continue

			for suffix in self.KNOWN_DH_FILES | self.NAMED_DH_FILES:
				if rel_name == suffix:
					self.addmsg('0011-15', 'non-prefixed debhelper file of package "%s"' % (pkgs[0],), fn)
					break
				elif rel_name.endswith('.%s' % (suffix,)):
					self.addmsg('0011-14', 'no matching package in debian/control', fn)
					break
			else:
				self.addmsg('0011-16', 'unknown debhelper file', fn)
