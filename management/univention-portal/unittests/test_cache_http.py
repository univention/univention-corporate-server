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

from unittest import mock

import pytest
import requests


UCS_INTERNAL_URL = "http://ucshost.test/univention/internal"
ETAG = "1234"
PORTAL_DATA_KEYS = [
    "portal",
    "entries",
    "folders",
    "categories",
    "user_links",
    "menu_links",
]
PORTAL_DATA = {key: key for key in PORTAL_DATA_KEYS}
GROUPS_DATA = {"username": ["list", "of", "groups"]}


@pytest.mark.parametrize(
    "class_name",
    ["CacheHTTP", "PortalFileCacheHTTP", "GroupFileCacheHTTP"],
)
def test_import(class_name, dynamic_class):
    assert dynamic_class(class_name)


def test_cache_http_sets_user_agent_header(mocker):
    from univention.portal.extensions.cache_http import CacheHTTP

    get_mock = mocker.patch("requests.get")
    cache_http = CacheHTTP(UCS_INTERNAL_URL)
    cache_http._load()

    expected_headers = {"user-agent": "portal-server"}
    get_mock.assert_called_once_with(mock.ANY, headers=expected_headers)


def test_portal_file_cache_http(requests_mock, dynamic_class):
    url = f"{UCS_INTERNAL_URL}/portal"

    requests_mock.get(
        url,
        status_code=requests.codes.ok,
        headers={"ETag": ETAG},
        json=PORTAL_DATA,
    )
    portal_file_cache_http = dynamic_class("PortalFileCacheHTTP")(url)
    portal_file_cache_http.refresh()

    requests_mock.get(
        url,
        request_headers={"If-None-Match": ETAG},
        status_code=requests.codes.not_modified,
        headers={"ETag": ETAG},
    )
    assert portal_file_cache_http.get() == PORTAL_DATA
    for item in PORTAL_DATA_KEYS:
        assert item == getattr(portal_file_cache_http, f"get_{item}")()


def test_group_file_cache_http(requests_mock, dynamic_class):
    url = f"{UCS_INTERNAL_URL}/groups"

    requests_mock.get(
        url,
        status_code=requests.codes.ok,
        headers={"ETag": ETAG},
        json=GROUPS_DATA,
    )
    group_file_cache_http = dynamic_class("GroupFileCacheHTTP")(UCS_INTERNAL_URL)
    group_file_cache_http.refresh()

    requests_mock.get(
        url,
        request_headers={"If-None-Match": ETAG},
        status_code=requests.codes.not_modified,
        headers={"ETag": ETAG},
    )
    assert group_file_cache_http.get() == GROUPS_DATA
