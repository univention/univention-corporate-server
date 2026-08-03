#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Test the UCS<->AD sync with wildcard support in allow-filter and deny-filter"
## exposure: dangerous
## packages:
##  - univention-ad-connector
## tags:
##  - skip_admember

import contextlib
from collections.abc import Generator

import pytest
from ldap import NO_SUCH_OBJECT
from ldap.filter import escape_filter_chars

from univention.config_registry import handler_set as ucr_set
from univention.testing import ucr as testing_ucr
from univention.testing.strings import random_string
from univention.testing.udm import UCSTestUDM

from adconnector import ADConnection, connector_running_on_this_host, restart_adconnector, wait_for_sync


AD = ADConnection()


@contextlib.contextmanager
def filter_setup(sync_mode: str) -> Generator[UCSTestUDM, None, None]:
    with UCSTestUDM() as udm:
        try:
            with testing_ucr.UCSTestConfigRegistry():
                config = [
                    f"connector/ad/mapping/syncmode={sync_mode}",
                ]
                ucr_set(config)
                restart_adconnector()
                yield udm
        finally:
            restart_adconnector()
    wait_for_sync()


def _assert_in_ucs(udm: UCSTestUDM, name: str, present: bool) -> None:
    if present:
        udm._primary_lo.lo.search(filter=f'uid={escape_filter_chars(name)}', attr=[], required=True)
    else:
        with pytest.raises(NO_SUCH_OBJECT):
            udm._primary_lo.lo.search(filter=f'uid={escape_filter_chars(name)}', attr=[], required=True)


def _assert_in_ad(name: str, present: bool) -> None:
    if present:
        AD.search(f'(sAMAccountName={escape_filter_chars(name)})', required=True)
    else:
        with pytest.raises(NO_SUCH_OBJECT):
            AD.search(f'(sAMAccountName={escape_filter_chars(name)})', required=True)


def _other(token: str) -> str:
    while True:
        other = random_string()
        if other != token:
            return other


def _contains(t: str) -> tuple[str, str, str, str, str]:
    u = _other(t)
    return f'*{t}*', f'pre{t}post', f'pre{u}post', f'xx{t}yy', f'xx{u}yy'


def _starts_with(t: str) -> tuple[str, str, str, str, str]:
    u = _other(t)
    return f'{t}*', f'{t}post', f'pre{u}', f'{t}suf', f'x{u}'


def _ends_with(t: str) -> tuple[str, str, str, str, str]:
    u = _other(t)
    return f'*{t}', f'pre{t}', f'{u}post', f'x{t}', f'{u}suf'


def _multiple_stars(t: str) -> tuple[str, str, str, str, str]:
    u = _other(t)
    return (
        f'{t[0]}.*{t[1]}.*{t[2:]}',
        f'{t[0]}.xx{t[1]}.yy{t[2:]}',
        f'{u[0]}.xx{u[1]}.yy{u[2:]}',
        f'{t[0]}.b{t[1]}.cd{t[2:]}',
        f'{u[0]}.ab{u[1]}.cd{u[2:]}',
    )


@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.parametrize("filter_type", ["allowfilter", "ignorefilter"])
@pytest.mark.parametrize(
    "pattern_builder",
    [_contains, _starts_with, _ends_with, _multiple_stars],
    ids=['contains', 'starts_with', 'ends_with', 'multiple_stars'],
)
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_wildcard_filter(sync_mode: str, filter_type: str, pattern_builder) -> None:
    """
    Test that `*` wildcards in the allow-filter (whitelist) and deny-filter
    (ignore-filter, blacklist) match attribute values like LDAP substring
    filters: `foo*` (prefix), `*foo` (suffix), `*foo*` (substring) and
    `f*o*bar` (multiple wildcards).

    Objects whose value matches the allow-filter are synced, all others are
    ignored. Objects whose value matches the deny-filter are ignored, all
    others are synced.
    """
    token = random_string(5)
    filter_value, ad_matching, ad_non_matching, ucs_matching, ucs_non_matching = pattern_builder(token)
    filter_ = f'(|(uid={filter_value})(sAMAccountName={filter_value}))'
    ucr_value = f'connector/ad/mapping/user/{filter_type}={filter_}'

    with filter_setup(sync_mode) as udm:
        ucr_set([ucr_value])
        restart_adconnector()

        # objects created in AD
        ad_dn_matching = AD.createuser(ad_matching)
        ad_dn_non_matching = AD.createuser(ad_non_matching)
        try:
            wait_for_sync()
            if filter_type == 'allowfilter':
                _assert_in_ucs(udm, ad_matching, present=True)
                _assert_in_ucs(udm, ad_non_matching, present=False)
            else:
                _assert_in_ucs(udm, ad_matching, present=False)
                _assert_in_ucs(udm, ad_non_matching, present=True)
        finally:
            AD.delete(ad_dn_matching)
            AD.delete(ad_dn_non_matching)

        # objects created in UCS
        udm.create_user('users/user', username=ucs_matching)
        udm.create_user('users/user', username=ucs_non_matching)
        wait_for_sync()
        if filter_type == 'allowfilter':
            _assert_in_ad(ucs_matching, present=True)
            _assert_in_ad(ucs_non_matching, present=False)
        else:
            _assert_in_ad(ucs_matching, present=False)
            _assert_in_ad(ucs_non_matching, present=True)
