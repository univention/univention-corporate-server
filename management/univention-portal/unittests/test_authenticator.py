#!/usr/bin/python2.7
#
# Univention Portal
#
# Copyright 2020 Univention GmbH
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

from os import path

import pytest
from univentionunittests import import_module


def test_imports(dynamic_class):
		assert dynamic_class('Authenticator')
		assert dynamic_class('OpenIDAuthenticator')
		assert dynamic_class('UMCAuthenticator')


class TestUmcAuthenticator:
	_umc_session_url = "umc_session_url"
	_portal_cookie_name = "portal_cookie_name"
	_umc_cookie_name = "umc_cookie_name"
	_default_cookie_name = "UMCSessionId"
	_username = "TestUser"
	_groups = ["TestGroup"]

	@pytest.fixture
	def user_module(self, request):
		use_installed = request.config.getoption('--installed-portal')
		return import_module('univention.portal.user', 'python/', 'univention.portal.user', use_installed=use_installed)

	@pytest.fixture
	def mocked_umc_authenticator(self, dynamic_class, mocker):
		UMCAuthenticator = dynamic_class('UMCAuthenticator')
		mocked_group_cache = mocker.Mock()
		mocked_group_cache.get.return_value = {self._username: self._groups}
		return UMCAuthenticator(self._umc_session_url, mocked_group_cache, self._portal_cookie_name, self._umc_cookie_name)

	def mock_requests_get(self, mocker, mocked_authenticator, json_return_value):
		def _requests_get_success(url, cookies={}):
			""" Get mocked response with test json load """
			print("Making a request to '%s'" % url)
			response_mock = mocker.Mock()
			response_mock.status_code = 200
			response_mock.json.return_value = json_return_value
			print("Received response with status 200")
			return response_mock

		def _get_error(url, cookies={}):
			""" Get mocked response with http error """
			print("Making a request to '%s'" % url)
			response_mock = mocker.Mock()
			response_mock.status_code = 404
			response_mock.json.return_value = {}
			print("Received response with status 404")
			return response_mock

		side_effects = [requests.ConnectionError, KeyError, _get_error, _get_success]
		return mocker.patch("{}.requests.get".format(mocked_authenticator.__module__), side_effect=side_effects)


	def test_default_init(self, dynamic_class):
		UMCAuthenticator = dynamic_class('UMCAuthenticator')
		default_umc_authenticator = UMCAuthenticator(self._umc_session_url, group_cache={})
		assert default_umc_authenticator.umc_session_url == self._umc_session_url
		assert default_umc_authenticator.group_cache == {}
		assert default_umc_authenticator.portal_cookie_name == self._default_cookie_name
		assert default_umc_authenticator.umc_cookie_name == self._default_cookie_name


	def test_refresh(self, mocked_umc_authenticator, mocker):
		mocked_umc_authenticator.refresh("reason")
		mocked_umc_authenticator.group_cache.refresh.assert_called_once_with(reason="reason")


	def test_get_existing_user(self, mocked_umc_authenticator, mocker, user_module):
		# Set up
		cookie = "session_cookie"
		request_mock = mocker.Mock()
		request_mock.get_cookie.return_value = cookie
		mocked_umc_authenticator._get_username = mocker.Mock(return_value=self._username)
		# Execute
		user = mocked_umc_authenticator.get_user(request_mock)
		request_mock.get_cookie.assert_called_once_with(self._portal_cookie_name)
		mocked_umc_authenticator._get_username.assert_called_once_with(cookie)
		assert isinstance(user, user_module.User)
		assert user.username == self._username
		assert user.groups == self._groups


	def test_get_non_existing_user(self, mocked_umc_authenticator, mocker, user_module):
		# Set up
		cookie = "session_cookie"
		request_mock = mocker.Mock()
		request_mock.get_cookie.return_value = cookie
		mocked_umc_authenticator._get_username = mocker.Mock(return_value=None)
		# Execute
		user = mocked_umc_authenticator.get_user(request_mock)
		request_mock.get_cookie.assert_called_once_with(self._portal_cookie_name)
		mocked_umc_authenticator._get_username.assert_called_once_with(cookie)
		assert isinstance(user, user_module.User)
		assert user.username == None
		assert user.groups == []


class TestOpenIdAuthenticator:

	def test_default_init(self, dynamic_class):
		OpenIDAuthenticator = dynamic_class('OpenIDAuthenticator')
		default_openid_authenticator = OpenIDAuthenticator("authorization_endpoint", "client_id")
		assert default_openid_authenticator.authorization_endpoint == "authorization_endpoint"
		assert default_openid_authenticator.client_id == "client_id"
		assert default_openid_authenticator.portal_cookie_name == "UniventionPortalSessionId"
		assert default_openid_authenticator.sessions == {}
