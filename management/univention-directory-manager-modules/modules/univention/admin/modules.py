#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
|UDM| access to handler modules.
"""
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

from __future__ import absolute_import

import os
import sys
import copy
import locale
import imp
import six
import ldap
from ldap.filter import filter_format

import univention.debug as ud
import univention.admin
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.hook
from univention.admin import localization
from univention.admin.layout import Tab, Group, ILayoutElement

import univention.config_registry
try:
	from typing import Any, Dict, List, Optional, Set, Tuple, Union  # noqa F401
	from typing_extensions import Protocol

	class UdmModule(Protocol):
		module = ''  # type: str
		operations = []  # type: List[str]
		property_descriptions = {}  # type: Dict[str, univention.admin.property]
		policy_apply_to = []  # type: List[str]
		policy_position_dn_prefix = ''  # type: str
		docleanup = 0  # type: int

		@staticmethod
		def identify(dn, attr):
			# type: (str, Dict[str, List[Any]]) -> bool
			pass
except ImportError:
	pass

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

translation = localization.translation('univention/admin')
_ = translation.translate

modules = {}  # type: Dict[str, UdmModule]
"""Mapping from module name to Python module."""
_superordinates = set()  # type: Set[str]
"""List of all module names (strings) that are _superordinates."""
containers = []  # type: List[UdmModule]


def update():
	# type: () -> None
	"""
	Scan file system and update internal list of |UDM| handler modules.
	"""
	global modules, _superordinates
	_modules = {}  # type: Dict[str, UdmModule]
	superordinates = set()  # type: Set[str]

	# since last update(), syntax.d and hooks.d may have changed (Bug #31154)
	univention.admin.syntax.import_syntax_files()
	univention.admin.hook.import_hook_files()

	def _walk(root, dir, files):
		# type: (str, str, List[str]) -> None
		for file in files:
			if not file.endswith('.py') or file.startswith('__'):
				continue
			p = os.path.join(dir, file).replace(root, '').replace('.py', '')
			p = p[1:]
			ud.debug(ud.ADMIN, ud.INFO, 'admin.modules.update: importing "%s"' % p)
			if dir.startswith('/usr/lib/pymodules/python2.7/'):
				ud.debug(ud.ADMIN, ud.INFO, 'Warning: still importing code from /usr/lib/pymodules/python2.7. Migration to dh_python is necessary!')
			parts = p.split(os.path.sep)
			mod, name = '.'.join(parts), '/'.join(parts)
			m = __import__(mod, globals(), locals(), name)
			m.initialized = 0
			if not hasattr(m, 'module'):
				ud.debug(ud.ADMIN, ud.ERROR, 'admin.modules.update: attribute "module" is missing in module %r' % (mod,))
				continue
			_modules[m.module] = m
			if isContainer(m):
				containers.append(m)

			superordinates.update(superordinate_names(m))

	for p in sys.path:
		dir = os.path.join(p, 'univention/admin/handlers')
		if not os.path.isdir(dir):
			continue
		os.path.walk(dir, _walk, p)
	modules = _modules
	_superordinates = superordinates

	# since last update(), syntax.d may have new choices
	# put here as one syntax wants to provide all modules
	univention.admin.syntax.update_choices()


def get(module):
	# type: (Union[UdmModule, str]) -> Optional[UdmModule]
	"""
	Get |UDM| module.

	:param module: either the name (str) of a module or the module itself.
	:returns: the module or `None` if no module exists with the requested name.
	"""
	global modules
	if not module:
		return None
	if isinstance(module, six.string_types):
		return modules.get(module)
	return module


def get_module(module):
	# type: (Union[UdmModule, str]) -> Optional[UdmModule]
	"""
	interim function, must only be used by `univention-directory-manager-modules`!

	.. deprecated :: UCS 4.4

	:param module: either the name (str) of a module or the module itself.
	:returns: the module or `None` if no module exists with the requested name.
	"""
	if not modules:
		ud.debug(ud.ADMIN, ud.WARN, 'univention.admin.modules.update() was not called')
		update()
	return get(module)


def init(lo, position, module, template_object=None, force_reload=False):
	# X-type: (univention.admin.uldap.access, univention.admin.uldap.position, UdmModule, univention.admin.handlers.simpleLdap, bool) -> None
	"""
	Initialize |UDM| handler module.

	:param lo: |LDAP| connection.
	:param position: |UDM| position instance.
	:param module: |UDM| handler module.
	:param template_object: Reference to a instance, from which the default values are used.
	:param force_reload: With `True` force Python to reload the module from the file system.
	"""
	# you better do a reload if init is called a second time
	# especially because update_extended_attributes
	# called twice will have side-effects
	if force_reload:
		imp.reload(module)
	# reset property descriptions to defaults if possible
	if hasattr(module, 'default_property_descriptions'):
		module.property_descriptions = copy.deepcopy(module.default_property_descriptions)
		# ud.debug(ud.ADMIN, ud.INFO, 'modules_init: reset default descriptions')

	# overwrite property descriptions
	univention.admin.ucr_overwrite_properties(module, lo)

	# check for properties with the syntax class LDAP_Search
	for pname, prop in module.property_descriptions.items():
		if prop.syntax.name == 'LDAP_Search':
			prop.syntax._load(lo)
			if prop.syntax.viewonly:
				module.mapping.unregister(pname, False)
		elif univention.admin.syntax.is_syntax(prop.syntax, univention.admin.syntax.complex) and hasattr(prop.syntax, 'subsyntaxes'):
			for text, subsyn in prop.syntax.subsyntaxes:
				if subsyn.name == 'LDAP_Search':
					subsyn._load(lo)

	# add new properties
	update_extended_options(lo, module, position)
	update_extended_attributes(lo, module, position)

	# get defaults from template
	if template_object:
		ud.debug(ud.ADMIN, ud.INFO, 'modules_init: got template object %s' % template_object.dn)
		template_object.open()

		# add template ext. attr. defaults
		if hasattr(template_object, 'property_descriptions'):
			for property_name, property in template_object.property_descriptions.items():
				if not (property_name == "name" or property_name == "description"):
					default = property.base_default
					if default and property_name in module.property_descriptions:
						if property.multivalue:
							if module.property_descriptions[property_name].multivalue:
								module.property_descriptions[property_name].base_default = []
								for i in range(0, len(default)):
									module.property_descriptions[property_name].base_default.append(default[i])
						else:
							module.property_descriptions[property_name].base_default = default
						ud.debug(ud.ADMIN, ud.INFO, "modules.init: added template default (%s) to property %s" % (property.base_default, property_name))

		# add template defaults
		for key in template_object.keys():
			if not (key == "name" or key == "description"):  # these keys are part of the template itself
				if key == '_options':
					if template_object[key] != [''] and template_object[key] != []:
						for option in module.options.keys():
							module.options[option].default = option in template_object[key]
					else:
						for option in module.options.keys():
							module.options[option].default = True
				else:
					if template_object.descriptions[key].multivalue:
						if module.property_descriptions[key].multivalue:
							module.property_descriptions[key].base_default = []
							for i in range(0, len(template_object[key])):
								module.property_descriptions[key].base_default.append(template_object[key][i])
						else:
							ud.debug(ud.ADMIN, ud.INFO, 'modules.init: template and object values not both multivalue !!')

					else:
						module.property_descriptions[key].base_default = template_object[key]
					module.property_descriptions[key].templates.append(template_object)
		ud.debug(ud.ADMIN, ud.INFO, 'modules_init: module.property_description after template: %s' % module.property_descriptions)
	else:
		ud.debug(ud.ADMIN, ud.INFO, 'modules_init: got no template')

	# re-build layout if there any overwrites defined
	univention.admin.ucr_overwrite_module_layout(module)

	# some choices depend on extended_options/attributes
	univention.admin.syntax.update_choices()

	module.initialized = 1


def update_extended_options(lo, module, position):
	# X-type: (univention.admin.uldap.access, UdmModule, univention.admin.uldap.position) -> None
	"""
	Overwrite options defined via |LDAP|.
	"""

	# get current language
	lang = locale.getlocale(locale.LC_MESSAGES)[0]
	ud.debug(ud.ADMIN, ud.INFO, 'modules update_extended_options: LANG=%s' % lang)

	module_filter = filter_format('(univentionUDMOptionModule=%s)', [name(module)])
	if name(module) == 'settings/usertemplate':
		module_filter = '(|(univentionUDMOptionModule=users/user)%s)' % (module_filter,)

	# append UDM extended options
	for dn, attrs in lo.search(base=position.getDomainConfigBase(), filter='(&(objectClass=univentionUDMOption)%s)' % (module_filter,)):
		oname = attrs['cn'][0]
		shortdesc = _get_translation(lang, attrs, 'univentionUDMOptionTranslationShortDescription;entry-%s', 'univentionUDMOptionShortDescription')
		longdesc = _get_translation(lang, attrs, 'univentionUDMOptionTranslationLongDescription;entry-%s', 'univentionUDMOptionLongDescription')
		default = attrs.get('univentionUDMOptionDefault', ['0'])[0] == '1'
		editable = attrs.get('univentionUDMOptionEditable', ['0'])[0] == '1'
		classes = attrs.get('univentionUDMOptionObjectClass', [])
		is_app_option = attrs.get('univentionUDMOptionIsApp', ['0'])[0] == '1'

		if not hasattr(module, 'options'):
			module.options = {}
		module.options[oname] = univention.admin.option(
			short_description=shortdesc,
			long_description=longdesc,
			default=default,
			editable=editable,
			objectClasses=classes,
			is_app_option=is_app_option)


class EA_Layout(dict):
	"""
	Extended attribute layout.
	"""

	def __init__(self, **kwargs):
		dict.__init__(self, kwargs)

	@property
	def name(self):
		# type: () -> str
		return self.get('name', '')

	@property
	def overwrite(self):
		# type: () -> Optional[str]
		return self.get('overwrite', None)

	@property
	def tabName(self):
		# type: () -> str
		return self.get('tabName', '')

	@property
	def groupName(self):
		# type: () -> str
		return self.get('groupName', '')

	@property
	def position(self):
		# type: () -> int
		return self.get('position', -1)

	@property
	def groupPosition(self):
		# type: () -> int
		return self.get('groupPosition', -1)

	@property
	def advanced(self):
		# type: () -> bool
		return self.get('advanced', False)

	@property
	def is_app_tab(self):
		# type: () -> bool
		return self.get('is_app_tab', False)

	def __cmp__(self, other):
		return cmp(self.groupName, other.groupName) or cmp(self.position, other.position)


def update_extended_attributes(lo, module, position):
	# X-type: (univention.admin.uldap.access, UdmModule, univention.admin.uldap.position) -> None
	"""
	Load extended attribute from |LDAP| and modify |UDM| handler.
	"""
	# add list of tabnames created by extended attributes
	if not hasattr(module, 'extended_attribute_tabnames'):
		module.extended_attribute_tabnames = []

	# append UDM extended attributes
	properties4tabs = {}  # type: Dict[str, List[EA_Layout]]
	overwriteTabList = []  # type: List[str]
	module.extended_udm_attributes = []  # type: List[univention.admin.extended_attribute]

	module_filter = filter_format('(univentionUDMPropertyModule=%s)', [name(module)])
	if name(module) == 'settings/usertemplate':
		module_filter = '(|(univentionUDMPropertyModule=users/user)%s)' % (module_filter,)

	for dn, attrs in lo.search(base=position.getDomainConfigBase(), filter='(&(objectClass=univentionUDMProperty)%s(univentionUDMPropertyVersion=2))' % (module_filter,)):
		# get CLI name
		pname = attrs['univentionUDMPropertyCLIName'][0]
		object_class = attrs.get('univentionUDMPropertyObjectClass', [])[0]
		if name(module) == 'settings/usertemplate' and object_class == 'univentionMail' and 'settings/usertemplate' not in attrs.get('univentionUDMPropertyModule', []):
			continue  # since "mail" is a default option, creating a usertemplate with any mail attribute would raise Object class violation: object class 'univentionMail' requires attribute 'uid'

		# get syntax
		propertySyntaxString = attrs.get('univentionUDMPropertySyntax', [''])[0]
		if propertySyntaxString and hasattr(univention.admin.syntax, propertySyntaxString):
			propertySyntax = getattr(univention.admin.syntax, propertySyntaxString)
		else:
			if lo.search(filter=filter_format(univention.admin.syntax.LDAP_Search.FILTER_PATTERN, [propertySyntaxString])):
				propertySyntax = univention.admin.syntax.LDAP_Search(propertySyntaxString)
			else:
				propertySyntax = univention.admin.syntax.string()

		# get hooks
		propertyHookString = attrs.get('univentionUDMPropertyHook', [''])[0]
		propertyHook = None
		if propertyHookString and hasattr(univention.admin.hook, propertyHookString):
			propertyHook = getattr(univention.admin.hook, propertyHookString)()
		register_ldap_connection = getattr(propertyHook, 'hook_ldap_connection', None)
		if register_ldap_connection:
			register_ldap_connection(lo, position)

		# get default value
		propertyDefault = attrs.get('univentionUDMPropertyDefault', [None])

		# value may change
		try:
			mayChange = int(attrs.get('univentionUDMPropertyValueMayChange', ['0'])[0])
		except:
			ud.debug(ud.ADMIN, ud.ERROR, 'modules update_extended_attributes: ERROR: processing univentionUDMPropertyValueMayChange threw exception - assuming mayChange=0')
			mayChange = 0

		# value is editable (only via hooks or direkt module.info[] access)
		editable = attrs.get('univentionUDMPropertyValueNotEditable', ['0'])[0] not in ['1', 'TRUE']

		copyable = attrs.get('univentionUDMPropertyCopyable', ['0'])[0] not in ['1', 'TRUE']

		# value is required
		valueRequired = (attrs.get('univentionUDMPropertyValueRequired', ['0'])[0].upper() in ['1', 'TRUE'])

		# value not available for searching
		try:
			doNotSearch = int(attrs.get('univentionUDMPropertyDoNotSearch', ['0'])[0])
		except:
			ud.debug(ud.ADMIN, ud.ERROR, 'modules update_extended_attributes: ERROR: processing univentionUDMPropertyDoNotSearch threw exception - assuming doNotSearch=0')
			doNotSearch = 0

		# check if CA is multivalue property
		if attrs.get('univentionUDMPropertyMultivalue', [''])[0] == '1':
			multivalue = 1
			map_method = None
			unmap_method = None
		else:
			multivalue = 0
			map_method = univention.admin.mapping.ListToString
			unmap_method = None
			if propertySyntaxString == 'boolean':
				map_method = univention.admin.mapping.BooleanListToString
				unmap_method = univention.admin.mapping.BooleanUnMap
			# single value ==> use only first value
			propertyDefault = propertyDefault[0]

		# Show this attribute in UDM/UMC?
		if attrs.get('univentionUDMPropertyLayoutDisable', [''])[0] == '1':
			layoutDisabled = True
		else:
			layoutDisabled = False

		# get current language
		lang = locale.getlocale(locale.LC_MESSAGES)[0]
		ud.debug(ud.ADMIN, ud.INFO, 'modules update_extended_attributes: LANG = %s' % str(lang))

		# get descriptions
		shortdesc = _get_translation(lang, attrs, 'univentionUDMPropertyTranslationShortDescription;entry-%s', 'univentionUDMPropertyShortDescription')
		longdesc = _get_translation(lang, attrs, 'univentionUDMPropertyTranslationLongDescription;entry-%s', 'univentionUDMPropertyLongDescription')

		# create property
		fullWidth = (attrs.get('univentionUDMPropertyLayoutFullWidth', ['0'])[0].upper() in ['1', 'TRUE'])
		module.property_descriptions[pname] = univention.admin.property(
			short_description=shortdesc,
			long_description=longdesc,
			syntax=propertySyntax,
			multivalue=multivalue,
			options=attrs.get('univentionUDMPropertyOptions', []),
			required=valueRequired,
			may_change=mayChange,
			dontsearch=doNotSearch,
			identifies=False,
			default=propertyDefault,
			editable=editable,
			copyable=copyable,
			size='Two' if fullWidth else None,
		)

		# add LDAP mapping
		if attrs['univentionUDMPropertyLdapMapping'][0].lower() != 'objectClass'.lower():
			module.mapping.register(pname, attrs['univentionUDMPropertyLdapMapping'][0], unmap_method, map_method)
		else:
			module.mapping.register(pname, attrs['univentionUDMPropertyLdapMapping'][0], univention.admin.mapping.nothing, univention.admin.mapping.nothing)

		if hasattr(module, 'layout'):
			tabname = _get_translation(lang, attrs, 'univentionUDMPropertyTranslationTabName;entry-%s', 'univentionUDMPropertyLayoutTabName', _('Custom'))
			overwriteTab = (attrs.get('univentionUDMPropertyLayoutOverwriteTab', ['0'])[0].upper() in ['1', 'TRUE'])
			# in the first generation of extended attributes of version 2
			# this field was a position defining the attribute to
			# overwrite. now it is the name of the attribute to overwrite
			overwriteProp = attrs.get('univentionUDMPropertyLayoutOverwritePosition', [''])[0]
			if overwriteProp == '0':
				overwriteProp = None
			deleteObjectClass = (attrs.get('univentionUDMPropertyDeleteObjectClass', ['0'])[0].upper() in ['1', 'TRUE'])
			tabAdvanced = (attrs.get('univentionUDMPropertyLayoutTabAdvanced', ['0'])[0].upper() in ['1', 'TRUE'])

			groupname = _get_translation(lang, attrs, 'univentionUDMPropertyTranslationGroupName;entry-%s', 'univentionUDMPropertyLayoutGroupName')
			try:
				groupPosition = int(attrs.get('univentionUDMPropertyLayoutGroupPosition', ['-1'])[0])
			except TypeError:
				groupPosition = 0

			ud.debug(ud.ADMIN, ud.INFO, 'update_extended_attributes: extended attribute (LDAP): %s' % str(attrs))

			# only one is possible ==> overwriteTab wins
			if overwriteTab and overwriteProp:
				overwriteProp = None

			# add tab name to list if missing
			if tabname not in properties4tabs and not layoutDisabled:
				properties4tabs[tabname] = []
				ud.debug(ud.ADMIN, ud.INFO, 'modules update_extended_attributes: custom fields init for tab %s' % tabname)

			# remember tab for purging if required
			if overwriteTab and tabname not in overwriteTabList and not layoutDisabled:
				overwriteTabList.append(tabname)

			if not layoutDisabled:
				# get position on tab
				# -1 == append on top
				priority = attrs.get('univentionUDMPropertyLayoutPosition', ['-1'])[0]
				try:
					priority = int(priority)
					if priority < 1:
						priority = -1
				except ValueError:
					ud.debug(ud.ADMIN, ud.WARN, 'modules update_extended_attributes: custom field for tab %s: failed to convert tabNumber to int' % tabname)
					priority = -1

				if priority == -1 and properties4tabs[tabname]:
					priority = max([-1, min((ea_layout.position for ea_layout in properties4tabs[tabname])) - 1])

				properties4tabs[tabname].append(EA_Layout(
					name=pname,
					tabName=tabname,
					position=priority,
					advanced=tabAdvanced,
					overwrite=overwriteProp,
					fullWidth=fullWidth,
					groupName=groupname,
					groupPosition=groupPosition,
					is_app_tab=any(option in [key for (key, value) in getattr(module, 'options', {}).items() if value.is_app_option] for option in attrs.get('univentionUDMPropertyOptions', [])),
				))
			else:
				for tab in getattr(module, 'layout', []):
					tab.remove(pname)

			module.extended_udm_attributes.append(univention.admin.extended_attribute(
				name=pname,
				objClass=object_class,
				ldapMapping=attrs['univentionUDMPropertyLdapMapping'][0],
				deleteObjClass=deleteObjectClass,
				syntax=propertySyntaxString,
				hook=propertyHook
			))

	# overwrite tabs that have been added by UDM extended attributes
	for tab in module.extended_attribute_tabnames:
		if tab not in overwriteTabList:
			overwriteTabList.append(tab)

	if properties4tabs:
		# remove layout of tabs that have been marked for replacement
		for tab in module.layout:
			if tab.label in overwriteTabList:
				tab.layout = []

		for tabname, priofields in properties4tabs.items():
			priofields = sorted(priofields)
			currentTab = None
			# get existing fields if tab has not been overwritten
			for tab in module.layout:
				if tab.label == tabname:
					# found tab in layout
					currentTab = tab
					# tab found ==> leave loop
					break
			else:
				# tab not found in current layout, so add it
				currentTab = Tab(tabname, tabname, advanced=True)
				module.layout.append(currentTab)
				# remember tabs that have been added by UDM extended attributes
				if tabname not in module.extended_attribute_tabnames:
					module.extended_attribute_tabnames.append(tabname)

			currentTab.is_app_tab = any(x.is_app_tab for x in priofields)

			# check if tab is empty ==> overwritePosition is impossible
			freshTab = len(currentTab.layout) == 0

			for ea_layout in priofields:
				if currentTab.advanced and not ea_layout.advanced:
					currentTab.advanced = False

				# if groupName is set check if it exists, otherwise create it
				if ea_layout.groupName:
					for item in currentTab.layout:
						if isinstance(item, ILayoutElement) and item.label == ea_layout.groupName:
							break
					else:  # group does not exist
						grp = Group(ea_layout.groupName)
						if ea_layout.groupPosition > 0:
							currentTab.layout.insert(ea_layout.groupPosition - 1, grp)
						else:
							currentTab.layout.append(grp)

				# - existing property shall be overwritten AND
				# - tab is not new and has not been cleaned before AND
				# - position >= 1 (top left position is defined as 1) AND
				# - old property with given position exists

				if currentTab.exists(ea_layout.name):
					continue
				elif ea_layout.overwrite and not freshTab:  # we want to overwrite an existing property
					# in the global fields ...
					if not ea_layout.groupName:
						replaced, layout = currentTab.replace(ea_layout.overwrite, ea_layout.name, recursive=True)
						if not replaced:  # the property was not found so we'll append it
							currentTab.layout.append(ea_layout.name)
					else:
						for item in currentTab.layout:
							if isinstance(item, ILayoutElement) and item.label == ea_layout.groupName:
								replaced, layout = item.replace(ea_layout.overwrite, ea_layout.name)
								if not replaced:  # the property was not found so we'll append it
									item.layout.append(ea_layout.name)
				else:
					if not ea_layout.groupName:
						currentTab.insert(ea_layout.position, ea_layout.name)
					else:
						for item in currentTab.layout:
							if isinstance(item, ILayoutElement) and item.label == ea_layout.groupName:
								item.insert(ea_layout.position, ea_layout.name)
								break

	# check for properties with the syntax class LDAP_Search
	for pname, prop in module.property_descriptions.items():
		if prop.syntax.name == 'LDAP_Search':
			prop.syntax._load(lo)
			if prop.syntax.viewonly:
				module.mapping.unregister(pname, False)
		elif univention.admin.syntax.is_syntax(prop.syntax, univention.admin.syntax.complex) and hasattr(prop.syntax, 'subsyntaxes'):
			for text, subsyn in prop.syntax.subsyntaxes:
				if subsyn.name == 'LDAP_Search':
					subsyn._load(lo)


def identify(dn, attr, module_name='', canonical=0, module_base=None):
	# type: (str, Dict[str, List[Any]], str, int, Optional[str]) -> List[UdmModule]
	"""
	Return list of |UDM| handlers capable of handling the given |LDAP| object.

	:param dn: |DN| of the |LDAP| object.
	:param atr: |LDAP| attributes.
	:param module_name: If given only the given module name is used if it is capable to handle the object.
	:param canonical: UNUSED!
	:param module_base: Optional string the module names must start with.
	:returns: the list of |UDM| modules.
	"""
	global modules
	res = []  # type: List[UdmModule]
	if 'univentionObjectType' in attr and attr['univentionObjectType'] and attr['univentionObjectType'][0] in modules:
		res.append(modules.get(attr['univentionObjectType'][0]))
	else:
		for name, module in modules.items():
			if module_base is not None and not name.startswith(module_base):
				continue
			if not hasattr(module, 'identify'):
				ud.debug(ud.ADMIN, ud.INFO, 'module %s does not provide identify' % module)
				continue

			if (not module_name or module_name == module.module) and module.identify(dn, attr):
				res.append(module)
	if not res:
		ud.debug(ud.ADMIN, ud.INFO, 'object could not be identified')
	for r in res:
		ud.debug(ud.ADMIN, ud.INFO, 'identify: found module %s on %s' % (r.module, dn))
	return res


def identifyOne(dn, attr, type=''):
	# type: (str, Dict[str, List[Any]], str) -> Optional[UdmModule]
	"""
	Return the |UDM| handler capable of handling the given |LDAP| object.

	:param dn: |DN| of the |LDAP| object.
	:param atr: |LDAP| attributes.
	:param type: If given only the given module name is used if it is capable to handle the object.
	:returns: the |UDM| modules or `None`.
	"""
	res = identify(dn, attr, type)
	if len(res) != 1:
		return None
	else:
		return res[0]


def recognize(module_name, dn, attr):
	module = get(module_name)
	if not hasattr(module, 'identify'):
		return False
	return module.identify(dn, attr)


def name(module):
	"""
	Return name of module.
	"""
	if not module:
		return ''
	return get(module).module


def superordinate_names(module_name):
	"""
	Return name of superordinate module.
	"""
	module = get(module_name)
	names = getattr(module, 'superordinate', [])
	if isinstance(names, basestring):
		names = [names]
	return names


def superordinate_name(module_name):
	"""
	Return name of first superordinate module.

	.. deprecated :: UCS 4.2
		Use :py:func:`superordinate_names` instead.
	"""
	names = superordinate_names(module_name)
	return names[0] if names else None


def superordinate(module):
	"""
	Return instance of superordinate module.

	.. deprecated :: UCS 4.2
		Use :py:func:`superordinates` instead.
	"""
	return get(superordinate_name(module))


def superordinates(module):
	"""
	Return instance of superordinate module.
	"""
	return [get(x) for x in superordinate_names(module)]


def subordinates(module):
	# type: (Any) -> List[UdmModule]
	"""
	Return list of instances of subordinate modules.

	:param module: ???
	:returns: list of |UDM| handler modules.
	"""
	return [mod for mod in modules.values() if name(module) in superordinate_names(mod) and not isContainer(mod)]


def find_superordinate(dn, co, lo):
	# type: (str, univention.admin.config, univention.admin.uldap.access) -> Optional[UdmModule]
	"""
	For a given |DN|, search in the |LDAP| path whether this LDAP object is
	below an object that is a superordinate or is a superordinate itself.

	:param dn: |DN|.
	:param co: |UDM| configuation object.
	:param lo: |LDAP| connection.
	:returns: the superordinate module or `None`.
	"""
	# walk up the ldap path and stop if we find an object type that is a superordinate
	while dn:
		attr = lo.get(dn)
		module = identifyOne(dn, attr)
		if isSuperordinate(module):
			return get(module)
		dn = lo.parentDn(dn)
	return None


def layout(module_name, object=None):
	"""return layout of properties"""
	module = get(module_name)
	defining_layout = None
	if object:
		ud.debug(ud.ADMIN, ud.ALL, 'modules.py layout: got a defined object')

	if object and hasattr(object, 'layout'):  # for dynamic modules like users/self
		ud.debug(ud.ADMIN, ud.ALL, 'modules.py layout:: layout is defined by the object')
		defining_layout = object.layout
	elif hasattr(module, 'layout'):
		defining_layout = module.layout
		ud.debug(ud.ADMIN, ud.ALL, 'modules.py layout:: layout is defined by the module')

	if defining_layout:
		if object and hasattr(object, 'options'):
			layout = []
			for tab in defining_layout:
				empty = True
				fields = []
				for line in tab.layout:
					nline = []
					for row in line:
						single = False
						nrow = []
						if isinstance(row, basestring):
							single = True
							row = [row]
						for field in row:
							prop = module.property_descriptions[field]
							nrow.append(field)
							if not prop.options or [opt for opt in prop.options if opt in object.options]:
								if not prop.license or [license for license in prop.license if license in object.lo.licensetypes]:
									empty = False
						if nrow:
							if single:
								nrow = nrow[0]
							nline.append(nrow)
					if nline:
						fields.append(nline)
				if fields and not empty:
					ntab = copy.deepcopy(tab)
					ntab.layout = fields
					layout.append(ntab)
			ud.debug(ud.ADMIN, ud.ALL, 'modules.py layout:: return layout decreased by given options')
			return layout
		else:
			ud.debug(ud.ADMIN, ud.ALL, 'modules.py layout:: return defining_layout.')
			return defining_layout

	else:
		return []


def options(module_name):
	"""return options available for module"""
	module = get(module_name)
	return getattr(module, 'options', {})


def attributes(module_name):
	# type: (str) -> List[Dict[str, str]]
	"""
	Return attributes for module.

	:param module_name: the name of the |UDM| module, e.g. `users/user`.
	"""
	module = get(module_name)
	attributes = []
	for attribute in module.property_descriptions.keys():
		attributes.append({'name': attribute, 'description': module.property_descriptions[attribute].short_description})
	return attributes


def short_description(module_name):
	"""
	Return short description for module.

	:param module_name: the name of the |UDM| module, e.g. `users/user`.
	:returns: The short descriptive text.
	"""
	module = get(module_name)
	if hasattr(module, 'short_description'):
		return module.short_description
	modname = name(module)
	if modname:
		return modname
	return repr(module)


def policy_short_description(module_name):
	# type: (str) -> str
	"""
	Return short description for policy module primarily used for tab headers.

	:param module_name: the name of the |UDM| policy module, e.g. `policies/pwhistory`.
	:returns: The short descriptive text.
	"""
	module = get(module_name)
	return getattr(module, 'policy_short_description', short_description(module))


def long_description(module_name):
	# type: (str) -> str
	"""
	Return long description for module.

	:param module_name: the name of the |UDM| module, e.g. `users/user`.
	:returns: The long descriptive text.
	"""
	module = get(module_name)
	return getattr(module, 'long_description', short_description(module))


def childs(module_name):
	# type: (str) -> int
	"""
	Return whether module may have subordinate modules.

	:param module_name: the name of the |UDM| module, e.g. `users/user`.
	:returns: `1` if the module has children, `0` otherwise.
	"""
	module = get(module_name)
	return getattr(module, 'childs', 0)


def virtual(module_name):
	# type: (str) -> bool
	"""
	Return whether module may have subordinate modules.

	:param module_name: the name of the |UDM| module, e.g. `users/user`.
	:returns: `True` if the module is virtual, `False` otherwise.
	"""
	module = get(module_name)
	return getattr(module, 'virtual', False)


def lookup(module_name, co, lo, filter='', base='', superordinate=None, scope='base+one', unique=False, required=False, timeout=-1, sizelimit=0):
	"""
	Return objects of module that match the given criteria.

	:param module_name: the name of the |UDM| module, e.g. `users/user`.
	"""
	module = get(module_name)
	tmpres = []

	if hasattr(module, 'lookup'):
		tmpres = module.lookup(co, lo, filter, base=base, superordinate=superordinate, scope=scope, unique=unique, required=required, timeout=timeout, sizelimit=sizelimit)

	# check for 'None' items just in case...
	return [item for item in tmpres if item]


def quickDescription(module_name, dn):
	module = get(module_name)
	rdn = univention.admin.uldap.explodeDn(dn, 1)[0]
	return getattr(module, 'quickDescription', rdn)


def isSuperordinate(module):
	"""
	Check if the module is a |UDM| superoridnate module.

	:param module: A |UDM| handler class.
	:returns: `True` if the handler is a superoridnate module, `False` otherwise.
	"""
	return name(module) in _superordinates


def isContainer(module):
	"""
	Check if the module is a |UDM| container module.

	:param module: A |UDM| handler class.
	:returns: `True` if the handler is a container module, `False` otherwise.
	"""
	return name(module).startswith('container/')


def isPolicy(module):
	"""
	Check if the module is a |UDM| policy module.

	:param module: A |UDM| handler class.
	:returns: `True` if the handler is a policy module, `False` otherwise.
	"""
	return name(module).startswith('policies/')


def defaultPosition(module, superordinate=None):
	# type: (Any, Any) -> str
	"""
	Returns default position for object of module.

	:param module: A |UDM| handler class.
	:param superordinate: A optional superordinate |UDM| object instance.
	:returns: The |DN| of the container for the object.
	"""
	rdns = ['users', 'dns', 'dhcp', 'shares', 'printers']
	base = univention.admin.uldap.getBaseDN()
	if superordinate:
		return superordinate.dn
	start = name(module).split('/')[0]
	if start in rdns:
		return 'cn=%s,%s' % (ldap.dn.escape_dn_chars(start), base)
	return base


def supports(module_name, operation):
	# type: (str, str) -> bool
	"""
	Check if module supports operation

	:param module_name: the name of the |UDM| module, e.g. `users/user`.
	:param operation: the name of the operation, e.g. 'modify'.
	:returns: `True` if the operation is supported, `False` otherwise.
	"""
	module = get(module_name)
	if not hasattr(module, 'operations'):
		return True
	return operation in module.operations


def objectType(co, lo, dn, attr=None, modules=[], module_base=None):
	if not dn:
		return []
	if attr is None:
		attr = lo.get(dn)
		if not attr:
			return []
	if 'univentionObjectType' in attr and attr['univentionObjectType']:
		return attr['univentionObjectType']

	if not modules:
		modules = identify(dn, attr, module_base=module_base)

	return [name(mod) for mod in modules]


def objectShadowType(co, lo, dn, attr=None, modules=[]):
	res = []
	for type in objectType(co, lo, dn, attr, modules):
		if type and type.startswith('container/'):
			res.append(objectShadowType(co, lo, lo.parentDn(dn)))
		else:
			res.append(type)
	return res


def findObject(co, lo, dn, type, attr=None, module_base=None):
	if attr is None:
		attr = lo.get(dn)
		if not attr:
			return None
	ndn = dn
	nattr = attr
	while True:
		for module in identify(ndn, nattr):
			if module and module.module == type:
				s = superordinate(module)
				if s:
					so = findObject(co, lo, ndn, s)
				else:
					so = None
				return module.object(co, lo, ndn, superordinate=so)
		ndn = lo.parentDn(ndn)
		if not ndn:
			break
		nattr = lo.get(ndn)


def policyOc(module_name):
	# type: (str) -> str
	"""
	Return the |LDAP| objectClass used to store the policy.

	:param module_name: the name of the |UDM| policy module, e.g. `policies/pwhistory`.
	:returns: the objectClass.
	"""
	module = get(module_name)
	return getattr(module, 'policy_oc', '')


def policiesGroup(module_name):
	# type: (Union[UdmModule, str]) -> str
	"""
	Return the name of the group the |UDM| policy belongs to.

	:param module_name: the name of the |UDM| policy module, e.g. `policies/pwhistory`.
	:returns: the group name.
	"""
	module = get(module_name)
	return getattr(module, 'policies_group', 'top')


def policies():
	# type: () -> List
	global modules
	res = {}  # type: Dict[str, List[str]]
	for mod in modules.values():
		if not isPolicy(mod):
			continue
		if not name(mod) == 'policies/policy':
			res.setdefault(policiesGroup(mod), []).append(name(mod))
	if not res:
		return []
	policies = []
	groupnames = sorted(res.keys())
	for groupname in groupnames:
		members = sorted(res[groupname])
		policies.append(univention.admin.policiesGroup(id=groupname, members=members))
	return policies


def policyTypes(module_name):
	# type: (str) -> List[str]
	"""
	Returns a list of policy types applying to the given module.

	:param module_name: the name of the |UDM| module, e.g. `users/user`.
	:returns: a list of |UDM| policy modules, e.g. `policies/pwhistory`.
	"""
	global modules

	res = []  # type: List[str]

	if not module_name or module_name not in modules:
		return res
	for name, module in modules.items():
		if not name.startswith('policies/') or not hasattr(module, 'policy_apply_to'):
			continue
		if module_name in module.policy_apply_to:
			res.append(name)

	return res


def policyPositionDnPrefix(module_name):
	# type: (str) -> str
	"""
	Return the relative |DN| for a policy.

	:param module_name: the name of the |UDM| policy module, e.g. `policies/pwhistory`.
	:return: A |DN| string to append to the |LDAP| base to get the container for the policy.
	"""
	module = get(module_name)
	if not hasattr(module, 'policy_position_dn_prefix'):
		return ""
	policy_position_dn_prefix = module.policy_position_dn_prefix
	if policy_position_dn_prefix.endswith(','):
		policy_position_dn_prefix = policy_position_dn_prefix[:-1]
	return policy_position_dn_prefix


def defaultContainers(module):
	# type: (univention.admin.handlers.simpleLdap) -> List[str]
	"""
	Checks for the attribute default_containers that should contain a
	list of RDNs of default containers.

	:param module: |UDM|
	:returns: a list of DNs.
	"""
	base = configRegistry['ldap/base']
	return ['%s,%s' % (rdn, base) for rdn in getattr(module, 'default_containers', [])]


def childModules(module_name):
	# type: (str) -> List[str]
	"""
	Return child modules if module is a super module.

	:param module_name: the name of the |UDM| module, e.g. `users/user`.
	:returns: List of child module names.
	"""
	module = get(module_name)
	return copy.deepcopy(getattr(module, 'childmodules', []))


def _get_translation(locale, attrs, name, defaultname, default=''):
	if locale:
		locale = locale.replace('_', '-').lower()
		if name % (locale,) in attrs:
			return attrs[name % (locale,)][0]
		locale = locale.split('-', 1)[0]
		name_short_lang = name % (locale,)
		if name_short_lang in attrs:
			return attrs[name_short_lang][0]
		for key in attrs:
			if key.startswith(name_short_lang):
				return attrs[key][0]
	return attrs.get(defaultname, [default])[0]
