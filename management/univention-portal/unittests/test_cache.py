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
		mocked_reloader.refresh.assert_not_called
		cache.refresh(reason="force")
		mocked_reloader.refresh.assert_called_with(reason="force", content=content)


class TestGroupFileCache:
	pass
