#!/usr/bin/python3
# vim:set fileencoding=utf-8:
# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Unit test for univention.config_registry.filters."""

import pytest

import univention.config_registry.filters as ucrf


@pytest.mark.parametrize("text,ret", [
    ([], []),
    (["key: val"], ["key=val"]),
    (["other"], ["other=''"]),
],)
def test_shell(text, ret,):
    assert ucrf.filter_shell(None, text,) == ret


@pytest.mark.parametrize("text,ret", [
    ([], []),
    (["key: val"], ["key"]),
],)
def test_keys_only(text, ret,):
    assert ucrf.filter_keys_only(None, text,) == ret


@pytest.mark.parametrize("text,ret", [
    ([], []),
    (["b: b", "a: a"], ["a: a", "b: b"]),
],)
def test_sort(text, ret,):
    assert ucrf.filter_sort(None, text,) == ret
