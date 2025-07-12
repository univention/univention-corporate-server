# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for extended options"""

from __future__ import annotations

from typing import Any

import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.admin.layout import Group, Tab


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/extended_options'
operations = ['add', 'edit', 'remove', 'search', 'move']
superordinate = 'settings/cn'

childs = False
short_description = _('Settings: Extended option')
object_name = _('Extended option')
object_name_plural = _('Extended options')
long_description = _('Options for extended attributes')

# fmt: off
options = {
    'default': univention.admin.option(
        short_description=short_description,
        default=True,
        objectClasses=['top', 'univentionUDMOption'],
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
        ldap_attribute='cn',
    ),
    'shortDescription': univention.admin.property(
        short_description=_('Default short description'),
        long_description=_('Short description for the option as shown on the Option tab.'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        required=True,
        ldap_attribute='univentionUDMOptionShortDescription',
    ),
    'longDescription': univention.admin.property(
        short_description=_('Default long description'),
        long_description=_('Long description for the option as shown on the Option tab.'),
        syntax=univention.admin.syntax.string,
        include_in_default_search=True,
        ldap_attribute='univentionUDMOptionLongDescription',
    ),
    'translationShortDescription': univention.admin.property(
        short_description=_('Translations of short description'),
        long_description=_('Translations of the short description for the option as shown on the Option tab'),
        syntax=univention.admin.syntax.translationTupleShortDescription,
        multivalue=True,
        include_in_default_search=True,
    ),
    'translationLongDescription': univention.admin.property(
        short_description=_('Translations of long description'),
        long_description=_('Translations of the long description for the option as shown on the Option tab'),
        syntax=univention.admin.syntax.translationTupleLongDescription,
        multivalue=True,
        include_in_default_search=True,
    ),
    'default': univention.admin.property(
        short_description=_('Default'),
        long_description=_('Enable option by default.'),
        syntax=univention.admin.syntax.boolean,
        ldap_attribute='univentionUDMOptionDefault',
        encoding='ASCII',
    ),
    'editable': univention.admin.property(
        short_description=_('Editable'),
        long_description=_('Option may be repeatedly turned on and off.'),
        syntax=univention.admin.syntax.boolean,
        ldap_attribute='univentionUDMOptionEditable',
        encoding='ASCII',
    ),
    'module': univention.admin.property(
        short_description=_('Needed module'),
        long_description=_('List of modules this option applies to.'),
        syntax=univention.admin.syntax.univentionAdminModules,
        multivalue=True,
        required=True,
        ldap_attribute='univentionUDMOptionModule',
    ),
    'objectClass': univention.admin.property(
        short_description=_('LDAP object class'),
        long_description=_('Mapping to LDAP objectClasses'),
        syntax=univention.admin.syntax.ldapObjectClass,
        multivalue=True,
        ldap_attribute='univentionUDMOptionObjectClass',
    ),
    'isApp': univention.admin.property(
        short_description=_('Application'),
        long_description=_('Specifies that the option belongs to a UCS Application'),
        syntax=univention.admin.syntax.boolean,
        ldap_attribute='univentionUDMOptionIsApp',
        encoding='ASCII',
    ),
}

layout = [
    Tab(_('General'), _('Basic values'), layout=[
        Group(_('General extended options settings'), layout=[
            'name',
            ["shortDescription", "longDescription"],
            ["translationShortDescription", "translationLongDescription"],
            ["default", "editable", "isApp"],
            ['module', "objectClass"],
        ]),
    ]),
]

mapping = univention.admin.mapping.mapping()
mapping.from_properties(property_descriptions)
# fmt: on


class object(univention.admin.handlers.simpleLdap):
    module = module

    def open(self) -> None:
        """Load and parse translations."""
        univention.admin.handlers.simpleLdap.open(self)

        for transKey in ['ShortDescription', 'LongDescription']:
            translations = [
                ('%s_%s' % (key[-5:-3].lower(), key[-2:].upper()), vals[0].decode('UTF-8'))
                for key, vals in self.oldattr.items()
                if key.startswith('univentionUDMOptionTranslation%s;entry-' % transKey)
            ]

            self.log.debug('open: added translations', msgid=transKey, msgstrs=translations)
            self['translation%s' % transKey] = translations

        self.save()

    def _ldap_modlist(self) -> list[tuple[str, Any, Any]]:
        """Save translations."""
        ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

        for transKey in ['ShortDescription', 'LongDescription']:
            if self.hasChanged('translation%s' % transKey):
                oldlist = {}
                newlist = {}

                for lang, txt in self.oldinfo.get('translation%s' % transKey, []):
                    lang = lang.replace('_', '-')
                    oldlist[lang] = txt.encode('UTF-8')
                    if lang not in newlist:
                        newlist[lang] = b''

                # duplicate lang entries will be removed due to use of dictionary
                for lang, txt in self.info.get('translation%s' % transKey, []):
                    lang = lang.replace('_', '-')
                    newlist[lang] = txt.encode('UTF-8')
                    if lang not in oldlist:
                        oldlist[lang] = b''

                # modlist for new items
                for lang, txt in oldlist.items():
                    if txt != newlist[lang]:
                        ml.append(('univentionUDMOptionTranslation%s;entry-%s' % (transKey, lang), txt, newlist[lang]))

        return ml


lookup = object.lookup
lookup_filter = object.lookup_filter
identify = object.identify
