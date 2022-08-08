#!/usr/bin/py.test
# -*- coding: utf-8 -*-
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
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

from univention.management.console.error import ServerError

from univention.unittests.umc import import_umc_module, umc_requests

import pytest
import six

umc_lib = import_umc_module('lib')


class TestUMCModule(object):
	def test_message_sanitizer(self):
		sanitizer = umc_lib.server.MessageSanitizer(default='')
		assert sanitizer.sanitize('message', {}) == ''
		assert sanitizer.sanitize('message', {"message": "Echt gut"}) == "Echt gut"
		if six.PY2:
			assert sanitizer.sanitize('message', {"message": u"Ächt gut"}) == b"\xc3\x84cht gut"

	def test_restart_isNeeded(self, instance, umc_request):
		instance.restart_isNeeded(umc_request)
		umc_request.expected_response(True)

	def test_ping(self, instance, umc_request):
		instance.ping(umc_request)
		umc_request.expected_response({'success': True})

	def test_restart(self, instance, mocker, umc_request):
		mocked_subprocess = mocker.patch.object(umc_lib.server, 'subprocess')
		out = b'''[ ok ] Restarting univention-management-console-server (via systemctl): univention-management-console-server.service.
		[ ok ] Restarting univention-management-console-web-server (via systemctl): univention-management-console-web-server.service.
		[ ok ] Restarting apache2 (via systemctl): apache2.service.
		'''
		popen_mock = mocker.Mock(**{'communicate.return_value': (out, '')})
		mocked_subprocess.PIPE = -1
		mocked_subprocess.STDOUT = 1
		mocked_subprocess.Popen.return_value = popen_mock
		instance.restart(umc_request)
		mocked_subprocess.call.assert_called_once_with('/usr/share/univention-updater/disable-apache2-umc')
		mocked_subprocess.Popen.assert_called_once_with('/usr/share/univention-updater/enable-apache2-umc', stderr=1, stdout=-1)
		umc_request.expected_response(True)

	@umc_requests([{}, {"message": "my message"}])
	def test_shutdown(self, instance, mocker, umc_request):
		mocked_subprocess = mocker.patch.object(umc_lib.server, 'subprocess')
		mocked_subprocess.call.side_effect = [0, 0]
		if umc_request.options.get("message"):
			message = umc_request.options.get("message")
			reason = 'The system will now be shut down ({})'.format(message)
		else:
			reason = 'The system will now be shut down'
		instance.shutdown(umc_request)
		assert mocked_subprocess.call.call_count == 2
		args, kwargs = mocked_subprocess.call.call_args_list[0]
		assert args[0] == ('/usr/bin/logger', '-f', '/var/log/syslog', '-t', 'UMC', reason)
		args, kwargs = mocked_subprocess.call.call_args_list[1]
		assert args[0] == ('/sbin/shutdown', '-h', 'now', reason)
		umc_request.expected_response(None)

	def test_failed_shutdown_failing(self, instance, mocker, umc_request):
		mocked_subprocess = mocker.patch.object(umc_lib.server, 'subprocess')
		mocked_subprocess.call.side_effect = [OSError, 1]
		with pytest.raises(ServerError):
			instance.shutdown(umc_request)
		assert mocked_subprocess.call.call_count == 2

	@umc_requests([{}, {"message": "my message"}])
	def test_reboot(self, instance, mocker, umc_request):
		mocked_subprocess = mocker.patch.object(umc_lib.server, 'subprocess')
		mocked_subprocess.call.side_effect = [0, 0]
		if umc_request.options.get("message"):
			message = umc_request.options.get("message")
			reason = 'The system will now be restarted ({})'.format(message)
		else:
			reason = 'The system will now be restarted'
		instance.reboot(umc_request)
		assert mocked_subprocess.call.call_count == 2
		args, kwargs = mocked_subprocess.call.call_args_list[0]
		assert args[0] == ('/usr/bin/logger', '-f', '/var/log/syslog', '-t', 'UMC', reason)
		args, kwargs = mocked_subprocess.call.call_args_list[1]
		assert args[0] == ('/sbin/shutdown', '-r', 'now', reason)
		umc_request.expected_response(None)

	def test_failed_reboot_failing(self, instance, mocker, umc_request):
		mocked_subprocess = mocker.patch.object(umc_lib.server, 'subprocess')
		mocked_subprocess.call.side_effect = [OSError, 1]
		with pytest.raises(ServerError):
			instance.reboot(umc_request)
		assert mocked_subprocess.call.call_count == 2
