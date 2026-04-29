#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Unit tests for update_udm_extensions"""

from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from univention.updater.scripts.updater import update_udm_extensions


_LISTENER = "/usr/lib/univention-directory-listener/system/udm_extension.py"
_STATUS = "/var/lib/univention-directory-listener/handlers/udm_extension"


def _mock_paths(mocker, listener_exists=True, status_exists=True, status_values=None):
    listener = MagicMock()
    listener.exists.return_value = listener_exists

    status = MagicMock()
    status.exists.return_value = status_exists
    status.read_text.side_effect = status_values or ["3\n"]

    def factory(path):
        if path == _LISTENER:
            return listener
        if path == _STATUS:
            return status
        return MagicMock()

    mocker.patch("univention.updater.scripts.updater.Path", side_effect=factory)
    return listener, status


class TestUpdateUdmExtensions:

    @pytest.fixture(autouse=True)
    def _patches(self, mocker):
        self.mock_log = mocker.patch("univention.updater.scripts.updater.log")
        self.mock_sleep = mocker.patch("univention.updater.scripts.updater.time.sleep")
        self.mock_check_call = mocker.patch("univention.updater.scripts.updater.check_call")

    def _logged(self, fragment):
        return any(fragment in str(c) for c in self.mock_log.call_args_list)

    def test_no_listener_skips_resync(self, mocker):
        _mock_paths(mocker, listener_exists=False)

        update_udm_extensions()

        self.mock_check_call.assert_not_called()

    def test_resync_process_error_is_logged(self, mocker):
        _mock_paths(mocker)
        self.mock_check_call.side_effect = CalledProcessError(1, "univention-directory-listener-ctrl")

        update_udm_extensions()

        assert self._logged("Failed")

    def test_status_reaches_three_logs_success(self, mocker):
        _mock_paths(mocker, status_values=["3\n"])

        update_udm_extensions()

        assert self._logged("Finished")

    def test_status_file_absent_during_resync_then_succeeds(self, mocker):
        _, status = _mock_paths(mocker, status_values=["3\n"])
        status.exists.side_effect = [False, False, True]

        update_udm_extensions()

        assert self._logged("Finished")

    def test_status_absent_until_timeout(self, mocker):
        _, status = _mock_paths(mocker)
        status.exists.return_value = False
        mocker.patch("univention.updater.scripts.updater.time.monotonic", side_effect=[0, 301])

        update_udm_extensions()

        assert self._logged("not finished")

    def test_timeout_logs_warning(self, mocker):
        _mock_paths(mocker, status_values=["1\n"] * 10)
        mocker.patch("univention.updater.scripts.updater.time.monotonic", side_effect=[0, 301])

        update_udm_extensions()

        assert self._logged("not finished")
