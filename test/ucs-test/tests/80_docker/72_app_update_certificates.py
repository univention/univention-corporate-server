#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Test update-certificates
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

from __future__ import annotations

import subprocess
from contextlib import suppress
from pathlib import Path
from shlex import quote

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
def test_app_update_certificates(appcenter: Appcenter, app_name: str, tmp_path: Path) -> None:
    check_dir = tmp_path / "called"
    setup = '#!/bin/sh'
    store_data = '#!/bin/sh'
    update_certificates = f'''#!/bin/sh
set -x
mkdir {quote(check_dir.as_posix())}
exit 0
'''

    app = App(name=app_name, version='1', build_package=False, call_join_scripts=False)
    check_files = [
        'etc/univention/ssl/docker-host-certificate/cert.perm',
        'etc/univention/ssl/docker-host-certificate/private.key',
        'usr/local/share/ca-certificates/ucs.crt',
        'etc/univention/ssl/%(hostname)s.%(domainname)s/cert.perm' % app.ucr,
        'etc/univention/ssl/%(hostname)s.%(domainname)s/private.key' % app.ucr,
    ]

    try:
        cleanup(app, check_dir, check_files)
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
        verify_certs(app, check_dir, check_files)
        cleanup(app, check_dir, check_files)

        subprocess.check_output(['univention-app', 'update-certificates', app_name], text=True)
        verify_certs(app, check_dir, check_files)
        cleanup(app, check_dir, check_files)

        subprocess.check_output(['univention-app', 'update-certificates'], text=True)
        verify_certs(app, check_dir, check_files)
        cleanup(app, check_dir, check_files)

        app = App(name=app_name, version='2', build_package=False, call_join_scripts=False)
        app.set_ini_parameter(
            DockerImage='docker-test.software-univention.de/alpine:3.7',
            DockerScriptUpdateCertificates='/root/certs',
            DockerScriptSetup='/setup',
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
        verify_certs(app, check_dir, check_files)
    finally:
        app.uninstall()
        app.remove()
