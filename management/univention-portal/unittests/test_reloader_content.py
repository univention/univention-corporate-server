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

import binascii
import json
from unittest import mock

import pytest
import stub_udm_client

import univention.admin.rest.client as udm_client
from univention.portal.extensions.reloader_content import GroupsContentFetcher, PortalContentFetcherUDMREST


stub_portal_dn = "cn=domain,cn=portal,cn=test"
stub_image = b"stub_image_content"
stub_image_base64 = binascii.b2a_base64(stub_image)


@pytest.fixture()
def portal_content_fetcher(mocker):
    put_mock = mocker.patch("requests.put")
    put_mock().status_code = 201
    return PortalContentFetcherUDMREST(stub_portal_dn, "/stub_root")


def test_portal_content_fetcher_propagates_connectionerror(mocker):
    content_fetcher = PortalContentFetcherUDMREST(stub_portal_dn, "/stub_root")
    udm_return = mocker.Mock()
    udm_return.get.side_effect = udm_client.ConnectionError
    mocker.patch.object(
        PortalContentFetcherUDMREST, "_create_udm_client",
        return_value=udm_return)

    with pytest.raises(udm_client.ConnectionError):
        content_fetcher.fetch()


def test_collect_asset_returns_relative_asset_url(portal_content_fetcher):
    asset_url = portal_content_fetcher._collect_asset(b"<svg />", "stub_name", "stub_dirname")
    assert asset_url == "./icons/stub_dirname/stub_name.svg"


def test_portal_content_fetcher_returns_content(mocker):
    result_mock = mock.Mock()
    result_mock.status_code = 201
    mocker.patch("requests.put", return_value=result_mock)
    mocker.patch.object(
        PortalContentFetcherUDMREST, "_create_udm_client",
        return_value=stub_udm_client.StubUDMClient())
    content_fetcher = PortalContentFetcherUDMREST(stub_portal_dn, "http://stub-host")
    content = content_fetcher.fetch()
    expected_content = """{
    "announcements": {
        "cn=stub_category,dc=stub,dc=test": {
            "allowedGroups": "stub_allowedGroups",
            "dn": "cn=stub_category,dc=stub,dc=test",
            "isSticky": "stub_isSticky",
            "message": "stub_message",
            "name": "stub_name",
            "needsConfirmation": "stub_needsConfirmation",
            "severity": "stub_severity",
            "title": "stub_title",
            "visibleFrom": "stub_visibleFrom",
            "visibleUntil": "stub_visibleeUntil"
        }
    },
    "categories": {
        "cn=stub_category,dc=stub,dc=test": {
            "display_name": "stub_displayName",
            "dn": "cn=stub_category,dc=stub,dc=test",
            "entries": [
                "stub_entry"
            ],
            "in_portal": false
        }
    },
    "entries": {
        "cn=stub_category,dc=stub,dc=test": {
            "activated": "stub_activated",
            "allowedGroups": "stub_allowedGroups",
            "anonymous": "stub_anonymous",
            "backgroundColor": "stub_backgroundColor",
            "description": "stub_description",
            "dn": "cn=stub_category,dc=stub,dc=test",
            "icon_url": "./icons/entries/stub_name.svg",
            "in_portal": false,
            "keywords": "stub_keywords",
            "linkTarget": "stub_linkTarget",
            "links": [
                {
                    "locale": "s",
                    "value": "t"
                },
                {
                    "locale": "s",
                    "value": "t"
                }
            ],
            "name": "stub_displayName",
            "target": "stub_target"
        }
    },
    "folders": {
        "cn=stub_category,dc=stub,dc=test": {
            "dn": "cn=stub_category,dc=stub,dc=test",
            "entries": [
                "stub_entry"
            ],
            "in_portal": false,
            "name": "stub_displayName"
        }
    },
    "menu_links": "stub_menuLinks",
    "portal": {
        "background": "./icons/backgrounds/stub_name.svg",
        "categories": [
            "stub_category"
        ],
        "defaultLinkTarget": "stub_defaultLinkTarget",
        "dn": "cn=cn=domain,cn=portal,cn=test,dc=stub,dc=test",
        "ensureLogin": "stub_ensureLogin",
        "logo": "./icons/logos/stub_name.svg",
        "name": "stub_displayName",
        "showUmc": true
    },
    "user_links": "stub_userLinks"
}"""
    assert content == expected_content


def test_group_content_fetcher_returns_content(mocker):
    stub_users = {
        'administrator': [
            'cn=computers,cn=groups,dc=univention,dc=intranet',
            'cn=dc backup hosts,cn=groups,dc=univention,dc=intranet',
            'cn=dc slave hosts,cn=groups,dc=univention,dc=intranet',
            'cn=domain admins,cn=groups,dc=univention,dc=intranet',
            'cn=domain users,cn=groups,dc=univention,dc=intranet',
            'cn=windows hosts,cn=groups,dc=univention,dc=intranet'],
        'join-backup': [
            'cn=backup join,cn=groups,dc=univention,dc=intranet',
            'cn=computers,cn=groups,dc=univention,dc=intranet',
            'cn=dc backup hosts,cn=groups,dc=univention,dc=intranet',
            'cn=dc slave hosts,cn=groups,dc=univention,dc=intranet',
            'cn=slave join,cn=groups,dc=univention,dc=intranet',
            'cn=windows hosts,cn=groups,dc=univention,dc=intranet'],
        'join-slave': [
            'cn=computers,cn=groups,dc=univention,dc=intranet',
            'cn=dc slave hosts,cn=groups,dc=univention,dc=intranet',
            'cn=slave join,cn=groups,dc=univention,dc=intranet'],
        'testuser': [
            'cn=domain users,cn=groups,dc=univention,dc=intranet'],
        'ucs-sso': [
            'cn=domain users,cn=groups,dc=univention,dc=intranet'],
        'user': [
            'cn=domain admins,cn=groups,dc=univention,dc=intranet',
            'cn=domain users,cn=groups,dc=univention,dc=intranet'],
    }

    mocker.patch.object(GroupsContentFetcher, "_get_users_from_ldap", return_value=stub_users)
    content_fetcher = GroupsContentFetcher()
    content = content_fetcher.fetch()
    assert json.loads(content) == stub_users
    assert len(content_fetcher.assets) == 0
