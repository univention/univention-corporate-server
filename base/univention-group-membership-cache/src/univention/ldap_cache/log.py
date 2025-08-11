#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import logging
from typing import Any  # noqa: F401


def log(*msgs):
    # type: (*Any) -> None
    logger = logging.getLogger('univention.ldap_cache')
    logger.info(*msgs)


def debug(*msgs):
    # type: (*Any) -> None
    logger = logging.getLogger('univention.ldap_cache')
    logger.debug(*msgs)
