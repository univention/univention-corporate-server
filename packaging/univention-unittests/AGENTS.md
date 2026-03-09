# univention-unittests

Pytest plugins and helpers for running unit tests against UCS-specific packages (mocking UCR, UDM, LDAP, etc.).

## Binary Packages

- `python3-univentionunittests` -- Pytest plugins for UCS unit testing
- `univention-unittests` -- Metapackage depending on the pytest plugins
- `univention-unittests-python` -- Transitional dummy package

## Directory Structure

- `python/` -- Python package with pytest plugins
- `univention-unittest` -- CLI entry-point script
- `setup.py` -- Python packaging
