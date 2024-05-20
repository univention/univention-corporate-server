#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test changing disabled and locked simultaneously
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

from __future__ import annotations

from datetime import datetime

import pytest

import univention.admin.uldap
from univention.lib.account import lock


@pytest.mark.parametrize("disabled", [False, True])
@pytest.mark.parametrize("locked", [False, True])
def test_user_modification_set_deactivation_and_locked(ucr, udm, disabled: bool, locked: bool) -> None:
    """Test changing disabled and locked simultaneously"""
    dn, _username = udm.create_user(**user_args(disabled=disabled, locked=locked))
    lock_account(dn, locked)

    check(dn, disabled, locked)

    disabled, locked = not disabled, not locked

    udm.modify_object('users/user', dn=dn, **user_args(disabled=disabled, locked=locked))
    lock_account(dn, locked)

    check(dn, disabled, locked)


def user_args(*, disabled: bool, locked: bool) -> dict[str, object]:
    kwargs = {
        "disabled": "1" if disabled else "0",
        "wait_for_replication": False,  # Primary only -> no UDN/UDL
        "wait_for": False,  # S4C is slow
    }
    if not locked:
        kwargs["locked"] = "0"
    return kwargs


def lock_account(dn: str, locked: bool) -> None:
    """Change read-only UDM property `users.user.locked`."""
    lock(dn, f'{datetime.utcnow():%Y%m%d%H%M%S}Z' if locked else '')


def check(dn: str, disabled: bool, locked: bool) -> None:
    # length of whitespace in sambaAcctFlags varies. cannot use utils.verify_ldap_object() to test it
    lo, _pos = univention.admin.uldap.getMachineConnection(ldap_master=False)
    user = lo.get(dn)

    assert user['krb5KDCFlags'] == [b'254' if disabled else b'126']
    if disabled:
        assert user['shadowExpire'][0] == b'1'
        assert b'D' in user['sambaAcctFlags'][0]
    if locked:
        assert disabled != (b'L' in user['sambaAcctFlags'][0])
