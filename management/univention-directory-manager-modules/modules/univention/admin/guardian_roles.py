# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| guardian roles handling"""

import itertools
from logging import getLogger

import univention.admin
import univention.admin.localization
import univention.admin.mapping
import univention.admin.syntax
from univention.admin.layout import Tab


log = getLogger('ADMIN')

translation = univention.admin.localization.translation('univention.admin')
_ = translation.translate


def member_role_properties():
    return {
        'guardianMemberRoles': univention.admin.property(
            short_description=_('Roles used by Guardian for access permissions, these roles are passed to the members of this group'),
            long_description=_("Lowercase ASCII alphanumeric string with underscores or dashes, in the format 'app:namespace:role' or 'app:namespace:role&app:namespace:context'"),
            syntax=univention.admin.syntax.GuardianRole,
            size='Two',
            multivalue=True,
        ),
    }


def role_properties():
    return {
        'guardianRoles': univention.admin.property(
            short_description=_('Roles used by Guardian for access permissions'),
            long_description=_("Lowercase ASCII alphanumeric string with underscores or dashes, in the format 'app:namespace:role' or 'app:namespace:role&app:namespace:context'"),
            syntax=univention.admin.syntax.GuardianRole,
            size='Two',
            multivalue=True,
        ),
        'guardianInheritedRoles': univention.admin.property(
            short_description=_('Roles used by Guardian for access permissions. Inherited by group membership'),
            long_description=_('Roles used by Guardian for access permissions. Inherited by group membership'),
            prevent_umc_default_popup=True,
            syntax=univention.admin.syntax.GuardianRole,
            size='Two',
            may_change=False,
            multivalue=True,
            dontsearch=True,
            show_in_lists=True,
            cli_enabled=False,
            lazy_loading_fn='open_guardian',
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
            'guardianInheritedRoles',
        ],
    )


@univention.admin._ldap_cache(ttl=60)
def get_group_role(lo: univention.admin.uldap.access, dn: str) -> list[str]:
    res = lo.authz_connection.get(dn, attr=['univentionGuardianMemberRoles'])
    return [x.decode('UTF-8') for x in res.get('univentionGuardianMemberRoles', [])]


# TODO:
# naive approach to get role strings for groups by searching the LDAP
def load_roles(lo: univention.admin.uldap.access, groups: list[str]) -> list[str]:
    return list(set(itertools.chain.from_iterable(get_group_role(lo, group) for group in groups)))


class GuardianBase:
    def open_guardian(self) -> None:
        if self.exists():
            groups = self.get('groups', [])
            if self.get('primaryGroup'):
                groups = [*groups, self['primaryGroup']]
            self.info['guardianInheritedRoles'] = load_roles(self.lo, groups)
            self.save()
