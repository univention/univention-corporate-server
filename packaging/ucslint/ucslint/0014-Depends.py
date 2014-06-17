#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:set fileencoding=utf-8 sw=4 ts=4 et:
#
# Copyright (C) 2008-2014 Univention GmbH
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
import re
import sys
from glob import glob
try:
    import univention.ucslint.base as uub
except ImportError:
    import ucslint.base as uub


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
    RE_FIELD = re.compile("([a-z0-9_]+)[ \t]*(?:(<<|<=|=|>=|>>)[ \t]*([-a-zA-Z0-9.+~]+))?")
    RE_INIT = re.compile("^(?:File|Subfile): (etc/init.d/.+)$")
    DEPS = {
            'uicr': (re.compile("(?:/usr/bin/)?univention-install-(?:config-registry(?:-info)?|service-info)"), set(('univention-config-dev',))),
            'umcb': (re.compile("(?:/usr/bin/)?dh-umc-module-build"), set(('univention-management-console-dev',))),
            'ucr': (re.compile("""(?:^|(?<=['";& \t]))(?:/usr/sbin/)?(?:univention-config-registry|ucr)(?:(?=['";& \t])|$)"""), set(('univention-config', '${misc:Depends}'))),
            'ial': (re.compile("/usr/share/univention-config-registry/init-autostart\.lib"), set(('univention-base-files',))),
            }

    def __init__(self):
        super(UniventionPackageCheck, self).__init__()
        self.name = '0014-Depends'

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
                }

    def postinit(self, path):
        """Checks to be run before real check or to create pre-calculated data for several runs. Only called once!"""
        pass

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
        except (OSError, IOError), e:
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
        build_arch = source_section.get('Build-Depends', '')
        build_arch = self._split_field(build_arch)
        build_arch = set(build_arch)
        self.debug('Build-Depends: %s' % (build_arch,))
        build_indep = source_section.get('Build-Depends-Indep', '')
        build_indep = self._split_field(build_indep)
        build_indep = set(build_indep)
        self.debug('Build-Depends-Indep: %s' % (build_indep,))
        build_deps = build_arch | build_indep

        fn = os.path.join(self.path, 'debian', 'rules')
        need = self._scan_script(fn)
        uses_uicr = 'uicr' in need
        uses_umcb = 'umcb' in need

        # Assert packages using "univention-install-" build-depens on "univention-config-dev" and depend on "univention-config"
        if uses_uicr and not build_deps & UniventionPackageCheck.DEPS['uicr'][1]:
            self.addmsg('0014-2', 'Missing Build-Depends: univention-config-dev', filename=fn)
        if uses_umcb and not build_deps & UniventionPackageCheck.DEPS['umcb'][1]:
            self.addmsg('0014-3', 'Missing Build-Depends: univention-management-console-dev', filename=fn)

    def check_package(self, section):
        """Check binary package for dependencies."""
        pkg = section['Package']
        self.debug('Package: %s' % (pkg,))

        pre = section.get('Pre-Depends', '')
        pre = self._split_field(pre)
        pre = set(pre)
        self.debug('Pre-Depends: %s' % (pre,))
        dep = section.get('Depends', '')
        dep = self._split_field(dep)
        dep = set(dep)
        self.debug('Depends: %s' % (dep,))
        all = pre | dep

        # Assert packages using "ucr" in preinst pre-depend on "univention-config"
        for ms in ('preinst',):
            fn = os.path.join(self.path, 'debian', '%s.%s' % (pkg, ms))
            if not os.path.exists(fn):
                continue
            need = self._scan_script(fn)
            if 'ucr' in need and not pre & UniventionPackageCheck.DEPS['ucr'][1]:
                self.addmsg('0014-4', 'Missing Pre-Depends: univention-config', filename=fn)

        # Assert packages using "ucr" depend on "univention-config"
        for ms in ('postinst', 'prerm', 'postrm'):
            fn = os.path.join(self.path, 'debian', '%s.%s' % (pkg, ms))
            if not os.path.exists(fn):
                continue
            need = self._scan_script(fn)
            if 'ucr' in need and not all & UniventionPackageCheck.DEPS['ucr'][1]:
                self.addmsg('0014-5', 'Missing Depends: univention-config, ${misc:Depends}', filename=fn)
        p = os.path.join(self.path, '[0-9][0-9]%s.inst' % (pkg,))
        for fn in glob(p):
            need = self._scan_script(fn)
            if 'ucr' in need and not all & UniventionPackageCheck.DEPS['ucr'][1]:
                self.addmsg('0014-4', 'Missing Depends: univention-config, ${misc:Depends}', filename=fn)
        # FIXME: scan all other files for ucr as well?

        # Assert packages using "init-autostart.lib" depends on "univention-base-files"
        init_files = set()
        init_files.add(os.path.join(self.path, 'debian', '%s.init' % (pkg,)))
        init_files.add(os.path.join(self.path, 'debian', '%s.init.d' % (pkg,)))
        try:
            fn = os.path.join(self.path, 'debian', '%s.univention-config-registry' % (pkg,))
            if os.path.exists(fn):
                f = open(fn, 'r')
                try:
                    for l in f:
                        m = UniventionPackageCheck.RE_INIT.match(l)
                        if m:
                            fn = os.path.join(self.path, 'conffiles', m.group(1))
                            init_files.add(fn)
                finally:
                    f.close()
        except IOError, e:
            self.addmsg('0014-0', 'failed to open and read file', filename=fn)
        for fn in init_files:
            if not os.path.exists(fn):
                continue
            need = self._scan_script(fn)
            if 'ial' in need and not all & UniventionPackageCheck.DEPS['ial'][1]:
                self.addmsg('0014-6', 'Missing Depends: univention-base-files', filename=fn)

    def check(self, path):
        """ the real check """
        super(UniventionPackageCheck, self).check(path)

        fn = os.path.join(path, 'debian', 'control')
        self.debug('Reading %s' % (fn,))
        try:
            parser = uub.ParserDebianControl(fn)
            self.path = path
        except uub.FailedToReadFile, e:
            self.addmsg('0014-0', 'failed to open and read file', filename=fn)
            return
        except uub.UCSLintException, e:
            self.addmsg('0014-1', 'parsing error', filename=fn)
            return

        self.check_source(parser.source_section)
        for section in parser.binary_sections:
            self.check_package(section)

        # Assert all files debian/$pkg.$suffix belong to a package $pkg declared in debian/control
        exists = {}
        for suffix in ('.univention-config-registry', '.univention-config-registry-variables', '.univention-config-registry-categories', '.univention-service'):
            pat = os.path.join(path, 'debian', '*%s' % (suffix,))
            for fn in glob(pat):
                pkg = os.path.basename(fn)[:-len(suffix)]
                exists.setdefault(pkg, []).append(fn)
        known = set((section['Package'] for section in parser.binary_sections))


if __name__ == '__main__':
    upc = UniventionPackageCheck()
    upc.check(os.path.curdir)
    msglist = upc.result()
    for msg in msglist:
        print str(msg)
