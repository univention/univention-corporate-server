#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Python setup
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2023 Univention GmbH
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
import subprocess
from email.utils import parseaddr

from debian.changelog import Changelog
from debian.deb822 import Deb822
from setuptools import Command, setup
from setuptools.command.build_py import build_py


dch = Changelog(open('debian/changelog'))
dsc = Deb822(open('debian/control'))
realname, email_address = parseaddr(dsc['Maintainer'])


class BuildI18N(Command):
    description = 'Compile .po files into .mo files'

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        data_files = self.distribution.data_files

        po_dir = os.path.join(os.path.dirname(os.curdir), 'src/')
        for path, _names, filenames in os.walk(po_dir):
            rel_path = path[len(po_dir):]
            for f in filenames:
                if not f.endswith('.po'):
                    continue
                lang = f[: -3]
                src = os.path.join(path, f)
                dest_path = os.path.join('build', 'locale', lang, 'LC_MESSAGES')
                dest_file = '%s.mo' % rel_path.replace('/', '-')
                dest = os.path.join(dest_path, dest_file)
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
                if not os.path.exists(dest):
                    print('Compiling %s' % src)
                    subprocess.call(['msgfmt', src, '-o', dest])
                else:
                    src_mtime = os.stat(src)[8]
                    dest_mtime = os.stat(dest)[8]
                    if src_mtime > dest_mtime:
                        print('Compiling %s' % src)
                        subprocess.call(['msgfmt', src, '-o', dest])
                data_files.append(('share/locale/%s/LC_MESSAGES' % lang, (dest, )))


class Build(build_py):
    sub_commands = build_py.sub_commands + [('build_i18n', None)]

    def run(self):
        build_py.run(self)


def all_xml_files_in(dir):
    return filter(lambda x: os.path.isfile(x) and x.endswith('.xml'), map(lambda x: os.path.join(dir, x), os.listdir(dir)))


setup(
    package_dir={'': 'src'},
    packages=['univention', 'univention.management', 'univention.management.console', 'univention.management.console.modules'],
    scripts=['scripts/univention-management-console-module', 'scripts/univention-management-console-client', 'scripts/univention-management-console-acls'],
    entry_points={
        'console_scripts': ['univention-management-console-server = univention.management.console.server:main'],
    },
    data_files=[('share/univention-management-console/categories', all_xml_files_in('data/categories'))],
    cmdclass={'build_py': Build, 'build_i18n': BuildI18N},
    test_suite='',

    name=dch.package,
    version=dch.version.full_version.split('A~')[0],
    maintainer=realname,
    maintainer_email=email_address,
    url='https://www.univention.de/',
    description='Univention Management Console',
)
