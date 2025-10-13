# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for the federated account objects"""

from __future__ import annotations

import univention.admin
import univention.admin.handlers
import univention.admin.localization
import univention.admin.mapping
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.users')
_ = translation.translate

module = 'users/federated_account'
operations = ['add', 'edit', 'remove', 'search']

childs = False
short_description = _('Federated account')
object_name = _('Federated account')
object_name_plural = _('Federated accounts')
long_description = _('This object represents a federated account. It is intended for functional purposes and is not counted as user object in the license.')

options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionFederatedAccount'],
    ),
}
property_descriptions = {
    'preferred_username': univention.admin.property(
        short_description=_('Display name'),
        long_description='',
        syntax=univention.admin.syntax.TwoThirdsString,
        include_in_default_search=True,
        required=False,
        copyable=True,
    ),
    'description': univention.admin.property(
        short_description=_('Description'),
        long_description='',
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        copyable=True,
    ),
    'univentionObjectIdentifier': univention.admin.property(
        short_description=_('Immutable Object Identifier'),
        long_description=_('Immutable attribute to track the identity of an object in UDM'),
        syntax=univention.admin.syntax.UUID,
        may_change=False,
        identifies=True,
        required=True,
        dontsearch=True,
    ),
}

layout = [
    Tab(_('General'), _('Basic settings'), layout=[
        Group(_('Federated account'), layout=[
            ['description'],
            ['preferred_username'],
            ['univentionObjectIdentifier'],
        ]),
    ]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('univentionObjectIdentifier', 'univentionObjectIdentifier', None, univention.admin.mapping.ListToString)
mapping.register('preferred_username', 'univentionPreferredUsername', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
    module = module


lookup_filter = object.lookup_filter
lookup = object.lookup
identify = object.identify
