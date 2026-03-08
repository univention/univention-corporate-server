# univention-printserver

Debian source package: Print server. Printers managed with UDM.

## Key contents
- `cups-printers.py`, `cups-pdf.py`, `ppds.py` -- LDAP listener modules for printer management
- `umc/` -- UMC module for printer administration
- `univention-cupsadmin`, `univention-lpadmin` -- CLI tools for printer management
- `conffiles/` -- UCR template files (includes `cupsd.conf`)
- `mark_models_as_deprecated.py` -- helper script for printer model deprecation
