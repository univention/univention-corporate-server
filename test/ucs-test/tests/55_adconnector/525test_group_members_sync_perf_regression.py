#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Unit-level regression tests for the group-membership-sync performance changes"
## exposure: safe
## packages:
##  - univention-ad-connector
## tags:
##  - skip_admember

"""
Unit tests for the group-membership-sync perf changes. No live AD/UCS needed:
we build the `ad` connector via `ad.__new__(ad)` (skipping __init__) and only
set the attributes each function actually touches.
"""

import ldap
import pytest

from univention.connector.ad import ad


def _new_connector():
    return ad.__new__(ad)


# --- _safe_dn() -------------------------------------------------------------

def test_safe_dn_valid():
    dn = ad._safe_dn("cn=foo,dc=example,dc=com")
    assert dn is not None
    assert str(dn).lower() == "cn=foo,dc=example,dc=com"


def test_safe_dn_malformed_returns_none_not_raise():
    # unescaped '+' is a multi-valued-RDN separator - what a buggy "+1"->"plus1"
    # mapping hook could leak through
    malformed = "cn=+1somebody,dc=example,dc=com"
    assert ad._safe_dn(malformed) is None


def test_safe_dn_properly_mapped_plus_is_fine():
    mapped = "cn=somebody,ou=plus1,dc=example,dc=com"
    assert ad._safe_dn(mapped) is not None


def test_safe_dn_case_insensitive_equality():
    a = ad._safe_dn("uid=Administrator,cn=users,dc=example,dc=com")
    b = ad._safe_dn("uid=administrator,cn=users,dc=example,dc=com")
    assert a is not None and b is not None
    assert a == b


# --- __compare_lowercase_dn() -----------------------------------------------

def _compare_lowercase_dn(connector, dn, dn_list):
    # name-mangled since it's a dunder method on class `ad`
    return connector._ad__compare_lowercase_dn(dn, dn_list)


def test_compare_lowercase_dn_matches_case_insensitively():
    connector = _new_connector()
    dn_list = ["CN=Someone,OU=Users,DC=example,DC=com"]
    assert _compare_lowercase_dn(connector, "cn=someone,ou=users,dc=example,dc=com", dn_list)


def test_compare_lowercase_dn_no_match():
    connector = _new_connector()
    dn_list = ["cn=someone-else,ou=users,dc=example,dc=com"]
    assert not _compare_lowercase_dn(connector, "cn=someone,ou=users,dc=example,dc=com", dn_list)


def test_compare_lowercase_dn_tolerates_malformed_entries():
    # one bad entry in dn_list shouldn't blow up the whole check
    connector = _new_connector()
    dn_list = ["cn=+1broken,dc=example,dc=com", "cn=someone,ou=users,dc=example,dc=com"]
    assert _compare_lowercase_dn(connector, "cn=someone,ou=users,dc=example,dc=com", dn_list)


def test_compare_lowercase_dn_malformed_needle_is_no_match():
    connector = _new_connector()
    dn_list = ["cn=someone,ou=users,dc=example,dc=com"]
    assert not _compare_lowercase_dn(connector, "cn=+1broken,dc=example,dc=com", dn_list)


# --- _batch_get_dns() / _batch_check_dns_exist() ----------------------------

class FakeLo:
    """stands in for self.lo: records search() calls, serves canned results"""

    def __init__(self, base, results_by_filter=None, raise_on_call=None, raise_on_call_exc=None):
        self.base = base
        self.calls = []
        self._results_by_filter = results_by_filter or {}
        self._raise_on_call = raise_on_call  # 0-based call index to raise on
        self._raise_on_call_exc = raise_on_call_exc

    def search(self, filter, base, scope, attr):
        self.calls.append({'filter': filter, 'base': base, 'scope': scope, 'attr': attr})
        if self._raise_on_call is not None and len(self.calls) - 1 == self._raise_on_call:
            raise self._raise_on_call_exc
        return self._results_by_filter.get(filter, [])


def test_batch_get_dns_empty_input_does_no_search():
    connector = _new_connector()
    connector.lo = FakeLo(base="dc=example,dc=com")
    found = connector._batch_get_dns([])
    assert found == {}
    assert connector.lo.calls == []


def test_batch_get_dns_chunks_requests():
    connector = _new_connector()
    connector.lo = FakeLo(base="dc=example,dc=com")
    dns = [f"uid=user{i},dc=example,dc=com" for i in range(11)]
    connector._batch_get_dns(dns, attr=['1.1'], chunk_size=5)
    # 11 DNs @ chunk_size=5 -> 3 searches of (5, 5, 1), not one giant filter
    assert len(connector.lo.calls) == 3
    assert [len(c['filter'].split('(entryDN=')) - 1 for c in connector.lo.calls] == [5, 5, 1]


def test_batch_get_dns_escapes_filter_special_characters():
    connector = _new_connector()
    connector.lo = FakeLo(base="dc=example,dc=com")
    dn = "cn=foo (bar)*,dc=example,dc=com"  # '*' and '(' need filter-escaping
    connector._batch_get_dns([dn], attr=['1.1'])
    built_filter = connector.lo.calls[0]['filter']
    assert '(bar)*' not in built_filter
    assert '\\28bar\\29\\2a' in built_filter  # escape_filter_chars() output


def test_batch_get_dns_returns_results_keyed_lowercase():
    connector = _new_connector()
    dn = "uid=user1,dc=example,dc=com"
    filter_s = f"(|(entryDN={dn}))"
    connector.lo = FakeLo(base="dc=example,dc=com", results_by_filter={filter_s: [("UID=User1,DC=Example,DC=Com", {'uid': [b'user1']})]})
    found = connector._batch_get_dns([dn], attr=['uid'])
    assert dn.lower() in found
    result_dn, result_attr = found[dn.lower()]
    assert result_dn == "UID=User1,DC=Example,DC=Com"  # server's casing, not ours
    assert result_attr == {'uid': [b'user1']}


def test_batch_check_dns_exist_missing_dn_is_absent_not_error():
    connector = _new_connector()
    connector.lo = FakeLo(base="dc=example,dc=com")
    found = connector._batch_check_dns_exist(["uid=ghost,dc=example,dc=com"])
    assert found == {}


def test_batch_get_dns_server_down_propagates():
    connector = _new_connector()
    connector.lo = FakeLo(base="dc=example,dc=com", raise_on_call=0, raise_on_call_exc=ldap.SERVER_DOWN())
    with pytest.raises(ldap.SERVER_DOWN):
        connector._batch_get_dns(["uid=user1,dc=example,dc=com"])


def test_batch_get_dns_other_exception_falls_back_gracefully():
    # caller falls back to per-member resolution instead of aborting the sync
    connector = _new_connector()
    connector.lo = FakeLo(base="dc=example,dc=com", raise_on_call=0, raise_on_call_exc=ldap.LDAPError())
    found = connector._batch_get_dns(["uid=user1,dc=example,dc=com"])
    assert found == {}


def test_batch_get_dns_one_bad_chunk_does_not_lose_other_chunks():
    connector = _new_connector()
    dn_ok = "uid=user-ok,dc=example,dc=com"
    filter_ok = f"(|(entryDN={dn_ok}))"
    connector.lo = FakeLo(
        base="dc=example,dc=com",
        results_by_filter={filter_ok: [("uid=user-ok,dc=example,dc=com", {})]},
    )
    # chunk 0 raises, chunk 1 (the "ok" one) must still come through
    calls = {'n': 0}
    real_search = connector.lo.search

    def flaky_search(filter, base, scope, attr):
        calls['n'] += 1
        if calls['n'] == 1:
            raise ldap.LDAPError()
        return real_search(filter, base, scope, attr)

    connector.lo.search = flaky_search
    found = connector._batch_get_dns(["uid=user-bad,dc=example,dc=com", dn_ok], chunk_size=1)
    assert dn_ok.lower() in found
    assert "uid=user-bad,dc=example,dc=com".lower() not in found


# --- one_group_member_sync_from_ucs() (write/sync mode, UCS->AD) -----------
# dormant in read mode, so never exercised before - also calls __compare_lowercase_dn()

class FakeLoAd:
    """stands in for self.lo_ad: records modify_s() calls"""

    def __init__(self, raise_exc=None):
        self.lo = self
        self.calls = []
        self._raise_exc = raise_exc

    def modify_s(self, dn, ml):
        self.calls.append((dn, ml))
        if self._raise_exc is not None:
            raise self._raise_exc


def _new_connector_for_sync_from_ucs(raise_exc=None):
    connector = _new_connector()
    connector.lo_ad = FakeLoAd(raise_exc=raise_exc)
    connector.group_members_cache_con = {}
    return connector


def test_sync_from_ucs_adds_member_not_yet_present():
    connector = _new_connector_for_sync_from_ucs()
    ad_group_object = {'dn': 'cn=group,dc=example,dc=com', 'attributes': {'member': [b'cn=someone-else,dc=example,dc=com']}}
    object_ = {'dn': 'cn=new-member,dc=example,dc=com'}

    connector.one_group_member_sync_from_ucs(ad_group_object, object_)

    assert connector.lo_ad.calls == [('cn=group,dc=example,dc=com', [(ldap.MOD_ADD, 'member', [b'cn=new-member,dc=example,dc=com'])])]


def test_sync_from_ucs_skips_when_already_member_case_insensitive():
    connector = _new_connector_for_sync_from_ucs()
    ad_group_object = {'dn': 'cn=group,dc=example,dc=com', 'attributes': {'member': [b'CN=Already-Member,DC=example,DC=com']}}
    object_ = {'dn': 'cn=already-member,dc=example,dc=com'}

    connector.one_group_member_sync_from_ucs(ad_group_object, object_)

    assert connector.lo_ad.calls == []  # already a member, nothing to do


def test_sync_from_ucs_malformed_existing_member_does_not_crash():
    # one unparseable entry (e.g. an unmapped literal '+') shouldn't break the rest
    connector = _new_connector_for_sync_from_ucs()
    ad_group_object = {
        'dn': 'cn=group,dc=example,dc=com',
        'attributes': {'member': [b'cn=+1broken,dc=example,dc=com', b'cn=known-member,dc=example,dc=com']},
    }
    object_ = {'dn': 'cn=known-member,dc=example,dc=com'}

    connector.one_group_member_sync_from_ucs(ad_group_object, object_)

    assert connector.lo_ad.calls == []  # matched via the well-formed entry


def test_sync_from_ucs_already_exists_is_caught_and_cache_still_updated():
    connector = _new_connector_for_sync_from_ucs(raise_exc=ldap.ALREADY_EXISTS())
    ad_group_object = {'dn': 'cn=group,dc=example,dc=com', 'attributes': {'member': []}}
    object_ = {'dn': 'cn=new-member,dc=example,dc=com'}

    connector.one_group_member_sync_from_ucs(ad_group_object, object_)  # must not raise

    assert 'cn=new-member,dc=example,dc=com' in connector.group_members_cache_con['cn=group,dc=example,dc=com']


def test_sync_from_ucs_updates_group_members_cache_con_on_success():
    connector = _new_connector_for_sync_from_ucs()
    ad_group_object = {'dn': 'cn=group,dc=example,dc=com', 'attributes': {'member': []}}
    object_ = {'dn': 'cn=new-member,dc=example,dc=com'}

    connector.one_group_member_sync_from_ucs(ad_group_object, object_)

    assert connector.group_members_cache_con['cn=group,dc=example,dc=com'] == {'cn=new-member,dc=example,dc=com'}
