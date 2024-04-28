#!/usr/share/ucs-test/runner python3
## desc: |
##  Check basic App-Center Operation failures (non existent apps) via UMC commands within a local testing appcenter.
## roles-not: [basesystem]
## packages:
##   - univention-management-console-module-appcenter
##   - univention-appcenter-dev
## tags: [appcenter]

import pytest

from univention.lib.umc import ConnectionError, HTTPError
from univention.testing.conftest import has_license

import appcentertest as app_test


HTTPException = (HTTPError, ConnectionError)


@pytest.fixture(scope="module", autouse=True)
def wrap():
    app_test.restart_umc()
    yield
    app_test.restart_umc()


@has_license()
def test_install_non_existent_dry_run(app_center, application) -> None:
    """Dry-run install an app that does not exist must fail."""
    with pytest.raises(HTTPException):
        app_center.install_dry_run([application])


@has_license()
def test_install_non_existent(app_center, application) -> None:
    """Install an app that does not exist must fail."""
    with pytest.raises(HTTPException):
        app_center.install([application])


@has_license()
def test_update_non_existent_dry_run(app_center, application) -> None:
    """Dry-run update an app that does not exist must fail."""
    with pytest.raises(HTTPException):
        app_center.upgrade_dry_run([application])


@has_license()
def test_update_non_existent(app_center, application) -> None:
    """Update an app that does not exist must fail."""
    with pytest.raises(HTTPException):
        app_center.upgrade([application])


@has_license()
def test_uninstall_non_existent_dry_run(app_center, application) -> None:
    """Dry-run uninstall an app that does not exist must fail."""
    with pytest.raises(HTTPException):
        app_center.remove_dry_run([application])


@has_license()
def test_uninstall_non_existent(app_center, application) -> None:
    """Uninstall an app that does not exist must fail."""
    with pytest.raises(HTTPException):
        app_center.remove([application])
