# univention-printserver

Integrates the CUPS print server into UCS. Printers are managed through UDM and applied via directory listener modules. Includes a PDF pseudo-printer and a UMC administration module.

## Binary Packages

- `univention-printserver` -- CUPS configuration, listener modules, join scripts
- `univention-printserver-pdf` -- PDF pseudo-printer setup
- `univention-management-console-module-printers` -- UMC module for printer admin

## Directory Structure

- `conffiles/` -- UCR templates for CUPS configuration
- `umc/` -- UMC module (JS frontend + Python backend)
- `cups-printers.py`, `cups-pdf.py`, `ppds.py` -- directory listener modules
- `univention-cupsadmin`, `univention-lpadmin` -- CLI admin tools
