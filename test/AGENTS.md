# test/

Test framework, test suites, CI scenarios, and tools for validating UCS installations, upgrades, and features.

## Subdirectories

### Debian source packages

- [generate-appliance/AGENTS.md](generate-appliance/AGENTS.md) -- Creates virtual appliance images for various virtualization platforms.
- [ucs-test/AGENTS.md](ucs-test/AGENTS.md) -- Main test framework and ~40 test module packages covering all UCS subsystems.
- [ucs-test-tools/AGENTS.md](ucs-test-tools/AGENTS.md) -- Small tool collection for UCS development and testing.
- [univention-demo-configuration/AGENTS.md](univention-demo-configuration/AGENTS.md) -- Restricted configuration for the demo.univention.de environment.

### Non-package directories

- [product-tests/AGENTS.md](product-tests/AGENTS.md) -- Shell-based product-level integration test scripts.
- [scenarios/AGENTS.md](scenarios/AGENTS.md) -- CI/CD test scenario configuration files (autotest `.cfg` files and KVM templates).
- [ucs-gui-tests/AGENTS.md](ucs-gui-tests/AGENTS.md) -- GUI-level installation tests using VNC/VM automation.
- [utils/AGENTS.md](utils/AGENTS.md) -- Shared shell and Python helper scripts used by CI test pipelines.
