# univention-nagios-servicechecks

Nagios plugins for monitoring CUPS, Squid, and OPSI services (daemon availability and web frontend checks).

## Binary Packages

- `univention-nagios-cups` -- CUPS daemon and webfrontend monitoring. Depends on `univention-monitoring-cups`.
- `univention-nagios-squid` -- Squid proxy service monitoring. Depends on `univention-monitoring-squid`.
- `univention-nagios-opsi` -- OPSI daemon and webfrontend monitoring. Depends on `univention-monitoring-opsi`.

## Directory Structure

- `check_univention_cups` -- Check script for CUPS.
- `check_univention_opsi` -- Check script for OPSI.
- `check_univention_squid` -- Check script for Squid.
- `conffiles/` -- UCR templates for Nagios NRPE check configuration.
- `*.inst` -- Join scripts.
