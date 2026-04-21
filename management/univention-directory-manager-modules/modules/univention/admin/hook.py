# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| hook definitions for modifying |LDAP| calls when objects are created, modifier or deleted."""

from __future__ import annotations

import inspect
import os
import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from univention.admin import localization


if TYPE_CHECKING:
    import univention.admin.handlers

    AddList = list[tuple[str, list[str]]]
    _Mod2 = tuple[str, list[str]]
    _Mod3 = tuple[str, list[str], list[str]]
    ModList = list[_Mod2 | _Mod3]

import univention.admin.mapping
from univention.admin.log import log


translation = localization.translation('univention/admin')
_ = translation.translate


def import_hook_files() -> None:
    """Load all additional hook files from :file:`.../univention/admin/hooks.d/*.py`"""
    for dir_ in sys.path:
        hooks_d = os.path.join(dir_, 'univention/admin/hooks.d/')
        if os.path.isdir(hooks_d):
            hooks_files = (os.path.join(hooks_d, f) for f in os.listdir(hooks_d) if f.endswith('.py'))
            for fn in hooks_files:
                try:
                    with open(fn, 'rb') as fd:
                        env = {
                            'simpleHook': simpleHook,
                            'AttributeHook': AttributeHook,
                        }
                        byte_code = compile(fd.read(), fn, "exec")
                        exec(byte_code, env)  # noqa: S102
                        sys.modules[__name__].__dict__.update(
                            dict(
                                inspect.getmembers(
                                    SimpleNamespace(**env), lambda m: inspect.isclass(m) and issubclass(m, (simpleHook, AttributeHook)) and m not in (simpleHook, AttributeHook),
                                ),
                            ),
                        )
                    log.debug('importing hook', hook=fn)
                except Exception:
                    log.exception('loading hook failed', hook=fn)


class simpleHook:
    """Base class for a |UDM| hook performing logging."""

    type = 'simpleHook'

    #
    # To use the LDAP connection of the parent UDM call in any of the following
    # methods, use obj.lo and obj.position.
    #

    def map(self, value: Any, encoding=()) -> list[bytes]:
        """
        This method can be overwritten to define special method to map |UDM| property value to |LDAP| attribute value.

        :param value: The UDM property value
        :param encoding: Optional encoding information
        :returns: The list of LDAP attributes.

        .. versionadded:: 5.2-6

          The corresponding ``map```and ``unmap`` methods are available since :uv:erratum:`5.2x414`.
        """
        return univention.admin.mapping.MapToBytes(value, encoding)

    def unmap(self, value: list[bytes], encoding=()) -> Any:
        """
        This method can be overwritten to define special un-map methods to map back from |LDAP| to |UDM|.

        :param value: The list of LDAP attributes
        :param encoding: Optional encoding information
        :returns: The UDM property value.

        .. versionadded:: 5.2-6

          The corresponding ``map```and ``unmap`` methods are available since :uv:erratum:`5.2x414`.
        """
        return univention.admin.mapping.UnmapToUnicode(value, encoding)

    def hook_open(self, obj: univention.admin.handlers.simpleLdap) -> None:
        """
        This method is called by the default open handler just before the current state of all properties is saved.

        :param obj: The |UDM| object instance.
        """
        log.debug('hook_open called')

    def hook_ldap_pre_create(self, obj: univention.admin.handlers.simpleLdap) -> None:
        """
        This method is called before an |UDM| object is created.
        It is called after the module validated all properties but before the add-list is created.

        :param obj: The |UDM| object instance.
        """
        log.debug('hook_ldap_pre_create called')

    def hook_ldap_addlist(self, obj: univention.admin.handlers.simpleLdap, al: AddList = []) -> AddList:
        """
        This method is called before an |UDM| object is created.

        Notice that :py:meth:`hook_ldap_modlist` will also be called next.

        :param obj: The |UDM| object instance.
        :param al: A list of two-tuples (ldap-attribute-name, list-of-values) which will be used to create the LDAP object.
        :returns: The (modified) add-list.
        """
        log.debug('hook_ldap_addlist called')
        return al

    def hook_ldap_post_create(self, obj: univention.admin.handlers.simpleLdap) -> None:
        """
        This method is called after the object was created in |LDAP|.

        :param obj: The |UDM| object instance.
        """
        log.debug('hook_ldap_post_create called')

    def hook_ldap_pre_modify(self, obj: univention.admin.handlers.simpleLdap) -> None:
        """
        This method is called before an |UDM| object is modified.
        It is called after the module validated all properties but before the modification-list is created.

        :param obj: The |UDM| object instance.
        """
        log.debug('hook_ldap_pre_modify called')

    def hook_ldap_modlist(self, obj: univention.admin.handlers.simpleLdap, ml: ModList = []) -> ModList:
        """
        This method is called before an |UDM| object is created or modified.

        :param obj: The |UDM| object instance.
        :param ml: A list of tuples, which are either two-tuples (ldap-attribute-name, list-of-new-values) or three-tuples (ldap-attribute-name, list-of-old-values, list-of-new-values). It will be used to create or modify the |LDAP| object.
        :returns: The (modified) modification-list.
        """
        log.debug('hook_ldap_modlist called')
        return ml

    def hook_ldap_pre_move(self, obj: univention.admin.handlers.simpleLdap) -> None:
        """
        This method is called before the object is moved in |LDAP|.

        :param obj: The |UDM| object instance.
        """
        log.debug('hook_ldap_post_modify called')

    def hook_ldap_post_move(self, obj: univention.admin.handlers.simpleLdap) -> None:
        """
        This method is called after the object was moved in |LDAP|.

        :param obj: The |UDM| object instance.
        """
        log.debug('hook_ldap_post_move called')

    def hook_ldap_post_modify(self, obj: univention.admin.handlers.simpleLdap) -> None:
        """
        This method is called after the object was modified in |LDAP|.

        :param obj: The |UDM| object instance.
        """
        log.debug('hook_ldap_post_modify called')

    def hook_ldap_pre_remove(self, obj: univention.admin.handlers.simpleLdap) -> None:
        """
        This method is called before an |UDM| object is removed.

        :param obj: The |UDM| object instance.
        """
        log.debug('hook_ldap_pre_remove called')

    def hook_ldap_post_remove(self, obj: univention.admin.handlers.simpleLdap) -> None:
        """
        This method is called after the object was removed from |LDAP|.

        :param obj: The |UDM| object instance.
        """
        log.debug('hook_ldap_post_remove called')


class AttributeHook(simpleHook):
    """
    Convenience Hook that essentially implements a mapping
    between |UDM| and |LDAP| for your extended attributes.
    Derive from this class, set :py:attr:`attribute_name` to the name of
    the |UDM| attribute and implement :py:meth:`map_attribute_value_to_udm`
    and :py:meth:`map_attribute_value_to_ldap`.

    .. warning::
        Only derive from this class when you are sure
        every system in your domain has the update installed that
        introduced this hook. (Nov 2018; UCS 4.3-2)
        Otherwise you will get errors when you are distributing your new
        hook via `ucs_registerLDAPExtension --udm_hook`

    .. deprecated:: 5.2-6
        Since UCS 5.2-5-errata :class:`simpleHook` provides :func:`map`
        and :func:`unmap`, which should be used instead.
    """

    udm_attribute_name = None  # not required anymore
    ldap_attribute_name = None  # not required anymore

    version = 3

    def map(self, value: Any, encoding=()) -> list[bytes]:
        return self.map_attribute_value_to_ldap(value)

    def unmap(self, value: list[bytes], encoding=()) -> Any:
        return self.map_attribute_value_to_udm(value)

    def map_attribute_value_to_ldap(self, value: Any) -> list[bytes]:
        """
        Return value as it shall be saved in |LDAP|.

        :param value: The |UDM| value.
        :returns: The |LDAP| value.
        """
        return value

    def map_attribute_value_to_udm(self, value: list[bytes]) -> Any:
        """
        Return value as it shall be used in |UDM| objects.

        The mapped value needs to be syntax compliant.

        :param value: The |LDAP| value.
        :returns: The |UDM| value.
        """
        return value
