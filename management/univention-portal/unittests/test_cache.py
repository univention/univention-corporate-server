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


def test_import(dynamic_class):
	assert dynamic_class('Cache')
	assert dynamic_class('PortalFileCache')
	assert dynamic_class('GroupFileCache')


def test_portal_cache_missing_file(dynamic_class):
	cache = dynamic_class('PortalFileCache')('/tmp/a/file/that/does/not/exist')
	assert cache.get() == {}


def test_portal_cache(dynamic_class):
	Cache = dynamic_class('PortalFileCache')
	# import sys
	# import json
	# cache_module = sys.modules[Cache.__module__]
	# content = {1: 2}
	# mock = mocker.mock_open(read_data=json.dumps(content))
	# mocker.patch.object(cache_module, 'open', mock)
	cache = Cache('unittests/caches/portal.json')
	assert cache.get_user_links() == []
	assert sorted(cache.get_entries().keys()) == [
			'cn=server-overview,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de',
			'cn=umc-domain,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de',
			'cn=univentionblog,cn=entry,cn=portals,cn=univention,dc=intranet,dc=example,dc=de',
		]
	assert cache.get_folders() == {}
	assert cache.get_portal()['dn'] == 'cn=domain,cn=portal,cn=portals,cn=univention,dc=intranet,dc=example,dc=de'
	assert sorted(cache.get_categories().keys()) == ['cn=domain-admin,cn=category,cn=portals,cn=univention,dc=intranet,dc=example,dc=de']
	assert cache.get_menu_links() == []


def test_cache_reload(dynamic_class, mocker):
	Cache = dynamic_class('PortalFileCache')
	mock = mocker.Mock()
	cache = Cache('unittests/caches/portal.json', reloader=mock)
	mock.refresh.assert_called_with(force=False)
	cache.refresh(force=True)
	mock.refresh.assert_called_with(force=True)


def test_cache_reload_on_get(dynamic_class, mocker):
	Cache = dynamic_class('PortalFileCache')
	mock = mocker.Mock()
	cache = Cache('unittests/caches/portal.json', reloader=mock)
	mock.refresh.call_count == 1
	cache.get()
	mock.refresh.call_count == 2
