# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin.localization
from univention.admin.syntax import UDM_Objects, languageCode, select, string, translationTuple


translation = univention.admin.localization.translation('univention.admin.handlers.portals.portal')
_ = translation.translate


class NewPortalCategories(UDM_Objects):
    """Syntax to select a portal from |LDAP| using :py:class:`univention.admin.handlers.portals.category`."""

    udm_modules = ('portals/category', )
    label = '%(name)s'
    empty_value = False
    simple = True


class NewPortalCategoryEntries(UDM_Objects):
    """Syntax to select a portal entries or folders from |LDAP|."""

    udm_modules = ('portals/entry', 'portals/folder')
    label = '%(name)s'
    empty_value = False
    simple = True


class NewPortalEntries(UDM_Objects):
    """Syntax to select a portal entries from |LDAP| using :py:class:`univention.admin.handlers.portals.entry`."""

    udm_modules = ('portals/entry', )
    label = '%(name)s'
    empty_value = False
    simple = True


class NewPortalFolders(UDM_Objects):
    """Syntax to select a portal entries from |LDAP| using :py:class:`univention.admin.handlers.portals.entry`."""

    udm_modules = ('portals/folder', )
    label = '%(name)s'
    empty_value = False
    simple = True


class NewPortalAnnouncements(UDM_Objects):
    """Syntax to select a portal announcement from |LDAP| using :py:class:`univention.admin.handlers.announcement.entry`."""

    udm_modules = ('portals/announcement', )
    label = '%(name)s'
    empty_value = False
    simple = True


class NewPortalComputer(UDM_Objects):
    """Syntax to select a |UCS| host from |LDAP| by |FQDN| running the portal service."""

    udm_modules = ('computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver')
    udm_filter = '!(univentionObjectFlag=docker)'
    use_objects = False


class NewPortalFontColor(select):
    """Syntax to select the color of the font in the portal."""

    choices = [
        ('white', _('White')),
        ('black', _('Black')),
    ]


class NewPortalDefaultLinkTarget(select):
    choices = [
        ('samewindow', _('Same tab')),
        ('newwindow', _('New tab')),
        ('embedded', _('Embedded')),
    ]


class NewPortalEntryLinkTarget(select):
    choices = [
        ('useportaldefault', _('Use default of portal')),
        ('samewindow', _('Same tab')),
        ('newwindow', _('New tab')),
        ('embedded', _('Embedded')),
    ]


class NewPortalAnnouncementSeverity(select):
    """Syntax to select the severity of an announcement."""

    choices = [
        ('info', _('Info')),
        ('warn', _('Warning')),
        ('success', _('Success')),
        ('danger', _('Danger')),
    ]


class LocalizedLink(translationTuple):
    subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Link'), string)]
    subsyntax_key_value = False


class LocalizedKeywords(translationTuple):
    """Syntax for translated keywords of a portal entry."""

    subsyntaxes = [(_('Language code (e.g. en_US)'), languageCode), (_('Keywords'), string)]
