#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for printer URIs"""

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.syntax
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/printeruri'
operations = ['add', 'edit', 'remove', 'search', 'move']
superordinate = 'settings/cn'

childs = False
short_description = _('Settings: Printer URI List')
object_name = _('Printer URI List')
object_name_plural = _('Printer URI Lists')
long_description = _('List of URIs for printers')
# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionPrinterURIs'],
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
    'printeruri': univention.admin.property(
        short_description=_('Printer URI'),
        long_description=_('Printer URI'),
        syntax=univention.admin.syntax.string,
        multivalue=True,
        include_in_default_search=True,
        dontsearch=True,
    ),
}

layout = [
    Tab(_('General'), _('Printer URI'), layout=[
        Group(_('General printer URI list settings'), layout=[
            'name',
            'printeruri',
        ]),
    ]),
]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('printeruri', 'printerURI')
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
