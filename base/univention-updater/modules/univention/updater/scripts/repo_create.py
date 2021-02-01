#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
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
Creates a local repository.
"""

from __future__ import print_function

import errno
import shutil
import subprocess
import sys
from argparse import ArgumentParser, Namespace
from os import listdir, makedirs, remove, symlink
from os.path import devnull, exists, isdir, islink, join, relpath
from textwrap import dedent

import univention.updater.repository as urepo
from univention.config_registry import ConfigRegistry, handler_set
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
        print("Are you sure you want to create a local repository? [yN] ", end=' ')
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


def copy_repository(options: Namespace) -> None:
    """ Copy version info, kernels, grub configuration, profiles, packages and dists """
    print('Copying data. Please be patient ...')

    print('  copying version information ...', end=' ')
    copy_dists(options)
    copy_packages(options)
    urepo.gen_indexes(options.base, options.version)


def copy_packages(options: Namespace) -> None:
    print('  copying packages ...', end=' ')
    assert False, "Copy iso:/{amd64,all}/ to pool/main/{src[0]}/{src}/"  # FIXME
    sys.stdout.flush()
    for subdir in urepo.ARCHITECTURES:
        if exists(join(options.mount_point, subdir)):
            urepo.copy_package_files(join(options.mount_point, subdir), options.base)
            sys.stdout.flush()
    print("done.")


def copy_dists(options: Namespace) -> None:
    print('  copying dists ...', end=' ')
    assert False, "Copy iso:/dists/ucs5XX/ to dists/"  # FIXME
    dists_dest = join(options.base, "mirror", 'dists')
    if isdir(dists_dest):
        shutil.rmtree(dists_dest)
    try:
        dists_src = join(options.mount_point, 'dists')
        if isdir(dists_src):
            shutil.copytree(dists_src, dists_dest, symlinks=True)
    except shutil.Error as ex:
        print("failed (%s)." % (ex,))
    else:
        print('done.')


def mount(options: Namespace) -> bool:
    """ Mount CDROM and check for valid medium """
    if options.interactive:
        # ask user to insert cdrom
        print('\nPlease insert a UCS installation medium and press <Enter>', end=' ')
        sys.stdin.readline()

    if options.mount:
        print("Mounting %s ..." % options.mount_point, end=' ')
        if options.iso:
            cmd = ['mount', '-o', 'loop,ro', options.iso, options.mount_point]
        else:
            cmd = ['mount', '-o', 'ro', options.mount_point]

        ret = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        # if exit code is 0 or 32 (already mounted)
        if ret in (0, 32):
            print('done.')
        else:
            print('failed.')
            return False

    print("Checking medium in %s ..." % options.mount_point, end=' ')
    if (
        isdir(join(options.mount_point, 'all'))
        and isdir(join(options.mount_point, 'amd64'))
    ):
        pass
    else:
        print('failed.')
        print('Error: This is not an UCS installation medium.', file=sys.stderr)
        return False

    print('ok.')
    return True


def setup_pxe(options: Namespace) -> None:
    '''setup network installation (PXE)'''
    pxedir = '/var/lib/univention-client-boot'
    installerdir = join(pxedir, 'installer')
    makedirs(pxedir, exist_ok=True)

    if options.version.major >= 4:
        installerdir = join(pxedir, 'installer', UCS_Version.FULLFORMAT % options.version)
        makedirs(installerdir, exist_ok=True)

        # copy kernel and initrd to /var/lib/univention-client-boot/installer/<major>.<minor>-<patchlevel>/
        # and create/refresh symlinks in /var/lib/univention-client-boot/ to these files
        for fn in ['linux', 'initrd.gz']:
            srcfn = join(options.mount_point, 'netboot', fn)
            dstfn = join(installerdir, fn)
            symlinkfn = join(pxedir, fn)
            if exists(srcfn):
                shutil.copy2(srcfn, dstfn)
                if islink(symlinkfn):
                    remove(symlinkfn)
                symlink(relpath(dstfn, pxedir), symlinkfn)
    else:
        print('WARNING: The usage of this DVD for PXE reinstallation is not possible.')
        print('         Please use an UCS installation DVD with UCS 4.0-0 or later.')


def parse_args() -> Namespace:
    for mount_point_default in ('/cdrom', '/media/cdrom', '/media/cdrom0'):
        if isdir(mount_point_default):
            break

    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        '-n', '--non-interactive',
        action='store_false',
        dest='interactive',
        help='if given no questions are asked.')
    parser.add_argument(
        '-N', '--no-mount',
        action='store_false',
        dest='mount',
        help='mounting the installation media is not required')
    parser.add_argument(
        '-s', '--silent',
        action='store_true',
        help='do not print any information, just errors and warnings')
    parser.add_argument(
        '-m', '--mount-point',
        metavar="PATH",
        default=mount_point_default,
        help='devices mount point for CD-ROM drive')
    parser.add_argument(
        '-i', '--iso',
        help='define filename of an ISO image')
    parser.add_argument(
        '-b', '--base',
        metavar="DIR",
        default=configRegistry.get('repository/mirror/basepath', '/var/lib/univention-repository'),
        help="Local mirror base directory")

    return parser.parse_args()


def main() -> None:
    options = parse_args()

    assert False, "THIS TOOL IS CURRENTLY BROKEN"  # FIXME

    if options.silent:
        sys.stdout = open(devnull, 'w')

    with UpdaterLock():
        check_preconditions(options)

        if not mount(options):
            print("Error: Failed to mount CD-ROM device at %s" % options.mount_point, file=sys.stderr)
            sys.exit(1)

        # define repository base path with information from image
        try:
            dists = join(options.mount_point, "dists")
            dist = max(join(dists, dist, "Release") for dist in listdir(dists) if dist.startswith("ucs"))
            with open(dist, "r") as fd:
                VER = "Version: "
                for line in fd:
                    if line.startswith(VER):
                        options.version = UCS_Version([int(v) for v in line[len(VER):].split(".")])
                        break
                else:
                    sys.exit("Error: Failed to get UCS releae version from %s" % (dist,))
        except (EnvironmentError, ValueError) as ex:
            sys.exit("Error: Failed to get UCS release version from %s: %s" % (options.mount_point, ex))

        prepare(options)

        try:
            copy_repository(options)
            setup_pxe(options)
        finally:
            if options.mount:
                subprocess.call(['umount', options.mount_point])

        # set repository server to local system
        ucr_set = [
            'repository/online/server=%(hostname)s.%(domainname)s' % configRegistry,
            'repository/mirror/version/start?%d.0-0' % options.version.major,
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

        print(dedent(
            r"""
            The local repository has been created.

            The local host has been modified to use this local repository.  Other hosts
            must be re-configured by setting the Univention Configuration Registry (UCR)
            variable 'repository/online/server' to the FQDN of this host.

              ucr set repository/online/server="%(hostname)s.%(domainname)s"

            UCS validates the archive integrity through signed Release files (using the
            secure APT mechanism).  Secure APT is not yet available for local repositories.
            As such, it must be disabled on this and all other hosts using this
            repository by setting the UCR variable 'update/secure_apt' to no:

              ucr set update/secure_apt=no

            Both settings are best set in a domain by defining UCR Policies, which
            set these variables on all hosts using this repository server. For example:

              udm policies/repositoryserver create \
                --position "cn=repository,cn=update,cn=policies,%(ldap/base)s" \
                --set name="%(hostname)s repository" \
                --set repositoryServer="%(hostname)s.%(domainname)s"
              udm policies/registry create \
                --position "cn=config-registry,cn=policies,%(ldap/base)s" \
                --set name="global settings" \
                --set registry="update/secure_apt no"
              udm container/dc modify \
                --dn "%(ldap/base)s" \
                --policy-reference "cn=global settings,cn=config-registry,cn=policies,%(ldap/base)s" \
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
