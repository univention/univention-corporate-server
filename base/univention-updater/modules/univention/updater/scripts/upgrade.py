#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (C) 2010-2021 Univention GmbH
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
Install UCS release and errata updates.
"""

from __future__ import print_function

import os
import sys
import time
import subprocess
import traceback
import logging
import socket
from argparse import ArgumentParser, FileType, Namespace
from typing import Iterable, List, Optional, NoReturn, Tuple

from univention.lib.ucs import UCS_Version
from univention.config_registry import ConfigRegistry, handler_set

from univention.admindiary.client import write_event
from univention.admindiary.events import UPDATE_STARTED, UPDATE_FINISHED_SUCCESS, UPDATE_FINISHED_FAILURE

from univention.updater.errors import ConfigurationError
from univention.updater.tools import UniventionUpdater
from univention.updater.locking import UpdaterLock

FN_STATUS = '/var/lib/univention-updater/univention-upgrade.status'

UCR_UPDATE_AVAILABLE = 'update/available'
LOGFN = '/var/log/univention/updater.log'

configRegistry = ConfigRegistry()
logfd = None
silent = False


def dprint(silent: bool, msg: str, newline: bool = True, debug: bool = False) -> None:
    """Print debug output."""
    if silent:
        return
    if logfd:
        if newline:
            print(msg, file=logfd)
        else:
            print('%-55s' % msg, end=' ', file=logfd)
        logfd.flush()
    if not debug:
        if newline:
            print(msg)
        else:
            print('%-55s' % msg, end=' ')
        sys.stdout.flush()


updater_status = {}


def update_status(**kwargs: str) -> None:
    '''
    update updater_status and write status to disk

    Keys:
    - current_version ==> UCS_Version ==> 2.3-1
    - next_version    ==> UCS_Version ==> 2.3-2
    - updatetype      ==> (LOCAL|NET|CDROM)
    - status          ==> (RUNNING|FAILED|DONE)
    - errorsource     ==> (SETTINGS|PREPARATION|PREUP|UPDATE|POSTUP)
    '''
    global updater_status
    updater_status.update(kwargs)
    # write temporary file
    fn = '%s.new' % FN_STATUS
    try:
        with open(fn, 'w+') as fd:
            for key, val in updater_status.items():
                fd.write('%s=%s\n' % (key, val))
    except EnvironmentError:
        dprint(silent, 'Warning: cannot update %s' % fn)
    try:
        os.rename(fn, FN_STATUS)
    except EnvironmentError:
        dprint(silent, 'Warning: cannot update %s' % FN_STATUS)


def readcontinue(msg: str) -> bool:
    """Print message and read yes/no/abort answer."""
    while True:
        try:
            choice = input(msg).lower().strip()
            if choice == '' or choice == 'y' or choice == 'j':
                print('')
                return True
            elif choice == 'n':
                print('')
                return False
            else:
                continue
        except KeyboardInterrupt:
            print('\n')
            return False


def _package_list(new_packages: Iterable[Tuple[str, ...]]) -> str:
    """Return comma separated list of packages."""
    return ",".join(p[0] for p in new_packages)


def performUpdate(options: Namespace, checkForUpdates: bool = False, silent: bool = False) -> Optional[bool]:
    for func in (do_package_updates, do_app_updates, do_release_update):
        if func(options, checkForUpdates, silent):
            if checkForUpdates:
                return True
            else:
                do_exec()
    return None


def do_release_update(options: Namespace, checkForUpdates: bool, silent: bool) -> bool:
    updater = UniventionUpdater()

    # get next release update version
    dprint(silent, 'Checking for release updates: ', newline=False)
    version_next = updater.release_update_available()
    if not version_next:
        dprint(silent, 'none')
        return False
    if options.updateto and UCS_Version(options.updateto) < UCS_Version(version_next):
        dprint(silent, '%s is available but updater has been instructed to stop at version %s.' % (version_next, options.updateto))
        return False
    dprint(silent, 'found: UCS %s' % version_next)
    if checkForUpdates:
        return True

    interactive = not (options.noninteractive or checkForUpdates)
    if interactive and not readcontinue('Do you want to update to %s [Y|n]?' % version_next):
        return False

    update_status(
        current_version=updater.current_version,
        next_version=version_next,
        status='RUNNING')

    dprint(silent, 'Starting update to UCS version %s at %s...' % (version_next, time.ctime()), debug=True)
    dprint(silent, 'Starting update to UCS version %s' % (version_next))
    time.sleep(1)
    params = ['--silent']
    if options.ignoressh:
        params.append('--ignoressh')
    if options.ignoreterm:
        params.append('--ignoreterm')
    retcode = subprocess.call(['/usr/share/univention-updater/univention-updater', 'net', '--updateto', '%s' % (version_next)] + params, env=os.environ)
    if retcode:
        dprint(silent, 'exitcode of univention-updater: %s' % retcode, debug=True)
        dprint(silent, 'ERROR: update failed. Please check /var/log/univention/updater.log\n')
        update_status(status='FAILED', errorsource='UPDATE')
        sys.exit(1)
    dprint(silent, 'Update to UCS version %s finished at %s...' % (version_next, time.ctime()), debug=True)
    return True


def do_package_updates(options: Namespace, checkForUpdates: bool, silent: bool) -> bool:
    interactive = not (options.noninteractive or checkForUpdates)
    updater = UniventionUpdater()
    # check if component updates are available
    dprint(silent, 'Checking for package updates: ', newline=False)
    new_packages, upgraded_packages, removed_packages = updater.component_update_get_packages()
    update_available = bool(new_packages + upgraded_packages + removed_packages)

    if not update_available:
        dprint(silent, 'none')
        return False

    # updates available ==> stop here in "check-mode"
    if checkForUpdates:
        dprint(silent, 'found')
        return True

    dprint(silent, 'found\n')
    if len(removed_packages) > 0:
        dprint(silent, 'The following packages will be REMOVED:\n %s' % _package_list(removed_packages))
    if len(new_packages) > 0:
        dprint(silent, 'The following packages will be installed:\n %s' % _package_list(new_packages))
    if len(upgraded_packages) > 0:
        dprint(silent, 'The following packages will be upgraded:\n %s' % _package_list(upgraded_packages))
    if interactive and not readcontinue('\nDo you want to continue [Y|n]?'):
        return False

    time.sleep(1)
    dprint(silent, 'Starting dist-update at %s...' % (time.ctime()), debug=True)
    dprint(silent, 'Starting package upgrade', newline=False)

    hostname = socket.gethostname()
    context_id = write_event(UPDATE_STARTED, {'hostname': hostname})
    if context_id:
        os.environ['ADMINDIARY_CONTEXT'] = context_id
    returncode = updater.run_dist_upgrade()

    if returncode:
        dprint(silent, 'exitcode of apt-get dist-upgrade: %s' % returncode, debug=True)
        dprint(silent, 'ERROR: update failed. Please check /var/log/univention/updater.log\n')
        update_status(status='FAILED', errorsource='UPDATE')
        write_event(UPDATE_FINISHED_FAILURE, {'hostname': hostname})
        sys.exit(1)
    dprint(silent, 'dist-update finished at %s...' % (time.ctime()), debug=True)
    dprint(silent, 'done')
    write_event(UPDATE_FINISHED_SUCCESS, {'hostname': hostname, 'version': 'UCS %(version/version)s-%(version/patchlevel)s errata%(version/erratalevel)s' % configRegistry})
    time.sleep(1)
    return True


def do_app_updates(options: Namespace, checkForUpdates: bool, silent: bool) -> Optional[bool]:
    dprint(silent, 'Checking for app updates: ', newline=False)
    if not options.app_updates:
        dprint(silent, 'skipped')
        return None

    interactive = not (options.noninteractive or checkForUpdates)
    try:
        from univention.appcenter.actions import get_action, Abort
        from univention.appcenter.app_cache import Apps
        import univention.appcenter.log as appcenter_log
        app_upgrade_search = get_action('upgrade-search')
        app_upgrade = get_action('upgrade')
        if app_upgrade is None:
            raise ImportError()
    except ImportError:
        # the new univention.appcenter package is not installed. Never mind
        # cannot be a dependency as the app center depends on updater...
        dprint(silent, 'unavailable')
        return False

    # check if component updates are available
    appcenter_log.log_to_logfile()

    # own logging
    logger = logging.getLogger('univention.appcenter.actions.upgrade.readme')
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    try:
        app_upgrade_search.call()
    except Abort:
        pass

    new_apps = list(app_upgrade.iter_upgradable_apps())
    if not new_apps:
        dprint(silent, 'none')
        return False
    elif checkForUpdates:
        dprint(silent, 'found')
        return True

    dprint(silent, 'found\n')
    dprint(silent, 'The following apps can be upgraded:\n')
    for app in new_apps:
        newer_app = Apps().find_candidate(app)
        if newer_app:
            dprint(silent, '%(name)s: Version %(old)s can be upgraded to %(new)s' % {
                'name': app.name,
                'old': app.version,
                'new': newer_app.version,
            })
        elif app.docker:
            dprint(silent, '%(name)s: The underlying container can be upgraded' % {
                'name': app.name,
            })
        else:
            # don't know how this is possible... but anyways
            dprint(silent, '%(name)s' % {
                'name': app.name,
            })

    dprint(silent, 'Starting univention-app upgrade at %s...' % time.ctime(), debug=True)
    dprint(silent, 'Most of the output for App upgrades goes to %s' % appcenter_log.LOG_FILE, debug=True)
    dprint(silent, '\nStarting app upgrade', newline=False)
    success = True
    for app in new_apps:
        if interactive and not readcontinue('\nDo you want to upgrade %s [Y|n]?' % app.name):
            continue
        success &= bool(app_upgrade.call_safe(
            app=app,
            noninteractive=not interactive,
            username=options.username,
            pwdfile=options.pwdfile.name if options.pwdfile else None,
        ))

    if not success:
        dprint(silent, 'ERROR: app upgrade failed. Please check %s\n' % appcenter_log.LOG_FILE)
        return False  # pretend no updates available; otherwise do_exec may result in infinite loop
    dprint(silent, 'univention-app upgrade finished at %s...' % time.ctime(), debug=True)
    dprint(silent, 'done')
    return not success  # pending updates


def parse_args(argv: Optional[List[str]] = None) -> Namespace:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--updateto",
        help="update up to specified version")
    parser.add_argument(
        "--check",
        action="store_true",
        help="check if updates are available")
    parser.add_argument(
        "--setucr",
        action="store_true",
        help="if set, variable update/available will be updated")
    parser.add_argument(
        "--ignoressh",
        action="store_true",
        help="pass --ignoressh to univention-updater")
    parser.add_argument(
        "--ignoreterm",
        action="store_true",
        help="pass --ignoreterm to univention-updater")
    parser.add_argument(
        "--noninteractive",
        action="store_true",
        help="Perform a non-interactive update")
    parser.add_argument(
        "--iso",
        help="ISO image for the repository update")
    parser.add_argument(
        "--cdrom",
        default="/dev/cdrom",
        help="CDROM device for the repository update")

    group = parser.add_argument_group("App updates")
    group.add_argument(
        "--enable-app-updates",
        dest="app_updates",
        action="store_true",
        help="Update installed Apps")
    group.add_argument(
        "--disable-app-updates",
        dest="app_updates",
        action="store_false",
        help="Skip updating installed Apps")
    group.add_argument(
        "--username",
        help="Name of the user used for registering the app")
    group.add_argument(
        "--pwdfile",
        type=FileType("r"),
        help="Name of the file containing the user password")

    parser.set_defaults(app_updates=True)
    options = parser.parse_args()

    if options.app_updates:
        if options.pwdfile and not options.username:
            parser.error("--pwdfile without --username")
        elif options.username and not options.pwdfile:
            parser.error("--username without --pwdfile")

    return options


def main() -> None:
    global logfd

    options = parse_args()

    try:
        logfd = open(LOGFN, 'a+')
        FORMAT = "%(asctime)-15s " + logging.BASIC_FORMAT
        logger = logging.getLogger('updater')
        handler = logging.StreamHandler(logfd)
        formatter = logging.Formatter(FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
    except EnvironmentError:
        print('Cannot open %s for writing' % LOGFN)
        sys.exit(1)

    configRegistry.load()

    if options.noninteractive:
        os.environ['UCS_FRONTEND'] = 'noninteractive'

    dprint(silent, '\nStarting univention-upgrade. Current UCS version is %(version/version)s-%(version/patchlevel)s errata%(version/erratalevel)s\n' % configRegistry)

    with UpdaterLock():
        if options.check:
            return do_update(options)

        update_local_repository(options)
        do_update(options)


def update_local_repository(options: Namespace) -> None:
    dprint(silent, 'Checking for local repository: ', newline=False)
    if configRegistry.is_true('local/repository', False) and configRegistry.is_true('repository/mirror', False):
        dprint(silent, 'found\n')
        if options.noninteractive or readcontinue('Update the local repository via network [Y|n]?'):
            if options.updateto:
                subprocess.call(('/usr/sbin/univention-repository-update', 'net', '--updateto', options.updateto))
            else:
                subprocess.call(('/usr/sbin/univention-repository-update', 'net'))
        elif options.noninteractive or readcontinue('Update the local repository via cdrom [Y|n]?'):
            if options.iso:
                subprocess.call(('/usr/sbin/univention-repository-update', 'cdrom', '--iso', options.iso))
            else:
                subprocess.call(('/usr/sbin/univention-repository-update', 'cdrom', '--device', options.cdrom))
    else:
        dprint(silent, 'none')


def do_update(options: Namespace) -> None:
    try:
        update_available = performUpdate(options, checkForUpdates=options.check, silent=False)
    except ConfigurationError as e:
        update_status(status='FAILED', errorsource='SETTINGS')
        print('The connection to the repository server failed: %s. Please check the repository configuration and the network connection.' % e, file=sys.stderr)
        sys.exit(3)
    except Exception:
        update_status(status='FAILED')
        print('An error occurred - see "%s" for details' % (LOGFN,))
        print('Traceback in univention-upgrade:', file=logfd)
        print(traceback.format_exc(), file=logfd)
        sys.exit(2)
    update_status(status='DONE')
    if options.setucr and configRegistry.is_true(UCR_UPDATE_AVAILABLE) != update_available:
        handler_set([
            '%s=%s' % (UCR_UPDATE_AVAILABLE, 'yes' if update_available else 'no'),
        ])

    if options.check:
        if update_available:
            dprint(silent, 'Please rerun command without --check argument to install.')
            sys.exit(0)
        else:
            print('No update available.')
            sys.exit(1)

    if update_available:
        do_exec()


def do_exec() -> NoReturn:
    # The updater/UCR/libs might have been replaced - re-execute!
    cmd = sys.argv + ['--setucr']
    print("execv(%r)" % (cmd,), file=logfd)
    os.execv(sys.argv[0], cmd)


if __name__ == '__main__':
    main()
