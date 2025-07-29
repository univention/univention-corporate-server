#!/usr/bin/python3
# SPDX-FileCopyrightText: 2008-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Univention Updater exceptions."""


class UpdaterException(Exception):
    """
    The root of all updater exceptions.

    >>> raise UpdaterException()  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    univention.updater.errors.UpdaterException
    """


class RequiredComponentError(UpdaterException):
    """
    Signal required component not available.

    :param str version: The UCS release version.
    :param components: A collection of components.
    :type components: set(str)
    """

    def __init__(self, version: str, components: set[str]) -> None:
        self.version = version
        self.components = components

    def __str__(self) -> str:
        """
        >>> raise RequiredComponentError('4.0-0', set(('a',)))  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        univention.updater.errors.RequiredComponentError: The update to UCS 4.0-0 is blocked because the component 'a' is marked as required.
        >>> raise RequiredComponentError('4.0-0', set(('a', 'b')))  #doctest: +ELLIPSIS,+IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        univention.updater.errors.RequiredComponentError: The update to UCS 4.0-0 is blocked because the components '...', '...' are marked as required.
        """
        return (
            "The update to UCS %s is blocked because the component %s is marked as required."
            if len(self.components) == 1
            else "The update to UCS %s is blocked because the components %s are marked as required."
        ) % (self.version, ', '.join("'%s'" % (_,) for _ in self.components))


class PreconditionError(UpdaterException):
    """
    Signal abort by release or component pre-/post-update script.

    :param str phase: either `preup` or `postup`.
    :param str order: either `pre` or `main` or `post`.
    :param str component: The name of the component or None.
    :param str script: The name of the failing script.

    >>> raise PreconditionError('preup', 'main', None, 'preup.sh')  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    univention.updater.errors.PreconditionError: ('preup', 'main', None, 'preup.sh')
    """

    def __init__(self, phase: str, order: str, component: str, script: str) -> None:
        Exception.__init__(self, phase, order, component, script)


class DownloadError(UpdaterException):
    """
    Signal temporary error in network communication.

    >>> raise DownloadError("file:///preup.sh", 404)  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    univention.updater.errors.DownloadError: Error downloading file:///preup.sh: 404
    """

    def __str__(self) -> str:
        return "Error downloading %s: %d" % self.args


class ConfigurationError(UpdaterException):
    """
    Signal permanent error in configuration.

    >>> raise ConfigurationError("file:///preup.sh", "not found")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    univention.updater.errors.ConfigurationError: Configuration error: not found
    """

    def __str__(self) -> str:
        return "Configuration error: %s" % self.args[1]


class VerificationError(ConfigurationError):
    """
    Signal permanent error in script verification.

    >>> raise VerificationError("file:///preup.sh", "not signed")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    univention.updater.errors.VerificationError: Verification error: not signed
    """

    def __str__(self) -> str:
        return "Verification error: %s" % self.args[1]


class CannotResolveComponentServerError(ConfigurationError):
    """
    Signal permanent error in component configuration.

    :param str component: The name of the component.
    :param bool for_mirror_list: `True` if the error happened while generating the list of repositories to mirror, `False` while generating the list of repositories for the server itself.

    >>> raise CannotResolveComponentServerError("comp", False)  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    univention.updater.errors.CannotResolveComponentServerError: Cannot resolve component server for disabled component 'comp' (mirror_list=False).
    """

    def __init__(self, component: str, for_mirror_list: bool) -> None:
        self.component = component
        self.for_mirror_list = for_mirror_list

    def __str__(self) -> str:
        return "Cannot resolve component server for disabled component '%s' (mirror_list=%s)." % (self.component, self.for_mirror_list)


class ProxyError(ConfigurationError):
    """
    Signal permanent error in proxy configuration.

    >>> raise ProxyError("file:///preup.sh", "blocked")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    univention.updater.errors.ProxyError: Proxy configuration error: blocked file:///preup.sh
    """

    def __str__(self) -> str:
        return "Proxy configuration error: %s %s" % (self.args[1], self.args[0])


class UnmetDependencyError(UpdaterException):
    """
    Signal unmet package dependencies

    >>> raise UnmetDependencyError("stderr")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    univention.updater.errors.UnmetDependencyError: You have unmet dependencies stderr
    """

    def __str__(self) -> str:
        return "You have unmet dependencies %s" % self.args[0]
