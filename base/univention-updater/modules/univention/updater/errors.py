#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright 2008-2021 Univention GmbH
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
"""
Univention Updater exceptions.
"""
try:
    from typing import Set  # noqa F401
except ImportError:
    pass


class UpdaterException(Exception):
    """
    The root of all updater exceptions.
    """


class RequiredComponentError(UpdaterException):
    """
    Signal required component not available.

    :param str version: The UCS release version.
    :param components: A collection of components.
    :type components: set(str)
    """

    def __init__(self, version, components):
        # type: (str, Set[str]) -> None
        self.version = version
        self.components = components

    def __str__(self):
        # type: () -> str
        """
        >>> '%s' % RequiredComponentError('4.0-0', set(('a',)))
        "The update to UCS 4.0-0 is blocked because the component 'a' is marked as required."
        >>> '%s' % RequiredComponentError('4.0-0', set(('a', 'b'))) #doctest: +ELLIPSIS
        "The update to UCS 4.0-0 is blocked because the components '...', '...' are marked as required."
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
    """

    def __init__(self, phase, order, component, script):
        # type: (str, str, str, str) -> None
        Exception.__init__(self, phase, order, component, script)


class DownloadError(UpdaterException):
    """
    Signal temporary error in network communication.
    """

    def __str__(self):
        # type: () -> str
        return "Error downloading %s: %d" % self.args


class ConfigurationError(UpdaterException):
    """
    Signal permanent error in configuration.
    """

    def __str__(self):
        # type: () -> str
        return "Configuration error: %s" % self.args[1]


class VerificationError(ConfigurationError):
    """
    Signal permanent error in script verification.
    """

    def __str__(self):
        # type: () -> str
        return "Verification error: %s" % self.args[1]


class CannotResolveComponentServerError(ConfigurationError):
    """
    Signal permanent error in component configuration.

    :param str component: The name of the component.
    :param bool for_mirror_list: `True` if the error happened while generating the list of repositories to mirror, `False` while generating the list of repositories for the server itself.
    """

    def __init__(self, component, for_mirror_list):
        # type: (str, bool) -> None
        self.component = component
        self.for_mirror_list = for_mirror_list

    def __str__(self):
        # type: () -> str
        return "Cannot resolve component server for disabled component '%s' (mirror_list=%s)." % (self.component, self.for_mirror_list)


class ProxyError(ConfigurationError):
    """
    Signal permanent error in proxy configuration.
    """

    def __str__(self):
        # type: () -> str
        return "Proxy configuration error: %s %s" % (self.args[1], self.args[0])


class UnmetDependencyError(UpdaterException):
    """
    Signal unmet package dependencies
    """

    def __str__(self):
        # type: () -> str
        return "You have unmet dependencies %s" % self.args[0]


if __name__ == '__main__':
    import doctest
    exit(doctest.testmod()[0])
