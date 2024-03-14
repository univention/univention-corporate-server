#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Test update-certificates
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import os
import subprocess

from dockertest import App

import pytest

def cleanup(app):
    if os.path.isdir(app.check_dir):
        os.rmdir(app.check_dir)
    if app.installed is True:
        for i in app.cert_files:
            if os.path.isfile(app.file(i)):
                os.remove(app.file(i))


def verify_certs(app):
    print(f'looking for {app.check_dir}')
    assert os.path.isdir(app.check_dir) is True
    print(f'{app.check_dir} exists')
    for i in app.cert_files:
        print(f'looking for {i} in container')
        assert os.path.isfile(app.file(i)) is True
        print(f'{i} exists')


@pytest.mark.exposure('dangerous')
def test_app_update_certificates(appcenter, app_name):
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

        app = App(name=name, version='2', build_package=False, call_join_scripts=False)
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
