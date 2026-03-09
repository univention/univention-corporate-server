# test/utils/

Not a Debian package. Shared shell and Python helper scripts used by CI test pipelines to set up and run test environments.

## Structure

- `utils.sh` -- Main shell utility library sourced by most test scripts.
- `start-*.sh` -- Scripts to launch specific test environments (AD connector, Keycloak, school multi-server, Samba, etc.).
- `utils-*.sh` -- Domain-specific utility libraries (school, keycloak, nubus, installation, etc.).
- `installation_test/` -- Installation test helpers.
- `guardian/`, `id-broker/`, `ram/` -- Per-component test setup helpers.
- `*.py` -- Python utilities for AD join/takeover, school installation, App Center, Keycloak load testing, etc.
- `ucs-ec2-list`, `ucs-ec2-terminate` -- EC2 instance management helpers.
