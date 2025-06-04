# account status flags in UDM users/user

This document describes various states related to user account disabling and locking, along with their corresponding UDM and LDAP representations.

## `locked`: Account locked due to authentication failures

Indicates the account has been locked because of too many failed authentication attempts.

- **LDAP attributes** any of:
  - `sambaAcctFlags` contains `L`
  - `krb5KDCFlags` bitmask includes the `???` bit (aka: `1 << 17`, `0x20000`).
  - ~~`pwdAccountLockedTime` (not in use) ~~
- **Related properties**:
  - `lockedTime`: timestamp when account lockout happened
    - **LDAP attribute:** `sambaBadPasswordTime`: Windows Filetime (100 nanoseconds since January 1, 1601.) of last bad password event.
  - `unlock=True`: Unlocks the account (sets `locked=0`, no corresponding LDAP attribute). Note: it's not possible to set `locked=1` -- except it is, by dark magic.
  - `unlockTime`: Calculated timestamp when the account will be automatically unlocked, based on policy and `lockedTime`
- **Property UDM search filter**:
  - `locked=` `1` | `0` | `posix` | `windows` | `all` | `none` | `*`

**Note**: `locked` is distinct from `disabled` - a locked user can still perform certain operations like changing his password.

## `disabled`: Account deactivated

Indicates the user account is deactivated. This affects authentication for Windows (Samba), Kerberos, and POSIX systems.

- **LDAP attributes** any of:
  - `sambaAcctFlags` contains `D`
  - `krb5KDCFlags` bitmask includes the `KRB5_KDB_REQUIRES_PRE_AUTH` bit (aka: `1 << 7`, `0x80`).
  - `shadowExpire == 1` or `shadowExpire < current time` or `userPassword` hash starts with `!`
- **Property UDM search filter**:
  - `disabled=` `1` | `0` | `posix` | `windows` | `all` | `none` | `kerberos` | `windows_kerberos` | `windows_posix` | `posix_kerberos` | `*`

**Note**: This may not disable login via LDAP (depending on configuration)

## `userexpiry`: Account expiration time

Defines a point in time after which the account is considered expired (i.e. disabled).

- **LDAP attributes**:
  - `sambaKickoffTime`: UNIX timestamp
  - `krb5ValidEnd`: GeneralizedTime (ASN.1 / X.680) (currently when stored via UDM time is set to `00:00:00` o'clock: `YYYYMMDD000000Z`)
  - `shadowExpire`: UNIX timestamp
- **Property UDM search filter**:
  - `userexpiry=` `2025-06-20` | `*`
  - `userexpiry=2025-*` does **NOT** work

**Note**: This value does not automatically sets `disable=True` in the account when the expiration time is reached.

## `accountActivationDate`: Future account activation

Allows defining a future date when the account becomes active.

- **LDAP Attribute**:
  - `krb5ValidStart` GeneralizedTime (ASN.1 / X.680) in UTC/Zulu
- **Behavior**:
  - Until this date, the account is created with `disabled=True`
  - Requires a [cron job](scripts/univention-delayed-account-activation) to reactivate the user by setting `disabled=False` once the date is reached
- **Property UDM search filter**:
  - `accountActivationDate=` `2025-06-20` | `2025-06-20 15:00`


## Account "active" property which combines all above states

There is effectively no pseudo property which combines all the states as indicator that an account is not active.
However a UDM search with a filter `"(|(disabled=1)(locked=1)(userexpiry<=$(date -I))"` allows to receive all inactive accounts:
`>>> univention.admin.modules.get('users/user').lookup(None, lo, "(|(disabled=1)(locked=1)(userexpiry<=2025-06-05)")`

## Related bugs
* [Bug 54317 - Setting a user account to locked in UDM still allows OpenLDAP bind with that user](https://forge.univention.org/bugzilla/show_bug.cgi?id=54317)
* [Bug 55633 - Disabled user does not show up in search result for disabled users if a user expiry date is set](https://forge.univention.org/bugzilla/show_bug.cgi?id=55633)
* [Bug 46351 - Account lockout via LDAP ppolicy not shown in UMC and probably not applied to Kerberos](https://forge.univention.org/bugzilla/show_bug.cgi?id=46351)
* [Bug 55452 - UDM representation of accountActivationDate](https://forge.univention.org/bugzilla/show_bug.cgi?id=55452)
* [Bug 54227 - account/userexpiry shown in UMC/UDM differs from value shown in MS ADUC](https://forge.univention.org/bugzilla/show_bug.cgi?id=54227)
* [Bug 36210 - Handling of userexpiry is unexact](https://forge.univention.org/bugzilla/show_bug.cgi?id=36210)
* [Bug 53808 - users/user broken searches](https://forge.univention.org/bugzilla/show_bug.cgi?id=53808)
* [Bug 50944 - AD-connector changes userexpiry += 1 day in a loop on certain timezones](https://forge.univention.org/bugzilla/show_bug.cgi?id=50944)
* [Bug 37924 - 60\_umc-system 33\_umc\_users\_user\_unset\_userexpiry failed in UCS 4.0-1](https://forge.univention.org/bugzilla/show_bug.cgi?id=37924)
* [Bug 54724 - Self password change not possible if future account expiry date is set to a date later than 2038-01-20](https://forge.univention.org/bugzilla/show_bug.cgi?id=54724)
* [Bug 44788 - setting the accountexpiry to 2038 causes the kerberos principal to expire: 1902-xx-xx and creates a locked account](https://forge.univention.org/bugzilla/show_bug.cgi?id=44788)
* [Bug 46880 - Traceback due to large value in sambaKickoffTime](https://forge.univention.org/bugzilla/show_bug.cgi?id=46880)
* [Bug 48880 - Strange notification in UMC users/user after setting deactivation to a date in the past](https://forge.univention.org/bugzilla/show_bug.cgi?id=48880)
* [Bug 46351 - Account lockout via LDAP ppolicy not shown in UMC and probably not applied to Kerberos](https://forge.univention.org/bugzilla/show_bug.cgi?id=46351)
* [Bug 52893 - ppolicy password lockout sometimes doesn't trigger Samba/AD password lockout](https://forge.univention.org/bugzilla/show_bug.cgi?id=52893)
* [Bug 57968 - UCR variables `auth/faillog`/`auth/faillog/lock_global` do not work at all with PAM service `univention-management-console`](https://forge.univention.org/bugzilla/show_bug.cgi?id=57968)
* [Bug 54318 - Lockout in Samba/AD doesn't trigger lockout in OpenLDAP](https://forge.univention.org/bugzilla/show_bug.cgi?id=54318)
* [Bug 52902 - Password lockout in Samba/AD doesn't trigger ppolicy lockout for OpenLDAP simple bind](https://forge.univention.org/bugzilla/show_bug.cgi?id=52902)
* [Bug 54319 - user accounts locked out in UDM don't get automatically unlocked after some time](https://forge.univention.org/bugzilla/show_bug.cgi?id=54319)
* [Bug 52910 - Unlocking previously Password locked account via PAM authentication not shown in UMC/UDM](https://forge.univention.org/bugzilla/show_bug.cgi?id=52910)
* [Bug 52913 - Password lockout in Samba/AD doesn't set locked bit in krb5KDCFlags in OpenLDAP](https://forge.univention.org/bugzilla/show_bug.cgi?id=52913)
* [Bug 53072 - No reset of ppolicy lockout on Replica or backup server](https://forge.univention.org/bugzilla/show_bug.cgi?id=53072)
* [Bug 57207 - Postfix/SASL-authentication doesnt honor account lockout caused by ppolicy](https://forge.univention.org/bugzilla/show_bug.cgi?id=57207)
* [Bug 53230 - ppolicy password lockout doesn't trigger PAM (faillog) password lockout ](https://forge.univention.org/bugzilla/show_bug.cgi?id=53230)
* [Bug 53231 - Automatic unlock of ppolicy lockout (like in faillog and samba)](https://forge.univention.org/bugzilla/show_bug.cgi?id=53231)
* [Bug 52892 - Password lockout in Samba/AD doesn't trigger lockout for PAM based authentication](https://forge.univention.org/bugzilla/show_bug.cgi?id=52892)
* [Bug 47802 - Uncheck "User has to change password on next login" removes shadowMax (although there is a global pw policy)](https://forge.univention.org/bugzilla/show_bug.cgi?id=47802)
* [Bug 53829 - Exception when giving seconds in accountActivationDate](https://forge.univention.org/bugzilla/show_bug.cgi?id=53829)
* [Bug 54159 - UDM REST API filter value for 'disabled' does not correspond to the resource value](https://forge.univention.org/bugzilla/show_bug.cgi?id=54159)
* [Bug 56816 - AD-Connector doesn't handle accountExpires == 0 properly, reject and traceback in log](https://forge.univention.org/bugzilla/show_bug.cgi?id=56816)
* [Bug 57362 - ASMC should only sync active accounts](https://forge.univention.org/bugzilla/show_bug.cgi?id=57362)
* [Bug 48190 - Active/Disabled state of user accounts should be synced to office365](https://forge.univention.org/bugzilla/show_bug.cgi?id=48190)
* [Bug 58060 - Add option to keep disabled users disabled / activate and deactivate users](https://forge.univention.org/bugzilla/show_bug.cgi?id=58060)
* [Bug 57239 - Import is activating deactivated (disabled) users](https://forge.univention.org/bugzilla/show_bug.cgi?id=57239)

## Related bugs with historic context / knowledge
* [Bug 46349 - Value of userexpiry derived from shadowExpire depends on timezone](https://forge.univention.org/bugzilla/show_bug.cgi?id=46349#c7)
* [Bug 39817 - Locked login methods ignored by Samba 4](https://forge.univention.org/bugzilla/show_bug.cgi?id=39817)
* [Bug 36486 - Users which are both expired and deactivated are rejected](https://forge.univention.org/bugzilla/show_bug.cgi?id=36486)
* [Bug 36330 - Failed to create user with expired password - invalid date format](https://forge.univention.org/bugzilla/show_bug.cgi?id=36330)
* TBC
