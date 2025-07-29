#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#


def test_setup_logger():
    from univention.portal import log

    log.setup_logger()
    unittest_logger = log.get_logger("unittest")
    unittest_logger.info("test_setup_logger works")
