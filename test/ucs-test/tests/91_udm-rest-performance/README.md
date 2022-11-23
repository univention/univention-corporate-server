# Performance tests for UDM Rest

## Structure

Performance test files with specifications are placed, as in every other section,
at the top level and have a number prefix. The test runs `locust` via a virtual environment
on one of the locust files in the directory `locustfiles`, which are suffixed with ``_locust_user.py``.
Utilities used by the locust files are located in `utils.py` and abstract base classes in `locustclasses.py` and `generic_user.py`.

Adjust locust configuration for a specific test in the top level performance test file
via the global variable `LOCUST_ENV_VARIABLES`.

## Paths

The path below which application relevant data and the python virtual environment
is stored is `/var/lib/udm-performance-tests/`. As the installation depends on this path,
it is not changeable via an environment variable.

## Installation and usage

During development, build and install the package locally. Otherwise, install it as any other package with:

```shell
univention-install ucs-test-udm-rest-performance
```

As any other section, all test can be run via:

```shell
ucs-test -E dangerous -s udm-performance-rest
```

To run the `locustfiles` manually, run:

```shell
/var/lib/ram-performance-tests/venv/bin/locust -t <runtime> -f <locustfile> --headless --host <hostfqdn> <user class>
```

For example:

```shell
/var/lib/ram-performance-tests/venv/bin/locust -t 1m -f /usr/share/ucs-test/91_udm-performance-test/locustfiles/udm_users_user_locust_user.py --headless --host backup1.ucs.local UsersUserGet
```

To run the complete test including the stats checks:

```shell
./01_udm_performance_test.py -f
```
