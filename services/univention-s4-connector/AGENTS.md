# univention-s4-connector

Debian source package: Modules for Samba4 Connector synchronisation.

## Key contents
- `modules/` -- contains the `univention.s4connector` Python module (no setup.py; installed via debian packaging)
- `s4-connector.py` -- LDAP listener module
- `univention-s4-connector` -- main connector script
- `scripts/` -- helper scripts
- `ldap/` -- LDAP schema extensions
- `conffiles/` -- UCR template files
- `server_password_change.d/` -- hooks for server password rotation
