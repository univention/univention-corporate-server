# test/scenarios/

Not a Debian package. Contains CI/CD test scenario configuration files that define automated test environments and execution plans.

## Structure

- `autotest-*.cfg` -- Scenario config files for automated test runs (install, update, UCS@school, etc.).
- `ad-connector/`, `s4-connector/` -- AD/S4 connector test scenarios.
- `ad-membermode/` -- AD member mode scenarios.
- `app-testing/`, `appliances/` -- App Center and appliance test scenarios.
- `base/`, `install-testing/`, `setup-testing/`, `update-testing/` -- Core system lifecycle scenarios.
- `keycloak/`, `ox-connector/`, `veyon/` -- Per-application test scenarios.
- `kvm-templates/`, `openstack-images/` -- VM/cloud image templates for test environments.
- `performance-testing/` -- Performance benchmarking scenarios.
- `umc/` -- UMC-specific scenarios.
- `ucs-appliance-testing/` -- Appliance-specific test scenarios.

The `.cfg` files are consumed by the UCS test automation framework (`ucs-ec2-tools` / `ucs-kvm-create`).
