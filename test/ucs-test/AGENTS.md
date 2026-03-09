# test/ucs-test/

Debian source package. The main UCS test framework and test suite collection.
Provides the `ucs-test` runner, shared Python/shell libraries (`univention.testing.*`), and dozens of categorized test packages.
Builds ~40 binary packages, each covering a specific UCS subsystem.

## Key binary packages

- **ucs-test** -- Meta package depending on the framework and all test modules.
- **ucs-test-framework** -- The `ucs-test` runner and Python test libraries.
- **ucs-test-libs** -- Common helper scripts shared across test modules.
- **ucs-test-modules-all** -- Meta package pulling in every `ucs-test-*` module.
- **ucs-test-\<area\>** -- Per-subsystem test modules: `base`, `ucr`, `ldap`, `udm`, `umc`, `samba`, `samba4`, `s4connector`, `adconnector`, `mail`, `docker`, `saml`, `keycloak`, `selenium`, `browser`, `appcenter`, `radius`, `self-service`, `crypto`, `udm-rest`, `authorization`, and more.

## Structure

- `tests/` -- Numbered test directories (one per module), each containing pytest test scripts.
- `univention/testing/` -- Python library (`univention.testing`) with test helpers, UDM/UMC/LDAP/connector utilities.
- `univention/appcenter/` -- App Center test helpers.
- `lib/` -- Shell helper libraries.
- `bin/` -- The `ucs-test` CLI entry point.
- `umc/` -- Test UMC module definitions.
- `debian/` -- Debian packaging (generates all binary packages from this single source).
