#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for prohibited user names"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/prohibited_username'
operations = ['add', 'edit', 'remove', 'search', 'move']
superordinate = 'settings/cn'

childs = False
short_description = _('Settings: Prohibited user names')
object_name = _('Prohibited user name')
object_name_plural = _('Prohibited user names')
long_description = _('Univention Prohibited user names')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionProhibitedUsernames'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description=_('Name'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'usernames': univention.admin.property(
        short_description=_('Prohibited user name'),
        long_description=_('Prohibited user name'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        include_in_default_search=True,
    ),
}

layout = [
    Tab(_('General'), _('Prohibited user names'), layout=[
        Group(_('General prohibited user names settings'), layout=[
            'name',
            'usernames',
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('usernames', 'prohibitedUsername', None, None)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
