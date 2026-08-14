#!/usr/bin/python3
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import sys
import types
from unittest.mock import MagicMock

import pytest
from univentionunittests import import_module


HOSTNAME = 'replica'
DOMAINNAME = 'example.test'
FQDN = ('%s.%s' % (HOSTNAME, DOMAINNAME)).encode('ASCII')


class PolicyResultFailed(Exception):
    """Stand-in for :class:`univention.lib.policy_result.PolicyResultFailed`, same signature."""

    def __init__(self, message, returncode):
        super().__init__(message)
        self.returncode = returncode


class FakeLDAP:
    """Minimal stand-in for :class:`univention.uldap.access`."""

    def __init__(self) -> None:
        self.objects: dict[str, dict[str, list[bytes]]] = {}
        self.lo = MagicMock()

    def get(self, dn):
        # uldap returns an empty dict for a DN which does not exist
        return self.objects.get(dn, {})


def _stub_modules():
    """
    Provide the modules `quota.py` imports.

    `listener` only exists inside the directory listener process, and the
    `univention` packages are not build dependencies of this package. The
    stub for `univention.lib.policy_result` carries a real exception class,
    because `postrun()` catches it.
    """
    listener = types.ModuleType('listener')
    listener.setuid = MagicMock(name='listener.setuid')
    listener.unsetuid = MagicMock(name='listener.unsetuid')
    listener.configRegistry = {'hostname': HOSTNAME, 'domainname': DOMAINNAME}

    policy_result = types.ModuleType('univention.lib.policy_result')
    policy_result.PolicyResultFailed = PolicyResultFailed
    policy_result.policy_result = MagicMock(name='policy_result')

    univention = types.ModuleType('univention')
    univention.lib = types.ModuleType('univention.lib')
    univention.lib.policy_result = policy_result
    univention.debug = MagicMock(name='univention.debug')
    univention.uldap = MagicMock(name='univention.uldap')

    sys.modules.update({
        'listener': listener,
        'univention': univention,
        'univention.lib': univention.lib,
        'univention.lib.policy_result': policy_result,
        'univention.debug': univention.debug,
        'univention.uldap': univention.uldap,
        'ldap': MagicMock(name='ldap'),
        'ldap.filter': MagicMock(name='ldap.filter'),
    })


_stub_modules()


@pytest.fixture(scope='session')
def quota():
    src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return import_module('quota', src_path, 'quota', use_installed=False)


@pytest.fixture
def ud(quota):
    """The mocked `univention.debug` module, reset for each test."""
    quota.ud.reset_mock()
    return quota.ud


@pytest.fixture
def cache(quota, tmp_path, monkeypatch):
    """Redirect the share cache and its todo directory into a temporary directory."""
    todo_dir = tmp_path / 'todo'
    todo_dir.mkdir()
    monkeypatch.setattr(quota, 'SHARE_CACHE_DIR', str(tmp_path))
    monkeypatch.setattr(quota, 'SHARE_CACHE_TODO_DIR', str(todo_dir))
    return tmp_path


@pytest.fixture
def lo(quota, monkeypatch):
    connection = FakeLDAP()
    monkeypatch.setattr(quota, '_get_ldap_connection', lambda: connection)
    return connection


@pytest.fixture
def policy_result(quota):
    """The stubbed `univention.lib.policy_result` module."""
    module = sys.modules['univention.lib.policy_result']
    module.policy_result.reset_mock(side_effect=True, return_value=True)
    return module
