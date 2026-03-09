# univention-system-setup

System setup wizard for UCS. Configures system name, domain, network, and software during initial setup or via the UMC web interface.

## Binary Packages

- `univention-system-setup` -- setup tools and Python library
- `univention-system-setup-boot` -- triggers setup wizard on next boot (Primary Directory Node only)
- `di-univention-system-setup` -- Debian installer udeb integration
- `univention-management-console-module-setup` -- UMC web module

## Key Directories

- `umc/` -- UMC module (Python backend + JS frontend)
- `conffiles/` -- UCR templates
- `city-data/` -- city/locale data for setup wizard
- `tests/` -- test suite
- `usr/` -- helper scripts and library modules
- `etc/` -- default configuration
- `systemd/` -- systemd service files

## Key Files

- `35univention-management-console-module-setup.inst` -- join script

## Notes

- Includes a UMC module with both Python backend and JavaScript frontend
- Has Debian installer (d-i) integration via the udeb package
