#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Unit-level regression tests for the group-membership-sync performance changes"
## exposure: safe
## packages:
##  - univention-ad-connector
## tags:
##  - skip_admember

"""
These are plain pytest unit tests, not integration tests: they never touch a
live AD or UCS LDAP server. They import the real univention.connector.ad
module (so they do need univention-ad-connector and its dependencies
installed, hence living under ucs-test) but construct the `ad` connector
object via `ad.__new__(ad)` - skipping __init__() entirely - and only fill in
the handful of attributes each function under test actually touches. This is
exposure:safe because nothing here ever opens a real LDAP connection.

Covers the 2026-10 performance work:
 - univention.dn.DN-based membership comparisons, replacing the old
   per-call ldap.dn.str2dn()/compare_dn() in __compare_lowercase_dn()
 - _safe_dn(): malformed-DN tolerance, specifically important for customer
   environments with custom position-mapping hooks that rewrite characters
   like a literal "+" in an OU name (e.g. AD "ou=+1" -> UCS "ou=plus1") -
   DN()-based code raises ValueError on unparseable DN syntax where the old
   plain-string comparisons could not fail this way
 - _batch_get_dns()/_batch_check_dns_exist(): chunking, entryDN filter
   construction/escaping, result-key casing, and graceful fallback on error
"""

import ldap
import pytest

from univention.connector.ad import ad


def _new_connector():
    """An `ad` instance with __init__() skipped - see module docstring."""
    return ad.__new__(ad)


# --- _safe_dn() -------------------------------------------------------------

def test_safe_dn_valid():
    dn = ad._safe_dn("cn=foo,dc=example,dc=com")
    assert dn is not None
    assert str(dn).lower() == "cn=foo,dc=example,dc=com"


def test_safe_dn_malformed_returns_none_not_raise():
    # An unescaped '+' is a multi-valued-RDN separator in DN syntax. This is
    # exactly the shape of value a buggy/partial custom position-mapping hook
    # (e.g. one meant to rewrite "+1" -> "plus1") could leak through.
    malformed = "cn=+1somebody,dc=example,dc=com"
    assert ad._safe_dn(malformed) is None


def test_safe_dn_properly_mapped_plus_is_fine():
    # once the custom mapping has done its job, the '+' is gone from the
    # string entirely and there is nothing for DN() to trip over
    mapped = "cn=somebody,ou=plus1,dc=example,dc=com"
    dn = ad._safe_dn(mapped)
    assert dn is not None


def test_safe_dn_case_insensitive_equality():
    a = ad._safe_dn("uid=Administrator,cn=users,dc=example,dc=com")
    b = ad._safe_dn("uid=administrator,cn=users,dc=example,dc=com")
    assert a is not None and b is not None
    assert a == b


# --- __compare_lowercase_dn() (name-mangled: _ad__compare_lowercase_dn) -----

def _compare_lowercase_dn(connector, dn, dn_list):
    # double-underscore attribute is name-mangled at the class level
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
    # a single malformed entry in dn_list must not blow up the whole check -
    # it should just never match, while a valid entry elsewhere still can
    connector = _new_connector()
    dn_list = ["cn=+1broken,dc=example,dc=com", "cn=someone,ou=users,dc=example,dc=com"]
    assert _compare_lowercase_dn(connector, "cn=someone,ou=users,dc=example,dc=com", dn_list)


def test_compare_lowercase_dn_malformed_needle_is_no_match():
    connector = _new_connector()
    dn_list = ["cn=someone,ou=users,dc=example,dc=com"]
    assert not _compare_lowercase_dn(connector, "cn=+1broken,dc=example,dc=com", dn_list)


# --- _batch_get_dns() / _batch_check_dns_exist() ----------------------------

class FakeLo:
    """Stands in for self.lo: records every search() call, serves canned results."""

    def __init__(self, base, results_by_filter=None, raise_on_call=None, raise_on_call_exc=None):
        self.base = base
        self.calls = []
        self._results_by_filter = results_by_filter or {}
        self._raise_on_call = raise_on_call  # call index (0-based) to raise on
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
    # 11 DNs at chunk_size=5 -> 3 searches (5, 5, 1), never one giant filter
    assert len(connector.lo.calls) == 3
    assert [len(c['filter'].split('(entryDN=')) - 1 for c in connector.lo.calls] == [5, 5, 1]


def test_batch_get_dns_escapes_filter_special_characters():
    connector = _new_connector()
    connector.lo = FakeLo(base="dc=example,dc=com")
    # '*' and '(' are LDAP-filter-special and must be escaped in the filter
    # value even though they're perfectly fine DN characters
    dn = "cn=foo (bar)*,dc=example,dc=com"
    connector._batch_get_dns([dn], attr=['1.1'])
    built_filter = connector.lo.calls[0]['filter']
    assert '(bar)*' not in built_filter  # raw value must not appear unescaped
    assert '\\28bar\\29\\2a' in built_filter  # escape_filter_chars() output for "(bar)*"


def test_batch_get_dns_returns_results_keyed_lowercase():
    connector = _new_connector()
    dn = "uid=user1,dc=example,dc=com"
    filter_s = f"(|(entryDN={dn}))"
    connector.lo = FakeLo(base="dc=example,dc=com", results_by_filter={filter_s: [("UID=User1,DC=Example,DC=Com", {'uid': [b'user1']})]})
    found = connector._batch_get_dns([dn], attr=['uid'])
    assert dn.lower() in found
    result_dn, result_attr = found[dn.lower()]
    assert result_dn == "UID=User1,DC=Example,DC=Com"  # server's canonical casing preserved
    assert result_attr == {'uid': [b'user1']}


def test_batch_check_dns_exist_missing_dn_is_absent_not_error():
    connector = _new_connector()
    connector.lo = FakeLo(base="dc=example,dc=com")  # no results configured -> nothing exists
    found = connector._batch_check_dns_exist(["uid=ghost,dc=example,dc=com"])
    assert found == {}


def test_batch_get_dns_server_down_propagates():
    connector = _new_connector()
    connector.lo = FakeLo(base="dc=example,dc=com", raise_on_call=0, raise_on_call_exc=ldap.SERVER_DOWN())
    with pytest.raises(ldap.SERVER_DOWN):
        connector._batch_get_dns(["uid=user1,dc=example,dc=com"])


def test_batch_get_dns_other_exception_falls_back_gracefully():
    # a chunk that errors for any other reason must not raise - the caller
    # (group_members_sync_to_ucs) relies on this to fall back to per-member
    # resolution instead of aborting the whole group sync
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
    # first call (chunk 0) raises, second call (chunk 1, the "ok" one) must still work
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
