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


import pytest

@pytest.fixture
def standard_portal(dynamic_class, mocker):
	Portal = dynamic_class('Portal')
	Scorer = dynamic_class('Scorer')
	PortalFileCache = dynamic_class('PortalFileCache')
	GroupFileCache = dynamic_class('GroupFileCache')
	return Portal(Scorer(), PortalFileCache('unittests/caches/portal.json'), GroupFileCache('unittests/caches.groups.json'))


@pytest.fixture
def mocked_portal(dynamic_class, mocker):
	Portal = dynamic_class('Portal')
	scorer = mocker.Mock()
	portal_cache = mocker.Mock()
	groups_cache = mocker.Mock()
	return Portal(scorer, portal_cache, groups_cache)


def test_portal_content(standard_portal):
	content = standard_portal.get_visible_content('hindenkampp', False)
	expected_content = {
		'category_dns': ['cn=domain-admin,cn=category,cn=portals,cn=univention,dc=intranet,dc=example,dc=de'],
		'entry_dns': [
			'cn=umc-domain,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de',
			'cn=server-overview,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de'],
		'folder_dns': []
	}
	assert content == expected_content


def test_portal_user_links(standard_portal):
	content = standard_portal.get_user_links('hindenkampp', False)
	expected_content = []
	assert content == expected_content


def test_portal_menu_links(standard_portal):
	content = standard_portal.get_menu_links('hindenkampp', False)
	expected_content = []
	assert content == expected_content


def test_portal_entries(standard_portal):
	content = standard_portal.get_visible_content('hindenkampp', False)
	content = standard_portal.get_entries(content)
	expected_content = {
		'cn=server-overview,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de': {
			'activated': True,
			'allowedGroups': [],
			'description': {
				'de_DE': u'Zeigt eine \xdcbersicht aller UCS Server in der Dom\xe4ne',
				'en_US': u'Provide an overview of all UCS server in the domain',
				'fr_FR': u"Vue d'ensemble de tous les serveurs UCS du domaine"},
			'dn': 'cn=server-overview,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de',
			'linkTarget': 'useportaldefault',
			'links': ['/univention/server-overview/'],
			'logo_name': '/univention/portal/icons/entries/server-overview.svg',
			'name': {
				'de_DE': u'Server\xfcbersicht',
				'en_US': u'Server overview',
				'fr_FR': u"Vue d'ensemble de serveurs"}},
		'cn=umc-domain,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de': {
			'activated': True,
			'allowedGroups': [],
			'description': {
				'de_DE': u'Univention Management Console zur Ver\xadwal\xadtung der UCS-Dom\xe4ne und des lokalen Systems',
				'en_US': u'Univention Management Console for admin\xadis\xadtra\xadting the UCS domain and the local system',
				'fr_FR': u'Console de gestion Univention pour admin\xadis\xadtrer le domaine UCS et le syst\xe8me local'},
			'dn': 'cn=umc-domain,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de',
			'linkTarget': 'useportaldefault',
			'links': ['/univention/management/'],
			'logo_name': '/univention/portal/icons/entries/umc-domain.svg',
			'name': {
				'de_DE': u'System- und Dom\xe4neneinstellungen',
				'en_US': u'System and domain settings',
				'fr_FR': u'R\xe9glages du syst\xe8me et du domaine'}}}
	assert content == expected_content


def test_portal_folders(standard_portal):
	content = standard_portal.get_visible_content('hindenkampp', False)
	content = standard_portal.get_folders(content)
	expected_content = {}
	assert content == expected_content


def test_portal_categories(standard_portal):
	content = standard_portal.get_visible_content('hindenkampp', False)
	content = standard_portal.get_categories(content)
	expected_content = {
		u'cn=domain-admin,cn=category,cn=portals,cn=univention,dc=intranet,dc=example,dc=de': {
			'display_name': {
				'de_DE': u'Verwaltung',
				'en_US': u'Administration'},
			'dn': u'cn=domain-admin,cn=category,cn=portals,cn=univention,dc=intranet,dc=example,dc=de',
			'entries': [
				'cn=umc-domain,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de',
				'cn=server-overview,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de']}}
	assert content == expected_content


def test_portal_meta(standard_portal):
	content = standard_portal.get_visible_content('hindenkampp', False)
	categories = standard_portal.get_categories(content)
	content = standard_portal.get_meta(content, categories)
	expected_content = {
		'anonymousEmpty': [],
		'autoLayoutCategories': False,
		'categories': [u'cn=domain-admin,cn=category,cn=portals,cn=univention,dc=intranet,dc=example,dc=de'],
		'content': [[u'cn=domain-admin,cn=category,cn=portals,cn=univention,dc=intranet,dc=example,dc=de',
			    [u'cn=umc-domain,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de',
			     u'cn=server-overview,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de']]],
		'defaultLinkTarget': u'embedded',
		'dn': u'cn=domain,cn=portal,cn=portals,cn=univention,dc=intranet,dc=example,dc=de',
		'ensureLogin': False,
		'fontColor': u'black',
		'logo': None,
		'name': {u'de_DE': u'Univention Portal',
			 u'en_US': u'Univention Portal',
			 u'fr_FR': u'Portail Univention'},
		'showApps': False
	}
	assert content == expected_content


def test_portal_refresh(mocked_portal):
	assert mocked_portal.refresh_cache() is None
	mocked_portal.portal_cache.refresh.assert_called_once()
	mocked_portal.groups_cache.refresh.assert_called_once()


def test_portal_score(mocked_portal, mocker):
	mocked_portal.scorer.score = mocker.Mock(return_value=5)
	request = mocker.Mock()
	assert mocked_portal.score(request) == 5
	mocked_portal.scorer.score.assert_called_once()
	mocked_portal.scorer.score.assert_called_with(request)
