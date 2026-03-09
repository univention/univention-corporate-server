# univention-pkgdb

Software package monitoring database. Tracks installed packages across UCS systems in a PostgreSQL database. Includes client tools, listener modules, and a UMC frontend.

## Binary Packages

- `univention-pkgdb` -- server-side components and database setup
- `python3-univention-pkgdb` -- Python library for DB access
- `univention-pkgdb-tools` -- client-side scanning/reporting tools
- `univention-management-console-module-pkgdb` -- UMC module

## Directory Structure

- `pyshared/` -- Python library modules
- `conffiles/` -- UCR templates
- `umc/` -- UMC module (JS frontend + Python backend)
- `sql/` -- SQL schema files
- `pkgdb.py`, `pkgdb-watch.py` -- directory listener modules
- `univention-pkgdb-scan`, `univention-pkgdb-check` -- CLI tools
