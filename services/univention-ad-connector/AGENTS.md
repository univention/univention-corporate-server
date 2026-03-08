# univention-ad-connector

Debian source package: Modules for AD Connector synchronisation. Implements UCS Active Directory Connector.

## Key contents
- `modules/` -- contains the `univention.connector` Python module (no setup.py; installed via debian packaging)
- `ad-connector.py` -- LDAP listener module
- `univention-ad-connector` -- main connector script
- `umc/` -- UMC module for AD Connector management
- `conffiles/` -- UCR template files
- `scripts/` -- helper scripts (e.g. `univention-adsearch`, `univention-adconnector-list-rejected`)
