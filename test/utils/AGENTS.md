# utils

Shell and Python utility scripts for CI/CD test orchestration.

## Key contents
- `utils.sh` -- Primary shared shell functions for test environments
- `start-test.sh` -- Main entry point for starting test runs
- `start-ucs-*.sh` -- Scripts to launch specific UCS test environments (Samba, AD connector, school, Keycloak, etc.)
- `utils-*.sh` -- Domain-specific utility functions (school, Keycloak, Nubus, installation, etc.)
- `ucs-ec2-list`, `ucs-ec2-terminate` -- EC2 instance management helpers
- `installation_test/` -- Installation test utilities
- `guardian/`, `id-broker/`, `ram/` -- Subsystem-specific CI helpers
