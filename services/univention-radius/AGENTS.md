# univention-radius

Debian source package: FreeRADIUS 802.1X integration for UCS.

## Key contents
- `setup.py` -- installs the `univention.radius` Python package
- `modules/` -- Python source for `univention.radius`
- `listener/` -- LDAP listener module
- `tests/` -- unit tests (see `pytest.ini`)
- `conffiles/` -- UCR template files for FreeRADIUS configuration
- `univention-radius-ntlm-auth-suidwrapper.c` -- C SUID wrapper for NTLM auth
- `usr/` -- additional installed files
