# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for locking objects"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/lock'
operations = ['edit', 'remove', 'search']
superordinate = 'settings/cn'

childs = False
short_description = _('Settings: Lock')
object_name = _('Lock')
object_name_plural = _('Locks')
long_description = _('Lock objects')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['lock'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('Name'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'locktime': univention.admin.property(
        short_description=_('Lock Time'),
        long_description=_('Locked until'),
        syntax=univention.admin.syntax.string,
        required=True,
        may_change=False,
    ),
}

layout = [
    Tab(_('General'), _('Lock Information'), layout=[
        Group(_('General lock settings'), layout=[
            ['name', 'locktime'],
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('locktime', 'lockTime', None, univention.admin.mapping.ListToString)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
