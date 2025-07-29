#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import pytest


def test_imports(dynamic_class):
    assert dynamic_class("Cache")
    assert dynamic_class("PortalFileCache")
    assert dynamic_class("GroupFileCache")


class TestPortalFileCache:
    @pytest.fixture
    def cache_file_path(self, get_file_path):
        return get_file_path("portal_cache.json")

    def test_missing_file(self, dynamic_class):
        cache = dynamic_class("PortalFileCache")("/tmp/a/file/that/does/not/exist")
        assert cache.get() == {}

    def test_getter(self, dynamic_class, cache_file_path):
        Cache = dynamic_class("PortalFileCache")
        cache = Cache(cache_file_path)
        assert cache.get_user_links() == []
        assert sorted(cache.get_entries().keys()) == [
            "cn=server-overview,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de",
            "cn=umc-domain,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de",
            "cn=univentionblog,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de",
        ]
        assert cache.get_folders() == {}
        assert cache.get_portal()["dn"] == "cn=domain,cn=portal,cn=portals,cn=univention,dc=intranet,dc=example,dc=de"
        assert sorted(cache.get_categories().keys()) == ["cn=domain-admin,cn=category,cn=portals,cn=univention,dc=intranet,dc=example,dc=de"]
        assert cache.get_menu_links() == []

    def test_reload(self, dynamic_class, cache_file_path, mocker):
        Cache = dynamic_class("PortalFileCache")
        mocked_reloader = mocker.Mock()
        cache = Cache(cache_file_path, reloader=mocked_reloader)
        content = cache.get()
        mocked_reloader.refresh.assert_not_called()
        cache.refresh(reason="force")
        mocked_reloader.refresh.assert_called_with(reason="force", content=content)


class TestGroupFileCache:
    pass
