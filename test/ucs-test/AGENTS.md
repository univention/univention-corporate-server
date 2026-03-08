# ucs-test

Debian source package: UCS test framework and test suite. Provides the `ucs-test` runner, shared Python/shell libraries (`univention.testing.*`), and dozens of categorized test packages. Produces ~40 binary packages for different test areas.

## Key contents
- `univention/testing/` -- `univention.testing` Python module (shared test libraries)
- `tests/` -- Categorized test suites (base, UCR, LDAP, Samba, UDM, UMC, mail, Docker, Keycloak, SAML, etc.)
- `bin/` -- Test runner executables
- `lib/` -- Additional shared test libraries (shell and Python)
- `debian/` -- Debian packaging (produces ~40 binary packages)
- `pyproject.toml` -- Python project configuration
