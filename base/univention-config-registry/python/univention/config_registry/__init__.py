# -*- coding: utf-8 -*-
#
"""Univention Configuration Registry module."""
#  main configuration registry classes
#
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
from __future__ import print_function
from univention.config_registry.backend import StrictModeException, SCOPE, ConfigRegistry  # noqa F401
from univention.config_registry.handler import run_filter as filter, ConfigHandlers as configHandlers  # noqa F401
from univention.config_registry.misc import key_shell_escape, validate_key, INVALID_KEY_CHARS as invalid_key_chars  # noqa F401
from univention.config_registry.filters import filter_shell, filter_keys_only, filter_sort  # noqa F401
from univention.config_registry.frontend import (  # noqa F401
	REPLOG_FILE, UnknownKeyException, main,
	handler_set, handler_unset, handler_commit, handler_filter,
	handler_get, handler_dump, handler_search,
	handler_register, handler_unregister, handler_update,
)
from univention.debhelper import parseRfc822  # noqa F401

if __name__ == '__main__':
	import sys
	try:
		main(sys.argv[1:])
	except StrictModeException as ex2:
		print(('E: UCR is running in strict mode and thus cannot accept the given input:'), file=sys.stderr)
		print(ex2, file=sys.stderr)
		sys.exit(1)

# vim:set sw=4 ts=4 noet:
