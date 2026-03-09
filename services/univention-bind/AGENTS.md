# univention-bind

Integrates the BIND9 DNS server into UCS. Zone data is sourced from LDAP or from Samba4.

## Binary Packages

- `univention-bind` -- DNS server configuration, join scripts, listener module

## Directory Structure

- `conffiles/` -- UCR templates for BIND configuration
- `bind.py` -- directory listener module for DNS zone updates
- `etc/` -- additional configuration files
- `usr/` -- helper utilities
- `import-zone` -- zone import script
