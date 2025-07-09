#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| objects."""

from __future__ import annotations

from logging import getLogger
from typing import Any

import ldap

import univention.admin.modules


log = getLogger('ADMIN')


def module(object: univention.admin.handlers.simpleLdap) -> str | None:
    """
    Return handler name for |UDM| object.

    :param object: |UDM| object instance
    :returns: |UDM| handler name or `None`.
    """
    return getattr(object, 'module', None)


def get_superordinate(module: univention.admin.modules.UdmModule, co: None, lo: univention.admin.uldap.access, dn: str) -> univention.admin.handlers.simpleLdap | None:
    """
    Searches for the superordinate object for the given DN.

    :param module: |UDM| module name
    :param co: |UDM| configuation object.
    :param lo: |LDAP| connection.
    :param dn: |DN|.
    :returns: the superoridnate or `None` if the object does not require a superordinate object or it is not found.
    """
    super_modules = set(univention.admin.modules.superordinate_names(module))
    if super_modules:
        while dn:
            attr = lo.authz_connection.get(dn)
            for module in {univention.admin.modules.name(x) for x in univention.admin.modules.identify(dn, attr)} & super_modules:
                super_module = univention.admin.modules._get(module)
                return get(super_module, co, lo, None, dn, authz='settings/cn' != super_module)
            dn = lo.parentDn(dn)

    return None


def get(module: univention.admin.modules.UdmModule, co: None, lo: univention.admin.uldap.access, position: univention.admin.uldap.position, dn: str = '', attr: dict[str, list[Any]] | None = None, superordinate: Any | None = None, attributes: Any | None = None, authz: bool = True) -> univention.admin.handlers.simpleLdap | None:
    """
    Return object of module while trying to identify objects of
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
            obj = univention.admin.modules.lookup(module.module, co, lo, base=dn, superordinate=superordinate, scope='base', unique=True, required=True, authz=authz)[0]
            obj.position.setDn(position.getDn() if position else dn)
            return obj
        except (ldap.NO_SUCH_OBJECT, univention.admin.uexceptions.noObject, IndexError):
            if not lo.authz_connection.get(dn, attr=['objectClass']):  # FIXME: information disclosure
                raise univention.admin.uexceptions.noObject(dn)
            if not univention.admin.modules.virtual(module.module):
                raise univention.admin.uexceptions.wrongObjectType('The object %s is not a %s.' % (dn, module.module))

    return module.object(co, lo, position, dn, superordinate=superordinate, attributes=attributes)


def get_object(lo: univention.admin.uldap.access, dn: str) -> univention.admin.handlers.simpleLdap:
    """
    Get a |UDM| object for the specified LDAP DN by automatically detecting the object type.
    Returns `None` if the object doesn't exists or no |UDM| handler exists for it.

    :param lo: |LDAP| connection.
    :param dn: |DN| of the object.
    """
    attr = lo.authz_connection.get(dn, ['*', '+'])
    for modname in univention.admin.modules.objectType(None, lo, dn, attr):
        module = univention.admin.modules.get(modname)
        if module:
            return module.object(None, lo, None, dn, None, attr)


def open(object: univention.admin.handlers.simpleLdap) -> None:
    """
    Initialization of properties not necessary for browsing etc.

    :param object: |UDM| object.
    """
    if not object:
        return

    if hasattr(object, 'open'):
        object.open()


def default(module: univention.admin.modules.UdmModule, co: None, lo: univention.admin.uldap.access, position: univention.admin.uldap.position) -> univention.admin.handlers.simpleLdap:
    """
    Create |UDM| object and initialize default values.

    :param module: |UDM| handler.
    :param co: |UDM| configuation object.
    :param lo: |LDAP| connection.
    :param position: |UDM| position instance.
    :returns: An initialized |UDM| object.
    """
    module = univention.admin.modules._get(module)
    object = module.object(co, lo, position)
    for name, property in module.property_descriptions.items():
        default = property.default(object)
        if default:
            object[name] = default
    return object


def description(object: univention.admin.handlers.simpleLdap) -> str:
    """
    Return short description for object.

    :param object: |UDM| object.
    """
    return object.description()


def shadow(
    lo: univention.admin.uldap.access, module: univention.admin.modules.UdmModule, object: univention.admin.handlers.simpleLdap, position: univention.admin.uldap.position
) -> tuple[univention.admin.handlers.simpleLdap, univention.admin.modules.UdmModule] | tuple[None, None]:
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
        attr = lo.authz_connection.get(dn)  # TODO: information disclosure?
        for m in univention.admin.modules.identify(dn, attr):
            if not univention.admin.modules.isContainer(m):
                o = get(m, None, lo, position=position, dn=dn)
                return (m, o)
    # module is not a container
    return (module, object)


def dn(object: univention.admin.handlers.simpleLdap) -> str | None:
    """
    Return the |DN| of the object.

    :param object: |UDM| object.
    :returns: the |DN| or `None`.
    """
    return getattr(object, 'dn', None)


def ocToType(oc: str) -> str | None:
    """
    Return the |UDM| module capabale of handling the given |LDAP| objectClass.

    :param oc: |LDAP| object class.
    :returns: name of the |UDM| module.
    """
    for module in univention.admin.modules.modules.values():
        if univention.admin.modules.policyOc(module) == oc:
            return univention.admin.modules.name(module)
    return None  # FIXME:


def fixedAttribute(object: univention.admin.handlers.simpleLdap, key: str) -> int:
    """
    Check if the named property is a fixed attribute (not overwritten by more specific policies).

    :param object: |UDM| object.
    :param key: |UDM| property name
    :returns: `True` if the property is fixed, `False` otherwise.
    """
    if not hasattr(object, 'fixedAttributes'):
        return False

    return object.fixedAttributes().get(key, False)


def emptyAttribute(object: univention.admin.handlers.simpleLdap, key: str) -> int:
    """
    Check if the named property is an empty attribute (reset to empty by a general policy).

    :param object: |UDM| object.
    :param key: |UDM| property name
    :returns: `True` if the property is empty, `False` otherwise.
    """
    if not hasattr(object, 'emptyAttributes'):
        return False

    return object.emptyAttributes().get(key, False)


def getPolicyReference(object: univention.admin.handlers.simpleLdap, policy_type: str) -> univention.admin.handlers.simplePolicy | None:
    """
    Return the policy of the requested type.

    :param object: |UDM| object.
    :param policy_type: Name of the |UDM| policy to lookup.
    :returns: The policy applying to the object or `None`.
    """
    # FIXME: Move this to handlers.simpleLdap?

    policyReference = None
    for policy_dn in object.policies:
        for m in univention.admin.modules.identify(policy_dn, object.lo.authz_connection.get(policy_dn)):
            if univention.admin.modules.name(m) == policy_type:
                policyReference = policy_dn
    log.debug('getPolicyReference: returning: %s', policyReference)
    return policyReference


def removePolicyReference(object: univention.admin.handlers.simpleLdap, policy_type: str) -> None:
    """
    Remove the policy of the requested type.

    :param object: |UDM| object.
    :param policy_type: Name of the |UDM| policy to lookup.
    """
    # FIXME: Move this to handlers.simpleLdap?

    remove = None
    for policy_dn in object.policies:
        for m in univention.admin.modules.identify(policy_dn, object.lo.authz_connection.get(policy_dn)):
            if univention.admin.modules.name(m) == policy_type:
                remove = policy_dn
    if remove:
        log.debug('removePolicyReference: removing reference: %s', remove)
        object.policies.remove(remove)


def replacePolicyReference(object: univention.admin.handlers.simpleLdap, policy_type: str, new_reference: univention.admin.handlers.simplePolicy) -> None:
    """
    Replace the policy of the requested type with a new instance.

    :param object: |UDM| object.
    :param policy_type: Name of the |UDM| policy to lookup.
    """
    # FIXME: Move this to handlers.simpleLdap?

    module = univention.admin.modules._get(policy_type)
    if not univention.admin.modules.recognize(module, new_reference, object.lo.authz_connection.get(new_reference)):
        log.debug('replacePolicyReference: error.')
        return

    removePolicyReference(object, policy_type)

    log.debug('replacePolicyReference: appending reference: %s', new_reference)
    object.policies.append(new_reference)


def restorePolicyReference(object: univention.admin.handlers.simpleLdap, policy_type: str) -> None:
    """
    Restore the policy of the requested type.

    :param object: |UDM| object.
    :param policy_type: Name of the |UDM| policy to lookup.
    """
    # FIXME: Move this to handlers.simpleLdap?
    try:
        module = univention.admin.modules._get(policy_type)
    except LookupError:
        return

    removePolicyReference(object, policy_type)

    restore = None
    for policy_dn in object.oldpolicies:
        if univention.admin.modules.recognize(module, policy_dn, object.lo.authz_connection.get(policy_dn)):
            restore = policy_dn
    if restore:
        object.policies.append(restore)


def wantsCleanup(object: univention.admin.handlers.simpleLdap) -> bool:
    """
    Check if the given object wants to perform a cleanup (delete
    other objects, etc.) before it is deleted itself.

    :param object: parent object.
    :returns: `True´ if a cleanup is requested, `False` otherwise.
    """
    # TODO: make this a method of object
    wantsCleanup = False

    object_module = module(object)
    object_module = univention.admin.modules._get(object_module)
    if hasattr(object_module, 'docleanup'):
        wantsCleanup = object_module.docleanup

    return wantsCleanup


def performCleanup(object: univention.admin.handlers.simpleLdap) -> None:
    """
    some objects create other objects. remove those if necessary.

    :param object: parent object.
    """
    try:
        object.cleanup()
    except Exception:
        pass  # TODO: add logging
