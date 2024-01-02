# -*- coding: utf-8 -*-
#
#  main configuration registry classes
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2024 Univention GmbH
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
