#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for running an app specific test file
#
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import os
from argparse import REMAINDER
from tempfile import gettempdir
from urllib.request import Request

from univention.appcenter.actions import StoreAppAction, UniventionAppAction, possible_network_error
from univention.appcenter.exceptions import NetworkError
from univention.appcenter.ucr import ucr_get, ucr_save
from univention.appcenter.utils import call_process, urlopen


class DevTest(UniventionAppAction):
    """Tests an App by downloading and running a test script. ATTENTION: No integrity checks! Scripts may be harmful to the environment, e.g., by creating users."""

    help = 'Tests an App'

    def setup_parser(self, parser):
        parser.add_argument('app', action=StoreAppAction, help='The ID of the App that shall be tested')
        parser.add_argument('--appcenter-server', help='The server from which the test script is downloaded. Useful if you want to test an App installed regularly with the newest test script from the Test App Center server')
        parser.add_argument('test_args', nargs=REMAINDER, help='Arguments passed to the test script')

    @possible_network_error
    def _download_file(self, server, app, fname):
        url = os.path.join(server or app.get_server(), 'univention-repository', app.get_ucs_version(), 'maintained', 'component', app.component_id, 'test')
        self.log('Downloading "%s"...' % url)
        request = Request(url)  # noqa: S310
        response = urlopen(request)
        content = response.read()
        self.log('Writing to "%s"...' % fname)
        with open(fname, 'wb') as f:
            f.write(content)
        os.chmod(fname, 0o755)

    def _run_file(self, app, fname, args):
        if os.path.exists(fname):
            self.log('Running %s with additional args %r' % (fname, args))
            return call_process([fname, *args], self.logger).returncode

    def main(self, args):
        self.log('Testing %s' % args.app)
        if not args.app.is_installed():
            self.log('%s is not installed' % args.app)
            return
        self.log('%s is installed' % args.app)
        fname = os.path.join(gettempdir(), '%s.test' % args.app.id)
        try:
            self._download_file(args.appcenter_server, args.app, fname)
        except NetworkError:
            self.log('No script downloaded.')
        return self._run_file(args.app, fname, args.test_args)


class DevTestSetup(UniventionAppAction):
    """Sets up a test environment for App Tests."""

    help = 'Test environment setup'

    def main(self, args):
        prev_unmaintained = ucr_get('repository/online/unmaintained', 'no')
        ucr_save({'repository/online/unmaintained': 'true'})
        ret_code = self._subprocess(['univention-install', '-y', 'ucs-test-selenium-runner']).returncode
        ucr_save({'repository/online/unmaintained': prev_unmaintained})
        return ret_code != 0
