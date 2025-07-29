#
#  main configuration registry classes
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Univention Configuration Registry module."""

from lazy_object_proxy import Proxy

from univention.config_registry.backend import (  # noqa: F401
    SCOPE, ConfigRegistry, Load, ReadOnlyConfigRegistry as _RCR, StrictModeException,
)
from univention.config_registry.filters import filter_keys_only, filter_shell, filter_sort  # noqa: F401
from univention.config_registry.frontend import (  # noqa: F401
    REPLOG_FILE, UnknownKeyException, handler_commit, handler_dump, handler_filter, handler_get, handler_register,
    handler_search, handler_set, handler_unregister, handler_unset, handler_update, main,
)
# ruff: noqa: A004
from univention.config_registry.handler import ConfigHandlers as configHandlers, run_filter as filter  # noqa: F401
from univention.config_registry.misc import (  # noqa: F401
    INVALID_KEY_CHARS as invalid_key_chars, key_shell_escape, validate_key,
)
from univention.debhelper import parseRfc822  # noqa: F401


ucr = Proxy(lambda: _RCR().load(autoload=Load.ONCE))  # type: _RCR
ucr_live = Proxy(lambda: _RCR().load(autoload=Load.ALWAYS))  # type: _RCR


def ucr_factory():  # type: () -> ConfigRegistry
    """
    Factory method to return private loaded UCR instance.

    :returns: A private UCR instance.
    """
    return ConfigRegistry().load()
