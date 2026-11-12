# Cerbos policy tests for UDM authorization

Test suites for the Cerbos policies
that `univention-configure-udm-authorization` generates
from the UDM authorization DSL.

## Requirements

The tests run on a UCS system, not on a developer machine:

- `univention-directory-manager-tools` with `univention-configure-udm-authorization`,
  because the policies are generated from the installed UDM modules and DSL files.
- Docker with access to `gitregistry.knut.univention.de`,
  because Cerbos runs from the image of the Univention Cerbos fork
  that provides the `ldapDN` functions.

## Run the tests

Copy the whole `cerbos-tests` directory to the UCS system,
not only the script,
and run it as `root`:

```bash
scp -r cerbos-tests root@primary.ucs.test:/opt/
ssh root@primary.ucs.test /opt/cerbos-tests/run-cerbos-tests
```

The script generates the policies into a temporary directory,
so the installed policy tree is not changed.
It replaces the LDAP base `dc=ucs,dc=test` in the fixtures
with `ucr get ldap/base`
and runs `cerbos compile` on the policies together with the suites.

Options after `--` go to `cerbos compile`,
for example to list every check with its result, not only the failed ones,
to evaluate strictly,
or to run a single suite:

```bash
/opt/cerbos-tests/run-cerbos-tests -- --verbose
/opt/cerbos-tests/run-cerbos-tests -- --strict-evaluation
/opt/cerbos-tests/run-cerbos-tests -- --test-filter='suite=DenyUidNumberZero'
```

The exit code is `0` if all tests pass and `4` if a test fails.

## Add a suite

Create a directory next to the existing ones:

```
cerbos-tests/<name>/
├── <name>_test.yaml
└── testdata/
    ├── principals.yaml
    └── resources.yaml
```

Cerbos loads the fixtures from the `testdata` directory next to the suite.
Write DNs below `dc=ucs,dc=test`;
the script replaces it with the LDAP base of the system.
See the [Cerbos documentation on testing policies](https://docs.cerbos.dev/cerbos/latest/policies/compile.html#testing)
for the format.
