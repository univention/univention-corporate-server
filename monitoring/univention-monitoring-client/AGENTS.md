# univention-monitoring-client

Monitoring client and plugins for UCS. Installs Prometheus-based monitoring support and Nagios-compatible check plugins for various UCS services.

## Binary Packages

- `univention-monitoring-client` -- Core monitoring client (Prometheus metrics, cron jobs).
- `univention-monitoring-plugins` -- Nagios/NRPE check plugins for UCS-specific functionality.
- `univention-monitoring-ad-connector` -- Plugin to monitor AD connector state.
- `univention-monitoring-raid` -- Plugin to monitor software RAID status.
- `univention-monitoring-s4-connector` -- Plugin to monitor Samba/S4 connector state.
- `univention-monitoring-samba` -- Plugin to monitor Samba state.
- `univention-monitoring-cups` -- Plugin to monitor CUPS daemon/webfrontend.
- `univention-monitoring-squid` -- Plugin to monitor Squid proxy service.
- `univention-monitoring-opsi` -- Plugin to monitor OPSI daemon/webfrontend.
- `univention-monitoring-smart` -- Plugin to monitor SMART hard disk status.

## Directory Structure

- `alerts*/` -- Alert/check definitions for various services (AD connector, S4 connector, Samba, service checks).
- `conffiles/` -- UCR templates for configuration files.
- `src/` -- Python source code.
- `umc/` -- UMC (Univention Management Console) module integration.
- `*.inst` / `*.uinst` -- Join/unjoin scripts for package installation/removal.
- `monitoring-client.py` -- Directory listener module.
- `univention-monitoring.schema` -- LDAP schema for monitoring objects.
