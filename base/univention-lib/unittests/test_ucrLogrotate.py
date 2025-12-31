#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest


@pytest.fixture
def logrotate_ucr(mock_ucr):
    mock_ucr["logrotate/rotate"] = "weekly"
    mock_ucr["logrotate/rotate/count"] = "12"
    mock_ucr["logrotate/create"] = "640 root adm"
    mock_ucr["logrotate/missingok"] = "yes"
    mock_ucr["logrotate/compress"] = "yes"
    mock_ucr["logrotate/notifempty"] = "yes"
    return mock_ucr


class TestLogrotateConfig:
    def test_empty(self, ucrLogrotate, mock_ucr):
        settings = ucrLogrotate.getLogrotateConfig("my-service", mock_ucr)
        assert settings["compress"] == "compress"
        assert settings["missingok"] == "missingok"
        assert settings["notifempty"] == "notifempty"
        assert len(settings) == 3

    def test_global(self, ucrLogrotate, logrotate_ucr):
        settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
        assert settings["rotate"] == "weekly"
        assert settings["rotate/count"] == "rotate 12"
        assert settings["create"] == "create 640 root adm"
        assert settings["compress"] == "compress"
        assert settings["missingok"] == "missingok"
        assert settings["notifempty"] == "notifempty"
        assert len(settings) == 6

    def test_global_modified(self, ucrLogrotate, logrotate_ucr):
        logrotate_ucr["logrotate/compress"] = "off"
        logrotate_ucr["logrotate/missingok"] = "disabled"
        logrotate_ucr["logrotate/notifempty"] = "no"
        settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
        assert settings["rotate"] == "weekly"
        assert settings["rotate/count"] == "rotate 12"
        assert settings["create"] == "create 640 root adm"
        assert len(settings) == 3

    def test_specific_rotate(self, ucrLogrotate, logrotate_ucr):
        logrotate_ucr["logrotate/my-service/rotate"] = "daily"
        logrotate_ucr["logrotate/my-other-service/rotate"] = "monthly"
        settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
        assert settings["rotate"] == "daily"
        assert settings["rotate/count"] == "rotate 12"
        assert settings["create"] == "create 640 root adm"
        assert settings["compress"] == "compress"
        assert settings["missingok"] == "missingok"
        assert settings["notifempty"] == "notifempty"
        assert len(settings) == 6

    def test_specific_rotate_count(self, ucrLogrotate, logrotate_ucr):
        logrotate_ucr["logrotate/my-service/rotate/count"] = "4"
        logrotate_ucr["logrotate/my-other-service/rotate/count"] = "8"
        settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
        assert settings["rotate"] == "weekly"
        assert settings["rotate/count"] == "rotate 4"
        assert settings["create"] == "create 640 root adm"
        assert settings["compress"] == "compress"
        assert settings["missingok"] == "missingok"
        assert settings["notifempty"] == "notifempty"
        assert len(settings) == 6

    def test_specific_create(self, ucrLogrotate, logrotate_ucr):
        logrotate_ucr["logrotate/my-service/create"] = "660 root root"
        logrotate_ucr["logrotate/my-other-service/create"] = "640 nobody nogroup"
        settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
        assert settings["rotate"] == "weekly"
        assert settings["rotate/count"] == "rotate 12"
        assert settings["create"] == "create 660 root root"
        assert settings["compress"] == "compress"
        assert settings["missingok"] == "missingok"
        assert settings["notifempty"] == "notifempty"
        assert len(settings) == 6

    def test_specific_compress(self, ucrLogrotate, logrotate_ucr):
        logrotate_ucr["logrotate/my-service/compress"] = "no"
        logrotate_ucr["logrotate/my-other-service/compress"] = "yes"
        settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
        assert settings["rotate"] == "weekly"
        assert settings["rotate/count"] == "rotate 12"
        assert settings["create"] == "create 640 root adm"
        assert settings["missingok"] == "missingok"
        assert settings["notifempty"] == "notifempty"
        assert len(settings) == 5

    def test_specific_missing_ok(self, ucrLogrotate, logrotate_ucr):
        logrotate_ucr["logrotate/my-service/missingok"] = "no"
        logrotate_ucr["logrotate/my-other-service/missingok"] = "yes"
        settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
        assert settings["rotate"] == "weekly"
        assert settings["rotate/count"] == "rotate 12"
        assert settings["create"] == "create 640 root adm"
        assert settings["compress"] == "compress"
        assert settings["notifempty"] == "notifempty"
        assert len(settings) == 5

    def test_specific_notifempty(self, ucrLogrotate, logrotate_ucr):
        logrotate_ucr["logrotate/my-service/notifempty"] = "no"
        logrotate_ucr["logrotate/my-other-service/notifempty"] = "yes"
        settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
        assert settings["rotate"] == "weekly"
        assert settings["rotate/count"] == "rotate 12"
        assert settings["create"] == "create 640 root adm"
        assert settings["compress"] == "compress"
        assert settings["missingok"] == "missingok"
        assert len(settings) == 5

    def test_specific_notifempty_modified(self, ucrLogrotate, logrotate_ucr):
        logrotate_ucr["logrotate/notifempty"] = "no"
        logrotate_ucr["logrotate/my-service/notifempty"] = "yes"
        settings = ucrLogrotate.getLogrotateConfig("my-service", logrotate_ucr)
        assert settings["rotate"] == "weekly"
        assert settings["rotate/count"] == "rotate 12"
        assert settings["create"] == "create 640 root adm"
        assert settings["compress"] == "compress"
        assert settings["missingok"] == "missingok"
        assert settings["notifempty"] == "notifempty"
        assert len(settings) == 6
