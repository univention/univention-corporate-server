#!/usr/bin/python3
#
# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2024 Univention GmbH
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

import pytest
import tornado.ioloop
import tornado.testing
import tornado.web

from univention.portal.extensions.cache_http import PortalFileCacheHTTP
from univention.portal.main import build_routes
from univention.portal.user import User


def async_method_patch(mocker, callable):
    mocker.MagicMock.__await__ = lambda _: callable().__await__()
    return mocker.MagicMock()


@pytest.fixture()
def user():
    return User(
        username=None,
        display_name=None,
        groups=[],
        headers={},
    )


@pytest.fixture()
def portal_mock(mocker, user):
    async def get_user():
        return user

    portal = mocker.Mock()
    portal.portal_cache = None
    portal.score = mocker.Mock(return_value=1)
    portal.get_user = async_method_patch(mocker, get_user)
    portal.refresh = mocker.Mock()
    portal.get_cache_id = mocker.Mock(return_value=None)
    portal.get_visible_content = mocker.Mock(return_value=None)
    portal.get_user_links = mocker.Mock(return_value=None)
    portal.get_menu_links = mocker.Mock(return_value=None)
    portal.get_entries = mocker.Mock(return_value=None)
    portal.get_folders = mocker.Mock(return_value=None)
    portal.get_categories = mocker.Mock(return_value=None)
    portal.get_meta = mocker.Mock(return_value={"showUmc": False})
    portal.auth_mode = mocker.Mock(return_value=None)
    portal.may_be_edited = mocker.Mock(return_value=None)
    portal.get_announcements = mocker.Mock(return_value=None)

    return portal


class TestPortalEntriesHandlerHttpCache:

    @pytest.fixture()
    def app(self, portal_mock):
        portal_mock.portal_cache = PortalFileCacheHTTP(
            ucs_internal_url='https://example.com',
        )
        routes = build_routes({
            "default": portal_mock,
        })
        return tornado.web.Application(routes)

    @pytest.mark.gen_test()
    def test_get_portals_json_http_backed_cache(self, http_client, base_url, portal_mock):
        response = yield http_client.fetch(f"{base_url}/_/portal.json")
        assert response.code == 200
        portal_mock.refresh.assert_called_once()


class TestPortalEntriesHandlerNoHttpCache:

    @pytest.fixture()
    def app(self, portal_mock):
        routes = build_routes({
            "default": portal_mock,
        })
        return tornado.web.Application(routes)

    @pytest.mark.gen_test()
    def test_get_portals_json_standard(self, http_client, base_url, portal_mock):
        response = yield http_client.fetch(f"{base_url}/_/portal.json")
        assert response.code == 200
        portal_mock.refresh.assert_not_called()


class TestPortalEntriesHandlerNoPortal(tornado.testing.AsyncHTTPTestCase):

    def get_app(self) -> tornado.web.Application:
        return tornado.web.Application(build_routes({}))

    def test_no_portals(self):
        response = self.fetch(r"/_/portal.json")
        assert response.code == 404
