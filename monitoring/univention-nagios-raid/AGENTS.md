# univention-nagios-raid

Nagios plugin to monitor software RAID (mdadm) status. Depends on `univention-monitoring-raid` and `univention-nagios-client`.

## Binary Packages

- `univention-nagios-raid` -- RAID monitoring plugin (uses `monitoring-plugins-contrib`).

## Directory Structure

- `conffiles/` -- UCR templates for Nagios NRPE check configuration.
- `*.inst` / `*.uinst` -- Join/unjoin scripts.
