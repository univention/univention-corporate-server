#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from importlib import reload
from os import path

import pytest


@pytest.fixture
def dynamic_class():
    from univention import portal
    return portal.get_dynamic_classes


# Helper function fixtures


@pytest.fixture
def patch_object_module(mocker):
    """Helper to patch module level library imports of an object or class"""

    def _(obj, module_name):
        return mocker.patch(f"{obj.__module__}.{module_name}")

    return _


@pytest.fixture
def get_file_path(request):
    """Helper to get the absolute path of test files in the unittests directory"""
    unittest_path = request.fspath.dirname
    files_directory = "files"

    def _(file_name):
        return path.join(unittest_path, files_directory, file_name)

    return _


@pytest.fixture
def mock_portal_config(mocker):
    """Returns a callable which can be used to inject configuration values."""
    from univention.portal import config

    reload(config)
    mocker.patch.object(config.load, "never_loaded", False)

    def _mock_portal_config(values):
        mocker.patch.object(config, "_DB", values)

    return _mock_portal_config


@pytest.fixture
def mocked_portal_config(get_file_path):
    from univention.portal import config

    reload(config)
    config._CONF = get_file_path("config*.json")
    return config
