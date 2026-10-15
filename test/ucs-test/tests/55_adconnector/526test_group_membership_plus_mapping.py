#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Group membership sync through a custom '+'-renaming position mapping, at a scale that spans multiple _batch_get_dns() chunks"
## exposure: dangerous
## packages:
##  - univention-ad-connector
## tags:
##  - skip_admember

"""
Integration regression test for the 2026-10 group-membership-sync
performance work (group_members_sync_to_ucs() / object_memberships_sync_to_ucs()):
 - the persisted-DN-mapping fast path and its fallback on a stale mapping
 - _batch_get_dns()/_batch_check_dns_exist() batching (CHUNK_SIZE=200 in the
   connector, so this test uses a group with MORE than 200 members to force
   more than one batch)
 - univention.dn.DN()-based membership comparisons

This specifically routes members through a custom position-mapping hook that
rewrites a literal '+' in an AD OU name to "plus" in UCS (ou=+1 -> ou=plus1),
mirroring a real customer setup. The new DN-parsing-heavy code is more
exposed to unusual DN syntax than the old plain-string comparisons were, so
this is the scenario most likely to surface a regression.
"""

import os

import pytest

from univention.config_registry import handler_set as ucr_set
from univention.testing import ucr as testing_ucr
from univention.testing.strings import random_string

from adconnector import ADConnection, restart_adconnector, wait_for_sync


AD = ADConnection()

# more than the connector's _batch_get_dns() chunk_size=200, so the test
# exercises at least two batches, not just one lucky single-chunk case
MEMBER_COUNT = 220

name = random_string()
ucs_ou_name = f"plus1{name}"
ad_ou_name = f"\\+1{name}"

mapping = f'''
import univention.connector
from univention.config_registry import ucr


def mapping_hook(ad_mapping):
    with ucr as view:
        ad_base = view.get("connector/ad/ldap/base", "")
        ldap_base = view.get("ldap/base", "")
        if ad_base and ldap_base:
            custom_position_mapping = [
                ("ou={ucs_ou_name}," + ldap_base, "ou={ad_ou_name}," + ad_base),
            ]
            for obj_type in ("ou", "user"):
                if ad_mapping.get(obj_type) is not None:
                    ad_mapping[obj_type].position_mapping = custom_position_mapping
    return ad_mapping
'''
mapping_file = "/etc/univention/connector/ad/localmapping.py"


@pytest.fixture(scope="module", autouse=True)
def create_localmapping():
    with open(mapping_file, "w") as f:
        f.write(mapping)
    restart_adconnector()
    yield
    os.remove(mapping_file)
    restart_adconnector()


@pytest.fixture(scope="module")
def mapped_ad_ou(ucr):
    ad_base = ucr.get("connector/ad/ldap/base")
    ad_ou_dn = f"ou={ad_ou_name},{ad_base}"
    AD.create(ad_ou_dn, {"objectclass": [b"top", b"organizationalUnit"]})
    return ad_ou_dn


def _create_ad_members(ad_ou_dn, count):
    """Create `count` AD users under the '+1'-mapped OU, return their DNs."""
    return [AD.createuser(f"{random_string()}{i}", position=ad_ou_dn) for i in range(count)]


@pytest.mark.parametrize("mode", ["read", "sync"])
def test_large_group_membership_through_mapped_ou(udm, ucr, mode, mapped_ad_ou):
    """
    A group with > chunk_size members, all living under the custom-mapped
    (literal '+') OU, must sync completely and correctly to UCS - this is
    the exact shape of workload the batching/caching changes target.
    """
    with testing_ucr.UCSTestConfigRegistry() as ucr:
        ucr_set([f'connector/ad/mapping/syncmode={mode}'])
        restart_adconnector()

        ucs_base = ucr.get("ldap/base")

        member_dns = _create_ad_members(mapped_ad_ou, MEMBER_COUNT)
        wait_for_sync()  # let the individual users sync in first (realistic ordering)

        groupname = random_string()
        group_dn = AD.group_create(groupname)
        for member_dn in member_dns:
            AD.add_to_group(group_dn, member_dn)

        wait_for_sync(min_wait_time=30)  # a 220-member group sync needs more than the default

        ucs_group_dn = f"cn={groupname},cn=groups,{ucs_base}"
        udm.verify_ldap_object(ucs_group_dn, retry_count=10, delay=3)
        group = udm.get_object('groups/group', ucs_group_dn)
        assert len(group['users']) == MEMBER_COUNT, (
            f"expected all {MEMBER_COUNT} members under the +1-mapped OU to sync, got {len(group['users'])}"
        )

        # remove roughly half - exercises the del_members path and the
        # group_members_cache_ucs eviction added for the staleness fix
        removed, kept = member_dns[: MEMBER_COUNT // 2], member_dns[MEMBER_COUNT // 2:]
        for member_dn in removed:
            AD.remove_from_group(group_dn, member_dn)

        wait_for_sync(min_wait_time=15)

        group = udm.get_object('groups/group', ucs_group_dn)
        assert len(group['users']) == len(kept), (
            f"expected {len(kept)} members left after removal, got {len(group['users'])}"
        )

        # re-add one previously-removed member - this specifically exercises
        # the persisted-DN-mapping fast path being correctly invalidated by
        # the earlier removal rather than permanently (and silently) treating
        # the member as "already there"
        re_added = removed[0]
        AD.add_to_group(group_dn, re_added)

        wait_for_sync(min_wait_time=10)

        group = udm.get_object('groups/group', ucs_group_dn)
        assert len(group['users']) == len(kept) + 1, (
            "removed-then-re-added member was not added back - "
            "possible stale group_members_cache_ucs / persisted-DN-mapping entry"
        )
