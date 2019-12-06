#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for running an app specific test file
#
# Copyright 2017-2019 Univention GmbH
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
#

import os
from argparse import REMAINDER
from urllib2 import Request
from tempfile import gettempdir

from univention.appcenter.actions import UniventionAppAction, StoreAppAction, possible_network_error
from univention.appcenter.ucr import ucr_save, ucr_get
from univention.appcenter.utils import urlopen, call_process
from univention.appcenter.exceptions import NetworkError


class DevTest(UniventionAppAction):
	'''Tests an App by downloading and running a test script. ATTENTION: No integrity checks! Scripts may be harmful to the environment, e.g., by creating users.'''
	help = 'Tests an App'

	def setup_parser(self, parser):
		parser.add_argument('app', action=StoreAppAction, help='The ID of the App that shall be tested')
		parser.add_argument('--appcenter-server', help='The server from which the test script is downloaded. Useful if you want to test an App installed regularly with the newest test script from the Test App Center server')
		parser.add_argument('test_args', nargs=REMAINDER, help='Arguments passed to the test script')

	@possible_network_error
	def _download_file(self, server, app, fname):
		url = os.path.join(server or app.get_server(), 'univention-repository', app.get_ucs_version(), 'maintained', 'component', app.component_id, 'test')
		self.log('Downloading "%s"...' % url)
		request = Request(url)
		response = urlopen(request)
		content = response.read()
		self.log('Writing to "%s"...' % fname)
		with open(fname, 'wb') as f:
			f.write(content)
		os.chmod(fname, 0o755)

	def _run_file(self, app, fname, args):
		if os.path.exists(fname):
			self.log('Running %s with additional args %r' % (fname, args))
			return call_process([fname] + args, self.logger).returncode

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
	'''Sets up a test environment for App Tests.'''
	help = 'Test environment setup'

	def main(self, args):
		chromium_version = "71.0.3578.80-1~deb9u1"  # Bug #48856
		prev_unmaintained = ucr_get('repository/online/unmaintained', 'no')
		ucr_save({'repository/online/unmaintained': 'true'})
		ret_code = self._subprocess(['univention-install', '-y', 'python-pip', 'ucs-test', 'xvfb', 'chromium=%s' % chromium_version, 'chromium-driver=%s' % chromium_version, 'python-xvfbwrapper']).returncode
		ret_code = self._subprocess(['pip', 'install', 'selenium==3.6.0']).returncode or ret_code
		ucr_save({'repository/online/unmaintained': prev_unmaintained})
		return ret_code != 0
