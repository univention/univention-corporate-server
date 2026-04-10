#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test changing disabled and locked simultaneously
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import pytest

import univention.admin.uldap


@pytest.mark.parametrize(
    "disabled,locked", [
        (True, False),
        pytest.param(True, True, marks=pytest.mark.xfail(
            reason="setting both, disabled and locked, not supported, see Bug #59178",
            raises=AssertionError,
            match="krb5KDCFlags: expected 131326 found [b'254']",
        )),
        (False, True),
        pytest.param(False, False, marks=pytest.mark.xfail(
            reason="setting both, disabled and locked, not supported, see Bug #59178",
            raises=AssertionError,
            match="krb5KDCFlags: expected 131326 found [b'254']",
        )),
    ],
    ids=[
        "disabled-not-locked",
        "disabled-and-locked",
        "not-disabled-locked",
        "not-disabled-not-locked",
    ],
)
def test_user_modification_set_deactivation_and_locked(udm, ldap_base, disabled, locked):
    """Test changing disabled and locked simultaneously"""
    # create with inital state
    user_dn = modify_and_check(udm, ldap_base, None, disabled, locked)
    # invert state
    modify_and_check(udm, ldap_base, user_dn, not disabled, not locked)
    # back to initial state
    modify_and_check(udm, ldap_base, user_dn, disabled, locked)


def modify_and_check(udm, ldap_base: str, dn: str, disabled: bool, locked: bool):
    print(f'*** disabled state={disabled!r} locked state={locked!r}')
    if dn:
        udm.modify_object('users/user', dn=dn, disabled=str(int(disabled)), locked=str(int(locked)))
    else:
        dn, _username = udm.create_user(position=f'cn=users,{ldap_base}', disabled=str(int(disabled)), locked=str(int(locked)))

    krb_state = 126
    if disabled:
        krb_state |= 1 << 7
    if locked:
        krb_state |= 1 << 17

    # length of whitespace in sambaAcctFlags varies. cannot use utils.verify_ldap_object() to test it
    lo, _pos = univention.admin.uldap.getMachineConnection(ldap_master=False)
    user = lo.get(dn)
    assert user['krb5KDCFlags'] == [str(krb_state).encode()], 'krb5KDCFlags: expected {!r} found {!r}'.format(krb_state, user['krb5KDCFlags'])
    assert not (disabled and b'D' not in user['sambaAcctFlags'][0]), 'sambaAcctFlags: expected D in flags, found {!r}'.format(user['sambaAcctFlags'])
    assert not ((locked and not disabled) and b'L' not in user['sambaAcctFlags'][0]), 'sambaAcctFlags: expected L in flags, found {!r}'.format(user['sambaAcctFlags'])
    assert not ((locked and disabled) and b'L' in user['sambaAcctFlags'][0]), 'sambaAcctFlags: unexpected L in flags: {!r}'.format(user['sambaAcctFlags'])
    assert not (disabled and user['shadowExpire'][0] != b'1'), 'shadowExpire: expected {!r} found {!r}'.format(['1'], user['shadowExpire'])

    return dn
