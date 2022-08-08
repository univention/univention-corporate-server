#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2022 Univention GmbH
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

"""
Creates a local repository.
"""

from __future__ import print_function

import errno
import subprocess
import sys
from argparse import ArgumentParser, Namespace
from os import makedirs, symlink
from os.path import devnull, exists, join
from textwrap import dedent

from univention.config_registry import ConfigRegistry, handler_set, handler_commit
from univention.lib.ucs import UCS_Version
from univention.updater.locking import UpdaterLock

configRegistry = ConfigRegistry()
configRegistry.load()


def check_preconditions(options: Namespace) -> None:
    """ Check for already existing mirror and for debmirror package """
    # check directories
    if exists(join(options.base, 'mirror')):
        print('Warning: The path %s/mirror already exists.' % options.base, file=sys.stderr)

    if options.interactive:
        print("Are you sure you want to create a local repository? [yN] ", end=' ', flush=True)
        sys.stdin.flush()
        if not sys.stdin.readline().startswith('y'):
            print('Aborted.', file=sys.stderr)
            sys.exit(1)

    # install univention-debmirror
    cmd = ('dpkg-query', '-W', '-f', '${Status}', 'univention-debmirror')
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    output = p.communicate()[0].decode("UTF-8")

    if output == 'install ok installed':
        return

    print('Installing univention-debmirror')
    ret = subprocess.call(['univention-install', '--yes', 'univention-debmirror'])
    if ret != 0:
        print('Error: Failed to install univention-debmirror', file=sys.stderr)
        sys.exit(1)


def prepare(options: Namespace) -> None:
    """ Set local/repository and create directory structure """
    if configRegistry.is_false('local/repository', True):
        handler_set(['local/repository=yes'])
        configRegistry.load()

    if configRegistry.is_false('repository/mirror', True):
        handler_set(['repository/mirror=yes'])
        configRegistry.load()

    makedirs(join(options.base, "mirror", "dists"), exist_ok=True)
    makedirs(join(options.base, "mirror", "pool", "main"), exist_ok=True)
    makedirs(join(options.base, "skel"), exist_ok=True)
    makedirs(join(options.base, "var"), exist_ok=True)


def parse_args() -> Namespace:

    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        '-n', '--non-interactive',
        action='store_false',
        dest='interactive',
        help='if given no questions are asked.')
    parser.add_argument(
        '-s', '--silent',
        action='store_true',
        help='do not print any information, just errors and warnings')
    parser.add_argument(
        '-b', '--base',
        metavar="DIR",
        default=configRegistry.get('repository/mirror/basepath', '/var/lib/univention-repository'),
        help="Local mirror base directory")

    return parser.parse_args()


def main() -> None:
    options = parse_args()

    if options.silent:
        sys.stdout = open(devnull, 'w')

    with UpdaterLock():
        check_preconditions(options)

        current_ucs_version = "%(version/version)s-%(version/patchlevel)s" % configRegistry
        options.version = UCS_Version(current_ucs_version)

        prepare(options)

        # set repository server to local system
        ucr_set = [
            'repository/online/server=%(hostname)s.%(domainname)s' % configRegistry,
            'repository/mirror/version/start?%s' % current_ucs_version,
        ]
        # set last version contained in repository
        end = configRegistry.get('repository/mirror/version/end', '').strip()
        if not end or UCS_Version(end) < options.version:
            ucr_set.append('repository/mirror/version/end=%s' % options.version)

        handler_set(ucr_set)

        # create symbolic link univention-repository
        try:
            symlink('.', join(options.base, 'mirror', 'univention-repository'))
        except EnvironmentError as ex:
            if ex.errno != errno.EEXIST:
                raise

        print('Starting mirror download. This can take a long time!')
        print('Check /var/log/univention/repository.log for the current status')
        subprocess.call(['univention-repository-update', 'net'])
        handler_commit([
            '/etc/apt/sources.list.d/15_ucs-online-version.list',
            '/etc/apt/sources.list.d/20_ucs-online-component.list',
        ])

        print(dedent(
            r"""
            The local repository has been prepared. The repository can be updated using:

              univention-repository-update net

            The local host has been modified to use this local repository.  Other hosts
            must be re-configured by setting the Univention Configuration Registry (UCR)
            variable 'repository/online/server' to the FQDN of this host.

              ucr set repository/online/server="%(hostname)s.%(domainname)s"

            The setting is best set in a domain by defining UCR Policies, which
            set this variable on all hosts using this repository server. For example:

              udm policies/repositoryserver create \
                --position "cn=repository,cn=update,cn=policies,%(ldap/base)s" \
                --set name="%(hostname)s repository" \
                --set repositoryServer="%(hostname)s.%(domainname)s"
              udm container/dc modify \
                --dn "%(ldap/base)s" \
                --policy-reference "cn=%(hostname)s repository,cn=repository,cn=update,cn=policies,%(ldap/base)s"
            """ % configRegistry))

        if options.version.minor != 0 or options.version.patchlevel != 0:
            print(dedent(
                """
                An UCS repository must always start with minor version 0, for example
                with UCS {ver.major}. Please synchronize the repository
                by using the tool 'univention-repository-update'.
                """).format(ver=options.version))


if __name__ == '__main__':
    main()
