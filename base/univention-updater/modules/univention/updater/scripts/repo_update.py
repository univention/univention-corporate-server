#!/usr/bin/python3
# -*- coding: utf-8 -*-
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
Update a local repository.
"""

from __future__ import print_function

import os
import errno
import shutil
import sys
import time
from argparse import ArgumentParser, Namespace
from textwrap import dedent, wrap

import univention.updater.repository as urepo
from univention.config_registry import ConfigRegistry, handler_commit, handler_set
from univention.lib.ucs import UCS_Version
from univention.updater.errors import UpdaterException, VerificationError
from univention.updater.locking import UpdaterLock
from univention.updater.mirror import UniventionMirror, makedirs

configRegistry = ConfigRegistry()
configRegistry.load()

# base directory for local repository
_mirror_base = configRegistry.get('repository/mirror/basepath', '/var/lib/univention-repository')
# directory of current version's repository
_current_version = '%s-%s' % (configRegistry.get('version/version'), configRegistry.get('version/patchlevel'))
_repo_base = os.path.join(_mirror_base, 'mirror', configRegistry.get('version/version'), 'maintained', '%s-0' % configRegistry.get('version/version'))


def copy_repository(options: Namespace, source: str, version: UCS_Version) -> None:
    """ Copy packages and scripts belonging to version from source directory into local repository """
    print('Please be patient, copying packages ...', end=' ')
    sys.stdout.flush()

    dest_repo = os.path.join(_mirror_base, 'mirror', '%(major)s.%(minor)s/maintained/%(major)s.%(minor)s-%(patchlevel)s' % version)

    # check if repository already exists
    if os.path.isdir(os.path.join(dest_repo)):
        print('\nWarning: repository for UCS version %(major)s.%(minor)s-%(patchlevel)s already exists' % version)
    else:
        # create directory structure
        for arch in urepo.ARCHITECTURES:
            makedirs(os.path.join(dest_repo, arch))

    # copy packages to new directory structure
    urepo.copy_package_files(source, dest_repo)

    # create Packages files
    print('Packages ...', end=' ')
    urepo.gen_indexes(dest_repo, version)

    print('Scripts ...', end=' ')
    for script in ('preup.sh', 'preup.sh.gpg', 'postup.sh', 'postup.sh.gpg'):
        if os.path.exists(os.path.join(source, script)):
            shutil.copy2(os.path.join(source, script), os.path.join(dest_repo, 'all', script))
    print('Done.')


def update_net(options: Namespace) -> None:
    """ Copy packages and scripts from remote mirror into local repository """
    mirror = UniventionMirror()
    # update local repository if available
    urepo.assert_local_repository()
    # mirror.run calls "apt-mirror", which needs /etc/apt/mirror.conf, which is
    # only generated with repository/mirror=true
    if not configRegistry.is_true('repository/mirror', False):
        print('Error: Mirroring for the local repository is disabled. Set the Univention Configuration Registry variable repository/mirror to yes.')
        sys.exit(1)

    # create mirror_base and symbolic link "univention-repository" if missing
    destdir = os.path.join(configRegistry.get('repository/mirror/basepath', '/var/lib/univention-repository'), 'mirror')
    makedirs(destdir)
    try:
        os.symlink('.', os.path.join(destdir, 'univention-repository'))
    except EnvironmentError as e:
        if e.errno != errno.EEXIST:
            raise

    if options.sync:
        # only update packages of current repositories
        mirror.run()
    elif options.errata_only:
        # trigger update to find new errata repositories
        handler_commit(['/etc/apt/mirror.list'])
        mirror.run()
    elif options.update_to:
        # trigger update to explicitly mirror until given versions
        handler_set(['repository/mirror/version/end=%s' % options.update_to])
        mirror = UniventionMirror()
        mirror.run()
    else:
        # mirror all future versions
        handler_commit(['/etc/apt/mirror.list'])
        nextupdate = mirror.release_update_available()
        mirror_run = False
        while nextupdate:
            handler_set(['repository/mirror/version/end=%s' % nextupdate])
            # UCR variable repository/mirror/version/end has change - reinit Mirror object
            mirror = UniventionMirror()
            mirror.run()
            mirror_run = True
            nextupdate = mirror.release_update_available(nextupdate)
        if not mirror_run:
            # sync only
            mirror.run()


def parse_args() -> Namespace:

    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        '-s', '--sync-only', action='store_true',
        dest='sync',
        help='if given no new release repositories will be added, just the existing will be updated')
    parser.add_argument(
        '-E', '--errata-only', action='store_true',
        help='if given only errata repositories will be updated')
    parser.add_argument(
        '-u', '--updateto',
        dest='update_to', default='',
        help='if given the repository is updated to the specified version but not higher')
    parser.add_argument(
        "command",
        choices=("net", ),
        help="Update command")

    return parser.parse_args()


def main() -> None:
    # PATH does not contain */sbin when called from cron
    os.putenv('PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin')

    options = parse_args()

    print('***** Starting univention-repository-update at %s\n' % time.ctime())

    urepo.assert_local_repository()

    with UpdaterLock():
        if options.command == 'net':
            local_server = '%(hostname)s.%(domainname)s' % configRegistry
            # BUG: The localhost has many names, FQDNs and addresses ...
            if configRegistry['repository/mirror/server'] == local_server:
                print('Error: The local server is configured as mirror source server (repository/mirror/server)')
                sys.exit(1)

            try:
                update_net(options)
            except VerificationError as ex:
                print("Error: %s" % (ex,))
                print('\n'.join(wrap(dedent(
                    """\
                    This can and should only be disabled temporarily using the UCR variable
                    'repository/mirror/verify'.
                    """
                ))))
                sys.exit(1)
            except UpdaterException as e:
                print("Error: %s" % e)
                sys.exit(1)


if __name__ == '__main__':
    main()
