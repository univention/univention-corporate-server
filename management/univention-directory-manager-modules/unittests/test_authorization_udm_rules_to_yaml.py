#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import argparse
import os
import pathlib
import subprocess
import sys
from unittest.mock import MagicMock

import jsondiff
import pytest
import yaml


_MOCKED_MODULES = [
    'univention.config_registry',
    'univention.logging',
    'univention.admin._ucr',
    'univention.license',
    'univention.admin.modules',
    'univention.admin.syntax',
    'univention.admin.blocklist',
    'univention.admin.uldap',
    'univention.admin.guardian_roles',
    'univention.admin.handlers',
    'univention.dn',
    'univention.lib.i18n',
]


def load_config():
    # Only called in a separate process: imports can retain mocks in module
    # globals and parent attributes even after sys.modules has been restored.
    for name in _MOCKED_MODULES:
        sys.modules[name] = MagicMock()
    from univention.admin.authorization.config import UDMAuthorizationConfig
    return UDMAuthorizationConfig


TEST_FILES = './unittests/test_authorization_udm_rules_to_yaml.d/'


@pytest.mark.parametrize('acl_file, expected_yaml_file', [
    (path, path.with_name(f'{path.stem}.yaml'))
    for path in pathlib.Path(TEST_FILES).glob('*.policy')
], ids=[path.name for path in pathlib.Path(TEST_FILES).glob('*.policy')])
def test_to_yaml(acl_file, expected_yaml_file):
    rules_yaml = subprocess.check_output(
        [sys.executable, __file__, '--to-yaml', str(acl_file)],
        env={**os.environ, 'PYTHONPATH': os.pathsep.join(sys.path)},
        text=True,
    )
    expected_rules = expected_yaml_file.read_text().rstrip()
    assert not jsondiff.diff(yaml.safe_load(rules_yaml), yaml.safe_load(expected_rules)), f'\nacl:\n{rules_yaml}\nexpected\n{expected_rules}'


def update_yaml_files():
    UDMAuthorizationConfig = load_config()
    for acl_file in pathlib.Path(TEST_FILES).glob('*.policy'):
        rules = UDMAuthorizationConfig(filename=str(acl_file))
        rules.parse()
        acl_file.with_name(f'{acl_file.stem}.yaml').write_text(rules.to_yaml())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', action='store_true')
    parser.add_argument('--to-yaml', type=pathlib.Path)
    args = parser.parse_args()
    if args.update:
        update_yaml_files()
    elif args.to_yaml:
        rules = load_config()(filename=str(args.to_yaml))
        rules.parse()
        print(rules.to_yaml())
