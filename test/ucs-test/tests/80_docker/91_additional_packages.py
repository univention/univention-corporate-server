#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Check additional packages
## tags: [appcenter]
## exposure: dangerous
## packages:
##   - univention-appcenter
## bugs:
##  - 42200

import pytest

from univention.config_registry import ConfigRegistry
from univention.testing.debian_package import DebianPackage
from univention.testing.utils import package_installed

from dockertest import App, copy_package_to_appcenter, get_app_name


class UCSTest_AppCenter_PackageIsNotInstalled(Exception):
    pass


class UCSTest_AppCenter_PackageIsInstalled(Exception):
    pass


@pytest.mark.exposure('dangerous')
def test_additional_packages(appcenter, app_name, app_version):
    ucr = ConfigRegistry()
    ucr.load()

    app = App(name=app_name, version=app_version)

    package_name1 = get_app_name()
    package_name2 = get_app_name()
    package_name3 = get_app_name()

    if ucr.get('server/role') == 'domaincontroller_master':
        app.set_ini_parameter(AdditionalPackagesMaster=f'{package_name1},{package_name2}')
        app.set_ini_parameter(AdditionalPackagesMember=f'{package_name3}')
    elif ucr.get('server/role') == 'domaincontroller_backup':
        app.set_ini_parameter(AdditionalPackagesMaster=f'{package_name2}')
        app.set_ini_parameter(AdditionalPackagesBackup=f'{package_name1}')
        app.set_ini_parameter(AdditionalPackagesMember=f'{package_name3}')
    elif ucr.get('server/role') == 'domaincontroller_slave':
        app.set_ini_parameter(AdditionalPackagesBackup=f'{package_name1}')
        app.set_ini_parameter(AdditionalPackagesSlave=f'{package_name2}')
        app.set_ini_parameter(AdditionalPackagesMember=f'{package_name3}')
    elif ucr.get('server/role') == 'memberserver':
        app.set_ini_parameter(AdditionalPackagesMaster=f'{package_name2}')
        app.set_ini_parameter(AdditionalPackagesSlave=f'{package_name1}')
        app.set_ini_parameter(AdditionalPackagesMember=f'{package_name3}')

    app.add_to_local_appcenter()

    package1 = DebianPackage(name=package_name1, version='0.1')
    package1.build()
    copy_package_to_appcenter(ucr['version/version'], app.app_directory, package1.get_binary_name())

    package2 = DebianPackage(name=package_name2, version='0.1')
    package2.build()
    copy_package_to_appcenter(ucr['version/version'], app.app_directory, package2.get_binary_name())

    package3 = DebianPackage(name=package_name3, version='0.1')
    package3.build()
    copy_package_to_appcenter(ucr['version/version'], app.app_directory, package3.get_binary_name())

    try:
        appcenter.update()

        app.install()

        if ucr.get('server/role') == 'domaincontroller_master':
            if not package_installed(package_name1):
                raise UCSTest_AppCenter_PackageIsNotInstalled()
            if not package_installed(package_name2):
                raise UCSTest_AppCenter_PackageIsNotInstalled()
            if package_installed(package_name3):
                raise UCSTest_AppCenter_PackageIsInstalled()
        elif ucr.get('server/role') == 'domaincontroller_backup':
            if not package_installed(package_name1):
                raise UCSTest_AppCenter_PackageIsNotInstalled()
            if package_installed(package_name2):
                raise UCSTest_AppCenter_PackageIsInstalled()
            if package_installed(package_name3):
                raise UCSTest_AppCenter_PackageIsInstalled()
        elif ucr.get('server/role') == 'domaincontroller_slave':
            if package_installed(package_name1):
                raise UCSTest_AppCenter_PackageIsInstalled()
            if not package_installed(package_name2):
                raise UCSTest_AppCenter_PackageIsNotInstalled()
            if package_installed(package_name3):
                raise UCSTest_AppCenter_PackageIsInstalled()
        elif ucr.get('server/role') == 'memberserver':
            if package_installed(package_name1):
                raise UCSTest_AppCenter_PackageIsInstalled()
            if package_installed(package_name2):
                raise UCSTest_AppCenter_PackageIsInstalled()
            if not package_installed(package_name3):
                raise UCSTest_AppCenter_PackageIsNotInstalled()

    finally:
        app.uninstall()
        app.remove()
