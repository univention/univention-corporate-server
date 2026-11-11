#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin


def test_searchable_is_linked_to_dontsearch():
    prop = univention.admin.property(searchable=False)

    assert prop.dontsearch is True
    assert prop.searchable is False

    prop.dontsearch = False
    assert prop.searchable is True

    prop.searchable = False
    assert prop.dontsearch is True
