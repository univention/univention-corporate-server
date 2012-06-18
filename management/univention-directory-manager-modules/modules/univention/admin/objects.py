# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  objects
#
# Copyright 2004-2012 Univention GmbH
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

import sys, re, ldap
import univention.debug
import univention.admin.modules

def module(object):
	'''returns module of object'''

	if hasattr(object, 'module'):
		return object.module
	else:
		res=re.findall('^<.?univention.admin.handlers.(.+)\.[^\. ]+ .*>$', str(object))
		if len(res) != 1:
			return None
		else:
			mod=res[0].replace('.', '/')
			return mod

def get_superordinate( module, co, lo, dn ):
	"""Searches for the superordinate object for the given DN. if the
	object does not require a superordinate object or it is not found
	None is returned."""
	super_module = univention.admin.modules.superordinate( module )
	if super_module:
		while dn:
			attr = lo.get( dn )
			if univention.admin.modules.identifyOne( dn, attr ) == super_module:
				return get( super_module, co, lo, None, dn )
			dn = lo.parentDn( dn )

	return None

def get(module, co, lo, position, dn='', attr = None, superordinate = None, attributes = [] ):
	'''return object of module while trying to create objects of
	superordinate modules as well'''

	# module was deleted
	if not module:
		return None

	if not superordinate:
		superordinate = get_superordinate( module, co, lo, dn or position.getDn() )

	return module.object( co, lo, position, dn, superordinate = superordinate, attributes = attributes )

def open(object):
	'''initialization of properties not neccessary for browsing etc.'''

	if not object:
		return

	if hasattr(object, 'open'):
		object.open()

def default(module, co, lo, position):
	univention.debug.function('admin.objects.default')
	module=univention.admin.modules.get(module)
	object=module.object(co, lo, position)
	for name, property in module.property_descriptions.items():
		default=property.default(object)
		if default:
			object[name]=default
	return object

def description(object):
	'''return short description for object'''

	if hasattr(object, 'description'):
		return object.description()
	else:
		description=None
		object_module=module(object)
		object_module=univention.admin.modules.get(object_module)
		if hasattr(object_module, 'property_descriptions'):
			for name, property in object_module.property_descriptions.items():
				if property.identifies:
					syntax=property.syntax
					description=syntax.tostring(object[name])
					break
		if not description:
			if object.dn:
				description=univention.admin.uldap.explodeDn(object.dn, 1)[0]
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'falling back to rdn: %s' % (object.dn))
			else:
				description='None'
		return description

def shadow(lo, module, object, position):
	'''if object is a container, return object and module the container
	shadows (that is usually the one that is subordinate in the LDAP tree)'''
	
	if not object:
		return (None, None)
	dn=object.dn
	# this is equivilent to if ...; while 1:
	while univention.admin.modules.isContainer(module):
		dn=lo.parentDn(dn)
		if not dn:
			return (None, None)
		attr=lo.get(dn)
		for m in univention.admin.modules.identify(dn, attr):
			if not univention.admin.modules.isContainer(m):
				o=get(m, None, lo, position=position, dn=dn)
				return (m, o)
	# module is not a container
	return (module, object)

def dn(object):
	if hasattr(object, 'dn'):
		return object.dn
	else:
		return None

def arg(object):
	if hasattr(object, 'arg'):
		return object.arg
	else:
		return None

def ocToType(oc):
	for module in univention.admin.modules.modules.values():
		if univention.admin.modules.policyOc(module) == oc:
			return univention.admin.modules.name(module)

def fixedAttribute(object, key):
	if not hasattr(object, 'fixedAttributes'):
		return 0
	
	return object.fixedAttributes().get(key, 0)

def emptyAttribute(object, key):
	if not hasattr(object, 'emptyAttributes'):
		return 0
	
	return object.emptyAttributes().get(key, 0)

def getPolicyReference(object, policy_type):
	#FIXME: Move this to handlers.simpleLdap?
	_d=univention.debug.function('admin.objects.getPolicyReference policy_type=%s' % (policy_type))

	policyReference=None
	for policy_dn in object.policies:
		for m in univention.admin.modules.identify(policy_dn, object.lo.get(policy_dn)):
			if univention.admin.modules.name(m) == policy_type:
				policyReference=policy_dn
	univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'getPolicyReference: returning: %s' % policyReference)
	return policyReference

def removePolicyReference(object, policy_type):
	#FIXME: Move this to handlers.simpleLdap?
	_d=univention.debug.function('admin.objects.removePolicyReference policy_type=%s' % (policy_type))

	remove=None
	for policy_dn in object.policies:
		for m in univention.admin.modules.identify(policy_dn, object.lo.get(policy_dn)):
			if univention.admin.modules.name(m) == policy_type:
				remove=policy_dn
	if remove:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'removePolicyReference: removing reference: %s' % remove)
		object.policies.remove(remove)

def replacePolicyReference(object, policy_type, new_reference):
	#FIXME: Move this to handlers.simpleLdap?
	_d=univention.debug.function('admin.objects.replacePolicyReference policy_type=%s new_reference=%s' % (policy_type, new_reference))

	module=univention.admin.modules.get(policy_type)
	if not univention.admin.modules.recognize(module, new_reference, object.lo.get(new_reference)):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'replacePolicyReference: error.')
		return

	removePolicyReference(object, policy_type)
	
	univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'replacePolicyReference: appending reference: %s' % new_reference)
	object.policies.append(new_reference)

def restorePolicyReference(object, policy_type):
	#FIXME: Move this to handlers.simpleLdap?
	_d=univention.debug.function('admin.objects.restorePolicyReference policy_type=%s' % (policy_type))
	module=univention.admin.modules.get(policy_type)
	if not module:
		return
	
	removePolicyReference(object, policy_type)

	restore=None
	for policy_dn in object.oldpolicies:
		if univention.admin.modules.recognize(module, policy_dn, object.lo.get(policy_dn)):
			restore=policy_dn
	if restore:
		object.policies.append(restore)

def wantsCleanup(object):
	'''check if the given object wants to perform a cleanup (delete
	other objects, etc.) before it is deleted itself'''

	#TODO make this a method of object
	wantsCleanup=0

	object_module=module(object)
	object_module=univention.admin.modules.get(object_module)
	if hasattr(object_module, 'docleanup'):
		wantsCleanup=object_module.docleanup
	
	return wantsCleanup

def performCleanup(object):
	'''some objects create other objects. remove those if neccessary.'''

	try:
		object.cleanup()
	except Exception, e:
		pass

