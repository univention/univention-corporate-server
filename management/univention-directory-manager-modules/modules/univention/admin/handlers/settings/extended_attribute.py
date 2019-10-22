# -*- coding: utf-8 -*-
#
# Univention UDM Module
#  UDM module for UDM properties
#
# Copyright 2004-2019 Univention GmbH
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
import univention.debug as ud

translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate
module = 'settings/extended_attribute'

operations = ['add', 'edit', 'remove', 'search', 'move']
superordinate = 'settings/cn'
childs = 0
short_description = _('Settings: Extended attribute')
object_name = _('Extended attribute')
object_name_plural = _('Extended attributes')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionUDMProperty'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Unique name'),
		long_description=_('Name which by default is used by UDM CLI and internally to identify the extended attribute'),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	),
	'shortDescription': univention.admin.property(
		short_description=_('Short description'),
		long_description=_('A short descriptive text which is used as label in the UMC'),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
	),
	'longDescription': univention.admin.property(
		short_description=_('Long description'),
		long_description=_('A longer descriptive text, which is shown as a bubble-help in the UMC'),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'translationShortDescription': univention.admin.property(
		short_description=_('Translations of short description'),
		long_description=_('Translations of the short description for other languages'),
		syntax=univention.admin.syntax.translationTupleShortDescription,
		multivalue=True,
		include_in_default_search=True,
	),
	'translationLongDescription': univention.admin.property(
		short_description=_('Translations of long description'),
		long_description=_('Translations of the long descriptive text for other languages'),
		syntax=univention.admin.syntax.translationTupleLongDescription,
		multivalue=True,
		include_in_default_search=True,
	),
	'translationTabName': univention.admin.property(
		short_description=_('Translations of tab name'),
		long_description=_('Translations of the name of the tab for other languages'),
		syntax=univention.admin.syntax.translationTupleTabName,
		multivalue=True,
	),
	'translationGroupName': univention.admin.property(
		short_description=_('Translations of group name'),
		long_description=_('Translations of the group name for other languages'),
		syntax=univention.admin.syntax.I18N_GroupName,
		multivalue=True,
	),
	'syntax': univention.admin.property(
		short_description=_('Syntax class'),
		long_description=_("When values are entered, the UMC performs a syntax check. Apart from standard syntax definitions (string) and (integer), there are three possibilities for expressing a binary condition. The syntax TrueFalse is represented at LDAP level using the strings true and false, the syntax TrueFalseUpper corresponds to the OpenLDAP boolean values TRUE and FALSE and the syntax boolean does not save any value or the string 1"),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
	),
	'hook': univention.admin.property(
		short_description=_('Hook class'),
		long_description=_('Name of a Python class implementing the univention.admin.hook interface, which can be used to execute additional actions when an object is created, modified or deleted'),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
	),
	'multivalue': univention.admin.property(
		short_description=_('Multi value'),
		long_description=_('This extended attribute can store multiple values instead of only a single value'),
		syntax=univention.admin.syntax.boolean,
		default=0,
	),
	'default': univention.admin.property(
		short_description=_('Default value'),
		long_description=_('Default value which is set for this extended attribute when a new object is created'),
		syntax=univention.admin.syntax.string,
	),
	'disableUDMWeb': univention.admin.property(
		short_description=_("Do not show this extended attribute in the UMC"),
		long_description=_('The extended attribute is not shown in the UMC. It can only be used from the UDM CLI or the Python interface'),
		syntax=univention.admin.syntax.boolean,
	),
	'tabName': univention.admin.property(
		short_description=_('Tab name'),
		long_description=_('Name of the tab in the UMC on which this extended attribute is be placed. A new tab is created automatically if no tab with the name exists'),
		syntax=univention.admin.syntax.string,
	),
	'tabPosition': univention.admin.property(
		short_description=_('Ordering number'),
		long_description=_('This number specifies the position on which this extended attributes is placed on the tab or in the group. The numeration starts at 1'),
		syntax=univention.admin.syntax.integer,
	),
	'groupName': univention.admin.property(
		short_description=_('Group name'),
		long_description=_('Related properties can be grouped. This field specifies the name of the group in which this extended attribute is put in. If no name is given, no group is used'),
		syntax=univention.admin.syntax.string,
	),
	'groupPosition': univention.admin.property(
		short_description=_('Group ordering number'),
		long_description=_('This number specifies the position on which this group is placed on the tab. The numbering starts at 1'),
		syntax=univention.admin.syntax.integer,
	),
	'tabAdvanced': univention.admin.property(
		short_description=_('Tab with advanced settings'),
		long_description=_('Put this extended attribute under "Advanced settings". No autonomous tab will be created'),
		syntax=univention.admin.syntax.boolean,
	),
	'overwriteTab': univention.admin.property(
		short_description=_('Overwrite existing tab'),
		long_description=_('If a tab with the given name already exists, it is replaced by a new tab only containing extended attributes'),
		syntax=univention.admin.syntax.boolean,
	),
	'overwritePosition': univention.admin.property(
		short_description=_('Overwrite existing widget'),
		long_description=_("In some cases it is useful to overwrite predefined input fields with extended attributes. If the internal UDM name of an attribute is configured here, its  input field is overwritten by this extended attribute. The UDM attribute name can only be determined by searching within /usr/lib/python2.7/dist-packages/univention/admin/handlers directory. It is the name which comes before the colon in the declarations of univention.admin.property objects, e.g., roomNumber for a  user's room number"),
		syntax=univention.admin.syntax.string,
	),
	'fullWidth': univention.admin.property(
		short_description=_('Span both columns'),
		long_description=_('The layout element used to represent this extended attribute in the UMC spans both columns'),
		syntax=univention.admin.syntax.boolean,
	),
	'ldapMapping': univention.admin.property(
		short_description=_('LDAP attribute'),
		long_description=_('Univention Corporate Server provides its own LDAP scheme for customer extensions. The LDAP object class univentionFreeAttributes can be used for extended attributes without restrictions. It offers 20 freely usable attributes (univentionFreeAttribute1 to univentionFreeAttribute20) and can be used in connection with any LDAP object (e.g., a user object)'),
		syntax=univention.admin.syntax.string,
		required=True,
	),
	'mayChange': univention.admin.property(
		short_description=_('Editable after creation'),
		long_description=_('This extended attribute can still be modified after the object has been created'),
		syntax=univention.admin.syntax.boolean,
	),
	'notEditable': univention.admin.property(
		short_description=_('Value is only managed internally'),
		long_description=_("This extended attribute can not be changed through UMC or UDM CLI, but only through the Python API or by hooks"),
		syntax=univention.admin.syntax.boolean,
		default='0',
	),
	'valueRequired': univention.admin.property(
		short_description=_('Value required'),
		long_description=_("A value for this extended attribute is required and must be given"),
		syntax=univention.admin.syntax.boolean,
	),
	'objectClass': univention.admin.property(
		short_description=_('LDAP object class'),
		long_description=_('Univention Corporate Server provides its own LDAP scheme for customer extensions. The LDAP object class univentionFreeAttributes can be used for extended attributes without restrictions. It offers 20 freely usable attributes (univentionFreeAttribute1 to univentionFreeAttribute20) and can be used in connection with any LDAP object (e.g., a user object)'),
		syntax=univention.admin.syntax.string,
		required=True,
	),
	'deleteObjectClass': univention.admin.property(
		short_description=_('Remove object class if the attribute is removed'),
		long_description=_('If possible, the LDAP object class is removed when this extended attribute gets unset'),
		syntax=univention.admin.syntax.boolean,
	),
	'module': univention.admin.property(
		short_description=_('Modules to be extended'),
		long_description=_('Modules this extended attribute is added to, e.g. "users/user" or "computers/windows"'),
		syntax=univention.admin.syntax.univentionAdminModules,
		multivalue=True,
		required=True,
	),
	'version': univention.admin.property(
		short_description=_('Version of extended attribute'),
		long_description=_('The ABI number used by this extended attribute'),
		syntax=univention.admin.syntax.string,
		required=True,
		default='2',
	),
	'CLIName': univention.admin.property(
		short_description=_('UDM CLI name'),
		long_description=_('The name for the extended attribute as used by UDM CLI'),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		default='<name>',
	),
	'options': univention.admin.property(
		short_description=_('Required options'),
		long_description=_('This extended attribute is only used when at least one of these options is enabled, e.g. "posix" or "samba"'),
		syntax=univention.admin.syntax.string_numbers_letters_dots,
		multivalue=True,
	),
	'doNotSearch': univention.admin.property(
		short_description=_('Exclude from UMC search'),
		long_description=_('Values of this extended attribute are not available for searching in the UMC'),
		syntax=univention.admin.syntax.boolean,
	),
	'copyable': univention.admin.property(
		short_description=_('Copyable'),
		long_description=_('Values of this extended attribute are automatically filled into the form when copying a object.'),
		syntax=univention.admin.syntax.boolean,
		copyable=True,
	),
}

layout = [
	Tab(_('General'), _('General settings'), layout=[
		Group(_("Extended attribute description"), layout=[
			["name", "CLIName"],
		]),
		Group(_("Short description"), layout=[
			["shortDescription"],
			["translationShortDescription"],
		]),
		Group(_("Long Description"), layout=[
			["longDescription"],
			["translationLongDescription"]
		]),
	]),
	Tab(_('Module'), _('Configuration of the modules to be extended'), layout=[
		["module"],
		["options"],
		["hook"],
	]),
	Tab(_('LDAP mapping'), _('Configuration of LDAP object class and LDAP attribute'), layout=[
		["objectClass", "ldapMapping"],
		["deleteObjectClass"],
	]),
	Tab(_('UMC'), _('Settings for UMC'), layout=[
		Group(_('General extended attribute settings'), layout=[
			"disableUDMWeb",
			"doNotSearch"
		]),
		Group(_('Attribute layout'), layout=[
			["tabPosition", "overwritePosition"],
			["fullWidth"],
		]),
		Group(_('Tab layout'), layout=[
			["tabName"],
			["translationTabName"],
			["overwriteTab", "tabAdvanced"],
		]),
		Group(_('Group layout'), layout=[
			["groupName"],
			["translationGroupName"],
			["groupPosition"],
		]),
	]),
	Tab(_('Data type'), _('Data type definition'), layout=[
		["syntax", "default"],
		["multivalue"],
		["valueRequired"],
		["mayChange"],
		["notEditable"],
		["copyable"],
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('module', 'univentionUDMPropertyModule')
mapping.register('shortDescription', 'univentionUDMPropertyShortDescription', None, univention.admin.mapping.ListToString)
mapping.register('longDescription', 'univentionUDMPropertyLongDescription', None, univention.admin.mapping.ListToString)
mapping.register('objectClass', 'univentionUDMPropertyObjectClass', None, univention.admin.mapping.ListToString)
mapping.register('deleteObjectClass', 'univentionUDMPropertyDeleteObjectClass', None, univention.admin.mapping.ListToString)
mapping.register('default', 'univentionUDMPropertyDefault', None, univention.admin.mapping.ListToString)
mapping.register('syntax', 'univentionUDMPropertySyntax', None, univention.admin.mapping.ListToString)
mapping.register('hook', 'univentionUDMPropertyHook', None, univention.admin.mapping.ListToString)
mapping.register('ldapMapping', 'univentionUDMPropertyLdapMapping', None, univention.admin.mapping.ListToString)
mapping.register('multivalue', 'univentionUDMPropertyMultivalue', None, univention.admin.mapping.ListToString)
mapping.register('disableUDMWeb', 'univentionUDMPropertyLayoutDisable', None, univention.admin.mapping.ListToString)
mapping.register('tabName', 'univentionUDMPropertyLayoutTabName', None, univention.admin.mapping.ListToString)
mapping.register('tabPosition', 'univentionUDMPropertyLayoutPosition', None, univention.admin.mapping.ListToString)
mapping.register('groupName', 'univentionUDMPropertyLayoutGroupName', None, univention.admin.mapping.ListToString)
mapping.register('groupPosition', 'univentionUDMPropertyLayoutGroupPosition', None, univention.admin.mapping.ListToString)
mapping.register('tabAdvanced', 'univentionUDMPropertyLayoutTabAdvanced', None, univention.admin.mapping.ListToString)
mapping.register('overwriteTab', 'univentionUDMPropertyLayoutOverwriteTab', None, univention.admin.mapping.ListToString)
mapping.register('overwritePosition', 'univentionUDMPropertyLayoutOverwritePosition', None, univention.admin.mapping.ListToString)
mapping.register('fullWidth', 'univentionUDMPropertyLayoutFullWidth', None, univention.admin.mapping.ListToString)
mapping.register('mayChange', 'univentionUDMPropertyValueMayChange', None, univention.admin.mapping.ListToString)
mapping.register('valueRequired', 'univentionUDMPropertyValueRequired', None, univention.admin.mapping.ListToString)
mapping.register('notEditable', 'univentionUDMPropertyValueNotEditable', None, univention.admin.mapping.ListToString)
mapping.register('doNotSearch', 'univentionUDMPropertyDoNotSearch', None, univention.admin.mapping.ListToString)
mapping.register('copyable', 'univentionUDMPropertyCopyable', None, univention.admin.mapping.ListToString)
mapping.register('version', 'univentionUDMPropertyVersion', None, univention.admin.mapping.ListToString)
mapping.register('CLIName', 'univentionUDMPropertyCLIName', None, univention.admin.mapping.ListToString)
mapping.register('options', 'univentionUDMPropertyOptions')


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_pre_create(self):
		super(object, self)._ldap_pre_create()

		if 'users/user' in self['module'] and self['valueRequired'] == '1' and not self.info.get('default'):
			raise univention.admin.uexceptions.valueRequired(_('Extending the users module is only possible if a default value for a required value is given.'), property='default')

	def open(self):
		# univentionUDMPropertyTranslation;entry-de-de: Meine Kurzbeschreibung 9
		# univentionUDMPropertyTranslation;entry-en-gb: This is my short description9

		univention.admin.handlers.simpleLdap.open(self)

		for transKey in ['ShortDescription', 'LongDescription', 'TabName', 'GroupName']:
			translations = []
			for key in self.oldattr.keys():
				if key.startswith('univentionUDMPropertyTranslation%s;entry-' % transKey):
					lang = '%s_%s' % (key[-5:-3].lower(), key[-2:].upper())
					txt = self.oldattr.get(key)[0]
					translations.append((lang, txt))

			ud.debug(ud.ADMIN, ud.INFO, 'extended_attribute: added translations for %s: %s' % (transKey, str(translations)))
			self['translation%s' % transKey] = translations

		self.save()

	def _ldap_modlist(self):
		# univentionUDMPropertyShortTranslation;entry-de-de: Meine Kurzbeschreibung 9
		# univentionUDMPropertyShortTranslation;entry-en-gb: This is my short description9

		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)

		for transKey in ['ShortDescription', 'LongDescription', 'TabName', 'GroupName']:
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
						ml.append(('univentionUDMPropertyTranslation%s;entry-%s' % (transKey, lang), oldlist[lang], newlist[lang]))

		return ml

	@classmethod
	def unmapped_lookup_filter(cls):
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'univentionUDMProperty'),
			univention.admin.filter.expression('univentionUDMPropertyVersion', '2'),
		])


lookup = object.lookup


def identify(dn, attr, canonical=0):
	return 'univentionUDMProperty' in attr.get('objectClass', []) and attr.get('univentionUDMPropertyVersion', ['0'])[0] == '2'
