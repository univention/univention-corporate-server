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

# TODO: use UCR variables for update, upgrade, install and remove commands
from __future__ import print_function

import os
import re
import shlex
import subprocess
import sys
import time
from argparse import ArgumentParser, Namespace  # noqa F401
from typing import Any, Container, List, NoReturn, Optional, Sequence  # noqa F401

from univention.config_registry import ConfigRegistry, handler_set, handler_unset
from univention.lib.policy_result import PolicyResultFailed, policy_result
from univention.updater.commands import (
    cmd_config,
    cmd_dist_upgrade,
    cmd_dist_upgrade_sim,
    cmd_install,
    cmd_remove,
    cmd_show,
    cmd_update,
    cmd_upgrade,
    cmd_upgrade_sim,
)
from univention.updater.locking import UpdaterLock, apt_lock
from univention.lib.policy_result import PolicyResultFailed, policy_result

try:
    from typing_extensions import Literal  # noqa F401
    _JOB = Literal["add", "remove"]
except ImportError:
    _JOB = str  # type: ignore


LOGNAME = '/var/log/univention/actualise.log'
RE_STAT = re.compile(br'^(\d+) upgraded, (\d+) newly installed, (\d+) to remove and (?:\d+) not upgraded.')
RE_APT = re.compile(r'^(?:deb|deb-src)\s+(?:\[[^]]+\]\s+)?([^:]*):')

configRegistry = ConfigRegistry()
configRegistry.load()

ldap_hostdn = configRegistry.get('ldap/hostdn')


class Tee(object):

    '''
    Writes the given string to several files at once. Could by used
    with the print statement
    '''

    def __init__(self, files: Sequence[str] = [], stdout: bool = True, filter: Optional[str] = None) -> None:
        self.stdout = stdout
        self.files = files
        self.filter = filter

    def call(self, command: Sequence[str], **kwargs: Any) -> int:
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)
        tee_command = ['tee', '-a'] + list(self.files)
        if self.stdout:
            if self.filter:
                tee = subprocess.Popen(tee_command, stdin=p.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                egrep = subprocess.Popen(['egrep', self.filter], stdin=tee.stdout)
                ret = egrep.wait()
            else:
                tee = subprocess.Popen(tee_command, stdin=p.stdout)
        else:
            tee = subprocess.Popen(tee_command, stdin=p.stdout, stdout=subprocess.DEVNULL)

        # Must wait for exit from back to front, only the exit status of p is relevant
        ret = tee.wait()
        ret = p.wait()

        return ret


def getUpdate() -> None:
    """
    Small function waiting for apt lockfile to vanish then starts apt-get update
    """

    print("Running apt-get update")
    with apt_lock(), open(LOGNAME, 'a') as logfile:
        res = subprocess.call(shlex.split(cmd_update), stdout=logfile, stderr=logfile)

    if res != 0:
        print("E: failed to update", file=sys.stderr)
        sys.exit(res)


def deactivateSourcesListMethods(methods: Container[str] = ['cdrom']) -> None:
    """
    Remove APT repositories using given scheme.

    :param methods: The list of URI schemes to remove.
    """
    FN = '/etc/apt/sources.list'
    lines = []
    deactivated_lines = []

    with open(FN, 'r') as f:
        for line in f:
            match = RE_APT.match(line)
            if match and match.group(1) in methods:
                line = '#' + line
                deactivated_lines.append('  ' + line)

            lines.append(line)

    if deactivated_lines:
        with open(FN, 'w') as f:
            f.write(''.join(lines))

        with open(LOGNAME, 'a+') as debug_file:
            debug_file.write('Hint: deactivated %d lines in %s:\n' % (len(deactivated_lines), FN))
            debug_file.write(''.join(deactivated_lines))


def check(configRegistry: ConfigRegistry, dist_upgrade: bool = False) -> bool:
    """
    Just probe if there are packages to add or remove

    :param dist_upgrade: Perform distribution upgrade instead of package updates.
    :returns: `True` if there are package changes.
    """
    getUpdate()

    # Probe for packages to actualise
    cmd = cmd_dist_upgrade_sim if dist_upgrade else cmd_upgrade_sim

    with apt_lock():
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        assert proc.stdout
        for line in proc.stdout:
            match = RE_STAT.match(line)
            if match:
                upgraded, newlyinstalled, remove = (int(_) for _ in match.groups())
                break
        else:
            return False

    return any((
        upgraded,
        newlyinstalled,
        remove,
        getPackageList(configRegistry, 'remove'),
        getPackageList(configRegistry, 'add'),
    ))


def getPackageList(configRegistry: ConfigRegistry, job: _JOB) -> List[str]:
    """
    Get a list of packages to remove or add, depending on the value of job.

    :param configRegistry: UCR instance.
    :param job: `add` or `remove`.
    :returns: List of package names.
    """
    try:
        packages_name = 'univention%sPackages%s' % (
            {
                "memberserver": "Member",
                "domaincontroller_slave": "Slave",
                "domaincontroller_master": "Master",
                "domaincontroller_backup": "Master",
            }[configRegistry['server/role']],
            {
                "remove": "Remove",
                "add": "",
            }[job],
        )
    except LookupError:
        exit("E: no valid job defined")

    try:
        results, _policies = policy_result(ldap_hostdn)
        return results.get(packages_name, [])
    except PolicyResultFailed as ex:
        sys.exit('failed to execute univention_policy_result: %s' % ex)


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Perform a (dist-)upgrade and (un-)install packages as set through policies")
    parser.add_argument("--dist-upgrade", action="store_true", help="Perform a dist-upgrade instead of a regular update")
    parser.add_argument("--silent", action="store_true", help="Don't show normal output, but error messages only")
    parser.add_argument("--check", action="store_true", help="Don't do anything, just check if updates are available")
    return parser.parse_args()


def run(opt: Namespace) -> int:
    os.putenv('PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin')
    os.environ['LC_ALL'] = 'C.UTF-8'
    os.environ['DEBIAN_FRONTEND'] = 'noninteractive'

    check_failed()
    remove_temp()

    pkgdb = None
    pkgdb_scope = None

    if opt.silent:
        # redirect stdout to /dev/null
        sys.stdout = open("/dev/null", "w")

    try:
        if opt.check:
            # Only probe for packages to add/remove
            return check(configRegistry, opt.dist_upgrade)

        if ldap_hostdn:
            logfile = open(LOGNAME, 'a')
            logfile.write('***** Starting univention-actualise at %s\n' % time.ctime())

            deactivateSourcesListMethods(methods=['cdrom'])

            getUpdate()

            # temporarily disable pkgdb
            pkgdb_scan = configRegistry.get('pkgdb/scan', getscope=True)
            if pkgdb_scan:
                # get value and UCR scope of variable pkgdb/scan
                pkgdb_scope, pkgdb = pkgdb_scan
                if pkgdb:
                    # disable pkgdb in UCR scope FORCED
                    handler_set(['pkgdb/scan=no'], {'force': True})

            rem_packages = getPackageList(configRegistry, 'remove')
            for package in rem_packages:
                # check if the package exists
                with apt_lock():
                    res = subprocess.call(shlex.split(cmd_show) + [package], stdout=logfile, stderr=logfile)
                if res == 0:
                    print("Removing packages: %s" % package)
                    with apt_lock():
                        res = subprocess.call(shlex.split(cmd_config), stdout=logfile, stderr=logfile)
                        if not res:
                            res = subprocess.call(shlex.split(cmd_remove) + [package], stdout=logfile, stderr=logfile)
                else:
                    print("The package %s doesn't exist." % package)
                    res = 0
                if res != 0:
                    print("E: failed to remove %s" % package, file=sys.stderr)
                    sys.exit(res)

            add_packages = getPackageList(configRegistry, 'add')
            for package in add_packages:
                with apt_lock():
                    res = subprocess.call(shlex.split(cmd_show) + [package], stdout=logfile, stderr=logfile)
                if res == 0:
                    print("Installing packages: %s" % package)
                    with apt_lock():
                        res = subprocess.call(shlex.split(cmd_config), stdout=logfile, stderr=logfile)
                        if not res:
                            res = subprocess.call(shlex.split(cmd_install) + [package], stdout=logfile, stderr=logfile)
                else:
                    print("The package %s doesn't exist." % package)
                    res = 0

                if res != 0:
                    print("E: failed to install %s" % package, file=sys.stderr)
                    sys.exit(res)

        else:
            # ldap/hostdn is not set
            if configRegistry['server/role'] != 'basesystem':
                print("W: ldap/hostdn is not set - please run univention-join", file=sys.stderr)

        if opt.dist_upgrade:
            msg = "Dist-upgrading system"
            cmd = cmd_dist_upgrade
        else:
            msg = "Upgrading system"
            cmd = cmd_upgrade

        print(msg)
        # TODO: use mkstemp and close directly the file descriptor

        with apt_lock():
            tee = Tee([LOGNAME], stdout=not opt.silent)
            res = tee.call(shlex.split(cmd_config))
        if res != 0:
            print("E: failed to configure packets, see %s for details." % LOGNAME, file=sys.stderr)
        else:
            tee = Tee([LOGNAME], stdout=not opt.silent, filter='(^Get|^Unpacking|^Preparing|^Setting up|packages upgraded)')
            res = tee.call(cmd.split(' '))
            if res != 0:
                print("E: failed to upgrade, see %s for details." % LOGNAME, file=sys.stderr)

        sys.exit(res)

    finally:
        if pkgdb:
            if pkgdb_scope == ConfigRegistry.FORCED:
                # old value was set in FORCED scope
                handler_set(['pkgdb/scan=%s' % pkgdb], {'force': True})
            else:
                # old value was set in any other scope ==> remove value in FORCED scope
                handler_unset(['pkgdb/scan'], {'force': True})

            if str(pkgdb).lower() in ("yes", "enable", "enabled", "true", "1"):
                subprocess.call(('/usr/sbin/univention-pkgdb-scan',))


def update_ucr_updatestatus() -> None:
    try:
        subprocess.call('/usr/share/univention-updater/univention-updater-check', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print('Warning: calling univention-updater-check failed.')


def check_failed() -> None:
    failure = '/var/lib/univention-updater/update-failed'
    if os.path.exists(failure):
        print('univention-actualise: univention-updater failed, stopping...')
        print('	   remove `%s\' to proceed' % failure)
        sys.exit(2)


def remove_temp() -> None:
    try:
        for root, dirs, files in os.walk('/etc/apt/sources.list.d'):
            for file in [file for file in files if file.startswith('00_ucs_temporary_')]:
                filename = os.path.join(root, file)
                print('Warning: Deleting `%s` from incomplete update.' % filename)
                os.remove(filename)
            del dirs[:]
    except EnvironmentError:
        print('Failed, aborting.')
        sys.exit(2)


def main() -> NoReturn:
    opt = parse_args()

    res = 0
    try:
        with UpdaterLock():
            res = run(opt)
    except SystemExit as ex:
        if ex.args[0] == 0:
            update_ucr_updatestatus()
    sys.exit(res)


if __name__ == '__main__':
    main()
