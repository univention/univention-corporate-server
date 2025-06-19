#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os

import jsondiff
import pytest
import yaml

from univention.authorization.udm_rules import UDMAuthorizationConfig


TEST_FILES = './unittests/test_authorization_udm_rules_to_yaml.d/'


@pytest.mark.parametrize('acl_file, expected_yaml_file', [
    ('test_simple.acl', 'test_simple.yaml'),
    ('test_multiple_positions.acl', 'test_multiple_positions.yaml'),
])
def test_to_yaml(acl_file, expected_yaml_file):
    acl_file = os.path.join(TEST_FILES, acl_file)
    expected_yaml_file = os.path.join(TEST_FILES, expected_yaml_file)
    rules = UDMAuthorizationConfig(filename=acl_file)
    rules.parse()
    rules_yaml = rules.to_yaml()
    with open(expected_yaml_file) as fh:
        expected_rules = fh.read().rstrip()
        assert not jsondiff.diff(
            yaml.safe_load(rules_yaml), yaml.safe_load(expected_rules)), f'\nacl:\n{rules_yaml}\nexpected\n{expected_rules}'
