# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| log functionality"""

import logging

from univention.logging import Structured


__all__ = ('log',)
log = Structured(logging.getLogger('ADMIN'))
log_ldap = Structured(logging.getLogger('LDAP'))
