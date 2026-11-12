#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Group membership converges and stays stable when AD and UCS change it independently while the connector is stopped"
## exposure: dangerous
## packages:
##  - univention-ad-connector
## tags:
##  - skip_admember

"""
sync-mode regression test: while the connector is down, remove one member
from a group in AD and add a different member to the same group in UCS.
Both changes are then picked up in the same poll batch once the connector
restarts, so this exercises group_members_sync_to_ucs() and
group_members_sync_from_ucs() running back to back for one group, sharing
group_members_cache_ucs/group_member_mapping_cache_ucs.

What is deliberately NOT asserted is which side wins. The connector's main
loop drains poll_ucs() before poll(), so for a group that changed on both
sides the UCS state is pushed to AD first and the AD-side change is
overwritten. That is the existing conflict resolution, not something these
commits change.

What is asserted is what actually matters: both directories converge on the
same membership, and that result is stable. The real risk is oscillation -
each direction's full reconciliation "correcting" what the other just did,
forever. Two poll cycles are checked, not one, so that would be caught.
"""

import subprocess

import ldap.dn

from univention.config_registry import handler_set as ucr_set
from univention.testing import ucr as testing_ucr
from univention.testing.strings import random_string

from adconnector import ADConnection, restart_adconnector, wait_for_sync


AD = ADConnection()
SERVICE = "univention-ad-connector"


def _stop_connector():
    subprocess.check_call(["service", SERVICE, "stop"])


def _start_connector():
    subprocess.check_call(["service", SERVICE, "start"])


def _names(dns):
    """Reduce DNs to their first RDN value, so UCS (uid=x) and AD (cn=x) compare."""
    return {ldap.dn.str2dn(dn)[0][0][1].lower() for dn in dns}


def _ad_member_names(ad_group_dn):
    return _names(m.decode('UTF-8') for m in AD.get(ad_group_dn, ['member']).get('member', []))


def _ucs_member_names(udm, group_dn):
    return _names(udm.get_object('groups/group', group_dn)['users'])


def test_conflicting_membership_changes_converge_without_oscillation(udm):
    """
    Remove member1 from the group in AD, add member2 to the group in UCS,
    both while the connector is down - then confirm both sides end up with
    the same membership and that it does not keep changing afterwards.
    """
    with testing_ucr.UCSTestConfigRegistry() as ucr:
        ucr_set(['connector/ad/mapping/syncmode=sync'])
        restart_adconnector()

        ad_base = ucr.get("connector/ad/ldap/base")

        username1 = random_string()
        username2 = random_string()
        user1_dn, _ = udm.create_user(username=username1)
        user2_dn, _ = udm.create_user(username=username2)
        wait_for_sync()

        groupname = random_string()
        group_dn, _ = udm.create_group(name=groupname, users=[user1_dn])
        wait_for_sync(min_wait_time=15)

        ad_group_dn = f"cn={groupname},cn=groups,{ad_base}"
        ad_user1_dn = f"cn={username1},cn=users,{ad_base}"

        # confirm the starting point is consistent before introducing the conflict
        assert username1.lower() in _ad_member_names(ad_group_dn), "setup: member1 never reached AD"

        _stop_connector()
        try:
            AD.remove_from_group(ad_group_dn, ad_user1_dn.encode('UTF-8'))  # AD-side change
            udm.modify_object('groups/group', dn=group_dn, append={'users': [user2_dn]})  # UCS-side change
        finally:
            _start_connector()

        wait_for_sync(min_wait_time=20)

        ucs_1 = _ucs_member_names(udm, group_dn)
        ad_1 = _ad_member_names(ad_group_dn)

        # the UCS-side addition is uncontroversial - no other side touched it
        assert username2.lower() in ucs_1, "member2's UCS-side addition did not stay in UCS"
        assert username2.lower() in ad_1, "member2's UCS-side addition never reached AD"

        # both directories must agree, whichever way the conflict was resolved
        assert ucs_1 == ad_1, f"UCS and AD disagree after the conflict: UCS={ucs_1} AD={ad_1}"

        # a second full poll cycle must not change anything - oscillation check
        wait_for_sync(min_wait_time=20)

        ucs_2 = _ucs_member_names(udm, group_dn)
        ad_2 = _ad_member_names(ad_group_dn)

        assert (ucs_2, ad_2) == (ucs_1, ad_1), (
            f"membership oscillated between poll cycles: "
            f"UCS {sorted(ucs_1)} -> {sorted(ucs_2)}, AD {sorted(ad_1)} -> {sorted(ad_2)}"
        )
