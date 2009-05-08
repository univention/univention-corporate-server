# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  basic functionality
#
# Copyright (C) 2004-2009 Univention GmbH
#
# http://www.univention.de/
# 
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import copy, types, string, re
import mapping
import univention.baseconfig
import univention.debug

baseConfig=univention.baseconfig.baseConfig()
baseConfig.load()

__path__.append("handlers")

def ucr_overwrite_properties (module, ucr_properties, property_descriptions):
	"""
	Overwrite properties in property_descriptions by UCR variables
	"""
	if module and ucr_properties and property_descriptions:
		for k, v in property_descriptions.iteritems ():
			for p in ucr_properties:
				p_v = baseConfig.get ('directory/manager/web/modules/%s/properties/%s/%s' % (module, k, p), None)
				if p_v != None:
					if hasattr (v, p):
						try:
							setattr (v, p, type (getattr (v, p)) (p_v))
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, \
									"properties: applied directory/manager/web/modules/%s/properties/%s/%s='%s'" % (module, k, p, p_v))
						except ValueError:
							univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, \
									"properties: unable to apply directory/manager/web/modules/%s/properties/%s/%s='%s'" % (module, k, p, p_v))
					else:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, \
								"properties: no property found for directory/manager/web/modules/%s/properties/%s/%s='%s'" % (module, k, p, p_v))
class property:
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

	def _replace(self,res,object):
		def repl(match):
			key = match.group('key')
			ext = match.group('ext')
			if object.has_key(key) and object[key]:
				if ext:
					try:
						return eval('object["%s"]%s' % (key, ext))
					except SyntaxError:
						return object[key]
				return object[key]
			elif key == 'dn' and object.dn:
				return object.dn
			return ''
		pattern = re.compile(r'<(?P<key>[^>]+)>(?P<ext>\[[\d:]+\])?')
		return pattern.sub(repl, res, 0)


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
		# multivalue defaults will only be a part of templates, so not multivalue is the common way for modules
		if (isinstance(self.base_default[0], (types.StringType, types.UnicodeType))) and not self.multivalue:
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
	desc = tab.short_description
	if hasattr (tab.short_description, 'data'):
		desc = tab.short_description.data
	p_v = baseConfig.get ('directory/manager/web/modules/%s/layout/%s/%s' % (module, desc, ucr_property), None)
	if not p_v:
		return None

	if p_v.lower() in ['0', 'false', 'no', 'off']:
		return False
	else:
		return True


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


class policiesGroup:
	def __init__(self, id, short_description=None, long_description='', members=[]):
		self.id=id
		if short_description==None:
			self.short_description=id
		else:
			self.short_description=short_description
		self.long_description=long_description
		self.members=members
