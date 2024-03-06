# -*- coding: utf-8 -*-
#
# Copyright 2024 Univention GmbH
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

"""|UDM| guardian roles handling"""

import re
from logging import getLogger
from typing import List, Optional  # noqa: F401

from ldap.filter import filter_format

import univention.admin
import univention.admin.localization
import univention.admin.mapping
from univention.admin.layout import Tab
from univention.admin.syntax import simple


log = getLogger('ADMIN')

translation = univention.admin.localization.translation('univention.admin')
_ = translation.translate


# TODO move to univention.admin.syntax
class GuardianRole(simple):
    regex = re.compile(
        r"^([a-z0-9-_]+:[a-z0-9-_]+:[a-z0-9-_]+)(&[a-z0-9-_]+:[a-z0-9-_]+:[a-z0-9-_]+)?$"
    )
    error_message = _(
        "Guardian role strings must be lowercase ASCII alphanumeric with hyphens and underscores, "
        "in the format 'app:namespace:role' or 'app:namespace:role&app:namespace:context'!"
    )


def member_role_properties():
    return {
        'guardianMemberRoles': univention.admin.property(
            short_description=_('Roles used by Guardian for access permissions, these roles are passed to the members of this group'),
            long_description=_("Lowercase ASCII alphanumeric string with underscores or dashes, in the format 'app:namespace:role' or 'app:namespace:role&app:namespace:context'"),
            syntax=GuardianRole,
            multivalue=True,
        )
    }


def role_properties():
    return {
        'guardianRoles': univention.admin.property(
            short_description=_('Roles used by Guardian for access permissions'),
            long_description=_("Lowercase ASCII alphanumeric string with underscores or dashes, in the format 'app:namespace:role' or 'app:namespace:role&app:namespace:context'"),
            syntax=GuardianRole,
            multivalue=True,
        ),
        'guardianInheritedRoles': univention.admin.property(
            short_description=_('Roles used by Guardian for access permissions. Inherited by group membership'),
            long_description=_('Roles used by Guardian for access permissions. Inherited by group membership'),
            syntax=GuardianRole,
            may_change=False,
            multivalue=True,
            dontsearch=True,
            show_in_lists=False,
            cli_enabled=False,
        ),
    }


def register_member_role_mapping(mapping):
    mapping.register('guardianMemberRoles', 'univentionGuardianMemberRoles', None, None)


def register_role_mapping(mapping):
    mapping.register('guardianRoles', 'univentionGuardianRoles', None, None)


def member_role_layout():
    return Tab(
        _('Guardian'),
        _('Manage roles that are used for authorization'),
        advanced=True,
        layout=[
            'guardianMemberRoles',
        ],
    )


def role_layout():
    return Tab(
        _('Guardian'),
        _('Manage roles that are used for authorization'),
        advanced=True,
        layout=[
            'guardianRoles',
            'guardianInheritedRoles'
        ],
    )


@univention.admin._ldap_cache(ttl=60)
def get_group_role(lo, dn):  # type: (univention.admin.uldap.access, str) -> list[str]
    res = lo.get(dn, attr=['univentionGuardianMemberRoles'])
    return [x.decode('UTF-8') for x in res.get('univentionGuardianMemberRoles', [])]


@univention.admin._ldap_cache(ttl=60)
def search_group_uniqueMembers(lo, dn):  # type: (univention.admin.uldap.access, str) -> List[str]
    return lo.searchDn(filter_format('(&(|(objectClass=univentionGroup)(objectClass=sambaGroupMapping))(uniqueMember=%s))', [dn]))


def get_nested_groups(lo, groups, recursion_list=None):  # type: (univention.admin.uldap.access, List[str], Optional[List[str]]) -> List[str]
    all_groups = []
    if recursion_list is None:
        recursion_list = []
    for group in groups:
        if group not in all_groups:
            all_groups.append(group)
        for dn in search_group_uniqueMembers(lo, group):
            if dn not in recursion_list:
                recursion_list.append(dn)
                all_groups += get_nested_groups(lo, [dn], recursion_list)
    return all_groups


# TODO
# naive approach to get role strings for groups by searching the LDAP
def load_roles(lo, groups, nested_groups=False):  # type: (univention.admin.uldap.access, List[str], bool) -> List[str]
    roles = []
    if nested_groups:
        groups = get_nested_groups(lo, groups)
    for group in groups:
        roles += get_group_role(lo, group)
    # this is slower in my tests
    #  import concurrent.futures
    #  import multiprocessing.pool
    #  THREAD_POOL_SIZE = multiprocessing.cpu_count()
    #  with concurrent.futures.ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE) as executor:
    #      futures = []
    #      for group in groups:
    #          futures.append(
    #              executor.submit(
    #                  get_group_role, lo, group
    #              )
    #          )
    #      for future in concurrent.futures.as_completed(futures):
    #          roles += future.result()
    return list(set(roles))


class GuardianBase(object):
    def open_guardian(self, nested_groups=False):  # type: (bool) -> None
        if self.exists():
            self.info['guardianInheritedRoles'] = load_roles(self.lo, self['groups'] + [self['primaryGroup']], nested_groups=nested_groups)
            self.save()
