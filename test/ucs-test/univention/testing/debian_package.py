#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2024 Univention GmbH
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

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile


class BuildRuntimeError(RuntimeError):
    pass


class InstallRuntimeError(RuntimeError):
    pass


class UninstallRuntimeError(RuntimeError):
    pass


class DebianPackage:
    """Class to build simple debian packages"""

    def __init__(self, name: str = 'testdeb', version: str = '1.0') -> None:
        self._package_name = name
        self._package_version = version
        self._create_debian_base_dir()

        self.__join_file: str | None = None
        self.__unjoin_file: str | None = None

    def _create_debian_base_dir(self) -> None:
        self._package_tempdir = tempfile.mkdtemp()

        self._package_path = os.path.join(self._package_tempdir, self._package_name)
        self._package_debian_path = os.path.join(self._package_path, 'debian')

        os.makedirs(self._package_debian_path)

        self._create_changelog()
        self._create_control()
        self._create_rules()
        self._create_install()

    def get_package_name(self) -> str:
        return self._package_name

    def get_temp_dir(self) -> str:
        return self._package_tempdir

    def get_binary_name(self) -> str:
        deb_file = f'{self._package_name}_{self._package_version}_all.deb'
        deb_package = os.path.join(self._package_tempdir, deb_file)
        return deb_package

    def __create_file_from_buffer(self, path, file_buffer, write_mode='w'):
        # type: (str, str, str) -> None
        with open(path, write_mode) as f:
            f.write(file_buffer)

    def create_join_script_from_buffer(self, joinscript_name: str, joinscript_buffer: str) -> None:
        self.__join_file = os.path.join(self._package_path, joinscript_name)
        self.__create_file_from_buffer(self.__join_file, joinscript_buffer)
        os.chmod(self.__join_file, 0o755)

    def create_unjoin_script_from_buffer(self, unjoinscript_name: str, unjoinscript_buffer: str) -> None:
        self.__unjoin_file = os.path.join(self._package_path, unjoinscript_name)
        self.__create_file_from_buffer(self.__unjoin_file, unjoinscript_buffer)
        os.chmod(self.__unjoin_file, 0o755)

    def create_usr_share_file_from_buffer(self, share_filename, schema_buffer, write_mode='w'):
        # type: (str, str, str) -> None
        share_file = os.path.join(self._package_path, 'usr/share/%s' % self._package_name, share_filename)
        dirpath = os.path.dirname(share_file)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        self.__create_file_from_buffer(share_file, schema_buffer, write_mode)

    def create_debian_file_from_buffer(self, debian_filename: str, debian_buffer: str) -> None:
        deb_file = os.path.join(self._package_debian_path, debian_filename)
        self.__create_file_from_buffer(deb_file, debian_buffer)

    def build(self) -> None:
        install = []
        if os.path.exists(os.path.join(self._package_path, 'usr/share')):
            install.append('usr/share/* usr/share')
        if self.__join_file:
            install.append('*.inst usr/lib/univention-install/')
        if self.__unjoin_file:
            install.append('*.uinst usr/lib/univention-uninstall/')
        self.create_debian_file_from_buffer('install', '\n'.join(install))

        sys.stdout.flush()
        if subprocess.call(['dpkg-buildpackage', '-rfakeroot', '-b', '-us', '-uc'], cwd=self._package_path):
            raise BuildRuntimeError()

    def install(self) -> None:
        deb_package = self.get_binary_name()

        sys.stdout.flush()
        if subprocess.call(['dpkg', '-i', deb_package]):
            raise InstallRuntimeError()

    def uninstall(self, purge: bool = False) -> None:
        sys.stdout.flush()
        if subprocess.call(['dpkg', '-r', self._package_name]):
            raise UninstallRuntimeError()
        if purge and subprocess.call(['dpkg', '--purge', self._package_name]):
            raise UninstallRuntimeError()

    def remove(self) -> None:
        shutil.rmtree(self._package_tempdir)

    def _create_changelog(self) -> None:
        changelog = '''%(package_name)s (%(package_version)s) unstable; urgency=low

  * Test package

 -- Univention GmbH <packages@univention.de>  Fri, 20 Sep 2013 01:01:01 +0200
''' % {'package_name': self._package_name, 'package_version': self._package_version}

        self.create_debian_file_from_buffer('changelog', changelog)

    def _create_control(self) -> None:
        control = '''source: %(package_name)s
Section: univention
Priority: optional
Maintainer: Univention GmbH <packages@univention.de>
Build-Depends: debhelper-compat (=12)
Standards-Version: 3.5.2

Package: %(package_name)s
Architecture: all
Depends: ${misc:Depends}
Description: UCS - Test package
 It is part of Univention Corporate Server (UCS), an
 integrated, directory driven solution for managing
 corporate environments. For more information about UCS,
 refer to: https://www.univention.de/
''' % {'package_name': self._package_name}

        self.create_debian_file_from_buffer('control', control)

    def _create_rules(self) -> None:
        rules = '''#!/usr/bin/make -f
%:
\tdh $@
override_dh_strip_nondeterminism: ; # Bug #46002
'''
        self.create_debian_file_from_buffer('rules', rules)

    def _create_install(self) -> None:
        install = '''
usr/share/* usr/share/
install/* usr/lib/univention-install/
uninstall/* usr/lib/univention-uninstall/
'''
        self.create_debian_file_from_buffer('install', install)


if __name__ == '__main__':
    deb = DebianPackage('testdeb')
    share_file = '''# testdeb
...
'''
    deb.create_usr_share_file_from_buffer('test', share_file)
    deb.create_join_script_from_buffer('66testdeb.inst', '...')
    deb.build()
    subprocess.call(['dpkg', '--contents', deb.get_binary_name()])
    deb.install()
    deb.uninstall()
    deb.remove()
