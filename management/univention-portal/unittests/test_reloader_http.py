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
from urllib.parse import urljoin

import pytest

from univention.portal.extensions import reloader, reloader_http


stub_asset_path = "icons/stub_folder/stub_file.sub_ext"
stub_assets_root = "http://stub_user:stub_password@stub_host.test/stub_assets_path/"
stub_cache_file = "/stub_path/stub_file"
stub_url = "http://stub_user:stub_password@stub_host.test/stub_path/file.json"
stub_portal_dn = "cn=domain,cn=portal,cn=test"


@pytest.fixture()
def http_reloader():
    """An instance of HttpReloader."""
    instance = reloader_http.HttpReloader(stub_url, stub_assets_root)
    content_fetcher_mock = mock.Mock()
    content_fetcher_mock.assets = []
    instance._create_content_fetcher = mock.Mock(return_value=content_fetcher_mock)
    return instance


@pytest.fixture()
def http_portal_reloader(mocker, mock_portal_config):
    """An instance of HttpPortalReloader."""
    mock_portal_config({"assets_root": "http://stub-host/"})
    instance = reloader_http.HttpPortalReloader(stub_url, stub_assets_root, stub_portal_dn)
    return instance


@pytest.mark.parametrize("url", [
    "http://stub-host.test/stub-path/file",
    "http://stub_user:stub_pass@stub-host.test/stub-path/file",
    "https://stub-host.test/stub-path/file",
    "https://stub_user:stub_pass@stub-host.test/stub-path/file",
])
def test_http_reloader_accepts_http_urls(url):
    http_reloader = reloader_http.HttpReloader(url, stub_assets_root)
    assert http_reloader._url == url


@pytest.mark.parametrize("url", [
    "file:///stub-path/file",
    "ftp://stub-host.test/stub-path/file",
    "/stub-path/file",
])
def test_http_reloader_raises_value_error_on_unsupported_urls(url):
    with pytest.raises(ValueError):
        reloader_http.HttpReloader(url, stub_assets_root)


@pytest.mark.parametrize("assets_root", [
    "file:///stub-path/file",
    "ftp://stub-host.test/stub-path/file",
    "/stub-path/file",
])
def test_http_reloader_raises_value_error_on_unsupported_assets_root_values(assets_root):
    with pytest.raises(ValueError):
        reloader_http.HttpReloader(stub_url, assets_root)


def test_cache_calls_http_reloader(http_reloader, mocker):
    from univention.portal.extensions.cache import Cache

    cache = Cache(cache_file=stub_cache_file, reloader=http_reloader)
    write_content_mock = mocker.patch.object(http_reloader, "_write_content")
    cache.refresh()
    write_content_mock.assert_not_called()


def test_http_reloader_uses_content_fetcher(http_reloader, mocker):
    result_mock = mock.Mock()
    result_mock.status_code = 201
    mocker.patch("requests.put", return_value=result_mock)

    http_reloader.refresh(reason="force")
    http_reloader._create_content_fetcher().fetch.assert_called_once()


def test_http_reloader_adds_user_agent_header(http_reloader, mocker):
    result_mock = mock.Mock()
    result_mock.status_code = 201
    put_mock = mocker.patch("requests.put", return_value=result_mock)
    stub_content = (b"stub_content", [])

    http_reloader._write_content(stub_content, stub_url)
    expected_headers = {"user-agent": "portal-listener"}
    put_mock.assert_called_once_with(url=mock.ANY, data=mock.ANY, headers=expected_headers)


def test_http_reloader_puts_content_to_url(http_reloader, mocker):
    result_mock = mock.Mock()
    result_mock.status_code = 201
    put_mock = mocker.patch("requests.put", return_value=result_mock)
    stub_content = (b"stub_content", [])
    http_reloader._generate_content = mock.Mock(return_value=stub_content)

    result = http_reloader.refresh(reason="force")
    put_mock.assert_called_once_with(url=stub_url, data=b"stub_content", headers=mock.ANY)
    assert result


def test_http_reloader_puts_assets_first(http_reloader, mocker):
    result_mock = mock.Mock()
    result_mock.status_code = 201
    put_mock = mocker.patch("requests.put", return_value=result_mock)
    stub_content = (b"stub_content", [
        ("stub_path/stub_directory/stub_asset.stub_ext", b"stub_asset_content"),
    ])
    http_reloader._generate_content = mock.Mock(return_value=stub_content)

    http_reloader.refresh(reason="force")

    expected_url = f"{stub_assets_root}stub_path/stub_directory/stub_asset.stub_ext"
    assert put_mock.call_args_list[0] == mock.call(
        url=expected_url, data=b"stub_asset_content", headers=mock.ANY)


@pytest.mark.parametrize("asset_path", [
    "../../../stub_asset",
    "/stub_asset",
])
def test_http_reloader_ensures_assets_url(asset_path, http_reloader):
    with pytest.raises(ValueError):
        http_reloader._create_asset_url(asset_path)


@pytest.mark.parametrize("assets_root", [
    "http://stub-host.test/stub-path/",
    "http://user:pass@stub-host.test/stub-path/",
    "https://stub-host.test/stub-path/",
    "https://user:pass@stub-host.test/stub-path/",
])
def test_http_reloader_creates_asset_urls(assets_root, http_reloader):
    http_reloader._assets_root = assets_root
    asset_url = http_reloader._create_asset_url(stub_asset_path)
    assert asset_url == urljoin(assets_root, stub_asset_path)


def test_http_portal_reloader_uses_portal_content_fetcher(http_portal_reloader):
    content_fetcher = http_portal_reloader._create_content_fetcher()
    assert isinstance(content_fetcher, reloader.PortalContentFetcher)


def test_http_portal_reloader_checks_reason(http_portal_reloader, mocker):
    check_reason_mock = mocker.patch.object(reloader, "check_portal_reason")
    http_portal_reloader._check_reason("stub_reason")
    check_reason_mock.assert_called_once_with("stub_reason")


def test_http_groups_reloader_uses_groups_content_fetcher():
    groups_reloader = reloader_http.HttpGroupsReloader(stub_url, stub_assets_root)
    content_fetcher = groups_reloader._create_content_fetcher()
    assert isinstance(content_fetcher, reloader.GroupsContentFetcher)


def test_http_groups_reloader_checks_reason(mocker):
    check_reason_mock = mocker.patch.object(reloader, "check_groups_reason")
    groups_reloader = reloader_http.HttpGroupsReloader(stub_url, stub_assets_root)
    groups_reloader._check_reason("stub_reason")
    check_reason_mock.assert_called_once_with("stub_reason")
