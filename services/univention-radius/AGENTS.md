# univention-radius

Integrates FreeRADIUS into UCS to support 802.1X network access control (wired and wireless). Authenticates against UCS LDAP/Samba.

## Binary Packages

- `univention-radius` -- FreeRADIUS configuration, join scripts, NTLM auth helper (C)
- `python3-univention-radius` -- Python modules for RADIUS authentication logic

## Directory Structure

- `modules/` -- Python package `univention.radius`
- `conffiles/` -- UCR templates for FreeRADIUS configuration
- `listener/` -- directory listener module
- `tests/` -- unit tests
- `usr/` -- helper scripts and auth wrappers
- `univention-radius-ntlm-auth-suidwrapper.c` -- C NTLM auth SUID wrapper
