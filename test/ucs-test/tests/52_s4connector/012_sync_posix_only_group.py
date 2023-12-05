#!/usr/share/ucs-test/runner pytest-3 -s -vv
## desc: "Create a Posix-only group in udm and check that the S4-Connector doesn't convert it"
## exposure: safe
## packages:
## - univention-s4-connector
## bugs:
##  - 56772

import pytest

from univention.testing.connector_common import (
    NormalGroup, create_udm_group, delete_udm_group, map_udm_group_to_con, verify_udm_object,
)

import s4connector
from s4connector import connector_running_on_this_host, connector_setup


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention S4 Connector not configured.")
def test_udm_group_option_unchanged_by_s4c(udm):
    """check that the UDM group option "posix" is not changed by the S4-Connector."""
    with connector_setup("sync") as s4:
        udm_group = NormalGroup()
        udm_group.group['options'] = ['posix']
        (udm_group_dn, s4_group_dn) = create_udm_group(udm, s4, udm_group, s4connector.wait_for_sync)

        del udm_group.group['options']    # verify_object doesn't handle options
        s4.verify_object(s4_group_dn, map_udm_group_to_con(udm_group.group))

        udm_group.group['sambaRID'] = []  # make verify_object confirm that this property not set
        verify_udm_object("groups/group", udm_group_dn, udm_group.group)

        delete_udm_group(udm, s4, udm_group_dn, s4_group_dn, s4connector.wait_for_sync)
