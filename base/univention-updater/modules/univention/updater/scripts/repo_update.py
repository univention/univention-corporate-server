#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright 2004-2021 Univention GmbH
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
import subprocess
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


def update_cdrom(options: Namespace) -> None:
    """ Copy repository from local DVD or ISO image """
    # try to mount update ISO image or DVD
    if options.iso_file:
        ret = subprocess.call(['mount', '-o', 'loop', options.iso_file, options.mount_point])
    elif options.device:
        ret = subprocess.call(['mount', options.device, options.mount_point])
    else:
        ret = subprocess.call(['mount', options.mount_point])

    # 0 == success, 32 == already mounted
    if ret not in (0, 32):
        if options.iso_file:
            print('Error: Failed to mount ISO image %s' % options.iso_file)
        else:
            print('Error: Failed to mount CD-ROM device at %s' % options.mount_point)
        sys.exit(1)

    try:
        # check update medium
        if not os.path.exists(os.path.join(options.mount_point, 'ucs-updates')):
            print('Error: This is not a valid UCS update medium')
            sys.exit(1)

        # find UCS version
        for entry in os.listdir(os.path.join(options.mount_point, 'ucs-updates')):
            directory = os.path.join(options.mount_point, 'ucs-updates', entry)
            if os.path.isdir(directory):
                # copy repository
                try:
                    version = UCS_Version(entry)
                except (NameError, ValueError):
                    print("Error: Failed to parse %s" % (entry,))
                    sys.exit(1)
                try:
                    copy_repository(options, directory, version)
                except (IOError, os.error) as why:
                    print('\nError: while copying %s: %s' % (entry, why))
                    sys.exit(1)
    finally:
        ret = subprocess.call(['umount', options.mount_point])
        if ret != 0:
            print('Error: Failed to umount %s' % options.mount_point)
            sys.exit(ret)


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
    elif options.security_only:
        # trigger update to find new security repositories
        handler_commit(['/etc/apt/mirror.list'])
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
    for mount_point_default in ('/cdrom', '/media/cdrom', '/media/cdrom0'):
        if os.path.isdir(mount_point_default):
            break

    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        '-i', '--iso',
        dest='iso_file',
        help='define filename of an ISO image')
    parser.add_argument(
        '-d', '--device',
        help='defines the device name of the CD-ROM drive')
    parser.add_argument(
        '-c', '--cdrom',
        dest='mount_point', default=mount_point_default,
        help='devices mount point for CD-ROM drive')
    parser.add_argument(
        '-s', '--sync-only', action='store_true',
        dest='sync',
        help='if given no new release repositories will be added, just the existing will be updated')
    parser.add_argument(
        '-S', '--security-only', action='store_true',
        help='if given only security repositories will be updated')
    parser.add_argument(
        '-E', '--errata-only', action='store_true',
        help='if given only errata repositories will be updated')
    parser.add_argument(
        '-u', '--updateto',
        dest='update_to', default='',
        help='if given the repository is updated to the specified version but not higher')
    parser.add_argument(
        "command",
        choices=("net", "cdrom"),
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
        elif options.command == 'cdrom':
            update_cdrom(options)


if __name__ == '__main__':
    main()
