# SPDX-FileCopyrightText: 2018-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Collection


class UdmError(Exception):
    """Base class of Exceptions raised by (simplified) UDM modules."""

    msg = ''

    def __init__(self, msg: str | None = None, dn: str | None = None, module_name: str | None = None) -> None:
        msg = msg or self.msg
        super().__init__(msg)
        self.dn = dn
        self.module_name = module_name


class ApiVersionMustNotChange(UdmError):
    """Raised when UDM.version() is called twice."""

    msg = 'The version of an UDM instance must not be changed.'


class ConnectionError(UdmError):
    """Raised when something goes wrong getting a connection."""


class ApiVersionNotSupported(UdmError):
    def __init__(
        self,
        msg: str | None = None,
        module_name: str | None = None,
        requested_version: int | None = None,
    ) -> None:
        self.requested_version = requested_version
        msg = msg or f'Module {module_name!r} is not supported in API version {requested_version!r}.'
        super().__init__(msg, module_name=module_name)


class CreateError(UdmError):
    """Raised when an error occurred when creating an object."""


class DeletedError(UdmError):
    def __init__(self, msg: str | None = None, dn: str | None = None, module_name: str | None = None) -> None:
        msg = msg or 'Object{} has already been deleted.'.format(f' {dn!r}' if dn else '')
        super().__init__(msg, dn, module_name)


class DeleteError(UdmError):
    """Raised when a client tries to delete a UDM object but fails."""

    def __init__(self, msg: str | None = None, dn: str | None = None, module_name: str | None = None) -> None:
        msg = msg or 'Object{} could not be deleted.'.format(f' {dn!r}' if dn else '')
        super().__init__(msg, dn, module_name)


class NotYetSavedError(UdmError):
    """
    Raised when a client tries to delete or reload a UDM object that is not
    yet saved.
    """

    msg = 'Object has not been created/loaded yet.'


class ModifyError(UdmError):
    """Raised if an error occurred when modifying an object."""


class MoveError(UdmError):
    """Raised if an error occurred when moving an object."""


class NoApiVersionSet(UdmError):
    """
    Raised when UDM.get() or UDM.obj_by_id() is used before setting an API
    version.
    """

    msg = 'No API version has been set.'


class NoObject(UdmError):
    """Raised when a UDM object could not be found at a DN."""

    def __init__(self, msg: str | None = None, dn: str | None = None, module_name: str | None = None) -> None:
        msg = msg or f'No object found at DN {dn!r}.'
        super().__init__(msg, dn, module_name)


class NoSuperordinate(UdmError):
    """Raised when no superordinate was supplied but one is needed."""

    def __init__(self, msg: str | None = None, dn: str | None = None, module_name: str | None = None, superordinate_types: Collection[str] | None = None) -> None:
        msg = msg or 'No superordinate was supplied, but one of type{} {} is required to create/save a {} object.'.format(
            's' if len(superordinate_types or ()) > 1 else '', ', '.join(superordinate_types or ()), module_name)
        super().__init__(msg, dn, module_name)


class SearchLimitReached(UdmError):
    """Raised when the search results in more objects than specified by the sizelimit."""

    def __init__(self, msg: str | None = None, dn: str | None = None, module_name: str | None = None, search_filter: str | None = None, sizelimit: int | None = None) -> None:
        msg = msg or 'The search_filter {} resulted in more objects than the specified sizelimit of {} allowed.'.format(
            search_filter or "''", sizelimit or "/",
        )
        self.search_filter = search_filter
        self.sizelimit = sizelimit
        super().__init__(msg, dn, module_name)


class MultipleObjects(UdmError):
    """
    Raised when more than one UDM object was found when there should be at
    most one.
    """


class UnknownModuleType(UdmError):
    """Raised when an LDAP object has no or empty attribute univentionObjectType."""

    def __init__(self, msg: str | None = None, dn: str | None = None, module_name: str | None = None) -> None:
        msg = msg or f'No or empty attribute "univentionObjectType" found at DN {dn!r}.'
        super().__init__(msg, dn, module_name)


class UnknownProperty(UdmError):
    """
    Raised when a client tries to set a property on :py:attr:`BaseObject.props`,
    that it does not support.
    """


class WrongObjectType(UdmError):
    """
    Raised when the LDAP object to be loaded does not match the module type
    (:py:attr:`BaseModule.name`).
    """

    def __init__(self, msg: str | None = None, dn: str | None = None, module_name: str | None = None, univention_object_type: str | None = None) -> None:
        msg = msg or f'Wrong UDM module: {dn!r} is not a {module_name!r}, but a {univention_object_type!r}.'
        super().__init__(msg, dn, module_name)
