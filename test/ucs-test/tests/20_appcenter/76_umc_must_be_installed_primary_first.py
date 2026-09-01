#!/usr/share/ucs-test/runner python3
## desc: |
##  Check that installing an app with the flag MustBeInstalledOnPrimaryFirst
##  is rejected on a backup node, as long as it is not installed in the
##  domain yet. A local testing appcenter is used.
## timeout: 900
## roles: [domaincontroller_backup]
## packages:
##   - univention-management-console-module-appcenter
##   - univention-appcenter-dev
## tags: [appcenter]

import logging

import appcentertest as app_test


@app_test.test_case
def test_backup_install_rejected(app_center, application):
    """
    Installing an app with MustBeInstalledOnPrimaryFirst must be rejected
    on a backup node as long as it is not installed in the domain yet.
    """
    package = app_test.DebianPackage(application)
    app = app_test.AppPackage(package, {
        "ID": application,
        "Code": next(app_test.AppPackage.CODES),
        "Version": "1.0",
        "Name": application,
        "DefaultPackages": package.name,
        "MustBeInstalledOnPrimaryFirst": "True",
    })
    app.build_and_publish()
    app.remove_tempdir()

    test = app_test.TestOperations(app_center, app.app_id)

    dry_run = app_center.install_dry_run([app.app_id])
    if test.dry_run_successful(dry_run):
        app_test.fail("Dry-install of app on backup node did not fail.")

    try:
        test.test_install(test_installed=False)
    except app_test.AppCenterCheckError:
        pass
    else:
        error = "Install of app on backup node did not fail."

        info = app_center.get(app.app_id)
        if not app_test.CheckOperations.uninstalled(app.app_id, info):
            error += " And the installation left traces."
        if app_center.is_installed(app.app_id, info=info):
            error += " And is marked as installed."
            app_center.remove([app.app_id])

        app_test.fail(error.strip())


def main():
    app_test.app_logger.log_to_stream()
    app_test.app_logger.get_base_logger().setLevel(logging.WARNING)

    with app_test.local_appcenter():
        test_backup_install_rejected()


if __name__ == '__main__':
    main()
