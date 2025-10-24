#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: update-check test
## packages:
##   - univention-appcenter
## bugs: [52308]
## tags: [appcenter]

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from univention.appcenter.actions.update import Update
from univention.appcenter.app_cache import AppCache


@pytest.fixture
def app_cache_mock():
    app_cache_mock = Mock(spec=AppCache)
    app_cache_mock.get_cache_dir.return_value = '/tmp/'
    app_cache_mock.get_server.return_value = 'https://127.0.0.1:3000'
    app_cache_mock.get_ucs_version.return_value = '5.2'

    return app_cache_mock


@pytest.fixture
def mock_update_common():
    """Provides common patches for Update tests"""
    update = Update()
    with patch.object(update, '_download_files', return_value=True), \
            patch.object(update, '_verify_file'), \
            patch.object(update, '_extract_archive'):
        yield update


def test_update_zsync(mock_update_common, app_cache_mock):
    update = mock_update_common
    with patch.object(update, '_download_apps_directly') as mock_direct, \
            patch.object(update, '_download_apps_zsync') as mock_zsync:
        update._download_apps(app_cache_mock)

        mock_zsync.assert_called_once_with(app_cache_mock)
        mock_direct.assert_not_called()


def test_update_skip_zsync(mock_update_common, app_cache_mock):
    update = mock_update_common
    with patch.object(update, '_download_apps_directly') as mock_direct, \
            patch.object(update, '_download_apps_zsync') as mock_zsync, \
            patch('univention.appcenter.actions.update.ucr_is_true') as ucr_mock:
        ucr_mock.side_effect = lambda var: var == 'appcenter/update/skip-zsync'
        update._download_apps(app_cache_mock)

        mock_direct.assert_called_once_with(app_cache_mock)
        mock_zsync.assert_not_called()


def test_fallback_on_zsync_failure(mock_update_common, app_cache_mock):
    update = mock_update_common

    subprocess_return = Mock()
    subprocess_return.returncode = 1
    with patch.object(update, '_download_apps_directly') as mock_direct, \
            patch.object(update, '_subprocess', return_value=subprocess_return) as mock_subprocess:
        update._download_apps(app_cache_mock)

        mock_direct.assert_called_once_with(app_cache_mock)
        mock_subprocess.assert_called_once()


@pytest.fixture
def zsync_stub(tmp_path: Path):
    zsync_stub_path = tmp_path / 'zsync'
    with zsync_stub_path.open('w') as fd:
        fd.write("""#!/bin/sh
sleep 10
exit 1""")
    zsync_stub_path.chmod(0o755)

    yield str(zsync_stub_path)

    zsync_stub_path.unlink()


def test_zsync_timeout(mock_update_common, zsync_stub: str, app_cache_mock):
    update = mock_update_common
    with patch.object(update, '_download_apps_directly') as mock_direct, \
            patch.object(update, '_subprocess', wraps=update._subprocess) as subprocess_mock, \
            patch('univention.appcenter.actions.update.ucr_get_int') as ucr_mock, \
            patch('univention.appcenter.actions.update.ZSYNC_BINARY_PATH', zsync_stub):
        ucr_mock.side_effect = lambda var, default=None: 1
        update._download_apps(app_cache_mock)
        mock_direct.assert_called_once_with(app_cache_mock)
        subprocess_mock.assert_called_once()
        call_args = subprocess_mock.call_args[0][0]
        assert call_args[0] == 'timeout'
        assert '1' in call_args


@pytest.fixture(params=['false', 'true'])
def set_zsync(ucr, request):
    ucr.handler_set([f'appcenter/update/skip-zsync={request.param}'])


@pytest.mark.usefixtures('set_zsync')
def test_univention_app_update(tmp_path: Path):
    subprocess.check_call(['univention-app', 'update', '--cache-dir', str(tmp_path)])
    assert len(list(tmp_path.iterdir())) > 5
