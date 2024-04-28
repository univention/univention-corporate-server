#!/usr/share/ucs-test/runner python3
## desc: |
##  Check basic App-Center Operation failures (already installed, not installed) via UMC commands within a local testing appcenter.
## roles-not: [basesystem]
## packages:
##   - univention-management-console-module-appcenter
##   - univention-appcenter-dev
## tags: [appcenter]

from univention.testing.conftest import has_license

import appcentertest as app_test


@has_license()
def test_already_installed_dry_run(app_center, package):
    """Try to dry-run install an app although it is already installed (must fail)."""
    test = app_test.TestOperations(app_center, package.app_id)
    with test.test_install_safe():
        result = app_center.install_dry_run([package.app_id])
        assert not test.dry_run_successful(result), "Dry-Install of already installed app did not fail."


@has_license()
def test_already_installed(app_center, package):
    """
    Try to install an app although it is already installed without prior
    dry-run (must fail).
    """
    test = app_test.TestOperations(app_center, package.app_id)
    with test.test_install_safe():
        result = app_center.install([package.app_id])
        assert not test.operation_successfull(result), "Install of already installed app did not fail."


@has_license()
def test_upgrade_without_dry_run(app_center, package):
    """Test a dry-run upgrade without having the app installed (must fail)."""
    test = app_test.TestOperations(app_center, package.app_id)
    result = app_center.upgrade_dry_run([package.app_id])
    assert not test.dry_run_successful(result), "Upgrade of not installed app did not fail."


@has_license()
def test_upgrade_without(app_center, package):
    """Test an upgrade without having the app installed (must fail)."""
    test = app_test.TestOperations(app_center, package.app_id)
    result = app_center.upgrade([package.app_id])
    assert not test.operation_successfull(result), "Upgrade of not installed app did not fail."


@has_license()
def test_uninstall_without_dry_run(app_center, package):
    """Test a dry-run uninstall without having the app installed (must fail)."""
    test = app_test.TestOperations(app_center, package.app_id)
    result = app_center.remove_dry_run([package.app_id])
    assert not test.dry_run_successful(result), "Uninstall of not installed app did not fail."


@has_license()
def test_uninstall_without(app_center, package):
    """Test an uninstall without having the app installed (must fail)."""
    test = app_test.TestOperations(app_center, package.app_id)
    result = app_center.remove([package.app_id])
    assert not test.operation_successfull(result), "Uninstall of not installed app did not fail."
