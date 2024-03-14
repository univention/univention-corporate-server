#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Test repository/app_center/installed with Docker/NonDocker Apps
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from univention.config_registry import ConfigRegistry

from dockertest import App, get_app_name, get_app_version, tiny_app

import pytest


@pytest.mark.exposure('dangerous')
def test_docker(appcenter):
    app_docker1 = app_docker2 = app_nondocker = None
    try:
        app_docker1 = tiny_app(get_app_name(), get_app_version())
        app_docker1.set_ini_parameter(Code='D1')
        app_docker1.add_to_local_appcenter()

        app_docker2 = tiny_app(get_app_name(), get_app_version())
        app_docker2.set_ini_parameter(Code='D2')
        app_docker2.add_to_local_appcenter()

        app_nondocker = App(name=get_app_name(), version=get_app_version(),
                            build_package=True)
        app_nondocker.set_ini_parameter(Code='ND')
        app_nondocker.add_to_local_appcenter()

        appcenter.update()

        ucr = ConfigRegistry()
        ucr.load()
        codes_old = ucr.get('repository/app_center/installed').split('-')
        assert 'D1' not in codes_old, 'Wrong old Codes: %r' % codes_old
        assert 'D2' not in codes_old, 'Wrong old Codes: %r' % codes_old
        assert 'ND' not in codes_old, 'Wrong old Codes: %r' % codes_old

        app_docker1.install()
        app_nondocker.install()

        ucr.load()
        codes_new = ucr.get('repository/app_center/installed').split('-')

        assert 'D1' in codes_new, 'Wrong new Codes: %r' % codes_new
        assert 'D2' not in codes_new, 'Wrong new Codes: %r' % codes_new
        assert 'ND' in codes_new, 'Wrong new Codes: %r' % codes_new

    finally:
        if app_docker1 is not None:
            app_docker1.uninstall()
            app_docker1.remove()
        if app_docker2 is not None:
            app_docker2.uninstall()
            app_docker2.remove()
        if app_nondocker is not None:
            app_nondocker.uninstall()
            app_nondocker.remove()
