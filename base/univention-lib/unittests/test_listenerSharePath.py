#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import doctest


def test_docstrings(listenerSharePath):
    assert doctest.testmod(listenerSharePath)
