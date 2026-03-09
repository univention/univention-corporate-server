# univention-s4-connector

Synchronises objects between UCS LDAP and the local Samba4 LDB directory. Shares the connector framework with univention-ad-connector.

## Binary Packages

- `python3-univention-connector-s4` -- Samba4-specific connector modules
- `univention-s4-connector` -- main package with service, join scripts, and UCR templates

## Directory Structure

- `modules/univention/s4connector/` -- Python S4 connector mapping and sync logic
- `conffiles/` -- UCR templates for connector configuration
- `scripts/` -- helper and migration scripts
- `ldap/` -- LDAP schema extensions
- `etc/` -- additional configuration
- `s4-connector.py` -- directory listener module
