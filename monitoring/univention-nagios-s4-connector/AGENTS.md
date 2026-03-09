# univention-nagios-s4-connector

Nagios plugin to monitor the state of UCS Samba/S4 connectors. Includes a SUID wrapper for privilege escalation during checks.

## Binary Packages

- `univention-nagios-s4-connector` -- S4 connector monitoring plugin. Depends on `univention-monitoring-s4-connector` and `univention-nagios-client`.

## Directory Structure

- `check_univention_s4_connector` -- Check script.
- `check_univention_s4_connector_suidwrapper.c` -- C SUID wrapper for the check script.
- `conffiles/` -- UCR templates for Nagios NRPE check configuration.
- `*.inst` / `*.uinst` -- Join/unjoin scripts.
