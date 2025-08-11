# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import univention.admin.handlers
import univention.admin.handlers.portals.announcement
import univention.admin.handlers.portals.category
import univention.admin.handlers.portals.entry
import univention.admin.handlers.portals.portal
from univention.admin.layout import Tab


translation = univention.admin.localization.translation('univention.admin.handlers.portals-portal')
_ = translation.translate

module = 'portals/all'
short_description = _('Portal: Settings')
long_description = _('Management of portals and their entries')
default_containers = [
    'cn=portal,cn=portals,cn=univention',
    'cn=entry,cn=portals,cn=univention',
    'cn=category,cn=portals,cn=univention',
    'cn=folder,cn=portals,cn=univention',
    'cn=announcement,cn=portals,cn=univention',
]

operations = ['search']
childmodules = [
    'portals/portal',
    'portals/entry',
    'portals/category',
    'portals/folder',
    'portals/announcement',
]
virtual = True
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Internal name'),
        long_description='',
        syntax=univention.admin.syntax.string_numbers_letters_dots,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
    'displayName': univention.admin.property(
        short_description=_('Display name'),
        long_description='',
        syntax=univention.admin.syntax.LocalizedDisplayName,
        multivalue=True,
        required=True,
    ),
}
layout = [Tab(_('General'), _('Basic settings'), layout=["name"])]
mapping = univention.admin.mapping.mapping()


class object(univention.admin.handlers.simpleLdap):
    module = module


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
    res = []
    for child in childmodules:
        portal_module = univention.admin.modules.get(child)
        res.extend(portal_module.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit))

    return res


def identify(dn, attr, canonical=False):
    pass
