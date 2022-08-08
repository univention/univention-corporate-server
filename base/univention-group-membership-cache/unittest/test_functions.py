#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
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
from univentionunittests import import_module


@pytest.fixture(scope="module")
def ldap_cache():
    module = import_module("univention.ldap_cache", "src/", "univention.ldap_cache", use_installed=False)
    return module

# mock the cache imported in the module


def test_groups_for_user(ldap_cache):
    """
    Test if groups_for_user() returns the correct groups.
    """
    groups_for_user = ldap_cache.groups_for_user
    groups = groups_for_user("cn=user,dc=example,dc=com")
    assert groups == ["cn=group1,dc=example,dc=com", "cn=group2,dc=example,dc=com"]


def test_users_in_group(ldap_cache):
    """
    Test if users_in_group() returns the correct users.
    """
    users_in_group = ldap_cache.users_in_group
    users = users_in_group("cn=group1,dc=example,dc=com")
    assert users == ["cn=user,dc=example,dc=com"]
