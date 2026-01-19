#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test that tracebacks in custom hook and sytanx files show the filename
## tags: [udm,udm-extensions,udm-ldapextensions,apptest,fbest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous


import traceback
from unittest.mock import patch

import pytest

from univention.admin.hook import import_hook_files
from univention.admin.syntax import import_syntax_files


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Fixture to provide a temporary directory and ensure it's in sys.path."""
    test_dir = str(tmp_path)
    monkeypatch.syspath_prepend(test_dir)
    return tmp_path


def test_hook_traceback_contains_filename(test_env):
    hook_dir = test_env / 'univention/admin/hooks.d'
    hook_dir.mkdir(parents=True)
    hook_file = hook_dir / 'broken_hook.py'
    hook_file.write_text("raise RuntimeError('Hook error')")

    captured_traceback = []

    def mock_exception(msg, *args, **kwargs):
        captured_traceback.append(traceback.format_exc())

    with patch('univention.admin.hook.log') as mock_log:
        mock_log.exception.side_effect = mock_exception
        import_hook_files()

        assert mock_log.exception.called
        assert 'broken_hook.py' in captured_traceback[0]
        assert 'RuntimeError: Hook error' in captured_traceback[0]


def test_syntax_traceback_contains_filename(test_env):
    syntax_dir = test_env / 'univention/admin/syntax.d'
    syntax_dir.mkdir(parents=True)
    syntax_file = syntax_dir / 'broken_syntax.py'
    syntax_file.write_text("raise RuntimeError('Syntax error')")

    captured_traceback = []

    def mock_exception(msg, *args, **kwargs):
        captured_traceback.append(traceback.format_exc())

    with patch('univention.admin.syntax.log') as mock_log:
        mock_log.exception.side_effect = mock_exception
        import_syntax_files()

        assert mock_log.exception.called
        assert 'broken_syntax.py' in captured_traceback[0]
        assert 'RuntimeError: Syntax error' in captured_traceback[0]
