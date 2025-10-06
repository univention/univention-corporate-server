This document describes various states related to user account disabling, locking, and password expiry, along with their corresponding UDM and LDAP representations for POSIX, Samba, Kerberos and Active Directory systems.

[TOC]

# Date formats

- Windows Filetime: 100 nanoseconds since January 1, 1601, UTC
- UNIX timestamp: number of seconds since January 1, 1970, UTC
- GeneralizedTime: timestamp `YYYYMMDDHHMMSSZ` (ASN.1 / X.680) in UTC/Zulu.

# UDM properties of `users/user` for account status information

## `locked`: Account locked due to authentication failures

Indicates the account has been locked because of too many failed authentication attempts.
Active Directory doesn't allow to set a `locked=True` state, which is why UDM denies this as well.

- **UCS OpenLDAP attributes** (any of):

  - `sambaAcctFlags` contains `L`
  - `krb5KDCFlags` bitmask includes the `???` bit (aka: `1 << 17`, `0x20000`).
  - `pwdAccountLockedTime`: unset by UDM during unlocking. Otherwise unused: Not set by any known components.
- **Related UDM properties**:

  - `lockedTime`: Windows Filetime timestamp when account lockout happened

    - **LDAP attribute:** `sambaBadPasswordTime`: Windows Filetime of last bad password event.
  - `unlock=True`: Unlocks the account (sets `locked=0`, no corresponding LDAP attribute). Note: it’s not possible to set `locked=1` directly without additional procedures.
  - `unlockTime`: Calculated timestamp when the account will be automatically unlocked, based on policy and `lockedTime`.
- **Property UDM search filter**:

  - `locked=` `1` | `0` | `posix` | `windows` | `all` | `none` | `*`

**Note**: `locked` is distinct from `disabled` – a locked user can still perform certain operations like changing their password.

- **Active Directory (and Samba) attributes**:

  - `lockoutTime`: (read only if != 0!) Windows Filetime, when the account was locked out.
  - `badPasswordTime`: (read only!) Windows Filetime, of last entered wrong password.
  - (`userAccountControl` bitmask includes `ADS_UF_LOCKOUT` (`0x10`))

## `passwordexpiry`: Password expiration time

Defines the point in time after which the password is considered expired.
After this time, the user can still attempt to log in, but must change the password to gain full access.

- **UCS OpenLDAP attributes**:

  - `shadowLastChange`: Number of days from January 1, 1970, up to the day the password was last modified.
  - `shadowMax`: The maximum number of days a password is valid (i.e., the password lifespan minus one day, depending on policy).
  - `krb5PasswordEnd`: GeneralizedTime, Kerberos considers this timestamp as the exact moment (beginning of that day) when the password becomes invalid.
- **Related UCS OpenLDAP attributes**:

  - `sambaPwdLastSet`: Unix timestamp, last date the password was set
  - `sambaPwdMustChange`: (unused in UDM since [Bug #13199](https://forge.univention.org/bugzilla/show_bug.cgi?id=13199))
  - `sambaBadPasswordTime`: Unix timestamp, the last time an incorrect password attempt was made.
  - `sambaBadPasswordCount`: Number of consecutive failed login attempts with an incorrect password.
- **Property UDM search filter**: Currently not possible to search for password expired accounts.
- **Related UDM properties**:

  - `pwdChangeNextLogin`: Boolean, indicating that the password has expired.

In POSIX, the date on which the password becomes expired is calculated as:
```text
Expiry Date = (January 1, 1970) + shadowLastChange + shadowMax + 1 (day)
```

**Note**: The Unix `shadow` mechanism regards the day of expiry (`shadowLastChange + shadowMax`) as the last valid day. The password becomes invalid the following day at 00:00.

**Note:**: If `krb5PasswordEnd` is set to `20241021000000Z`, Kerberos will treat October 21, 2024 as already expired starting at 00:00 UTC.

- **Active Directory (and Samba) attributes**:

  - `pwdLastSet`: Windows Filetime, the time when the user's password was last set (`0` means password must be changed at next login).
  - `badPwdCount`: Number of consecutive failed login attempts with an incorrect password.

## `disabled`: Account deactivated

Indicates the user account is deactivated. This affects authentication for Windows (Samba), Kerberos, and POSIX systems.

- **UCS OpenLDAP attributes** (any of):

  - `sambaAcctFlags` contains `D`
  - `krb5KDCFlags` bitmask includes the `KRB5_KDB_REQUIRES_PRE_AUTH` bit (aka: `1 << 7`, `0x80`).
  - `shadowExpire == 1` or `shadowExpire < current time` or `userPassword` hash starts with `!`
- **Property UDM search filter**:

  - `disabled=` `1` | `0` | `posix` | `windows` | `all` | `none` | `kerberos` | `windows_kerberos` | `windows_posix` | `posix_kerberos` | `*`

**Note**: This may not disable login via LDAP (depending on configuration).

- **Active Directory (and Samba) attributes**:

  - `userAccountControl` bitmask includes `ADS_UF_ACCOUNT_DISABLE` (`0x02`)

## `userexpiry`: Account expiration time

Defines a point in time after which the account is considered expired (i.e., disabled).

- **UCS OpenLDAP attributes**:

  - `sambaKickoffTime`: UNIX timestamp
  - `krb5ValidEnd`: GeneralizedTime (currently when stored via UDM time is set to `00:00:00` o'clock: `YYYYMMDD000000Z`)
  - `shadowExpire`: UNIX timestamp when the account is considered expired
- **Property UDM search filter**:

  - `userexpiry=` `2025-06-20` | `*`
  - `userexpiry=2025-*` does **NOT** work

**Note**: This value does not automatically set `disabled=True` in the account when the expiration time is reached.

- **Active Directory (and Samba) attributes**:

  - `accountExpires` Windows Filetime

## `accountActivationDate`: Future account activation

Allows defining a future date when the account becomes active.

- **UCS OpenLDAP attributes**:
  - `krb5ValidStart` GeneralizedTime
- **Behavior**:
  - Until this date, the account is created with `disabled=True`.
  - Requires a [cron job](scripts/univention-delayed-account-activation) to reactivate the user by setting `disabled=False` once the date is reached.
- **Property UDM search filter**:
  - `accountActivationDate=` `2025-06-20` | `2025-06-20 15:00`

## `password`: Account password

The password of a user account is stored in different attributes. UDM keeps them consistent.

- **UCS OpenLDAP attributes**:
  - `userPassword`: POSIX crypt (or bcrypt) hash
  - `pwhistory`: History of set `userPassword` crypt hashes
  - `krb5Key` + `krb5KeyVersionNumber`: Kerberos Keys (ASN.1 DER-encoded EncryptionKey structure): multi valued password hash with different encryption types
  - `sambaNTPassword`: NT hash (16 bytes) (can be converted to a `arcfour-hmac-md5` Kerberos Key)
  - `sambaLMPassword`: LM hash: unsafe, disabled via UCR `password/samba/lmhash=false`
  - `sambaPasswordHistory`: History of salted `sambaNTPassword` hash as MD5sum-Hexdigest. Not set by UDM anymore, but present in historic environments. ([Bug #52230](https://forge.univention.org/bugzilla/show_bug.cgi?id=52230))
- **Related UDM properties**:
  - `overridePWHistory`: Disable password history checks during setting the password via UDM.
  - `overridePWLength`: Disable password complexity checks during setting the password via UDM.
- **Property UDM search filter**:
  - It's not allowed to search for password hashes.
- **Active Directory (and Samba) attributes**:
  - `unicodePwd` in AD: quoted UTF-16LE cleartext password, stored encrypted. Write-Only.
  - `unicodePwd` in Samba: HexDigest of NT hash.
  - `ntPwdHistory`: Passsword history of NT hashes
  - `dBCSPwd`: LM hash
  - `supplementalCredentials`: Stores modern Kerberos keys and other credential material (AES keys, etc.) in AD. This is where AD stores the equivalents of krb5Key. Currently not set by AD-Connector.
  - `msDS-KeyVersionNumber`: `krb5KeyVersionNumber` equivalent. Can't be set directly ([Bug #32082](https://forge.univention.org/bugzilla/show_bug.cgi?id=32082)).

**Note**: `userPassword` may contain `{K5KEY}`, `{KINIT}`, `{LANMAN}`, `{SASL}`. E.g. in cases we can't create a crypt hash when synching password hashes from AD/Samba 4 to UCS. Different components evaluate them differently.

## Account "active" property which combines disabled+locked+userexpiry states

There is effectively no pseudo property which combines all the states as an indicator that an account is fully active.
However, a UDM search with a filter that groups these conditions can list all inactive accounts. For example:

```shell
udm users/user list --filter "(|(disabled=1)(locked=1)(userexpiry<=$(date -I))"
```
```python
univention.admin.modules.get('users/user').lookup(None, lo, filter_format("(|(disabled=1)(locked=1)(userexpiry<=%s))", [datetime.date.today().isoformat()]))
```

# Inconsistency in handling of password expiry semantics (Shadow vs Kerberos) ([Bug #57681](https://forge.univention.org/bugzilla/show_bug.cgi?id=57681))

* When both `shadowLastChange + shadowMax` and `krb5PasswordEnd` point to the same calendar day (e.g., `2024-10-21`), Kerberos regards the password as expired at 00:00 on that day, while Unix regards that day as still valid until 23:59:59.
* As a result, on the day of expiry:

  1. Some services (e.g., `pam_krb5`) consider the password expired immediately after midnight and trigger a password change.
  2. Other services (e.g., `pam_unix` and LDAP overlays like `shadowbind`) still consider the password valid until the next day.
* This discrepancy can cause user-flow issues. For example, Single Sign-On (SSO) integrations such as SimpleSAMLphp will see Kerberos marking the password as expired (thus prompting a change), while Unix still allows login. After a user changes their password through the SSO flow, the Unix side continues to accept the old password until the end of that calendar day, leading to repeated prompts.

* For a user with:

  * `shadowLastChange + shadowMax` = `2024-10-21`
  * `krb5PasswordEnd` = `20241021000000Z`
* On October 21, 2024:

  * Kerberos: Immediately treats password as expired at `2024-10-21 00:00:00Z`.
  * Unix (shadow): Treats `2024-10-21` as the last valid day; password expires at `2024-10-22 00:00:00` local time.
* Consequently, depending on which attribute is checked first, the system may inconsistently require a password change (Kerberos) or allow login (Unix).

To align both mechanisms so that "expiration date" consistently means "the first moment of the expiry day," it is recommended to configure `shadowMax` to one day less than the interval used in the Kerberos policy:

* If `pwhistoryPolicy.expiryInterval` is defined (e.g., 90 days), set:

  ```text
  shadowMax = pwhistoryPolicy.expiryInterval - 1
  ```
* This ensures that:

  * Unix password expiry (`shadowLastChange + shadowMax + 1`) occurs at 00:00 on the same day as Kerberos (`krb5PasswordEnd`).
  * Both POSIX and Kerberos will mark the password as expired at 00:00 on the configured expiry date (e.g., if the policy says “expires on 2024-10-21,” neither system will allow the user to log in at any time on that date).

## Clarifying "Expiry Date" semantics

* Ambiguity exists in the term “expiry date.” Two interpretations are:

  1. The first moment of the expiry day (i.e., 2024-10-21 00:00) – after this moment, login is disallowed.
  2. The last valid day (i.e., the user may log in on 2024-10-21 until 23:59:59; at 2024-10-22 00:00, login is disallowed).
* We recommend adopting interpretation 1, treating the configured expiry date as the first moment when login is disallowed.

## Verification of Shadow and Kerberos behaviors

* Verified against `man 5 shadow` and the Unix shadow implementation: `shadowLastChange` is indeed days since epoch, and `shadowMax` + 1 defines expiry days count. Unix checks `(now - shadowLastChange) > shadowMax` (i.e., if number of days since last change strictly exceeds `shadowMax`, the day of `shadowLastChange + shadowMax` is still valid).
* Verified Kerberos behavior from RFC 4120 and MIT Kerberos implementation: `krb5PasswordEnd` is interpreted as the moment after which the password is no longer valid (i.e., a strict `>=` comparison against current time).
* Conclusion: To force both systems to recognize expiry at the same instant (00:00 of the expiry date), configure `shadowMax = krb5ExpiryInterval - 1`.

# Related bugs
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

# Related bugs with historic context / knowledge
* [Bug 57681 - Day of password expiry, a passwordchange is prompted but not followed through with sso login](https://forge.univention.org/bugzilla/show_bug.cgi?id=57681)
* [Bug 46349 - Value of userexpiry derived from shadowExpire depends on timezone](https://forge.univention.org/bugzilla/show_bug.cgi?id=46349#c7)
* [Bug 39817 - Locked login methods ignored by Samba 4](https://forge.univention.org/bugzilla/show_bug.cgi?id=39817)
* [Bug 36486 - Users which are both expired and deactivated are rejected](https://forge.univention.org/bugzilla/show_bug.cgi?id=36486)
* [Bug 36330 - Failed to create user with expired password - invalid date format](https://forge.univention.org/bugzilla/show_bug.cgi?id=36330)
* TBC

# Ressources
* [Active Directory Technical Specification](https://winprotocoldoc.z19.web.core.windows.net/MS-ADTS/%5bMS-ADTS%5d.pdf)
* [Active Directory Technical Specification: all versions](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/)
* https://learn.microsoft.com/en-us/windows/win32/adsi/winnt-account-lockout#resetting-the-account-lockout-status
* https://learn.microsoft.com/en-us/answers/questions/1129755/active-directory-not-able-to-update-lockouttime-at
