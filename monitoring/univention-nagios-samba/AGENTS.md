# univention-nagios-samba

Nagios plugin to monitor UCS Samba DRS replication failures. Includes a SUID wrapper for privilege escalation during checks.

## Binary Packages

- `univention-nagios-samba` -- Samba monitoring plugin. Depends on `univention-monitoring-samba` and `univention-nagios-client`.

## Directory Structure

- `check_univention_samba_drs_failures` -- Check script for Samba DRS replication failures.
- `check_univention_samba_drs_failures_suidwrapper.c` -- C SUID wrapper for the check script.
- `conffiles/` -- UCR templates for Nagios NRPE check configuration.
- `*.inst` / `*.uinst` -- Join/unjoin scripts.
