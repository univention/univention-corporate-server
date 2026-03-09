# univention-nagios-smart

Nagios plugin to monitor SMART status of hard disks. Includes a Perl check script and a C SUID wrapper for privilege escalation.

## Binary Packages

- `univention-nagios-smart` -- SMART monitoring plugin. Depends on `smartmontools`, `univention-monitoring-smart`, and `univention-nagios-client`.

## Directory Structure

- `check_smart.pl` -- Perl script for SMART status checks.
- `check_smart_suidwrapper.c` -- C SUID wrapper for the check script.
- `conffiles/` -- UCR templates for Nagios NRPE check configuration.
- `*.inst` / `*.uinst` -- Join/unjoin scripts.
- `Makefile` -- Builds the SUID wrapper binary.
