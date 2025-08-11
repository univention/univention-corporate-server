#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import argparse
import pathlib

import jsondiff
import pytest
import yaml

from univention.admin.authorization.config import UDMAuthorizationConfig


TEST_FILES = './unittests/test_authorization_udm_rules_to_yaml.d/'


@pytest.mark.parametrize('acl_file, expected_yaml_file', [
    (path, path.with_name(f'{path.stem}.yaml'))
    for path in pathlib.Path(TEST_FILES).glob('*.policy')
], ids=[path.name for path in pathlib.Path(TEST_FILES).glob('*.policy')])
def test_to_yaml(acl_file, expected_yaml_file):
    rules = UDMAuthorizationConfig(filename=str(acl_file))
    rules.parse()
    rules_yaml = rules.to_yaml()
    expected_rules = expected_yaml_file.read_text().rstrip()
    assert not jsondiff.diff(yaml.safe_load(rules_yaml), yaml.safe_load(expected_rules)), f'\nacl:\n{rules_yaml}\nexpected\n{expected_rules}'


def update_yaml_files():
    for acl_file in pathlib.Path(TEST_FILES).glob('*.policy'):
        rules = UDMAuthorizationConfig(filename=str(acl_file))
        rules.parse()
        acl_file.with_name(f'{acl_file.stem}.yaml').write_text(rules.to_yaml())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', action='store_true')
    args = parser.parse_args()
    if args.update:
        update_yaml_files()
