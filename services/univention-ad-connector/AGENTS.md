# univention-ad-connector

Synchronises objects (users, groups, containers, GPOs) between UCS LDAP and a remote Microsoft Active Directory. Includes a UMC module for monitoring connector status.

## Binary Packages

- `python3-univention-connector` -- base connector sync framework
- `python3-univention-connector-ad` -- AD-specific connector modules
- `univention-ad-connector` -- main package with service, join scripts, and UCR templates
- `univention-ad-connector-exchange` -- Exchange attribute mapping extension
- `univention-management-console-module-adconnector` -- UMC module

## Directory Structure

- `modules/univention/connector/` -- Python connector framework and AD mapping logic
- `conffiles/` -- UCR templates for connector configuration
- `umc/` -- UMC module (JS frontend + Python backend)
- `scripts/` -- helper scripts
- `*univention-ad-connector*.inst` -- join/unjoin scripts
