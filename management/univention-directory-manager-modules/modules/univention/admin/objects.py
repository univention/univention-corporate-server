# -*- coding: utf-8 -*-
"""
|UDM| objects.
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

import re
import ldap

import univention.debug as ud
import univention.admin.modules
try:
	from typing import Any, Dict, List, Optional, Tuple, Union  # noqa F401
except ImportError:
	pass


def module(object):
	# type: (univention.admin.handlers.simpleLdap) -> Optional[str]
	"""
	Return handler name for |UDM| object.

	:param object: |UDM| object instance
	:returns: |UDM| handler name or `None`.
	"""
	if hasattr(object, 'module'):
		return object.module
	else:
		res = re.findall('^<.?univention.admin.handlers.(.+)\.[^\. ]+ .*>$', str(object))
		if len(res) != 1:
			return None
		else:
			mod = res[0].replace('.', '/')
			return mod


def get_superordinate(module, co, lo, dn):
	# type: (univention.admin.modules.UdmModule, univention.admin.uldap.config, univention.admin.uldap.access, str) -> Optional[univention.admin.handlers.simpleLdap]
	"""
	Searches for the superordinate object for the given DN.

	:param module: ???
	:param co: |UDM| configuation object.
	:param lo: |LDAP| connection.
	:param dn: |DN|.
	:returns: the superoridnate or `None` if the object does not require a superordinate object or it is not found.
	"""
	super_modules = set(univention.admin.modules.superordinate_names(module))
	if super_modules:
		while dn:
			attr = lo.get(dn)
			super_module = set(univention.admin.modules.name(x) for x in univention.admin.modules.identify(dn, attr)) & super_modules
			if super_module:
				super_module = univention.admin.modules.get(list(super_module)[0])
				return get(super_module, co, lo, None, dn)
			dn = lo.parentDn(dn)

	return None


def get(module, co, lo, position, dn='', attr=None, superordinate=None, attributes=None):
	# type: (univention.admin.modules.UdmModule, univention.admin.uldap.config, univention.admin.uldap.access, univention.admin.uldap.position, str, Dict[str, List[Any]], Any, Any) -> univention.admin.handlers.simpleLdap
	"""
	Return object of module while trying to create objects of
	superordinate modules as well.

	:param module: |UDM| handler.
	:param co: |UDM| configuation object.
	:param lo: |LDAP| connection.
	:param position: |UDM| position instance.
	"""
	# module was deleted
	if not module:
		return None

	if not superordinate:
		superordinate = get_superordinate(module, co, lo, dn or position.getDn())

	if dn:
		try:
			obj = univention.admin.modules.lookup(module.module, co, lo, base=dn, superordinate=superordinate, scope='base', unique=True, required=True)[0]
			obj.position.setDn(position.getDn() if position else dn)
			return obj
		except (ldap.NO_SUCH_OBJECT, univention.admin.uexceptions.noObject):
			if not lo.get(dn):
				raise univention.admin.uexceptions.noObject(dn)
			ud.debug(ud.ADMIN, ud.ERROR, 'univention.admin.objects.get(): The object %s is not a %s. Ignoring this error.' % (dn, module.module,))
			return module.object(co, lo, position, dn, superordinate=superordinate, attributes=attributes)
			# raise univention.admin.uexceptions.wrongObjectType('The object %s is not a %s.' % (dn, module.module,))

	return module.object(co, lo, position, dn, superordinate=superordinate, attributes=attributes)


def open(object):
	# type: (univention.admin.handlers.simpleLdap) -> None
	"""
	Initialization of properties not necessary for browsing etc.

	:param object: |UDM| object.
	"""

	if not object:
		return

	if hasattr(object, 'open'):
		object.open()


def default(module, co, lo, position):
	# type: (univention.admin.modules.UdmModule, univention.admin.uldap.config, univention.admin.uldap.access, univention.admin.uldap.position) -> univention.admin.handlers.simpleLdap
	"""
	Create |UDM| object and initialize default values.

	:param module: |UDM| handler.
	:param co: |UDM| configuation object.
	:param lo: |LDAP| connection.
	:param position: |UDM| position instance.
	:returns: An initialized |UDM| object.
	"""
	_d = ud.function('admin.objects.default')  # noqa: F841
	module = univention.admin.modules.get(module)
	object = module.object(co, lo, position)
	for name, property in module.property_descriptions.items():
		default = property.default(object)
		if default:
			object[name] = default
	return object


def description(object):
	# type: (univention.admin.handlers.simpleLdap) -> str
	"""
	Return short description for object.

	:param object: |UDM| object.
	"""
	if hasattr(object, 'description'):
		return object.description()
	else:
		description = None
		object_module = module(object)
		object_module = univention.admin.modules.get(object_module)
		if hasattr(object_module, 'property_descriptions'):
			for name, property in object_module.property_descriptions.items():
				if property.identifies:
					syntax = property.syntax
					description = syntax.tostring(object[name])
					break
		if not description:
			if object.dn:
				description = univention.admin.uldap.explodeDn(object.dn, 1)[0]
				ud.debug(ud.ADMIN, ud.INFO, 'falling back to rdn: %s' % (object.dn))
			else:
				description = 'None'
		return description


def shadow(lo, module, object, position):
	# type: (univention.admin.uldap.access, univention.admin.modules.UdmModule, univention.admin.handlers.simpleLdap, univention.admin.uldap.position) -> Union[Tuple[univention.admin.handlers.simpleLdap, univention.admin.modules.UdmModule], Tuple[None, None]]
	"""
	If object is a container, return object and module the container
	shadows (that is usually the one that is subordinate in the LDAP tree).

	:param lo: |LDAP| connection.
	:param module: |UDM| handler.
	:param object: |UDM| object.
	:param position: |UDM| position instance.
	:returnd: 2-tuple (module, object) or `(None, None)`
	"""
	if not object:
		return (None, None)
	dn = object.dn
	# this is equivalent to if ...; while 1:
	while univention.admin.modules.isContainer(module):
		dn = lo.parentDn(dn)
		if not dn:
			return (None, None)
		attr = lo.get(dn)
		for m in univention.admin.modules.identify(dn, attr):
			if not univention.admin.modules.isContainer(m):
				o = get(m, None, lo, position=position, dn=dn)
				return (m, o)
	# module is not a container
	return (module, object)


def dn(object):
	# type: (univention.admin.handlers.simpleLdap) -> Optional[str]
	"""
	Return the |DN| of the object.

	:param object: |UDM| object.
	:returns: the |DN| or `None`.
	"""
	if hasattr(object, 'dn'):
		return object.dn
	else:
		return None


def ocToType(oc):
	# type: (str) -> Optional[str]
	"""
	Return the |UDM| module capabale of handling the given |LDAP| objectClass.

	:param oc: |LDAP| object class.
	:returns: name of the |UDM| module.
	"""
	for module in univention.admin.modules.modules.values():
		if univention.admin.modules.policyOc(module) == oc:
			return univention.admin.modules.name(module)


def fixedAttribute(object, key):
	# type: (univention.admin.handlers.simpleLdap, str) -> int
	"""
	Check if the named property is a fixed attribute (not overwritten my more specific policies).

	:param object: |UDM| object.
	:param key: |UDM| property name
	:returns: `1` if the property is fixed, `0` otherwise.
	"""
	if not hasattr(object, 'fixedAttributes'):
		return 0

	return object.fixedAttributes().get(key, 0)


def emptyAttribute(object, key):
	# type: (univention.admin.handlers.simpleLdap, str) -> int
	"""
	Check if the named property is an empty attribute (reset to empty by a general policy).

	:param object: |UDM| object.
	:param key: |UDM| property name
	:returns: `1` if the property is empty, `0` otherwise.
	"""
	if not hasattr(object, 'emptyAttributes'):
		return 0

	return object.emptyAttributes().get(key, 0)


def getPolicyReference(object, policy_type):
	# type: (univention.admin.handlers.simpleLdap, str) -> Optional[univention.admin.handlers.simplePolicy]
	"""
	Return the policy of the requested type.

	:param object: |UDM| object.
	:param policy_type: Name of the |UDM| policy to lookup.
	:returns: The policy applying to the object or `None`.
	"""
	# FIXME: Move this to handlers.simpleLdap?
	_d = ud.function('admin.objects.getPolicyReference policy_type=%s' % (policy_type))  # noqa: F841

	policyReference = None
	for policy_dn in object.policies:
		for m in univention.admin.modules.identify(policy_dn, object.lo.get(policy_dn)):
			if univention.admin.modules.name(m) == policy_type:
				policyReference = policy_dn
	ud.debug(ud.ADMIN, ud.INFO, 'getPolicyReference: returning: %s' % policyReference)
	return policyReference


def removePolicyReference(object, policy_type):
	# type: (univention.admin.handlers.simpleLdap, str) -> None
	"""
	Remove the policy of the requested type.

	:param object: |UDM| object.
	:param policy_type: Name of the |UDM| policy to lookup.
	"""
	# FIXME: Move this to handlers.simpleLdap?
	_d = ud.function('admin.objects.removePolicyReference policy_type=%s' % (policy_type))  # noqa: F841

	remove = None
	for policy_dn in object.policies:
		for m in univention.admin.modules.identify(policy_dn, object.lo.get(policy_dn)):
			if univention.admin.modules.name(m) == policy_type:
				remove = policy_dn
	if remove:
		ud.debug(ud.ADMIN, ud.INFO, 'removePolicyReference: removing reference: %s' % remove)
		object.policies.remove(remove)


def replacePolicyReference(object, policy_type, new_reference):
	# type: (univention.admin.handlers.simpleLdap, str, univention.admin.handlers.simplePolicy) -> None
	"""
	Replace the policy of the requested type with a new instance.

	:param object: |UDM| object.
	:param policy_type: Name of the |UDM| policy to lookup.
	"""
	# FIXME: Move this to handlers.simpleLdap?
	_d = ud.function('admin.objects.replacePolicyReference policy_type=%s new_reference=%s' % (policy_type, new_reference))  # noqa: F841

	module = univention.admin.modules.get(policy_type)
	if not univention.admin.modules.recognize(module, new_reference, object.lo.get(new_reference)):
		ud.debug(ud.ADMIN, ud.INFO, 'replacePolicyReference: error.')
		return

	removePolicyReference(object, policy_type)

	ud.debug(ud.ADMIN, ud.INFO, 'replacePolicyReference: appending reference: %s' % new_reference)
	object.policies.append(new_reference)


def restorePolicyReference(object, policy_type):
	# type: (univention.admin.handlers.simpleLdap, str) -> None
	"""
	Restore the policy of the requested type.

	:param object: |UDM| object.
	:param policy_type: Name of the |UDM| policy to lookup.
	"""
	# FIXME: Move this to handlers.simpleLdap?
	_d = ud.function('admin.objects.restorePolicyReference policy_type=%s' % (policy_type))  # noqa: F841
	module = univention.admin.modules.get(policy_type)
	if not module:
		return

	removePolicyReference(object, policy_type)

	restore = None
	for policy_dn in object.oldpolicies:
		if univention.admin.modules.recognize(module, policy_dn, object.lo.get(policy_dn)):
			restore = policy_dn
	if restore:
		object.policies.append(restore)


def wantsCleanup(object):
	# type: (univention.admin.handlers.simpleLdap) -> int
	"""
	Check if the given object wants to perform a cleanup (delete
	other objects, etc.) before it is deleted itself.

	:param object: parent object.
	:returns: `1´ if a cleanup is requested, `0` otherwise.
	"""
	# TODO make this a method of object
	wantsCleanup = 0

	object_module = module(object)
	object_module = univention.admin.modules.get(object_module)
	if hasattr(object_module, 'docleanup'):
		wantsCleanup = object_module.docleanup

	return wantsCleanup


def performCleanup(object):
	# type: (univention.admin.handlers.simpleLdap) -> None
	"""
	some objects create other objects. remove those if necessary.

	:param object: parent object.
	"""
	try:
		object.cleanup()
	except Exception:
		pass
