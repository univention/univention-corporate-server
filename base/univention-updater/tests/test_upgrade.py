#!/usr/bin/python3
# pylint: disable-msg=C0301,W0212,C0103,R0904
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Unit test for univention.updater.scripts.upgrade"""

import sys

import pytest


if sys.version_info < (3,):
    pytest.skip(
        "unsupported Python version, upgrade.py package from scripts folder is not available for Python2 skipping test.",
        allow_module_level=True,
    )

from univention.updater.scripts.upgrade import parse_args


def test_parse_args_rejects_invalid_update_to_bug49061(mocker):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        mocker.patch('sys.argv', ['/usr/sbin/univention-upgrade', '--updateto=4.0.0'])
        parse_args()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1


def test_parse_args_accepts_valid_update_to_bug49061(mocker):
    mocker.patch('sys.argv', ['/usr/sbin/univention-upgrade', '--updateto=4.0-0'])
    options = parse_args()
    assert options.updateto == '4.0-0'
