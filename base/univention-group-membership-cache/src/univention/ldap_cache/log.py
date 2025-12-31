#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import logging
from typing import Any


def log(*msgs: Any) -> None:
    logger = logging.getLogger('univention.ldap_cache')
    logger.info(*msgs)


def debug(*msgs: Any) -> None:
    logger = logging.getLogger('univention.ldap_cache')
    logger.debug(*msgs)
