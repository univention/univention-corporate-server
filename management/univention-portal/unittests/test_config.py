#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import pytest


def test_load_config_success(mocked_portal_config):
    # Set up
    mocked_portal_config._DB = {"old": "value"}
    expected_config = {"port": 8090, "fqdn": "dataport.ucs", "url": "http://127.0.0.1:8090", "test": True}
    # Execute
    assert mocked_portal_config.load.never_loaded is True
    mocked_portal_config.load()
    assert mocked_portal_config.load.never_loaded is False
    assert expected_config == mocked_portal_config._DB


def test_load_config_error(mocker, mocked_portal_config):
    # Set up
    mocked_portal_config._DB = {"old": "value"}
    mocker.patch.object(mocked_portal_config, "open", side_effect=EnvironmentError)
    # Execute
    assert mocked_portal_config.load.never_loaded is True
    mocked_portal_config.load()
    assert {} == mocked_portal_config._DB
    assert mocked_portal_config.load.never_loaded is True
    assert {} == mocked_portal_config._DB


def test_fetch_key(mocker, mocked_portal_config):
    # Set up
    def config_loaded():
        mocked_portal_config.load.never_loaded = False

    load_mock = mocker.patch.object(mocked_portal_config, "load", side_effect=config_loaded)
    mocked_portal_config._DB = {"port": 443, "fqdn": "dataport.ucs"}
    # Execute
    assert mocked_portal_config.fetch("port") == 443
    assert mocked_portal_config.load.never_loaded is False
    assert mocked_portal_config.fetch("fqdn") == "dataport.ucs"
    with pytest.raises(KeyError):
        mocked_portal_config.fetch("no_key")
    load_mock.assert_called_once()
