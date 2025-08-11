#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import pytest


class TestUCR:
    def __init__(self):
        self.items = {}

    def get(self, key, default=None):
        return self.items.get(key, default)

    def get_int(self, key, default=None):
        val = self.get(key)
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    def __contains__(self, key):
        return key in self.items

    def __getitem__(self, key):
        # raises KeyError... lets see how this ends
        return self.items[key]

    def __delitem__(self, key):
        del self.items[key]

    def __setitem__(self, key, value):
        self.items[key] = value

    def keys(self):
        return self.items.keys()

    def is_false(self, key=None, default=False, value=None):
        if value is None:
            value = self.get(key)  # type: ignore
            if value is None:
                return default
        return value.lower() in ('no', 'false', '0', 'disable', 'disabled', 'off')

    def is_true(self, key=None, default=False, value=None):
        if value is None:
            value = self.get(key)  # type: ignore
            if value is None:
                return default
        return value.lower() in ('yes', 'true', '1', 'enable', 'enabled', 'on')

    def load(self):
        pass


@pytest.fixture
def mock_ucr():
    return TestUCR()
