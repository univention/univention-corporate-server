#!/usr/bin/python3
#
# Univention App Center
#  univention-app wrapper for ucr functions
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from copy import deepcopy

from univention.config_registry import ConfigRegistry
from univention.config_registry.frontend import ucr_update
from univention.config_registry.handler import run_filter


_UCR = ConfigRegistry()
_UCR.load()


def ucr_load():
    _UCR.load()


def ucr_get(key, default=None):
    return _UCR.get(key, default)


def ucr_get_int(key, default=None):
    return _UCR.get_int(key, default)


def ucr_save(values):
    changed_values = {}
    _UCR.load()
    for k, v in values.items():
        if _UCR.get(k) != v:
            changed_values[k] = v  # noqa: PERF403
    if changed_values:
        ucr_update(_UCR, changed_values)
    return changed_values


def ucr_includes(key):
    return key in _UCR


def ucr_is_true(key, default=False, value=None):
    return _UCR.is_true(key, default=default, value=value)


def ucr_is_false(key):
    return _UCR.is_false(key)


def ucr_keys():
    return _UCR.keys()


def ucr_evaluated_as_true(value):
    if isinstance(value, str):
        value = value.lower()
    return _UCR.is_true(value=value)


def ucr_run_filter(string, additional=None):
    ucr = _UCR
    if additional:
        # memory only ucr. not saved.
        # if we would... NEVER __setitem__ on ucr!
        ucr = deepcopy(ucr)
        for k, v in additional.items():
            ucr[k] = str(v)
    return run_filter(string, ucr).decode('UTF-8')


def ucr_instance():
    return _UCR
