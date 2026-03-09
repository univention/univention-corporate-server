# univention-heimdal

Kerberos (Heimdal) integration for UCS. Provides KDC with LDAP-backed key storage, member configuration, and shared Kerberos configuration.

## Binary Packages

- `univention-heimdal-kdc` -- Kerberos Key Distribution Center
- `univention-heimdal-member` -- Kerberos Managed Node client
- `univention-heimdal-common` -- shared Kerberos configuration

## Key Files

- `conffiles/` -- UCR templates for krb5.conf, KDC config
- `keytab.py`, `keytab-member.py` -- keytab management (listener modules)
- `salt_krb5Keys` -- Kerberos key salting
- `univention-create-keytab` -- keytab creation tool
- `*.inst` -- join scripts

## Notes

- Uses LDAP directory listener modules for keytab synchronization
