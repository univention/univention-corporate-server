#!/usr/bin/pytest-3
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

import univention.radius.utils as mut


@pytest.mark.parametrize("text,mac", [
    ("00:11:22:33:44:55", "00:11:22:33:44:55"),
    ("00-11-22-33-44-55", "00:11:22:33:44:55"),
    ("0011.2233.4455", "00:11:22:33:44:55"),
    ("001122334455", "00:11:22:33:44:55"),
])
def test_mac(text, mac):
    assert mut.decode_stationId(text) == mac


@pytest.mark.parametrize("text,user", [
    ("user", "user"),
    ("host/foo.bar", "foo$"),
])
def test_username(text, user):
    assert mut.parse_username(text) == user
