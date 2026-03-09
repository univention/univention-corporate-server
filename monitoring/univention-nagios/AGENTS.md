# univention-nagios

Nagios client and common support for UCS. Provides NRPE server configuration, listener modules for Nagios service registration, and base check plugins.

## Binary Packages

- `univention-nagios-client` -- Nagios client support (NRPE, monitoring plugins, listener). Depends on `univention-monitoring-client`.
- `univention-nagios-common` -- Common Nagios support (listener, UDM tools).

## Directory Structure

- `conffiles/` -- UCR templates for NRPE and Nagios configuration.
- `usr/` -- Installed files (check scripts, library modules).
- `nagios-client.py` -- Directory listener module.
- `*.inst` -- Join scripts.
