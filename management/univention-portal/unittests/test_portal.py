#!/usr/bin/python3
#
# Univention Portal
#
# Copyright 2020-2021 Univention GmbH
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

import pytest


def test_imports(dynamic_class):
	assert dynamic_class("Portal")


class TestPortal:
	@pytest.fixture
	def mocked_user(self, mocker):
		user = mocker.Mock()
		user.username = "hindenkampp"
		user.display_name = "Hans Hindenkampp"
		user.groups = []
		user.headers = {}
		return user

	@pytest.fixture
	def mocked_anonymous_user(self, mocker):
		user = mocker.Mock()
		user.username = None
		user.display_name = None
		user.groups = []
		user.headers = {}
		return user

	@pytest.fixture
	def standard_portal(self, dynamic_class, mocker, get_file_path):
		Portal = dynamic_class("Portal")
		cache_file_path = get_file_path("portal_cache.json")
		scorer = dynamic_class("Scorer")()
		portal_cache = dynamic_class("PortalFileCache")(cache_file_path)
		authenticator = dynamic_class("UMCAuthenticator")("ucs", "session_url", "group_cache")
		return Portal(scorer, portal_cache, authenticator)

	@pytest.fixture
	def mocked_portal(self, dynamic_class, mocker):
		async def async_magic():
			return

		Portal = dynamic_class("Portal")
		scorer = mocker.Mock()
		portal_cache = mocker.Mock()
		authenticator = mocker.Mock()
		mocker.MagicMock.__await__ = lambda x: async_magic().__await__()
		authenticator.get_user = mocker.MagicMock()
		authenticator.login_user = mocker.MagicMock()
		authenticator.login_request = mocker.MagicMock()
		return Portal(scorer, portal_cache, authenticator)

	def test_user(self, mocked_portal, mocker):
		request = "request"
		loop = asyncio.get_event_loop()
		loop.run_until_complete(mocked_portal.get_user(request))
		mocked_portal.authenticator.get_user.assert_called_once_with(request)

	def test_login(self, mocked_portal, mocker):
		request = "request"
		loop = asyncio.get_event_loop()
		loop.run_until_complete(mocked_portal.login_user(request))
		loop.run_until_complete(mocked_portal.login_request(request))
		mocked_portal.authenticator.login_user.assert_called_once_with(request)
		mocked_portal.authenticator.login_request.assert_called_once_with(request)

	def test_visible_content(self, mocked_user, standard_portal):
		content = standard_portal.get_visible_content(mocked_user, False)
		expected_content = {
			"category_dns": ["cn=domain-admin,cn=category,cn=portals,cn=univention,dc=intranet,dc=example,dc=de"],
			"entry_dns": ["cn=server-overview,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de", "cn=umc-domain,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de", "cn=univentionblog,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de"],
			"folder_dns": [],
		}
		assert content == expected_content

	def test_user_links(self, mocked_user, mocked_anonymous_user, standard_portal):
		content_with_user = standard_portal.get_visible_content(mocked_user, False)
		content_no_user = standard_portal.get_visible_content(mocked_anonymous_user, False)
		content_with_user = standard_portal.get_user_links(content_with_user)
		content_no_user = standard_portal.get_user_links(content_no_user)
		expected_content = []
		assert content_no_user == expected_content
		assert content_with_user == expected_content

	def test_menu_links(self, mocked_user, standard_portal):
		content = standard_portal.get_visible_content(mocked_user, False)
		content = standard_portal.get_menu_links(content)
		expected_content = []
		assert content == expected_content

	def test_portal_entries(self, mocked_user, standard_portal):
		content = standard_portal.get_visible_content(mocked_user, False)
		content = standard_portal.get_entries(content)
		expected_content = [
			{
				"activated": True,
				"allowedGroups": [],
				"anonymous": True,
				"description": {
					"de_DE": u"Zeigt eine \xdcbersicht aller UCS Server in der Dom\xe4ne",
					"en_US": u"Provide an overview of all UCS server in the domain",
					"fr_FR": u"Vue d'ensemble de tous les serveurs UCS du domaine",
				},
				"dn": "cn=server-overview,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de",
				"in_portal": True,
				"linkTarget": "useportaldefault",
				"links": ["/univention/server-overview/"],
				"logo_name": "/univention/portal/icons/entries/server-overview.svg",
				"name": {"de_DE": u"Server\xfcbersicht", "en_US": u"Server overview", "fr_FR": u"Vue d'ensemble de serveurs"},
			},
			{
				"activated": True,
				"allowedGroups": [],
				"anonymous": True,
				"description": {
					"de_DE": u"Univention Management Console zur Ver\xadwal\xadtung der UCS-Dom\xe4ne und des lokalen Systems",
					"en_US": u"Univention Management Console for admin\xadis\xadtra\xadting the UCS domain and the local system",
					"fr_FR": u"Console de gestion Univention pour admin\xadis\xadtrer le domaine UCS et le syst\xe8me local",
				},
				"dn": "cn=umc-domain,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de",
				"in_portal": True,
				"linkTarget": "useportaldefault",
				"links": ["/univention/management/"],
				"logo_name": "/univention/portal/icons/entries/umc-domain.svg",
				"name": {"de_DE": u"System- und Dom\xe4neneinstellungen", "en_US": u"System and domain settings", "fr_FR": u"R\xe9glages du syst\xe8me et du domaine"},
			},
			{
				"activated": True,
				"allowedGroups": [
					"cn=g1,cn=groups,dc=intranet,dc=example,dc=de",
					"cn=g2,cn=groups,dc=intranet,dc=example,dc=de"
				],
				"anonymous": True,
				"description": {
					"de_DE": "News, Tipps und Best Practices",
					"en_US": "News, tips and best practices",
					"fr_FR": "Nouvelles, conseils et bonne pratique"
				},
				"dn": "cn=univentionblog,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de",
				"in_portal": True,
				"linkTarget": "newwindow",
				"links": [
					"https://www.univention.com/news/blog-en/"
				],
				"logo_name": "/univention/portal/icons/entries/univentionblog.png",
				"name": {
					"de_DE": "Univention Blog",
					"en_US": "Univention Blog",
					"fr_FR": "Univention Blog"
				}
			},
		]
		assert content == expected_content

	def test_folders(self, mocked_user, standard_portal):
		content = standard_portal.get_visible_content(mocked_user, False)
		content = standard_portal.get_folders(content)
		expected_content = []
		assert content == expected_content

	def test_categories(self, mocked_user, standard_portal):
		content = standard_portal.get_visible_content(mocked_user, False)
		content = standard_portal.get_categories(content)
		expected_content = [
			{
				"display_name": {"de_DE": u"Verwaltung", "en_US": u"Administration"},
				"dn": u"cn=domain-admin,cn=category,cn=portals,cn=univention,dc=intranet,dc=example,dc=de",
				"entries": ["cn=umc-domain,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de", "cn=server-overview,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de", u"cn=univentionblog,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de"],
			},
		]
		assert content == expected_content

	def test_meta(self, mocked_user, standard_portal):
		content = standard_portal.get_visible_content(mocked_user, False)
		categories = standard_portal.get_categories(content)
		content = standard_portal.get_meta(content, categories)
		expected_content = {
			"anonymousEmpty": [],
			"autoLayoutCategories": False,
			"categories": [u"cn=domain-admin,cn=category,cn=portals,cn=univention,dc=intranet,dc=example,dc=de"],
			"content": [
				[
					u"cn=domain-admin,cn=category,cn=portals,cn=univention,dc=intranet,dc=example,dc=de",
					[u"cn=umc-domain,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de", u"cn=server-overview,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de", u"cn=univentionblog,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de"],
				]
			],
			"defaultLinkTarget": u"embedded",
			"dn": u"cn=domain,cn=portal,cn=portals,cn=univention,dc=intranet,dc=example,dc=de",
			"in_portal": True,
			"ensureLogin": False,
			"fontColor": u"black",
			"logo": None,
			"name": {u"de_DE": u"Univention Portal", u"en_US": u"Univention Portal", u"fr_FR": u"Portail Univention"},
			"showApps": False,
		}
		assert content == expected_content

	def test_refresh(self, mocked_portal, mocker):
		mocked_portal.portal_cache.refresh = mocker.Mock(return_value=None)
		mocked_portal.authenticator.refresh = mocker.Mock(return_value=None)
		assert mocked_portal.refresh() is None
		mocked_portal.portal_cache.refresh.assert_called_once()
		mocked_portal.authenticator.refresh.assert_called_once()

	def test_score(self, mocked_portal, mocker):
		mocked_portal.scorer.score = mocker.Mock(return_value=5)
		request = mocker.Mock()
		assert mocked_portal.score(request) == 5
		mocked_portal.scorer.score.assert_called_once()
		mocked_portal.scorer.score.assert_called_with(request)
