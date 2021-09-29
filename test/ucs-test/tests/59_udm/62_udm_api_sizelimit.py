#!/usr/share/ucs-test/runner pytest-3
# -*- coding: utf-8 -*-
## desc: Test sizelimit for UDM API
## exposure: safe
## roles: [domaincontroller_master]
## tags: [udm_api]
## packages: [python-univention-directory-manager]
## bugs: [53832, 53833]
import pytest
from univention.udm.exceptions import SearchLimitReached

from univention.udm import UDM


def test_sizelimit():
    # No need to create any objects since there is at least two groups on any UCS
    udm = UDM.admin().version(1)
    groups_module = udm.get("groups/group")
    with pytest.raises(SearchLimitReached):
        list(groups_module.search("", sizelimit=1))


def test_sizelimit_force_lookup():
    # No need to create any objects since there is at least two groups on any UCS
    udm = UDM.admin().version(1)
    groups_module = udm.get("groups/group")
    del groups_module._orig_udm_module.lookup_filter
    with pytest.raises(SearchLimitReached):
        list(groups_module.search("", sizelimit=1))
