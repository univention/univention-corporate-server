# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from .handler import ListenerModuleHandler
    from .handler_configuration import ListenerModuleConfiguration


class ListenerModuleAdapter:
    """
    Adapter to convert the :py:mod:`univention.listener.listener_module interface` to
    the existing listener module interface.

    Use in a classic listener module like this:

        globals().update(ListenerModuleAdapter(MyListenerModuleConfiguration()).get_globals())
    """

    def __init__(self, module_configuration: ListenerModuleConfiguration, *args: Any, **kwargs: Any) -> None:
        """:param ListenerModuleConfiguration module_configuration: configuration object"""
        self.config = module_configuration
        self._ldap_cred: dict[str, str] = {}
        self._module_handler_obj: ListenerModuleHandler | None = None
        self._saved_old: Mapping[str, Sequence[bytes]] = {}
        self._saved_old_dn: str | None = None
        self._rename = False
        self._renamed = False
        self._run_checks()

    def _run_checks(self) -> None:
        pass

    def get_globals(self) -> dict[str, Any]:
        """
        Returns the variables to be written to the module namespace, that
        make up the legacy listener module interface.

        :return: a mapping with keys: `name`, `description`, `filter_s`,
            `attributes`, `modrdn`, `handler`, `initialize`, `clean`, `prerun`,
            `postrun`, `setdata`, ..
        :rtype: dict
        """
        name = self.config.get_name()
        description = self.config.get_description()
        filter_s = self.config.get_ldap_filter() if self.config.get_active() else '(objectClass=listenerModuleDeactivated)'
        attributes = self.config.get_attributes()
        priority = self.config.get_priority()
        modrdn = 1
        handler = self._handler
        initialize = self._lazy_initialize
        clean = self._lazy_clean
        prerun = self._lazy_pre_run
        postrun = self._lazy_post_run
        setdata = self._setdata
        return {
            "name": name,
            "description": description,
            "filter": filter_s,
            "attributes": attributes,
            "priority": priority,
            "modrdn": modrdn,
            "handler": handler,
            "initialize": initialize,
            "clean": clean,
            "prerun": prerun,
            "postrun": postrun,
            "setdata": setdata,
        }

    def _setdata(self, key: str, value: str) -> None:
        """
        Store LDAP connection credentials passes by the listener (one by one)
        to the listener module. Passes them to the handler object once they
        are complete.

        :param str key: one of `basedn`, `basedn`, `bindpw`, `ldapserver`
        :param str value: credentials
        """
        self._ldap_cred[key] = value
        if set(self._ldap_cred) >= {'basedn', 'bindpw', 'ldapserver'}:
            self._module_handler._set_ldap_credentials(
                self._ldap_cred['basedn'],
                self._ldap_cred['binddn'],
                self._ldap_cred['bindpw'],
                self._ldap_cred['ldapserver'],
            )
            self._ldap_cred.clear()

    @property
    def _module_handler(self) -> ListenerModuleHandler:
        """Make sure to not create more than one instance of a listener module."""
        if not self._module_handler_obj:
            self._module_handler_obj = self.config.get_listener_module_instance()
        return self._module_handler_obj

    def _handler(self, dn: str, new: Mapping[str, Sequence[bytes]], old: Mapping[str, Sequence[bytes]], command: str) -> None:
        """
        Function called by listener when a LDAP object matching the filter is
        created/modified/moved/deleted.

        :param str dn: the objects DN
        :param dict new: new LDAP objects attributes
        :param dict old: previous LDAP objects attributes
        :param str command: LDAP modification type
        """
        if command == 'r':
            self._saved_old = old
            self._saved_old_dn = dn
            self._rename = True
            self._renamed = False
            return
        elif command == 'a' and self._rename:
            old = self._saved_old

        try:
            if old and not new:
                self._module_handler.remove(dn, old)
            elif old and new:
                if self._renamed and not self._module_handler.diff(old, new):
                    # ignore second modify call after a move if no non-metadata
                    # attribute changed
                    self._rename = self._renamed = False
                    return
                self._module_handler.modify(dn, old, new, self._saved_old_dn if self._rename else None)
                self._renamed = self._rename
                self._rename = False
                self._saved_old_dn = None
            elif not old and new:
                self._module_handler.create(dn, new)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self._module_handler.error_handler(dn, old, new, command, exc_type, exc_value, exc_traceback)

    def _lazy_initialize(self) -> None:
        return self._module_handler.initialize()

    def _lazy_clean(self) -> None:
        return self._module_handler.clean()

    def _lazy_pre_run(self) -> None:
        return self._module_handler.pre_run()

    def _lazy_post_run(self) -> None:
        return self._module_handler.post_run()
