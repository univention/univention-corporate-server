#!/usr/bin/python3
#
# Univention Portal
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
#
import asyncio
import json

import pytest
import tornado
from univentionunittests import import_module


@pytest.fixture
def user_module(request):
	use_installed = request.config.getoption("--installed-portal")
	return import_module("univention.portal.user", "python/", "univention.portal.user", use_installed=use_installed)


def test_imports(dynamic_class):
	assert dynamic_class("Authenticator")
	assert dynamic_class("UMCAuthenticator")


class TestUMCAuthenticator:
	_auth_mode = "ucs"
	_umc_session_url = "umc_session_url"
	_umc_cookie_name = "UMCSessionId"
	_username = "TestUser"
	_groups = ["TestGroup"]

	@pytest.fixture
	def mocked_authenticator(self, dynamic_class, patch_object_module, mocker):
		Authenticator = dynamic_class("UMCAuthenticator")
		mocked_group_cache = mocker.Mock()
		mocked_group_cache.get.return_value = {self._username.lower(): self._groups}
		authenticator = Authenticator(self._auth_mode, self._umc_session_url, mocked_group_cache)
		authenticator.httpclient_fetch = patch_object_module(authenticator, "AsyncHTTPClient.fetch")
		return authenticator

	def test_default_init(self, dynamic_class):
		Authenticator = dynamic_class("UMCAuthenticator")
		default_authenticator = Authenticator(self._auth_mode, self._umc_session_url, group_cache={})
		assert default_authenticator.auth_mode == self._auth_mode
		assert default_authenticator.umc_session_url == self._umc_session_url
		assert default_authenticator.group_cache == {}

	def test_refresh(self, mocked_authenticator, mocker):
		mocked_authenticator.refresh("reason")
		mocked_authenticator.group_cache.refresh.assert_called_once_with(reason="reason")

	def test_get_existing_user(self, mocked_authenticator, mocker, user_module):
		# Set up
		cookie = "session_cookie"
		request_mock = mocker.Mock()
		cookie_mock = mocker.Mock()
		cookie_mock.value = cookie
		request_mock.cookies = {self._umc_cookie_name: cookie_mock}
		request_mock.request.headers = {}

		async def async_magic():
			return (self._username.lower(), self._username)

		mocker.MagicMock.__await__ = lambda x: async_magic().__await__()
		mocked_authenticator._get_username = mocker.MagicMock()
		# Execute
		loop = asyncio.get_event_loop()
		user = loop.run_until_complete(mocked_authenticator.get_user(request_mock))
		mocked_authenticator._get_username.assert_called_once_with({self._umc_cookie_name: cookie})
		assert isinstance(user, user_module.User)
		assert user.username == self._username.lower()
		assert user.groups == [x.lower() for x in self._groups]

	def test_get_non_existing_user(self, mocked_authenticator, mocker, user_module):
		# Set up
		cookie = "session_cookie"
		request_mock = mocker.Mock()
		cookie_mock = mocker.Mock()
		cookie_mock.value = cookie
		request_mock.cookies = {self._umc_cookie_name: cookie_mock}
		request_mock.request.headers = {}

		async def async_magic():
			return (None, None)

		mocker.MagicMock.__await__ = lambda x: async_magic().__await__()
		mocked_authenticator._get_username = mocker.MagicMock()
		# Execute
		loop = asyncio.get_event_loop()
		user = loop.run_until_complete(mocked_authenticator.get_user(request_mock))
		mocked_authenticator._get_username.assert_called_once_with({self._umc_cookie_name: cookie})
		assert isinstance(user, user_module.User)
		assert user.is_anonymous()
		assert user.username is None
		assert user.groups == []

	def test_get_username(self, mocked_authenticator, mocker):
		async def async_magic():
			return self._username

		async def async_magic_none():
			return

		loop = asyncio.get_event_loop()
		mocker.MagicMock.__await__ = lambda x: async_magic().__await__()
		mocked_authenticator._ask_umc = mocker.MagicMock()
		assert loop.run_until_complete(mocked_authenticator._get_username({self._umc_cookie_name: "test_session"})) == (self._username.lower(), self._username)
		assert loop.run_until_complete(mocked_authenticator._get_username({})) == (None, None)
		mocker.MagicMock.__await__ = lambda x: async_magic_none().__await__()
		mocked_authenticator._ask_umc = mocker.MagicMock()
		assert loop.run_until_complete(mocked_authenticator._get_username({self._umc_cookie_name: "test_session"})) == (None, None)

	def test_ask_umc_request_success(self, mocked_authenticator, mocker):
		def _side_effect(req):
			""" Side effect to simulate successful request with different response data """
			print("Making a request to '%s'" % req.url)

			response_mock = mocker.Mock()

			async def async_magic():
				return response_mock

			mocker.MagicMock.__await__ = lambda x: async_magic().__await__()
			async_response_mock = mocker.MagicMock(return_value=asyncio.Future())
			async_response_mock.return_value.set_result(response_mock)
			test_cookie = req.headers.get('Cookie', '').split(',')
			test_cookie = [c.strip().split('=') for c in test_cookie]
			test_cookie = dict((k.strip(), v.strip()) for k, v in test_cookie).get(self._umc_cookie_name, "")
			if test_cookie:
				response_mock.body = json.dumps({"result": {"username": self._username}}).encode()
			else:
				response_mock.body = b'{}'
			print("Received response with status 200")
			return async_response_mock

		mocked_authenticator.httpclient_fetch.side_effect = _side_effect
		test_session = {self._umc_cookie_name: "test_session"}
		loop = asyncio.get_event_loop()

		# Execute with valid session expecting username to be returned
		assert loop.run_until_complete(mocked_authenticator._ask_umc(test_session, {})) == self._username
		assert mocked_authenticator.httpclient_fetch.call_count == 1

		# Execute with unknown session expecting username to be None due to KeyError
		assert loop.run_until_complete(mocked_authenticator._ask_umc({self._umc_cookie_name: ""}, {})) is None
		assert mocked_authenticator.httpclient_fetch.call_count == 2

	def test_ask_umc_request_error(self, mocked_authenticator, mocker):
		def _side_effect(req):
			""" Side effect to simulate request with a http error """
			print("Making a request to '%s'" % req.url)
			response_mock = mocker.Mock()
			response_mock.status_code = 404
			response_mock.body.decode.return_value = b'X'

			async def async_magic():
				return response_mock

			mocker.MagicMock.__await__ = lambda x: async_magic().__await__()
			async_response_mock = mocker.MagicMock(return_value=asyncio.Future())
			async_response_mock.return_value.set_result(response_mock)
			print("Received response with status 404")
			return async_response_mock

		loop = asyncio.get_event_loop()

		mocked_authenticator.httpclient_fetch.side_effect = _side_effect
		test_session = {self._umc_cookie_name: "test_session"}
		# Execute while expecting a catched internal ValueError
		assert loop.run_until_complete(mocked_authenticator._ask_umc(test_session, {})) is None
		assert mocked_authenticator.httpclient_fetch.call_count == 1
		# Execute while expecting catched internal RequestException
		mocked_authenticator.httpclient_fetch.side_effect = [tornado.httpclient.HTTPError(404), IOError]
		assert loop.run_until_complete(mocked_authenticator._ask_umc(test_session, {})) is None
		assert loop.run_until_complete(mocked_authenticator._ask_umc(test_session, {})) is None
		assert mocked_authenticator.httpclient_fetch.call_count == 3
