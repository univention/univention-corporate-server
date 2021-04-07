from os.path import dirname, join
from importlib.util import module_from_spec, spec_from_file_location
import json
import sys

import pytest


DN = "cn=test"
ATTR = "enabledServiceProviderIdentifierGroup"

spec = spec_from_file_location("udl1", join(dirname(__file__), "../listener/univention-saml-groups.py"))
udl = module_from_spec(spec)
spec.loader.exec_module(udl)  # type: ignore
sys.modules["udl1"] = udl


class TestGetGroup(object):
    def test_unset(self):
        assert udl.get_group({}) == set()

    def test_empty(self):
        assert udl.get_group({ATTR: []}) == set()

    def test_set(self):
        assert udl.get_group({ATTR: [b"1", b"2"]}) == {"1", "2"}


class TestUpdateGroups(object):

    def test_empty(self):
        groups = {}
        udl.update_groups(groups, DN, set(), set())
        assert groups == {}

    def test_remove_existing(self):
        groups = {"sp1": [DN]}
        udl.update_groups(groups, DN, {"sp1"}, set())
        assert groups == {"sp1": []}

    def test_remove_other(self):
        groups = {"sp1": ["other"]}
        udl.update_groups(groups, DN, {"sp1"}, set())
        assert groups == {"sp1": ["other"]}

    def test_add(self):
        groups = {}
        udl.update_groups(groups, DN, set(), {"sp1"})
        assert groups == {"sp1": [DN]}

    def test_add_existing(self):
        groups = {"sp1": [DN]}
        udl.update_groups(groups, DN, set(), {"sp1"})
        assert groups == {"sp1": [DN]}


class TestHandler(object):

    @pytest.fixture
    def groups(self, mocker, tmpdir):
        path_json = tmpdir.join("json")
        path_tmp = tmpdir.join("json.tmp")
        mocker.patch("udl1.path", path_json)
        mocker.patch("udl1.tmp_path", path_tmp)
        return path_json

    def test_missing(self, groups):
        udl.handler(DN, {}, {})
        assert groups.check(file=1, exists=1)

    def test_add(self, groups):
        udl.handler(DN, {ATTR: [b"sp1"]}, {})
        assert json.loads(groups.read()) == {"sp1": [DN]}

    def test_remove(self, groups):
        groups.write(json.dumps({"sp1": [DN]}))
        udl.handler(DN, {}, {ATTR: [b"sp1"]})
        assert json.loads(groups.read()) == {"sp1": []}
