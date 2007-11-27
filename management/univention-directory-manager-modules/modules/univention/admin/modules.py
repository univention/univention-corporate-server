#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  access to handler modules
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

import os, sys, ldap, types, copy
import univention.debug
import univention.admin
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.localization

translation=univention.admin.localization.translation('univention/admin')
_=translation.translate

modules={}
containers=[]

def update():
	'''scan handler modules'''
	global modules
	modules={}

	def _walk(root, dir, files):
		global modules
		for file in files:
			if not file.endswith('.py') or file.startswith('__'):
				continue
			p=os.path.join(dir, file).replace(root, '').replace('.py', '')
			p=p[1:]
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'admin.modules.update: importing "%s"' % p)
			m=__import__(p)
			m.initialized=0
			modules[m.module]=m
			if isContainer(m):
				containers.append(m)

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
		#univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules_init: reset default descriptions')

	# get defaults from template
	if template_object:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules_init: got template object %s' % template_object)
		template_object.open()
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
						else: univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules.init: template and object values not both multivalue !!')

					else:
						module.property_descriptions[key].base_default=template_object[key]
					module.property_descriptions[key].templates.append(template_object)
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules_init: module.property_description after template: %s' % module.property_descriptions)
	else:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules_init: got no template')

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
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'deleteValues %s' % deleteValues)
		else:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'No deleteValues')

		deleteObjectClass=0
		tabname = attrs.get('univentionAdminPropertyLayoutTabName',[_('Custom')])[0]
		if attrs.get('univentionAdminPropertyDeleteObjectClass'):
			deleteObjectClass=attrs.get('univentionAdminPropertyDeleteObjectClass')[0]
		if not custom_fields.has_key(tabname):
			custom_fields[tabname] = []
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules init: custom fields init for Tab %s' % tabname)
		tabposition = attrs.get('univentionAdminPropertyLayoutPosition',['-1'])[0]
		try:
			tabposition = int(tabposition)
		except:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'modules init: custom field for tab %s: failed to convert tabNumber to int' % tabname)
		if tabposition == -1 and len(custom_fields[tabname]) > 0:
			for pos, el in custom_fields[tabname]:
				try:
					if int(pos) <= tabposition:
						tabposition = int(pos)-1
				except:
					univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'modules init: custom field for tab %s: failed to set tabposition' % tabname)

		custom_fields[tabname].append((tabposition, univention.admin.field(pname)))
		module.ldap_extra_objectclasses.extend( ([(attrs.get('univentionAdminPropertyObjectClass', [])[0], pname, propertySyntaxString, attrs['univentionAdminPropertyLdapMapping'][0], deleteValues, deleteObjectClass )]))

	if custom_fields:
		#if module.initialized: # reload custom attributes
		removetab = []
		for tab in module.layout:
			if tab.short_description in custom_fields.keys():
				removetab.append(tab)
		for tab in removetab:
			module.layout.remove(tab)
		for tabname in custom_fields.keys():
			priofields = custom_fields[tabname]
			priofields.sort()
			fields=[]
			lastfield = ''
			for (prio, field) in priofields:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules init: custom fields found prio %s'% prio)
				if not lastfield:
					lastfield = field
					lastprio = prio
				else:
					try:
						if int(prio) > int(lastprio)+1:
							fields.append([lastfield])
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules init: single custom field added %s'% fields)
							lastfield = field
							lastprio = prio
						else:
							fields.append([lastfield,field])
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules init: two custom fields added %s'% fields)
							lastfield = ''
							lastprio = ''
					except: # if int(prio) failes
						 fields.append([lastfield,field])
						 univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules init: two custom fields added %s'% fields)
						 lastfield = ''
						 lastprio = ''

			if lastfield:
				fields.append([lastfield])
			module.layout.append(univention.admin.tab(tabname, tabname, fields))
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modules init: one custom field added %s'% fields)

	# check for properties with the syntax class LDAP_Search
	for pname, prop in module.property_descriptions.items():
		if prop.syntax.name == 'LDAP_Search':
			prop.syntax._load( lo )
			if prop.syntax.viewonly:
				module.mapping.unregister( pname )
		elif prop.syntax.type == 'complex' and hasattr( prop.syntax, 'subsyntaxes' ):
			for text, subsyn in prop.syntax.subsyntaxes:
				if subsyn.name == 'LDAP_Search':
					subsyn._load( lo )
				

	module.initialized=1

def identify(dn, attr, type='', canonical=0):

	global modules
	res=[]
	for module in modules.values():
		if name(module).startswith('dns/zone_'):
			continue
		if not hasattr(module, 'identify'):
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'module %s does not provide identify' % module)
			pass
		elif module.identify(dn, attr) and not type or type == module.module:
			res.append(module)
	if not res:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'object could not be identified')
	for r in res:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'identify: found module %s on %s'%(r.module,dn) )
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

def layout(module_name, object=None):
	'''return layout of properties'''
	module = get(module_name)
	defining_layout = None
	if object:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'modules.py layout:: got an definied object')

	if object and hasattr(object, 'layout'): # for dynamic modules like users/self
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'modules.py layout:: layout is defined by the object')
		defining_layout = object.layout
	elif hasattr(module, 'layout'):
		defining_layout = module.layout
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'modules.py layout:: layout is defined by the module')

	if defining_layout:
		if object and hasattr(object, 'options'):
			layout = []
			for tab in defining_layout:
				empty  = True
				fields = []
				for line in tab.fields:
					nline = []
					for row in line:
						single = False
						nrow = []
						if isinstance(row, univention.admin.field):
							single = True
							row = [row]
						for field in row:
							prop = module.property_descriptions[field.property]
							nrow.append(field)
							if not field.property == 'filler' and (not prop.options or [opt for opt in prop.options if opt in object.options]):
								empty = False
						if nrow:
							if single:
								nrow = nrow[0]
							nline.append(nrow)
					if nline:
						fields.append(nline)
				if fields and not empty:
					ntab=copy.deepcopy(tab)
					ntab.fields=fields
					layout.append(ntab)
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'modules.py layout:: return layout decreased by given options')
			return layout
		else:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'modules.py layout:: return defining_layout.')
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

def objectType(co, lo, dn, attr=None, modules=[]):
	if not dn:
		return []
	if not attr:
		attr=lo.get(dn)
		if not attr:
			return []
	if not modules:
		modules=identify(dn, attr)
	return [name(mod) for mod in modules]

def objectShadowType(co, lo, dn, attr=None, modules=[]):
	res=[]
	for type in objectType(co, lo, dn, attr, modules):
		if type and type.startswith('container/'):
			res.append(objectShadowType(co, lo, lo.parentDn(dn)))
		else:
			res.append(type)
	return res

def findObject(co, lo, dn, type, attr=None):
	if not attr:
		attr=lo.get(dn)
		if not attr:
			return None
	ndn=dn
	nattr=attr
	while 1:
		for module in identify(ndn, nattr):
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

def policyTypes(module):
	if not module:
		return
	global modules
	res=[]
	for mod in modules.values():
		if not name(mod).startswith('policies'):
			continue
		if not hasattr(mod, 'policy_apply_to'):
			continue
		if name(module) in mod.policy_apply_to:
			res.append(name(mod))
	if not res:
		pass
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
	return getattr(module, 'wizardoperations', {"find":[_("Find"), _("Find Object(s)")], "add":[_("Add"), _("Add Object(s)")]})

def childModules(module_name):
	'''return child modules if module is a super module'''
	module = get(module_name)
	return copy.deepcopy( getattr(module, 'childmodules', []) )

update()
