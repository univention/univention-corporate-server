# univention-pam

PAM (Pluggable Authentication Modules) and NSS (Name Service Switch) login configuration. Supports authentication via flat files, LDAP, Kerberos 5, and SSSD.

## Binary Packages

- `univention-pam`

## Key Directories

- `conffiles/` -- UCR templates for PAM and NSS configuration
- `server_password_change.d/` -- scripts run on server password changes
- `tests/` -- test suite

## Key Files

- `11univention-pam.inst` -- join script
- `faillog.py` -- login failure tracking
- `ldap-group-to-file.py` -- LDAP group sync to local files
- `nscd.py`, `nss.py` -- NSS/NSCD listener modules
- `well-known-sid-name-mapping.py` -- Windows SID mapping
- `univention-create-homedir` -- home directory creation script

## Notes

- Has LDAP directory listener modules (`faillog.py`, `nscd.py`, `nss.py`)
