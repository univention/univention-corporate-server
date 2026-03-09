# univention-admin-diary

Logs administrative actions (user creation, package installs, etc.) to a database backend (PostgreSQL or MariaDB) via rsyslog RELP. Provides a UMC module for viewing diary entries.

## Binary Packages

- `univention-admin-diary-backend` -- rsyslog-based backend service
- `python3-univention-admin-diary-backend` -- backend Python library (SQLAlchemy)
- `univention-admin-diary-client` -- client-side rsyslog forwarding
- `python3-univention-admin-diary` -- shared Python library
- `univention-management-console-module-admindiary` -- UMC module

## Directory Structure

- `python/` -- Python library modules
- `conffiles/` -- UCR templates (rsyslog config)
- `umc/` -- UMC module (JS frontend + Python backend)
- `listener/` -- directory listener module
- `scripts/` -- helper scripts
- `sql/` -- not present; database creation via `create-database`, `create-tables` scripts
