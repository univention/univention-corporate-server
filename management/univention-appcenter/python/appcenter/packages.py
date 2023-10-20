#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2016-2023 Univention GmbH
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
Univention App Center
 Package functions
"""

import fcntl
import os
import re
import time
from contextlib import contextmanager
from logging import Handler, LogRecord  # noqa: F401
from typing import Dict, Iterable, Iterator, List  # noqa: F401

from six import string_types

from univention.appcenter.log import LogCatcher, get_base_logger
from univention.appcenter.utils import call_process
from univention.lib.package_manager import LockError, PackageManager  # LockError is actually imported from other files!


package_logger = get_base_logger().getChild('packages')


LOCK_FILE = '/var/run/univention-appcenter.lock'


class _PackageManagerLogHandler(Handler):

    def emit(self, record):
        # type: (LogRecord) -> None
        if record.name.startswith('packagemanager.dpkg'):
            if isinstance(record.msg, string_types):
                record.msg = record.msg.rstrip() + '\r'
            if record.name.startswith('packagemanager.dpkg.percentage'):
                record.levelname = 'DEBUG'
                record.levelno = 10


def get_package_manager():
    # type: () -> PackageManager
    if get_package_manager._package_manager is None:  # type: ignore
        package_manager = PackageManager(lock=False)
        package_manager.set_finished()  # currently not working. accepting new tasks
        package_manager.logger.parent = get_base_logger()
        log_filter = _PackageManagerLogHandler()
        package_manager.logger.addHandler(log_filter)
        get_package_manager._package_manager = package_manager  # type: ignore
    return get_package_manager._package_manager  # type: ignore


get_package_manager._package_manager = None  # type: ignore


def reload_package_manager():
    # type: () -> None
    if get_package_manager._package_manager is not None:  # type: ignore
        get_package_manager().reopen_cache()


def packages_are_installed(pkgs, strict=True):
    # type: (Iterable[str], bool) -> bool
    package_manager = get_package_manager()
    if strict:
        return all(package_manager.is_installed(pkg) for pkg in pkgs)
    else:
        # app.is_installed(package_manager, strict=True) uses
        # apt_pkg.CURSTATE. Not desired when called during
        # installation of umc-module-appcenter together with
        # several other (app relevant) packages; for example
        # in postinst or joinscript (on Primary Node).
        # see Bug #33535 and Bug #31261
        for pkg_name in pkgs:
            try:
                pkg = package_manager.get_package(pkg_name, raise_key_error=True)
            except KeyError:
                return False
            else:
                if not pkg.is_installed:
                    return False
        return True


@contextmanager
def package_lock():
    # type: () -> Iterator[None]
    try:
        fd = open(LOCK_FILE, 'w')
        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except EnvironmentError:
        raise LockError('Could not acquire lock!')
    else:
        package_logger.debug('Holding LOCK')
        try:
            yield
        finally:
            package_logger.debug('Releasing LOCK')
            try:
                os.unlink(LOCK_FILE)
            except EnvironmentError:
                pass
            fd.close()


def wait_for_dpkg_lock(timeout=120):
    # type: (int) -> bool
    lock_files = ['/var/lib/dpkg/lock', '/var/lib/apt/lists/lock']
    lock_file_string = ' or '.join(lock_files)
    package_logger.debug(f'Trying to get a lock for {lock_file_string}...')
    first = True
    while first or timeout > 0:
        returncode = call_process(['fuser'] + lock_files).returncode
        if returncode == 0:
            if first:
                package_logger.info(f'Could not lock {lock_file_string}. Is another process using it? Waiting up to {timeout} seconds')
                first = False
            # there seems to be a timing issue with the fuser approach
            # in which the second (the apt) process releases its lock before
            # re-grabbing it once again
            # we hope to minimize this error by having a relatively high sleep duration
            sleep_duration = 3
            time.sleep(sleep_duration)
            timeout -= sleep_duration
        else:
            if not first:
                package_logger.info('Finally got the lock. Continuing...')
            return True
    package_logger.info('Unable to get a lock. Giving up...')
    return False


def _apt_args(dry_run=False):
    # type: (bool) -> List[str]
    apt_args = ['-o', 'DPkg::Options::=--force-confold', '-o', 'DPkg::Options::=--force-overwrite', '-o', 'DPkg::Options::=--force-overwrite-dir', '--trivial-only=no', '--assume-yes', '--auto-remove']
    return apt_args


def _apt_get(action, pkgs):
    # type: (str, List[str]) -> int
    env = os.environ.copy()
    env['DEBIAN_FRONTEND'] = 'noninteractive'
    apt_args = _apt_args()
    ret = call_process(['/usr/bin/apt-get'] + apt_args + [action] + pkgs, logger=package_logger, env=env).returncode == 0
    reload_package_manager()
    return ret


def _apt_get_dry_run(action, pkgs):
    # type: (str, List[str]) -> Dict[str, List[str]]
    apt_args = _apt_args()
    logger = LogCatcher(package_logger)
    success = call_process(['/usr/bin/apt-get'] + apt_args + [action, '-s'] + pkgs, logger=logger).returncode == 0
    install, remove, broken = [], [], []
    install_regex = re.compile(r'^(Inst) ([^ ]*?) \((.*?) ')
    upgrade_remove_regex = re.compile(r'^(Remv|Inst) ([^ ]*?) \[(.*?)\]')
    for line in logger.stdout():
        for regex in [install_regex, upgrade_remove_regex]:
            match = regex.match(line)
            if match:
                operation, pkg_name, version = match.groups()
                if operation == 'Inst':
                    install.append(pkg_name)
                elif operation == 'Remv':
                    remove.append(pkg_name)
                break
    if not success:
        for pkg in pkgs:
            if action == 'install' and pkg not in install:
                broken.append(pkg)
            if action == 'remove' and pkg not in remove:
                broken.append(pkg)
    return dict(zip(['install', 'remove', 'broken'], [install, remove, broken]))


def install_packages_dry_run(pkgs):
    # type: (List[str]) -> Dict[str, List[str]]
    return _apt_get_dry_run('install', pkgs)


def dist_upgrade_dry_run():
    # type: () -> Dict[str, List[str]]
    return _apt_get_dry_run('dist-upgrade', [])


def install_packages(pkgs):
    # type: (List[str]) -> int
    return _apt_get('install', pkgs)


def remove_packages_dry_run(pkgs):
    # type: (List[str]) -> Dict[str, List[str]]
    return _apt_get_dry_run('remove', pkgs)


def remove_packages(pkgs):
    # type: (List[str]) -> int
    return _apt_get('remove', pkgs)


def dist_upgrade():
    # type: () -> int
    return _apt_get('dist-upgrade', [])


def update_packages():
    # type: () -> None
    call_process(['/usr/bin/apt-get', 'update'], logger=package_logger)
    reload_package_manager()


def mark_packages_as_manually_installed(pkgs):
    # type: (List[str]) -> None
    call_process(['/usr/bin/apt-mark', 'manual'] + pkgs, logger=package_logger)
    reload_package_manager()
