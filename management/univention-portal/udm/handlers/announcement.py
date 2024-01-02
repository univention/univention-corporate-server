# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2022-2024 Univention GmbH
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

import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.portals-portal')
_ = translation.translate

superordinate = 'settings/cn'
module = 'portals/announcement'
default_containers = ['cn=announcement,cn=portals,cn=univention']
childs = False
operations = ['add', 'edit', 'remove', 'search']
short_description = _('Portal: Announcement')
object_name = _('Portal announcement')
object_name_plural = _('Portal announcements')
long_description = _('One folder in https://fqhn/univention/portal which holds one or more portals/announcement objects. Belongs to one or more portals/portal objects')
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionNewPortalAnnouncement'],
    ),
}
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Internal name'),
        long_description='',
        syntax=univention.admin.syntax.string_numbers_letters_dots,
        include_in_default_search=True,
        required=True,
        may_change=False,
        identifies=True,
    ),
    'allowedGroups': univention.admin.property(
        short_description=_('Restrict visibility to groups'),
        long_description=_('If one or more groups are selected then the portal announcement will only be visible to logged in users that are in any of the selected groups. If no groups are selected then the portal entry is always visible.'),
        syntax=univention.admin.syntax.GroupDN,
        multivalue=True,
        required=False,
    ),
    'needsConfirmation': univention.admin.property(
        short_description=_('Needs Confirmation (not yet implemented!)'),
        long_description=_('If enabled, the user will see a "Confirm" button and the announcement will persist until it is clicked.'),
        syntax=univention.admin.syntax.TrueFalseUp,
        default='FALSE',
        dontsearch=True,
        required=False,
    ),
    'isSticky': univention.admin.property(
        short_description=_('Sticky'),
        long_description=_("If enabled, the announcement can't be closed and will persist until the time ends (or never)."),
        syntax=univention.admin.syntax.TrueFalseUp,
        default='FALSE',
        dontsearch=True,
        required=False,
    ),
    'severity': univention.admin.property(
        short_description=_('Severity'),
        long_description=_('A color theme the announcement should appear in.'),
        syntax=univention.admin.syntax.NewPortalAnnouncementSeverity,
        dontsearch=True,
        required=False,
    ),
    'title': univention.admin.property(
        short_description=_('Title'),
        long_description=_('The title of the announcement, usually written in bold above the message.'),
        syntax=univention.admin.syntax.LocalizedDisplayName,
        multivalue=True,
        required=True,
    ),
    'message': univention.admin.property(
        short_description=_('Message'),
        long_description=_('The message of the announcement, usually written in normal text below the title.'),
        syntax=univention.admin.syntax.LocalizedDisplayName,
        multivalue=True,
        required=False,
    ),
    'visibleFrom': univention.admin.property(
        short_description=_('Start date'),
        long_description=_('The date when the announcement will first appear.'),
        syntax=univention.admin.syntax.iso8601Date,
        dontsearch=True,
        required=False,
    ),
    'visibleUntil': univention.admin.property(
        short_description=_('End date'),
        long_description=_('The date when the announcement will last appear.'),
        syntax=univention.admin.syntax.iso8601Date,
        dontsearch=True,
        required=False,
    ),
}

layout = [
    Tab(_('General'), _('Announcement options'), layout=[
        Group(_('General'), layout=[
            ["name"],
        ]),
        Group(_('Content'), layout=[
            ["title"],
            ["message"],
        ]),
        Group(_('Time'), layout=[
            ["visibleFrom", "visibleUntil"],
        ]),
        Group(_('Options'), layout=[
            ["isSticky"],
            ["severity"],
            ["allowedGroups"],
        ]),
    ]),
]


def mapTranslationValue(vals, encoding=()):
    return [u' '.join(val).encode(*encoding) for val in vals]


def unmapTranslationValue(vals, encoding=()):
    return [val.decode(*encoding).split(u' ', 1) for val in vals]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('allowedGroups', 'univentionNewPortalAnnouncementAllowedGroups')
mapping.register('needsConfirmation', 'univentionNewPortalAnnouncementNeedsConfirmation', None, univention.admin.mapping.ListToString)
mapping.register('isSticky', 'univentionNewPortalAnnouncementIsSticky', None, univention.admin.mapping.ListToString)
mapping.register('severity', 'univentionNewPortalAnnouncementSeverity', None, univention.admin.mapping.ListToString)
mapping.register('title', 'univentionNewPortalAnnouncementTitle', mapTranslationValue, unmapTranslationValue)
mapping.register('message', 'univentionNewPortalAnnouncementMessage', mapTranslationValue, unmapTranslationValue)
mapping.register('visibleFrom', 'univentionNewPortalAnnouncementVisibleFrom', None, univention.admin.mapping.ListToString)
mapping.register('visibleUntil', 'univentionNewPortalAnnouncementVisibleUntil', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
    module = module


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
