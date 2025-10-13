#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import pytest
import tornado.testing
import tornado.web

from univention.portal.extensions.cache_http import PortalFileCacheHTTP
from univention.portal.main import build_routes
from univention.portal.user import User


def async_method_patch(mocker, callable):
    mocker.MagicMock.__await__ = lambda _: callable().__await__()
    return mocker.MagicMock()


@pytest.fixture
def user():
    return User(
        username=None,
        display_name=None,
        groups=[],
        headers={},
    )


@pytest.fixture
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

    @pytest.fixture
    def app(self, portal_mock):
        portal_mock.portal_cache = PortalFileCacheHTTP(
            ucs_internal_url='https://example.com',
        )
        routes = build_routes({
            "default": portal_mock,
        })
        return tornado.web.Application(routes)

    @pytest.mark.gen_test
    def test_get_portals_json_http_backed_cache(self, http_client, base_url, portal_mock):
        response = yield http_client.fetch(f"{base_url}/_/portal.json")
        assert response.code == 200
        portal_mock.refresh.assert_called_once()


class TestPortalEntriesHandlerNoHttpCache:

    @pytest.fixture
    def app(self, portal_mock):
        routes = build_routes({
            "default": portal_mock,
        })
        return tornado.web.Application(routes)

    @pytest.mark.gen_test
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
