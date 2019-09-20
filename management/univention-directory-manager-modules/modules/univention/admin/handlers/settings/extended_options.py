# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for extended options
#
# Copyright 2011-2019 Univention GmbH
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

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
from univention.debug import debug, ADMIN, INFO

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/extended_options'
operations = ['add', 'edit', 'remove', 'search', 'move']
superordinate = 'settings/cn'

childs = 0
short_description = _('Settings: Extended option')
object_name = _('Extended option')
object_name_plural = _('Extended options')
long_description = _('Options for extended attributes')

options = {
	'default': univention.admin.option(
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
	),
	'shortDescription': univention.admin.property(
		short_description=_('Default short description'),
		long_description=_('Short description for the option as shown on the Option tab.'),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
	),
	'longDescription': univention.admin.property(
		short_description=_('Default long description'),
		long_description=_('Long description for the option as shown on the Option tab.'),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
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
	),
	'editable': univention.admin.property(
		short_description=_('Editable'),
		long_description=_('Option may be repeatedly turned on and off.'),
		syntax=univention.admin.syntax.boolean,
	),
	'module': univention.admin.property(
		short_description=_('Needed module'),
		long_description=_('List of modules this option applies to.'),
		syntax=univention.admin.syntax.univentionAdminModules,
		multivalue=True,
		required=True,
	),
	'objectClass': univention.admin.property(
		short_description=_('LDAP object class'),
		long_description=_('Mapping to LDAP objectClasses'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
	),
	'isApp': univention.admin.property(
		short_description=_('Application'),
		long_description=_('Specifies that the option belongs to a UCS Application'),
		syntax=univention.admin.syntax.boolean,
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
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('shortDescription', 'univentionUDMOptionShortDescription', None, univention.admin.mapping.ListToString)
mapping.register('longDescription', 'univentionUDMOptionLongDescription', None, univention.admin.mapping.ListToString)
mapping.register('default', 'univentionUDMOptionDefault', None, univention.admin.mapping.ListToString)
mapping.register('editable', 'univentionUDMOptionEditable', None, univention.admin.mapping.ListToString)
mapping.register('module', 'univentionUDMOptionModule')
mapping.register('objectClass', 'univentionUDMOptionObjectClass')
mapping.register('isApp', 'univentionUDMOptionIsApp', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def open(self):
		"""Load and parse translations."""
		univention.admin.handlers.simpleLdap.open(self)

		for transKey in ['ShortDescription', 'LongDescription']:
			translations = []
			for key in self.oldattr.keys():
				if key.startswith('univentionUDMOptionTranslation%s;entry-' % transKey):
					lang = '%s_%s' % (key[-5:-3].lower(), key[-2:].upper())
					txt = self.oldattr.get(key)[0]
					translations.append((lang, txt))

			debug(ADMIN, INFO, 'extended_option: added translations for %s: %s' % (transKey, translations))
			self['translation%s' % transKey] = translations

		self.save()

	def _ldap_modlist(self):
		"""Save translations."""
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

		for transKey in ['ShortDescription', 'LongDescription']:
			if self.hasChanged('translation%s' % transKey):
				oldlist = {}
				newlist = {}

				for lang, txt in self.oldinfo.get('translation%s' % transKey, []):
					lang = lang.replace('_', '-')
					oldlist[lang] = txt
					if lang not in newlist:
						newlist[lang] = ''

				# duplicate lang entries will be removed due to use of dictionary
				for lang, txt in self.info.get('translation%s' % transKey, []):
					lang = lang.replace('_', '-')
					newlist[lang] = txt
					if lang not in oldlist:
						oldlist[lang] = ''

				# modlist for new items
				for lang, txt in oldlist.items():
					if txt != newlist[lang]:
						ml.append(('univentionUDMOptionTranslation%s;entry-%s' % (transKey, lang), oldlist[lang], newlist[lang]))

		return ml


lookup = object.lookup
identify = object.identify
