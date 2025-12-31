# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


"""
Listener module API

To create a listener module (LM) with this API, create a Python file in
:file:`/usr/lib/univention-directory-listener/system/` which includes:

1. a subclass of :py:class:`ListenerModuleHandler`
2. with an inner class `Configuration` that has at least the class attributes `name`, `description` and `ldap_filter`

See :file:`/usr/share/doc/univention-directory-listener/examples/` for examples.
"""


from .api_adapter import ListenerModuleAdapter
from .exceptions import ListenerModuleConfigurationError, ListenerModuleRuntimeError
from .handler import ListenerModuleHandler
from .handler_configuration import ListenerModuleConfiguration


__all__ = [
    'ListenerModuleAdapter',
    'ListenerModuleConfiguration',
    'ListenerModuleConfigurationError',
    'ListenerModuleHandler',
    'ListenerModuleRuntimeError',
]
