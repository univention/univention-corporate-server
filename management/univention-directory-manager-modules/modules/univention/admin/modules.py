#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  access to handler modules
#
# Copyright 2004-2011 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import os, sys, ldap, types, copy, locale
import univention.debug as ud
import univention.admin
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.hook
import univention.admin.localization
from univention.admin.layout import Tab, Group, ILayoutElement

translation=univention.admin.localization.translation('univention/admin')
_=translation.translate

modules={}
superordinates=set()  # list of all module names (strings) that are superordinates
containers=[]

def update():
	'''scan handler modules'''
	global modules, superordinates
	modules={}
	superordinates=set()

	def _walk(root, dir, files):
		global modules, superordinates
		for file in files:
			if not file.endswith('.py') or file.startswith('__'):
				continue
			p=os.path.join(dir, file).replace(root, '').replace('.py', '')
			p=p[1:]
			ud.debug(ud.ADMIN, ud.INFO, 'admin.modules.update: importing "%s"' % p)
			parts=p.split(os.path.sep)
			mod, name='.'.join(parts), '/'.join(parts)
			m=__import__(mod, globals(), locals(), name)
			m.initialized=0
			modules[m.module]=m
			if isContainer(m):
				containers.append(m)

			# update the list of superordinates
			superordinate = superordinate_name(m)
			if superordinate:
				superordinates.add(superordinate)


	for p in sys.path:
		dir=os.path.join(p, 'univention/admin/handlers')
		if not os.path.isdir(dir):
			continue
		os.path.walk(dir, _walk, p)

def get(module):
	'''if module is instance of module, return that; if module is string, return the
	corresponding instance of that module'''
	global modules
	if not module:
		return None
	if isinstance(module, types.StringTypes):
		return modules.get(module)
	return module

def init(lo, position, module, template_object=None):
	# reset property descriptions to defaults if possible
	if hasattr(module,'default_property_descriptions'):
		module.property_descriptions=copy.deepcopy(module.default_property_descriptions)
		#ud.debug(ud.ADMIN, ud.INFO, 'modules_init: reset default descriptions')

	# overwrite property descriptions
	univention.admin.ucr_overwrite_properties( module, lo )

	# append custom properties
	custom_fields = {}
	module.ldap_extra_objectclasses=[]
	for dn, attrs in lo.search(base=position.getDomainConfigBase(), filter='(&(objectClass=univentionAdminProperty)(univentionAdminPropertyModule=%s))' % name(module)):
		pname=attrs['cn'][0]
		propertySyntaxString=attrs.get('univentionAdminPropertySyntax', [''])[0]
		if propertySyntaxString and hasattr(univention.admin.syntax, propertySyntaxString):
			propertySyntax = getattr(univention.admin.syntax, propertySyntaxString)
		else:
			if lo.search( filter = univention.admin.syntax.LDAP_Search.FILTER_PATTERN % propertySyntaxString ):
				propertySyntax = univention.admin.syntax.LDAP_Search( propertySyntaxString )
			else:
				propertySyntax = univention.admin.syntax.string()

		propertyDefault = attrs.get('univentionAdminPropertyDefault', [''])[0]

		if attrs.get('univentionAdminPropertyMultivalue', [''])[0] == '1':
			multivalue=1
			map_method=None
		else:
			multivalue=0
			map_method=univention.admin.mapping.ListToString

		module.property_descriptions[pname]=univention.admin.property(
			short_description=attrs['univentionAdminPropertyShortDescription'][0],
			long_description=attrs.get('univentionAdminPropertyLongDescription',[''])[0],
			syntax=propertySyntax,
			multivalue=multivalue,
			options=[],
			required=0,
			may_change=1,
			dontsearch=1,
			identifies=0,
			default=propertyDefault
		)

		if attrs['univentionAdminPropertyLdapMapping'][0].upper() != 'ObjectClass'.upper():
			module.mapping.register(pname, attrs['univentionAdminPropertyLdapMapping'][0], None, map_method)
		else:
			module.mapping.register(pname, attrs['univentionAdminPropertyLdapMapping'][0], univention.admin.mapping.nothing, univention.admin.mapping.nothing)

		deleteValues=attrs.get('univentionAdminPropertyDeleteValues')
		if deleteValues:
			ud.debug(ud.ADMIN, ud.INFO, 'deleteValues %s' % deleteValues)
		else:
			ud.debug(ud.ADMIN, ud.INFO, 'No deleteValues')

		deleteObjectClass=0
		tabname = attrs.get('univentionAdminPropertyLayoutTabName',[_('Custom')])[0]
		if attrs.get('univentionAdminPropertyDeleteObjectClass'):
			deleteObjectClass=attrs.get('univentionAdminPropertyDeleteObjectClass')[0]
		if not custom_fields.has_key(tabname):
			custom_fields[tabname] = []
			ud.debug(ud.ADMIN, ud.INFO, 'modules init: custom fields init for Tab %s' % tabname)
		tabposition = attrs.get('univentionAdminPropertyLayoutPosition',['-1'])[0]
		try:
			tabposition = int(tabposition)
		except:
			ud.debug(ud.ADMIN, ud.WARN, 'modules init: custom field for tab %s: failed to convert tabNumber to int' % tabname)
		if tabposition == -1 and len(custom_fields[tabname]) > 0:
			for pos, el in custom_fields[tabname]:
				try:
					if int(pos) <= tabposition:
						tabposition = int(pos)-1
				except:
					ud.debug(ud.ADMIN, ud.WARN, 'modules init: custom field for tab %s: failed to set tabposition' % tabname)

		custom_fields[ tabname ].append( ( tabposition, pname ) )
		module.ldap_extra_objectclasses.extend( ([(attrs.get('univentionAdminPropertyObjectClass', [])[0], pname, propertySyntaxString, attrs['univentionAdminPropertyLdapMapping'][0], deleteValues, deleteObjectClass )]))

	if custom_fields:
		#if module.initialized: # reload custom attributes
		removetab = []
		for tab in module.layout:
			if tab.description in custom_fields.keys():
				removetab.append(tab)
		for tab in removetab:
			module.layout.remove(tab)
		for tabname in custom_fields.keys():
			priofields = custom_fields[tabname]
			priofields.sort()
			fields=[]
			lastfield = ''
			for (prio, field) in priofields:
				ud.debug(ud.ADMIN, ud.INFO, 'modules init: custom fields found prio %s'% prio)
				if not lastfield:
					lastfield = field
					lastprio = prio
				else:
					try:
						if int(prio) > int(lastprio)+1:
							fields.append([lastfield])
							ud.debug(ud.ADMIN, ud.INFO, 'modules init: single custom field added %s'% fields)
							lastfield = field
							lastprio = prio
						else:
							fields.append([lastfield,field])
							ud.debug(ud.ADMIN, ud.INFO, 'modules init: two custom fields added %s'% fields)
							lastfield = ''
							lastprio = ''
					except: # if int(prio) failes
						 fields.append([lastfield,field])
						 ud.debug(ud.ADMIN, ud.INFO, 'modules init: two custom fields added %s'% fields)
						 lastfield = ''
						 lastprio = ''

			if lastfield:
				fields.append([lastfield])
			module.layout.append( Tab( tabname, tabname, fields ) )
			ud.debug(ud.ADMIN, ud.INFO, 'modules init: one custom field added %s'% fields)

	# check for properties with the syntax class LDAP_Search
	for pname, prop in module.property_descriptions.items():
		if prop.syntax.name == 'LDAP_Search':
			prop.syntax._load( lo )
			if prop.syntax.viewonly:
				module.mapping.unregister( pname )
		elif univention.admin.syntax.is_syntax( prop.syntax, univention.admin.syntax.complex ) and hasattr( prop.syntax, 'subsyntaxes' ):
			for text, subsyn in prop.syntax.subsyntaxes:
				if subsyn.name == 'LDAP_Search':
					subsyn._load( lo )

	# add new properties
	update_extended_options(lo, module, position)
	update_extended_attributes( lo, module, position )

	# get defaults from template
	if template_object:
		ud.debug(ud.ADMIN, ud.INFO, 'modules_init: got template object %s' % template_object.dn)
		template_object.open()

		# add template ext. attr. defaults
		if hasattr(template_object, 'property_descriptions'):
			for property_name, property in template_object.property_descriptions.items():
				if not (property_name == "name" or property_name == "description"): 
					default = property.base_default
					if default and module.property_descriptions.has_key(property_name):
						if property.multivalue:
							if module.property_descriptions[property_name].multivalue:
								module.property_descriptions[property_name].base_default=[]
								for i in range(0,len(default)):
									module.property_descriptions[property_name].base_default.append(default[i])
						else:
							module.property_descriptions[property_name].base_default=default
						ud.debug(ud.ADMIN, ud.INFO, "modules.init: added template default (%s) to property %s" % (property.base_default, property_name))

		# add template defaults
		for key in template_object.keys():
			if not (key=="name" or key=="description"): # these keys are part of the template itself
				if key == '_options':
					if not template_object[key] == ['']:
						for option in module.options.keys():
							module.options[option].default = option in template_object[key]
					else:
						for option in module.options.keys():
							module.options[option].default = True
				else:
					if template_object.descriptions[key].multivalue:
						if module.property_descriptions[key].multivalue:
							module.property_descriptions[key].base_default=[]
							for i in range(0,len(template_object[key])):
								module.property_descriptions[key].base_default.append(template_object[key][i])
						else: ud.debug(ud.ADMIN, ud.INFO, 'modules.init: template and object values not both multivalue !!')

					else:
						module.property_descriptions[key].base_default=template_object[key]
					module.property_descriptions[key].templates.append(template_object)
		ud.debug(ud.ADMIN, ud.INFO, 'modules_init: module.property_description after template: %s' % module.property_descriptions)
	else:
		ud.debug(ud.ADMIN, ud.INFO, 'modules_init: got no template')


	# re-build layout if there any overwrites defined
	univention.admin.ucr_overwrite_module_layout( module )

	module.initialized=1

def update_extended_options(lo, module, position):
	"""Overwrite options defined via LDAP."""

	# get current language
	lang = locale.getlocale(locale.LC_MESSAGES)[0]
	ud.debug(ud.ADMIN, ud.INFO, 'modules update_extended_options: LANG=%s' % lang)
	if lang:
		lang = lang.replace('_','-').lower()
	else:
		lang = 'xxxxx'

	# append UDM extended options
	for dn, attrs in lo.search(base=position.getDomainConfigBase(), filter='(&(objectClass=univentionUDMOption)(univentionUDMOptionModule=%s))' % name(module)):
		oname = attrs['cn'][0]
		shortdesc = attrs.get('univentionUDMOptionTranslationShortDescription;entry-%s' % lang, attrs['univentionUDMOptionShortDescription'])[0]
		longdesc = attrs.get('univentionUDMOptionTranslationLongDescription;entry-%s' % lang, attrs.get('univentionUDMOptionLongDescription', ['']))[0]
		default = attrs.get('univentionUDMOptionDefault', ['0'])[0] == '1'
		editable = attrs.get('univentionUDMOptionEditable', ['0'])[0] == '1'
		classes = attrs.get('univentionUDMOptionObjectClass', [])

		module.options[oname] = univention.admin.option(
				short_description=shortdesc,
				long_description=longdesc,
				default=default,
				editable=editable,
				objectClasses=classes)

class EA_Layout( dict ):
	def __init__( self, **kwargs ):
		dict.__init__( self, kwargs )

	@property
	def name( self ):
		return self.get( 'name', '' )

	@property
	def fillWidth( self ):
		return self.get( 'fillWidth', False )

	@property
	def overwrite( self ):
		return self.get( 'overwrite', None )

	@property
	def tabName( self ):
		return self.get( 'tabName', '' )

	@property
	def groupName( self ):
		return self.get( 'groupName', '' )

	@property
	def position( self ):
		return self.get( 'position', -1 )

	@property
	def groupPosition( self ):
		return self.get( 'groupPosition', -1 )

	@property
	def advanced( self ):
		return self.get( 'advanced', False )

	def __cmp__( self, other ):
		if self.groupName < other.groupName:
			return -1
		if other.groupName < self.groupName:
			return 1
		if self.position < other.position:
			return -1
		if other.position < self.position:
			return 1
		return 0

def update_extended_attributes(lo, module, position):

	# add list of tabnames created by extended attributes
	if not hasattr(module, 'extended_attribute_tabnames'):
		module.extended_attribute_tabnames = []

	# append UDM extended attributes
	properties4tabs = {}
	overwriteTabList = []
	module.extended_udm_attributes = []
	for dn, attrs in lo.search( base = position.getDomainConfigBase(),
								filter='(&(objectClass=univentionUDMProperty)(univentionUDMPropertyModule=%s)(univentionUDMPropertyVersion=2))' % name(module) ):
		# get CLI name
		pname=attrs['univentionUDMPropertyCLIName'][0]

		# get syntax
		propertySyntaxString=attrs.get('univentionUDMPropertySyntax', [''])[0]
		if propertySyntaxString and hasattr(univention.admin.syntax, propertySyntaxString):
			propertySyntax = getattr(univention.admin.syntax, propertySyntaxString)
		else:
			if lo.search( filter = univention.admin.syntax.LDAP_Search.FILTER_PATTERN % propertySyntaxString ):
				propertySyntax = univention.admin.syntax.LDAP_Search( propertySyntaxString )
			else:
				propertySyntax = univention.admin.syntax.string()

		# get hooks
		propertyHookString=attrs.get('univentionUDMPropertyHook', [''])[0]
		propertyHook = None
		if propertyHookString and hasattr(univention.admin.hook, propertyHookString):
			propertyHook = getattr(univention.admin.hook, propertyHookString)()

		# get default value
		propertyDefault = attrs.get('univentionUDMPropertyDefault', [''])

		# value may change
		try:
			mayChange = int( attrs.get('univentionUDMPropertyValueMayChange', ['0'])[0] )
		except:
			ud.debug(ud.ADMIN, ud.ERROR, 'modules update_extended_attributes: ERROR: processing univentionUDMPropertyValueMayChange throwed exception - assuming mayChange=0')
			mayChange = 0

		# value is editable (only via hooks or direkt module.info[] access)
		editable = attrs.get('univentionUDMPropertyValueNotEditable', ['0'])[0] not in ['1', 'TRUE']

		# value is required
		valueRequired = ( attrs.get('univentionUDMPropertyValueRequired',[ '0' ])[0].upper() in [ '1', 'TRUE' ] )

		# value not available for searching
		try:
			doNotSearch = int( attrs.get('univentionUDMPropertyDoNotSearch',[ '0' ])[0] )
		except:
			ud.debug(ud.ADMIN, ud.ERROR, 'modules update_extended_attributes: ERROR: processing univentionUDMPropertyDoNotSearch throwed exception - assuming doNotSearch=0')
			doNotSearch = 0

		# check if CA is multivalue property
		if attrs.get('univentionUDMPropertyMultivalue', [''])[0] == '1':
			multivalue = 1
			map_method = None
		else:
			multivalue = 0
			map_method = univention.admin.mapping.ListToString
			# single value ==> use only first value
			propertyDefault = propertyDefault[0]

		# Show this attribute in UDM/UMC?
		if attrs.get('univentionUDMPropertyLayoutDisable', [''])[0] == '1':
			layoutDisabled = True
		else:
			layoutDisabled = False

		# get current language
		lang = locale.getlocale( locale.LC_MESSAGES )[0]
		ud.debug(ud.ADMIN, ud.INFO, 'modules update_extended_attributes: LANG = %s' % str(lang))
		if lang:
			lang = lang.replace('_','-').lower()
		else:
			lang = 'xxxxx'

		# get descriptions
		shortdesc = attrs.get('univentionUDMPropertyTranslationShortDescription;entry-%s' % lang, attrs['univentionUDMPropertyShortDescription'] )[0]
		longdesc = attrs.get('univentionUDMPropertyTranslationLongDescription;entry-%s' % lang, attrs.get('univentionUDMPropertyLongDescription', ['']))[0]

		# create property
		# FIXME: must add attribute to honor fullWidth (should be defined by the syntax)
		module.property_descriptions[pname] = univention.admin.property(
			short_description = shortdesc,
			long_description = longdesc,
			syntax = propertySyntax,
			multivalue = multivalue,
			options = attrs.get('univentionUDMPropertyOptions',[]),
			required = valueRequired,
			may_change = mayChange,
			dontsearch = doNotSearch,
			identifies = 0,
			default = propertyDefault,
			editable = editable
		)

		# add LDAP mapping
		if attrs['univentionUDMPropertyLdapMapping'][0].lower() != 'objectClass'.lower():
			module.mapping.register(pname, attrs['univentionUDMPropertyLdapMapping'][0], None, map_method)
		else:
			module.mapping.register(pname, attrs['univentionUDMPropertyLdapMapping'][0], univention.admin.mapping.nothing, univention.admin.mapping.nothing)


		if hasattr( module, 'layout' ):
			tabname = attrs.get('univentionUDMPropertyTranslationTabName;entry-%s' % lang, attrs.get('univentionUDMPropertyLayoutTabName',[ _('Custom') ]) )[0]
			overwriteTab = ( attrs.get('univentionUDMPropertyLayoutOverwriteTab',[ '0' ])[0].upper() in [ '1', 'TRUE' ] )
			# in the first generation of extended attributes of version 2
			# this field was a position defining the attribute to
			# overwrite. now it is the name of the attribute to overwrite
			overwriteProp = attrs.get( 'univentionUDMPropertyLayoutOverwritePosition', [ '' ] )[ 0 ]
			if overwriteProp == '0':
				overwriteProp = None
			fullWidth = ( attrs.get('univentionUDMPropertyLayoutFullWidth',[ '0' ])[0].upper() in [ '1', 'TRUE' ] )
			deleteObjectClass = ( attrs.get('univentionUDMPropertyDeleteObjectClass', ['0'])[0].upper() in [ '1', 'TRUE' ] )
			tabAdvanced = ( attrs.get('univentionUDMPropertyLayoutTabAdvanced',[ '0' ])[0].upper() in [ '1', 'TRUE' ] )

			groupname = attrs.get( 'univentionUDMPropertyTranslationGroupName;entry-%s' % lang, attrs.get( 'univentionUDMPropertyLayoutGroupName', [ '' ] ) )[ 0 ]
			try:
				groupPosition = int( attrs.get( 'univentionUDMPropertyLayoutGroupPosition', [ '-1' ] )[ 0 ] )
			except TypeError:
				groupPosition = 0

			ud.debug( ud.ADMIN, ud.INFO, 'update_extended_attributes: extended attribute (LDAP): %s' % str( attrs ) )

			# only one is possible ==> overwriteTab wins
			if overwriteTab and overwriteProp:
				overwriteProp = None

			# add tab name to list if missing
			if not tabname in properties4tabs and not layoutDisabled:
				properties4tabs[ tabname ] = []
				ud.debug(ud.ADMIN, ud.INFO, 'modules update_extended_attributes: custom fields init for tab %s' % tabname)

			# remember tab for purging if required
			if overwriteTab and not tabname in overwriteTabList and not layoutDisabled:
				overwriteTabList.append(tabname)

			if not layoutDisabled:
				# get position on tab
				# -1 == append on top
				tabPosition = attrs.get( 'univentionUDMPropertyLayoutPosition', [ '-1' ] )[ 0 ]
				try:
					tabPosition = int( tabPosition )
				except:
					ud.debug(ud.ADMIN, ud.WARN, 'modules update_extended_attributes: custom field for tab %s: failed to convert tabNumber to int' % tabname)
					tabPosition = -1

				if tabPosition == -1:
					for ea_layout in properties4tabs[ tabname ]:
						try:
							if ea_layout.position <= tabPosition:
								tabPosition = pos-1
						except:
							ud.debug(ud.ADMIN, ud.WARN, 'modules update_extended_attributes: custom field for tab %s: failed to set tabPosition' % tabname)

				properties4tabs[ tabname ].append( EA_Layout( name = pname, tabName = tabname, position = tabPosition, advanced = tabAdvanced, overwrite = overwriteProp, fullWidth = fullWidth, groupName = groupname, groupPosition = groupPosition ) )

			module.extended_udm_attributes.extend( [ univention.admin.extended_attribute( pname, attrs.get('univentionUDMPropertyObjectClass', [])[0],
																				  attrs['univentionUDMPropertyLdapMapping'][0], deleteObjectClass,
																				  propertySyntaxString,
																				  propertyHook ) ] )

	# overwrite tabs that have been added by UDM extended attributes
	for tab in module.extended_attribute_tabnames:
		if not tab in overwriteTabList:
			overwriteTabList.append(tab)

	if properties4tabs:
		lastprio = -1000

		# remove layout of tabs that have been marked for replacement
		removetab = []
		for tab in module.layout:
			if tab.label in overwriteTabList:
				tab.layout = []

		for tabname in properties4tabs.keys():
			priofields = properties4tabs[ tabname ]
			priofields.sort()
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
				currentTab = Tab( tabname, tabname, advanced = True )
				module.layout.append( currentTab )
				# remember tabs that have been added by UDM extended attributes
				if not tabname in module.extended_attribute_tabnames:
					module.extended_attribute_tabnames.append( tabname )

			# check if tab is empty ==> overwritePosition is impossible
			freshTab = len( currentTab.layout ) == 0

			for ea_layout in priofields:
				if currentTab.advanced and not ea_layout.advanced:
					currentTab.advanced = False

				# if groupName is set check if it exists, otherwise create it
				if ea_layout.groupName:
					for item in currentTab.layout:
						if isinstance( item, ILayoutElement ) and item.label == ea_layout.groupName:
							break
					else: # group does not exist
						grp = Group( ea_layout.groupName )
						if ea_layout.groupPosition > 0:
							currentTab.layout.insert( ea_layout.groupPosition - 1, grp )
						else:
							currentTab.layout.append( grp )

				# - existing property shall be overwritten AND
				# - tab is not new and has not been cleaned before AND
				# - position >= 1 (top left position is defined as 1) AND
				# - old property with given position exists

				if currentTab.exists( ea_layout.name ):
					continue
				elif ea_layout.overwrite and not freshTab: # we want to overwrite an existing property
					# in the global fields ...
					if not ea_layout.groupName:
						replaced, layout = currentTab.replace( ea_layout.overwrite, ea_layout.name, recursive = True )
						if not replaced: # the property was not found so we'll append it
							currentTab.layout.append( ea_layout.label )
					else:
						for item in currentTab.layout:
							if isinstance( item, ILayoutElement ) and item.label == ea_layout.groupName:
								replaced, layout = item.replace( ea_layout.overwrite, ea_layout.name )
								if not replaced: # the property was not found so we'll append it
									item.append( ea_layout.label )
				else:
					if not ea_layout.groupName:
						currentTab.insert( ea_layout.position, ea_layout.name )
					else:
						for item in currentTab.layout:
							if isinstance( item, ILayoutElement ) and item.label == ea_layout.groupName:
								item.insert( ea_layout.position, ea_layout.name )
								break


	# check for properties with the syntax class LDAP_Search
	for pname, prop in module.property_descriptions.items():
		if prop.syntax.name == 'LDAP_Search':
			prop.syntax._load( lo )
			if prop.syntax.viewonly:
				module.mapping.unregister( pname )
		elif univention.admin.syntax.is_syntax( prop.syntax, univention.admin.syntax.complex ) and hasattr( prop.syntax, 'subsyntaxes' ):
			for text, subsyn in prop.syntax.subsyntaxes:
				if subsyn.name == 'LDAP_Search':
					subsyn._load( lo )

def identify( dn, attr, module_name = '', canonical = 0, module_base = None ):

	global modules
	res=[]
	if 'univentionObjectType' in attr and attr[ 'univentionObjectType' ] and attr[ 'univentionObjectType' ][ 0 ] in modules:
		res.append( modules.get( attr[ 'univentionObjectType' ][ 0 ] ) )
	else:
		for name, module in modules.items():
			if module_base is not None and not name.startswith( module_base ):
				continue
			if not hasattr(module, 'identify'):
				ud.debug(ud.ADMIN, ud.INFO, 'module %s does not provide identify' % module)
				continue

			if ( not module_name or module_name == module.module ) and module.identify(dn, attr):
				res.append(module)
	if not res:
		ud.debug(ud.ADMIN, ud.INFO, 'object could not be identified')
	for r in res:
		ud.debug(ud.ADMIN, ud.INFO, 'identify: found module %s on %s'%(r.module,dn) )
	return res

def identifyOne(dn, attr, type=''):

	res=identify(dn, attr, type)
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
	'''return name of module'''
	if not module:
		return ''
	return get(module).module

def superordinate_name(module_name):
	'''return name of superordinate module'''
	module = get(module_name)
	return getattr(module, 'superordinate', '')

def superordinate(module):
	'''return instance of superordinate module'''
	return get(superordinate_name(module))

def subordinates(module):
	'''return list of instances of subordinate modules'''
	global modules
	return [mod for mod in modules.values()
		if superordinate_name(mod) == name(module) and not isContainer(mod)]

def find_superordinate( dn, co, lo ):
	'''For a given DN, search in the LDAP path whether this LDAP object is
	below an object that is a superordinate or is a superordinate itself.
	Returns the superordinate module or None.'''

	# walk up the ldap path and stop if we find an object type that is a superordinate
	while dn:
		attr = lo.get( dn )
		module = identifyOne(dn, attr) 
		if isSuperordinate(module):
			return get(module)
		dn = lo.parentDn( dn )
	return None

def layout(module_name, object=None):
	'''return layout of properties'''
	module = get(module_name)
	defining_layout = None
	if object:
		ud.debug(ud.ADMIN, ud.ALL, 'modules.py layout:: got an definied object')

	if object and hasattr(object, 'layout'): # for dynamic modules like users/self
		ud.debug(ud.ADMIN, ud.ALL, 'modules.py layout:: layout is defined by the object')
		defining_layout = object.layout
	elif hasattr(module, 'layout'):
		defining_layout = module.layout
		ud.debug(ud.ADMIN, ud.ALL, 'modules.py layout:: layout is defined by the module')

	if defining_layout:
		if object and hasattr(object, 'options'):
			layout = []
			for tab in defining_layout:
				empty  = True
				fields = []
				for line in tab.layout:
					nline = []
					for row in line:
						single = False
						nrow = []
						if isinstance( row, basestring ):
							single = True
							row = [row]
						for field in row:
							prop = module.property_descriptions[field]
							nrow.append( field )
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
					ntab=copy.deepcopy(tab)
					ntab.layout=fields
					layout.append(ntab)
			ud.debug(ud.ADMIN, ud.ALL, 'modules.py layout:: return layout decreased by given options')
			return layout
		else:
			ud.debug(ud.ADMIN, ud.ALL, 'modules.py layout:: return defining_layout.')
			return defining_layout

	else:
		return []

def options(module_name):
	'''return options available for module'''
	module=get(module_name)
	return getattr(module, 'options', {})

def attributes(module_name):
	'''return attributes for module'''
	module=get(module_name)
	attributes=[]
	for attribute in module.property_descriptions.keys():
		attributes.append( {'name': attribute, 'description': module.property_descriptions[ attribute ].short_description } )
	return attributes

def short_description(module_name):
	'''return short description for module'''
	module = get(module_name)
	if hasattr(module, 'short_description'):
		return module.short_description
	modname = name(module)
	if modname:
		return modname
	return repr(module)

def policy_short_description(module_name):
	'''return short description for policy module
	   primarily used for tab headers'''
	module = get(module_name)
	return getattr(module, 'policy_short_description', short_description(module))

def long_description(module_name):
	'''return long description for module'''
	module = get(module_name)
	return getattr(module, 'long_description', short_description(module))

def childs(module_name):
	'''return whether module may have subordinate modules'''
	module = get(module_name)
	return getattr(module, 'childs', 0)

def virtual(module_name):
	'''return whether module may have subordinate modules'''
	module = get(module_name)
	return getattr(module, 'virtual', False)

def lookup(module_name, co, lo, filter='', base='', superordinate=None, scope='base+one', unique=0, required=0, timeout=-1, sizelimit=0):
	'''return objects of module that match the given criteria'''
	module = get(module_name)
	tmpres=[]

	if hasattr(module, 'lookup'):
		tmpres=module.lookup(co, lo, filter, base=base, superordinate=superordinate, scope=scope, unique=unique, required=required, timeout=timeout, sizelimit=sizelimit)

	# check for 'None' items just in case...
	return [item for item in tmpres if item]

def quickDescription(module_name, dn):
	module = get(module_name)
	rdn = univention.admin.uldap.explodeDn(dn, 1)[0]
	return getattr(module, 'quickDescription', rdn)

def isSuperordinate(module):
	return name(module) in superordinates

def isContainer(module):
	return name(module).startswith('container/')

def isPolicy(module):
	return name(module).startswith('policies/')

def defaultPosition(module, superordinate=None):
	'''returns default position for object of module'''
	rdns = [ 'users', 'dns', 'dhcp', 'shares', 'printers' ]
	base = univention.admin.uldap.getBaseDN()
	if superordinate:
		return superordinate.dn
	start = name(module).split('/')[0]
	if start in rdns:
		return 'cn=%s,%s' % (start, base)
	return base

def supports(module_name, operation):
	'''check if module supports operation'''
	module = get(module_name)
	if not hasattr(module, 'operations'):
		return True
	return operation in module.operations

def objectType( co, lo, dn, attr = None, modules = [], module_base = None ):
	if not dn:
		return []
	if attr is None:
		attr = lo.get( dn )
		if not attr:
			return []
	if 'univentionObjectType' in attr and attr[ 'univentionObjectType' ]:
		return attr[ 'univentionObjectType' ]

	if not modules:
		modules = identify( dn, attr, module_base = module_base )

	return [ name( mod ) for mod in modules ]

def objectShadowType(co, lo, dn, attr=None, modules=[]):
	res=[]
	for type in objectType(co, lo, dn, attr, modules):
		if type and type.startswith('container/'):
			res.append(objectShadowType(co, lo, lo.parentDn(dn)))
		else:
			res.append(type)
	return res

def findObject( co, lo, dn, type, attr = None, module_base = None ):
	if attr is None:
		attr = lo.get( dn )
		if not attr:
			return None
	ndn=dn
	nattr=attr
	while 1:
		for module in identify( ndn, nattr ):
			if module and module.module == type:
				s=superordinate(module)
				if s:
					so=findObject(co, lo, ndn, s)
				else:
					so=None
				return module.object(co, lo, ndn, superordinate=so)
		ndn=lo.parentDn(ndn)
		if not ndn:
			break
		nattr=lo.get(ndn)

def policyOc(module_name):
	module = get(module_name)
	return getattr(module, 'policy_oc', '')

def policiesGroup(module_name):
	module = get(module_name)
	return getattr(module, 'policies_group', 'top')

def policies():
	global modules
	res={}
	for mod in modules.values():
		if not isPolicy(mod):
			continue
		if not name(mod) == 'policies/policy':
			res.setdefault(policiesGroup(mod), []).append(name(mod))
	if not res:
		return []
	policies=[]
	groupnames=res.keys()
	groupnames.sort()
	for groupname in groupnames:
		members=res[groupname]
		members.sort()
		policies.append(univention.admin.policiesGroup(id=groupname, members=members))
	return policies

def policyTypes( module_name ):
	"""Returns a list of policy types applying to the given module"""
	global modules

	res=[]

	if not module_name or not module_name in modules:
		return res
	for name, module in modules.items():
		if not name.startswith( 'policies/' ) or not hasattr( module, 'policy_apply_to' ):
			continue
		if module_name in module.policy_apply_to:
			res.append( name )

	return res

def policyPositionDnPrefix(module_name):
	module = get(module_name)
	if not hasattr(module, 'policy_position_dn_prefix'):
		return ""
	policy_position_dn_prefix=module.policy_position_dn_prefix
	if policy_position_dn_prefix.endswith(','):
		policy_position_dn_prefix=policy_position_dn_prefix[:-1]
	return policy_position_dn_prefix

def defaultContainers( module ):
	'''checks for the attribute default_containers that should contain a
	list of RDNs of default containers. This function returns a list of
	DNs.'''
	dns = []
	if hasattr( module, 'default_containers' ):
		rdns = module.default_containers
		base = univention.admin.uldap.getBaseDN()
		for rdn in rdns:
			dns.append( '%s,%s' % ( rdn, base ) )

	return dns

def wantsWizard(module_name):
	'''use module in wizard?'''
	module = get(module_name)
	return getattr(module, 'usewizard', False)

def wizardMenuString(module_name):
	module = get(module_name)
	menustring = getattr(module, 'wizardmenustring')
	if menustring:
		return menustring
	return short_description(module)

def wizardDescription(module_name):
	module = get(module_name)
	return getattr(module, 'wizarddescription', '')

def wizardPath(module_name):
	module = get(module_name)
	return getattr(module, 'wizardpath', '')

def wizardOperations(module_name):
	'''return wizard operations supported by module'''
	module = get(module_name)
	return getattr(module, 'wizardoperations', {"find":[_("Search"), _("Search object(s)")], "add":[_("Add"), _("Add object(s)")]})

def childModules(module_name):
	'''return child modules if module is a super module'''
	module = get(module_name)
	return copy.deepcopy( getattr(module, 'childmodules', []) )

univention.admin.syntax.import_syntax_files()
univention.admin.hook.import_hook_files()

# The update will cause in a recursion, see https://forge.univention.org/bugzilla/show_bug.cgi?id=22439
# update()

