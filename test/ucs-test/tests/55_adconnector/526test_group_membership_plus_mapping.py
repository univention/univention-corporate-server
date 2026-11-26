#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Group membership sync (both directions) through a custom '+'-renaming position mapping, with a group large enough to be meaningful"
## exposure: dangerous
## packages:
##  - univention-ad-connector
## tags:
##  - skip_admember

"""
Group-membership-sync regression test, routed through a custom position
mapping that rewrites a literal '+' in an AD OU to "plus" in UCS (ou=+1 ->
ou=plus1, a real customer setup). DN-parsing-heavy code is more exposed to
unusual DN syntax than the old plain-string comparisons were.

test_large_group_membership_through_mapped_ou(): AD->UCS, with enough
members that the per-member classification actually costs something.

test_group_membership_ucs_to_ad_through_mapped_ou(): the UCS->AD direction,
untested elsewhere since it's dormant in read mode.
"""

import os
import time

import ldap
import pytest

from univention.config_registry import handler_set as ucr_set
from univention.testing import ucr as testing_ucr
from univention.testing.strings import random_string
from univention.uldap import getAdminConnection

from adconnector import ADConnection, configRegistry, restart_adconnector, wait_for_sync


AD = ADConnection()

MEMBER_COUNT = 220

# two separate mapped OUs - one per test/direction, so their OU creates don't
# collide (same pattern as 169test_custom_position_mapping.py)
name = random_string()
ucs_ou_name = f"plus1{name}"
ad_ou_name = f"\\+1{name}"

# test_group_membership_ucs_to_ad_through_mapped_ou() is parametrized over
# "mode" and reuses this same OU for each parametrize case; if both cases
# shared one name, the second create would race the first case's teardown
# (cleanup deleting the UCS object / that delete syncing to AD). One mapped
# OU pair per mode value sidesteps that entirely.
modes2 = ("write", "sync")
name2 = {m: random_string() for m in modes2}
ucs_ou_name2 = {m: f"plus2{name2[m]}" for m in modes2}
ad_ou_name2 = {m: f"\\+2{name2[m]}" for m in modes2}

_extra_position_mappings = ",\n                ".join(
    f'("ou={ucs_ou_name2[m]}," + ldap_base, "ou={ad_ou_name2[m]}," + ad_base)' for m in modes2
)

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
                {_extra_position_mappings},
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
def mapped_ad_ou():
    # module-scoped, so can't depend on the function-scoped `ucr` fixture
    configRegistry.load()
    ad_base = configRegistry.get("connector/ad/ldap/base")
    ucs_base = configRegistry.get("ldap/base")
    ad_ou_dn = f"ou={ad_ou_name},{ad_base}"
    AD.create(ad_ou_dn, {"objectclass": [b"top", b"organizationalUnit"]})
    yield ad_ou_dn
    # AD.delete() carries the subtree-delete control, so this takes the test
    # users with it. Without this a failed run leaves hundreds of objects
    # behind that the connector keeps syncing into every later run.
    AD.delete(ad_ou_dn)
    # Delete the UCS side here too instead of waiting for the delete to sync:
    # create_localmapping() tears down right after and takes the
    # "ou=+1x -> ou=plus1x" translation with it, which would strand the UCS
    # copy for good.
    _delete_ucs_subtree(f"ou={ucs_ou_name},{ucs_base}")


def _delete_ucs_subtree(dn):
    """Delete dn and everything below it, deepest entry first."""
    lo = getAdminConnection()
    try:
        entries = lo.searchDn(base=dn, scope="sub")
    except ldap.NO_SUCH_OBJECT:
        return
    for entry in sorted(entries, key=lambda x: x.count(","), reverse=True):
        try:
            lo.lo.delete_s(entry)
        except ldap.NO_SUCH_OBJECT:
            pass


def _create_ad_members(ad_ou_dn, count):
    return [AD.createuser(f"{random_string()}{i}", position=ad_ou_dn) for i in range(count)]


def _wait_for_count(count_of, expected, timeout=180, interval=3):
    """
    Poll until count_of() reports `expected`, and return the last value seen.

    wait_for_sync() only sleeps a fixed amount, so every assertion behind it is
    a bet on how fast this machine syncs. A group of 220 members routinely
    needs longer than the sleep allows, and the test then fails on timing
    rather than on behaviour. Polling is fast when the connector is fast and
    patient when it is not.
    """
    deadline = time.monotonic() + timeout
    count = count_of()
    while count != expected and time.monotonic() < deadline:
        time.sleep(interval)
        count = count_of()
    return count


def _ucs_member_count(udm, group_dn):
    """Members of the UCS group, or None while it does not exist yet."""
    try:
        return len(udm.get_object('groups/group', group_dn)['users'])
    except Exception:
        return None


def _ad_member_count(ad_group_dn):
    return len({m.decode('UTF-8').lower() for m in AD.get(ad_group_dn, ['member']).get('member', [])})


@pytest.mark.parametrize("mode", ["read", "sync"])
def test_large_group_membership_through_mapped_ou(udm, ucr, mode, mapped_ad_ou):
    """A large group under the custom-mapped OU must sync fully to UCS."""
    with testing_ucr.UCSTestConfigRegistry() as ucr:
        ucr_set([f'connector/ad/mapping/syncmode={mode}'])
        restart_adconnector()

        ucs_base = ucr.get("ldap/base")

        member_dns = _create_ad_members(mapped_ad_ou, MEMBER_COUNT)
        wait_for_sync()  # let the users sync in first

        groupname = random_string()
        group_dn = AD.group_create(groupname)
        try:
            for member_dn in member_dns:
                AD.add_to_group(group_dn, member_dn.encode('UTF-8'))

            ucs_group_dn = f"cn={groupname},cn=groups,{ucs_base}"
            got = _wait_for_count(lambda: _ucs_member_count(udm, ucs_group_dn), MEMBER_COUNT)
            assert got == MEMBER_COUNT, (
                f"expected all {MEMBER_COUNT} members under the +1-mapped OU to sync, got {got}"
            )

            # remove half - exercises del_members + the group_members_cache_ucs eviction
            removed, kept = member_dns[: MEMBER_COUNT // 2], member_dns[MEMBER_COUNT // 2:]
            for member_dn in removed:
                AD.remove_from_group(group_dn, member_dn.encode('UTF-8'))

            got = _wait_for_count(lambda: _ucs_member_count(udm, ucs_group_dn), len(kept))
            assert got == len(kept), f"expected {len(kept)} members left after removal, got {got}"

            # re-add a removed member - checks the persisted-DN fast path doesn't
            # stay stuck thinking they're still a member
            AD.add_to_group(group_dn, removed[0].encode('UTF-8'))

            got = _wait_for_count(lambda: _ucs_member_count(udm, ucs_group_dn), len(kept) + 1)
            assert got == len(kept) + 1, "re-added member did not come back - stale cache?"
        finally:
            # the group lives next to the mapped OU, so the fixture teardown
            # does not catch it
            AD.delete(group_dn)


SMALL_MEMBER_COUNT = 5


@pytest.mark.parametrize("mode", ["write", "sync"])
def test_group_membership_ucs_to_ad_through_mapped_ou(udm, ucr, mode):
    """Symmetric UCS->AD counterpart - same custom mapping, opposite direction."""
    with testing_ucr.UCSTestConfigRegistry() as ucr:
        ucr_set([f'connector/ad/mapping/syncmode={mode}'])
        restart_adconnector()

        ad_base = ucr.get("connector/ad/ldap/base")
        ucs_base = ucr.get("ldap/base")
        ucs_ou = ucs_ou_name2[mode]
        ad_ou = ad_ou_name2[mode]

        udm.create_object("container/ou", name=ucs_ou)
        ad_ou_dn = f"ou={ad_ou},{ad_base}"
        assert _wait_for_count(lambda: 1 if AD.get(ad_ou_dn) else 0, 1), (
            f"the mapped OU never reached AD as {ad_ou_dn}"
        )
        AD.verify_object(ad_ou_dn, {'name': f"+2{name2[mode]}"})

        member_dns = [
            udm.create_user(position=f"ou={ucs_ou},{ucs_base}")[0]
            for _ in range(SMALL_MEMBER_COUNT)
        ]
        wait_for_sync()  # let the users sync over first

        groupname = random_string()
        group_dn, _ = udm.create_group(name=groupname, users=member_dns)

        ad_group_dn = f"cn={groupname},cn=groups,{ad_base}"
        got = _wait_for_count(lambda: _ad_member_count(ad_group_dn), SMALL_MEMBER_COUNT)
        assert got == SMALL_MEMBER_COUNT, (
            f"expected all {SMALL_MEMBER_COUNT} members under the +2-mapped OU to sync to AD, got {got}"
        )

        # remove half - exercises group_members_sync_from_ucs()'s del path
        removed, kept = member_dns[: SMALL_MEMBER_COUNT // 2], member_dns[SMALL_MEMBER_COUNT // 2:]
        udm.modify_object('groups/group', dn=group_dn, remove={'users': removed})

        got = _wait_for_count(lambda: _ad_member_count(ad_group_dn), len(kept))
        assert got == len(kept), f"expected {len(kept)} AD members left after removal, got {got}"

        # re-add a removed member - checks group_members_cache_con isn't stale
        udm.modify_object('groups/group', dn=group_dn, append={'users': [removed[0]]})

        got = _wait_for_count(lambda: _ad_member_count(ad_group_dn), len(kept) + 1)
        assert got == len(kept) + 1, "re-added member did not come back - stale cache?"
