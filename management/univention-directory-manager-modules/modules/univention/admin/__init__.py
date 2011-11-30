# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  basic functionality
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

import copy, types, string, re
import mapping
import univention.config_registry
import univention.debug

configRegistry=univention.config_registry.ConfigRegistry()
configRegistry.load()

# baseconfig legacy
baseConfig=configRegistry

# __path__.append("handlers")

def ucr_overwrite_properties( module, lo ):
	"""
	Overwrite properties in property_descriptions by UCR variables
	"""
	prop_obj = property()
	ucr_prefix = 'directory/manager/web/modules/%s/properties/' % module.module
	if not module:
		return
	
	for var in configRegistry.keys():
		if not var.startswith( ucr_prefix ):
			continue
		try: 
			prop, attr = var[ len( ucr_prefix ) : ].split( '/', 1 )
			# ingore internal attributes
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ucr_overwrite_properties: found variable: %s' % var )
			if attr.startswith( '__' ):
				continue
			if prop in module.property_descriptions:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ucr_overwrite_properties: found property' )
				if hasattr( module.property_descriptions[ prop ], attr ):
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ucr_overwrite_properties: set property attribute %s to %s' % ( attr, configRegistry[ var ] ) )
					if attr in ( 'syntax', ):
						if hasattr(univention.admin.syntax, configRegistry[ var ]):
							syntax = getattr( univention.admin.syntax, configRegistry[ var ] )
							setattr( module.property_descriptions[ prop ], attr, syntax() )
						else:
							if lo.search( filter = univention.admin.syntax.LDAP_Search.FILTER_PATTERN % configRegistry[ var ] ):
								syntax = univention.admin.syntax.LDAP_Search( configRegistry[ var ] )
								syntax._load( lo )
								setattr( module.property_descriptions[ prop ], attr, syntax )
							else:
								syntax = univention.admin.syntax.string()
								setattr( module.property_descriptions[ prop ], attr, syntax() )
					else:
						setattr( module.property_descriptions[ prop ], attr, type( getattr( module.property_descriptions[ prop ], attr ) ) ( configRegistry[ var ] ) )
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ucr_overwrite_properties: get property attribute: %s' % getattr( module.property_descriptions[ prop ], attr ) )
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'ucr_overwrite_properties: get property attribute (type): %s' % type( getattr( module.property_descriptions[ prop ], attr ) ) )
		except Exception, e:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'ucr_overwrite_properties: failed to set property attribute: %s' % str( e ) )
			continue

def pattern_replace( pattern, object ):
	"""Replaces patterns like <attribute:command,...>[range] with values
	of the specified UDM attribute."""

	global_commands = []
	def modify_text( text, commands ):
		# apply all string commands
		for iCmd in commands:
			if iCmd == 'lower':
				text = text.lower()
			elif iCmd == 'upper':
				text = text.upper()
			elif iCmd == 'umlauts':
				for umlaut, code in property.UMLAUTS.items():
					text = text.replace( umlaut, code )

				text = text.encode( 'ascii', 'replace' )
			elif iCmd in ( 'trim', 'strip' ):
				text = text.strip()
		return text

	def repl(match):
		key = match.group('key')
		ext = match.group('ext')
		strCommands = []

		# check within the key for additional commands to be applied on the string
		# (e.g., 'firstname:lower,umlaut') these commands are found after a ':'
		if ':' in key:
			# get the corrected key without following commands
			key, tmpStr = key.rsplit(':', 1)

			# get all commands in lower case and without leading/trailing spaces
			strCommands = [iCmd.lower().strip() for iCmd in tmpStr.split(',')]

			# if this is a list of global commands store the
			# commands and return an empty string
			if not key:
				global_commands.extend( strCommands )
				return ''

		# make sure the key value exists
		if object.has_key( key ) and object[ key ]:
			val = modify_text( object[key], strCommands )
			# try to apply the indexing instructions, indicated through '[...]'
			if ext:
				try:
					return eval('val%s' % (ext))
				except SyntaxError:
					return val
			return val

		elif key == 'dn' and object.dn:
			return object.dn
		return ''

	regex = re.compile(r'<(?P<key>[^>]+)>(?P<ext>\[[\d:]+\])?')
	value = regex.sub(repl, pattern, 0)
	if global_commands:
		value = modify_text( value, global_commands )

	return value


class property:
	UMLAUTS = { 'ä' :'ae', 'Ä' : 'Ae', 'ö' : 'oe', 'Ö' : 'Oe', 'ü' : 'ue', 'Ü' : 'Ue', 'ß' : 'ss', 'Á' : 'A', 'Â' : 'A', 'Ã' : 'A', 'Ä' : 'A', 'Å' : 'A', 'Æ' : 'AE', 'Ç' : 'C', 'È' : 'E', 'É' : 'E', 'Ê' : 'E', 'Ë' : 'E', 'Ì' : 'I', 'Í' : 'I', 'Î' : 'I', 'Ï' : 'I', 'Ð' : 'D', 'Ñ' : 'N', 'Ò' : 'O', 'Ó' : 'O', 'Ô' : 'O', 'Õ' : 'O', 'Ö' : 'O', 'Ù' : 'U', 'Ú' : 'U', 'Û' : 'U', 'à' : 'a', 'â' : 'a', 'á' : 'a', 'ã' : 'a', 'æ' : 'ae', 'ç' : 'c', 'è' : 'e', 'é' : 'e', 'ê' : 'e', 'ë' : 'e', 'ì' : 'i', 'í' : 'i', 'î' : 'i', 'ï' : 'i', 'ñ' : 'n', 'ò' : 'o', 'ó' : 'o', 'ô' : 'o', 'ù' : 'u', 'ú' : 'u', 'û' : 'u', 'ý' : 'y', 'ÿ' : 'y', 'Ĉ' : 'C', 'ĉ' : 'c' }

	def __init__(self, short_description='', long_description='', syntax=None, module_search=None, multivalue=0, one_only=0, parent=None, options=[], license=[], required=0, may_change=1, identifies=0, unique=0, default=None, dontsearch=0, show_in_lists=0, editable=1, configObjectPosition=None,configAttributeName=None):
		self.short_description=short_description
		self.long_description=long_description
		if type(syntax) == types.ClassType:
			self.syntax=syntax()
		else:
			self.syntax=syntax
		self.module_search=module_search
		self.multivalue=multivalue
		self.one_only=one_only
		self.parent=parent
		self.options=options
		self.license=license
		self.required=required
		self.may_change=may_change
		self.identifies=identifies
		self.unique=unique
		self.base_default=default
		self.dontsearch=dontsearch
		self.show_in_lists=show_in_lists
		self.editable=editable
		self.configObjectPosition=configObjectPosition
		self.configAttributeName=configAttributeName
		self.templates=[]

	def new(self):
		if self.multivalue:
			return []
		else:
			return None

	def _replace( self, res, object ):
		return pattern_replace( res, object )

	def default(self, object):
		if not object.set_defaults:
			if self.multivalue:
				return ['']
			else:
				return ''

		if not self.base_default:
			return self.new()

		if isinstance(self.base_default, (types.StringType, types.UnicodeType)):
			return self._replace(self.base_default, object)

		# we can not import univention.admin.syntax here (recursive import) so we need to find another way to identify a complex syntax
		if getattr( self.syntax, 'subsyntaxes', None ) is not None and isinstance( self.base_default[ 0 ], ( list, tuple ) ) and not self.multivalue:
			return self.base_default[ 0 ]
		# multivalue defaults will only be a part of templates, so not multivalue is the common way for modules
		elif (isinstance(self.base_default[0], (types.StringType, types.UnicodeType))) and not self.multivalue:
			res=self.base_default[0]
			for p in self.base_default[1]:
				if not object[p]:
					return self.new()
				res=res.replace('<'+p+'>', object[p])
			return res

		elif (isinstance(self.base_default[0], (types.StringType, types.UnicodeType))):
			for i in range(0,len(self.base_default)):
				if isinstance(self.base_default[i], (types.StringType, types.UnicodeType)):
					self.base_default[i]=self._replace(self.base_default[i],object)
				else: # must be a list of loaded custom attributes then, so we return it if it has content
					if len(self.base_default[i])>0:
						if self.multivalue and type(self.base_default[i]) != types.ListType:
							return [self.base_default[i]]
						else:
							return self.base_default[i]
					else:
						# return the first element, this is only related to empty custom attributes which are loaded wrong, needs to be fixed elsewhere
						if i>0:
							if self.multivalue and not isinstance(self.base_default[0], types.ListType):
								return [self.base_default[0]]
							else:
								return self.base_default[0]
						else:
							return self.new()
			return self.base_default

		elif isinstance(self.base_default[0], types.FunctionType) or callable( self.base_default[ 0 ] ):
			for p in self.base_default[1]:
				if not object[p]:
					return self.new()
			return self.base_default[0](object, self.base_default[2])
		else:
			return self.new()

	def safe_default(self, object):
		def safe_parse(default):
			if not default:
				return False
			try:
				self.syntax.parse(default)
				return True
			except:
				return False
		defaults = self.default(object)
		if isinstance(defaults, types.ListType):
			return [ self.syntax.parse(d) for d in defaults if safe_parse(d) ]
		elif safe_parse(defaults):
			return self.syntax.parse(defaults)
		return defaults

	def check_default(self, object):
		defaults = self.default(object)
		try:
			if isinstance(defaults, types.ListType):
				for d in defaults:
					if d:
						self.syntax.parse(d)
			elif defaults:
				self.syntax.parse(defaults)
		except univention.admin.uexceptions.valueError, exc:
			raise univention.admin.uexceptions.templateSyntaxError([t['name'] for t in self.templates])

	def matches(self, options):
		if not self.options:
			return True
		return bool(set(self.options).intersection(set(options)))

class option:
	def __init__(self, short_description='', long_description='', default=0, editable=0, disabled = 0, objectClasses = None):
		self.short_description=short_description
		self.long_description=long_description
		self.default=default
		self.editable=editable
		self.disabled = disabled
		self.objectClasses = set()
		if objectClasses:
			self.objectClasses = set(objectClasses)

	def matches(self, objectClasses):
		if not self.objectClasses:
			return True
		for oc in self.objectClasses:
			if not oc in objectClasses:
				return False
		return True

def ucr_overwrite_layout (module, ucr_property, tab):
	"""
	Overwrite the advanced setting in the layout
	"""
	desc = tab[ 'name' ]
	if hasattr (tab[ 'name' ], 'data'):
		desc = tab.tab[ 'name' ].data
	# replace invalid characters by underscores
	desc = re.sub(univention.config_registry.invalid_key_chars, '_', desc).replace('/','_')
	p_v = configRegistry.get ('directory/manager/web/modules/%s/layout/%s/%s' % (module, desc, ucr_property), None)
	if not p_v:
		return None

	if p_v.lower() in ['0', 'false', 'no', 'off']:
		return False
	else:
		return True

def ucr_overwrite_module_layout( module ):
	'''
	Overwrite the tab layout
	'''
	univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, "layout overwrite" )
	# there are modules without a layout definition
	if not hasattr( module, 'layout' ):
		return

	new_layout = []
	for tab in module.layout[ : ]:
		desc = tab.label
		if hasattr( tab.label, 'data' ):
			desc = tab.label.data

		# replace invalid characters by underscores
		desc = re.sub(univention.config_registry.invalid_key_chars, '_', desc).replace('/','_')

		tab_layout = configRegistry.get( 'directory/manager/web/modules/%s/layout/%s' % ( module.module, desc ) )
		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, "layout overwrite: tab_layout='%s'" % tab_layout )
		tab_name = configRegistry.get( 'directory/manager/web/modules/%s/layout/%s/name' % ( module.module, desc ) )
		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, "layout overwrite: tab_name='%s'" % tab_name )
		tab_descr = configRegistry.get( 'directory/manager/web/modules/%s/layout/%s/description' % ( module.module, desc ) )
		univention.debug.debug( univention.debug.ADMIN, univention.debug.INFO, "layout overwrite: tab_descr='%s'" % tab_descr )
		if tab_name:
			tab[ 'name' ] = tab_name
		if tab_descr:
			tab[ 'description' ] = tab_descr
		if tab_layout and tab_layout.lower() != 'none':
			layout = []
			for row in tab_layout.split( ';' ):
				line = []
				for col in row.split( ',' ):
					col = col.strip()
					if not col:
						continue
					if col in module.property_descriptions:
						line.append( col )
					else:
						univention.debug.debug( univention.debug.ADMIN, univention.debug.ERROR, "layout overwrite: unknown property: %s" % col )
				layout.append( line )
			tab[ 'layout' ] = { 'label' : _( 'General' ), 'layout' : layout }
		if not tab_layout or tab_layout.lower() != 'none':
			new_layout.append( tab )

	del module.layout
	module.layout = new_layout

class extended_attribute(object):
	def __init__(self, name, objClass, ldapMapping, deleteObjClass = False, syntax = 'string', hook = None):
		self.name = name
		self.objClass = objClass
		self.ldapMapping = ldapMapping
		self.deleteObjClass = deleteObjClass
		self.syntax = syntax
		self.hook = hook

	def __repr__(self):
		hook = None
		if self.hook:
			hook = self.hook.type
		return " univention.admin.extended_attribute: { name: '%s', oc: '%s', attr: '%s', delOC: '%s', syntax: '%s', hook: '%s' }" % (self.name, self.objClass, self.ldapMapping, self.deleteObjClass, self.syntax, hook)


class tab:
	def __init__(self, short_description='', long_description='', fields=[], advanced = False):
		self.short_description=short_description
		self.long_description=long_description
		self.fields=fields
		self.advanced = advanced

	def set_fields(self, fields):
		self.fields = fields

	def get_fields(self):
		return self.fields

	def __repr__(self):
		string = " univention.admin.tab: { short_description: '%s', long_description: '%s', advanced: '%s', fields: [" % (self.short_description, self.long_description, self.advanced)
		for field in self.fields:
			string = "%s %s," % (string, field)
		return string + " ] }"

class field:
	def __init__(self, property='', type='', first_only=0, short_description='', long_description='', hide_in_resultmode=0, hide_in_normalmode=0, colspan=None, width=None):
		self.property=property
		self.type=type
		self.first_only=first_only
		self.short_description=short_description
		self.long_description=long_description
		self.hide_in_resultmode=hide_in_resultmode
		self.hide_in_normalmode=hide_in_normalmode
		self.colspan=colspan
		self.width=width

	def __repr__(self):
		return " univention.admin.field: { short_description: '%s', long_description: '%s', property: '%s', type: '%s', first_only: '%s', hide_in_resultmode: '%s', hide_in_normalmode: '%s', colspan: '%s', width: '%s' }" % (
			self.short_description, self.long_description, self.property, self.type, self.first_only, self.hide_in_resultmode, self.hide_in_normalmode, self.colspan, self.width )

	def __cmp__(self, other):
		# at the moment the sort is only needed for layout of the registry module
		if other.property == 'registry':
			return 1
		if self.property == 'registry':
			return 0
		return cmp(self.property, other.property)

class policiesGroup:
	def __init__(self, id, short_description=None, long_description='', members=[]):
		self.id=id
		if short_description==None:
			self.short_description=id
		else:
			self.short_description=short_description
		self.long_description=long_description
		self.members=members

if __name__ == '__main__':
	prop = property( '_replace' )
	for pattern in ( '<firstname>', '<firstname> <lastname>', '<firstname:upper>', '<:trim,upper><firstname> <lastname>     ', '<:lower><firstname> <lastname>', '<:umlauts><firstname> <lastname>' ):
		print "pattern: '%s'" % pattern
		print " -> '%s'" % prop._replace( pattern, { 'firstname' : 'Andreas', 'lastname' : 'Büsching' } )
