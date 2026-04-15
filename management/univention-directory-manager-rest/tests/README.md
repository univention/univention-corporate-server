# Test Organization

## TL;DR: Run the tests

The test suite requires an LDAP server along with the UDM REST API.
You can run it as follows:

```bash
cp .env.udm-rest-api.example .env.udm-rest-api
mkdir secret
echo -n univention > secret/ldap.secret
echo -n univention > secret/machine.secret
docker compose up --detach ldap-server udm-rest-api
```

Then execute the tests:

- In a container:

```bash
docker compose run --build --rm test
```

- Locally:

```bash
# Use "pipenv" to have the right environment
pushd docker/testrunner
pipenv sync -d
pipenv shell
popd
pytest run tests/integration
```

## Target structure

The target structure for testing shall eventually follow this pattern:

```
└── tests  # top-level tests folder
    ├── README.md  # explains test organization inside this folder
    ├── unit  # name this unit_and_integration if keeping both here
    ├── integration  # optional: omit if kept together with unit tests
    └── e2e
```

### Unit tests

No unit tests are available at the time of writing,
as the container is built from upstream Debian packages
and no source code is kept in this repository.

### Integration tests

Tests which check the *integration* of multiple containers will be grouped into
the folder `integration`.

New tests are written as plain `pytest` based test cases.

### End to end tests

This repository contains no end-to-end tests. *End to end* is understood as
tests against the full running stack, so they are expected to be kept
separately.
