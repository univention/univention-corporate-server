#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Test update-certificates
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import os
import subprocess

import pytest

from dockertest import App, Appcenter


def cleanup(app: App, check_dir: Path, cert_files: list[str]) -> None:
    if check_dir.is_dir():
        check_dir.rmdir()
    if app.installed:
        for i in cert_files:
            with suppress(FileNotFoundError):
                app.file(i).unlink()  # Py3.8+ missing_ok=True


def verify_certs(app: App, check_dir: Path, cert_files: list[str]) -> None:
    assert check_dir.is_dir()
    for i in cert_files:
        assert app.file(i).is_file()


@pytest.mark.exposure('dangerous')
def test_app_update_certificates(appcenter: Appcenter, app_name: str) -> None:
    check_dir = f'/tmp/update-certificates-test-{app_name}'
    setup = '#!/bin/sh'
    store_data = '#!/bin/sh'
    update_certificates = f'''#!/bin/sh
set -x
mkdir "{check_dir}"
exit 0
'''

    app = App(name=app_name, version='1', build_package=False, call_join_scripts=False)
    app.check_dir = check_dir
    check_files = []
    check_files.append('etc/univention/ssl/docker-host-certificate/cert.perm')
    check_files.append('etc/univention/ssl/docker-host-certificate/private.key')
    check_files.append('usr/local/share/ca-certificates/ucs.crt')
    check_files.append('etc/univention/ssl/%(hostname)s.%(domainname)s/cert.perm' % app.ucr)
    check_files.append('etc/univention/ssl/%(hostname)s.%(domainname)s/private.key' % app.ucr)

    app.cert_files = check_files

    try:
        cleanup(app)
        app.set_ini_parameter(
            DockerImage='docker-test.software-univention.de/alpine:3.6',
            DockerScriptUpdateCertificates='/certs',
            DockerScriptSetup='/setup',
            DockerScriptStoreData='/store_data',
            DockerScriptInit='/sbin/init',
        )
        app.add_script(update_certificates=update_certificates)
        app.add_script(setup=setup)
        app.add_script(store_data=store_data)
        app.add_to_local_appcenter()
        appcenter.update()
        app.install()
        app.verify(joined=False)
        verify_certs(app)
        cleanup(app)
        subprocess.check_output(['univention-app', 'update-certificates', app_name], text=True)
        verify_certs(app)
        cleanup(app)
        subprocess.check_output(['univention-app', 'update-certificates'], text=True)
        verify_certs(app)
        cleanup(app)

        app = App(name=app_name, version='2', build_package=False, call_join_scripts=False)
        app.check_dir = check_dir
        app.cert_files = check_files
        app.set_ini_parameter(
            DockerImage='docker-test.software-univention.de/alpine:3.7',
            DockerScriptSetup='/setup',
            DockerScriptUpdateCertificates='/root/certs',
            DockerScriptStoreData='/store_data',
            DockerScriptInit='/sbin/init',
        )
        app.add_script(update_certificates=update_certificates)
        app.add_script(setup=setup)
        app.add_script(store_data=store_data)
        app.add_to_local_appcenter()
        appcenter.update()
        app.upgrade()
        app.verify(joined=False)
        verify_certs(app)
    finally:
        app.uninstall()
        app.remove()
