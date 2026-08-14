#!/usr/bin/python3
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os

import pytest
from conftest import FQDN, PolicyResultFailed


SHARE1 = 'cn=share1,cn=shares,dc=example,dc=test'
SHARE2 = 'cn=share2,cn=shares,dc=example,dc=test'
ATTRS1 = {'univentionShareHost': [FQDN], 'univentionSharePath': [b'/mnt/share1']}
ATTRS2 = {'univentionShareHost': [FQDN], 'univentionSharePath': [b'/mnt/share2']}
POLICY = {'univentionQuotaSoftLimitSpace': [b'1024']}


@pytest.fixture
def todo(cache):
    """Create todo entries for the given DNs."""
    def _todo(*dns):
        for dn in dns:
            (cache / 'todo' / dn).touch()
    return _todo


@pytest.fixture
def sorted_listdir(monkeypatch):
    """Make `postrun()` process the todo entries in a deterministic order."""
    listdir = os.listdir
    monkeypatch.setattr(os, 'listdir', lambda path: sorted(listdir(path)))


def cache_file(cache, dn):
    return cache / dn


def levels(ud):
    return [call.args[1] for call in ud.debug.call_args_list]


def test_writes_the_cache(quota, cache, lo, policy_result, todo):
    todo(SHARE1)
    lo.objects[SHARE1] = ATTRS1
    policy_result.policy_result.return_value = (POLICY, {})

    quota.postrun()

    assert quota._read_share_and_policy_result(SHARE1) == (ATTRS1, POLICY)
    assert not (cache / 'todo' / SHARE1).exists()


def test_share_moved_to_another_host(quota, cache, lo, policy_result, todo):
    todo(SHARE1)
    lo.objects[SHARE1] = {'univentionShareHost': [b'other.example.test'], 'univentionSharePath': [b'/mnt/share1']}
    cache_file(cache, SHARE1).touch()

    quota.postrun()

    assert not cache_file(cache, SHARE1).exists()
    assert not (cache / 'todo' / SHARE1).exists()
    policy_result.policy_result.assert_not_called()


def test_share_without_host_attribute(quota, cache, lo, policy_result, todo):
    """A share object without `univentionShareHost` must not raise a `TypeError`."""
    todo(SHARE1)
    lo.objects[SHARE1] = {'univentionSharePath': [b'/mnt/share1']}
    cache_file(cache, SHARE1).touch()

    quota.postrun()

    assert not cache_file(cache, SHARE1).exists()
    assert not (cache / 'todo' / SHARE1).exists()
    policy_result.policy_result.assert_not_called()


def test_share_removed_while_getting_the_policy_result(quota, cache, lo, policy_result, todo, ud):
    """Bug #53550: the share vanishes between the LDAP lookup and `univention-policy-result`."""
    todo(SHARE1)
    lo.objects[SHARE1] = ATTRS1
    cache_file(cache, SHARE1).touch()

    def vanish(dn, *args, **kwargs):
        del lo.objects[dn]
        raise PolicyResultFailed("Error getting univention-policy-result for '%s': LDAP Error: No such object" % dn, 1)

    policy_result.policy_result.side_effect = vanish

    quota.postrun()

    # the todo entry is obsolete and the cached share is gone
    assert not (cache / 'todo' / SHARE1).exists()
    assert not cache_file(cache, SHARE1).exists()
    assert ud.WARN in levels(ud)


def test_policy_result_fails_for_an_existing_share(quota, cache, lo, policy_result, todo, ud):
    """A transient failure must keep the todo entry, so that the next postrun retries it."""
    todo(SHARE1)
    lo.objects[SHARE1] = ATTRS1
    policy_result.policy_result.side_effect = PolicyResultFailed('could not open policy for %s' % SHARE1, 1)

    quota.postrun()

    assert (cache / 'todo' / SHARE1).exists()
    assert not cache_file(cache, SHARE1).exists()
    assert ud.ERROR in levels(ud)

    # the retry succeeds once the policy can be read again
    policy_result.policy_result.side_effect = None
    policy_result.policy_result.return_value = (POLICY, {})

    quota.postrun()

    assert quota._read_share_and_policy_result(SHARE1) == (ATTRS1, POLICY)
    assert not (cache / 'todo' / SHARE1).exists()


def test_a_failing_share_does_not_block_the_others(quota, cache, lo, policy_result, todo, sorted_listdir):
    """Bug #53550: `postrun()` aborted and left the remaining todo entries unprocessed."""
    todo(SHARE1, SHARE2)
    lo.objects[SHARE1] = ATTRS1
    lo.objects[SHARE2] = ATTRS2

    def fail_for_share1(dn, *args, **kwargs):
        if dn == SHARE1:
            raise PolicyResultFailed("Error getting univention-policy-result for '%s': LDAP Error: No such object" % dn, 1)
        return (POLICY, {})

    policy_result.policy_result.side_effect = fail_for_share1

    quota.postrun()

    assert quota._read_share_and_policy_result(SHARE2) == (ATTRS2, POLICY)
    assert not (cache / 'todo' / SHARE2).exists()
    assert not cache_file(cache, SHARE1).exists()
