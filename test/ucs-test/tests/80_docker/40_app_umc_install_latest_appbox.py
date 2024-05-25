#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Create and install a simple app with latest appbox image
## tags: [docker, SKIP]
## bugs: [51847]
## exposure: dangerous
## packages:
##   - docker.io

import json

import pytest
import requests

from dockertest import App, Appcenter, UMCFailure, get_app_name


URL = 'https://docker.software-univention.de/v2/ucs-appbox-amd64/tags/list'
USERNAME = 'ucs'
PASSWORD = 'readonly'


@pytest.fixture(scope="module")
def data():
    resp = requests.get(URL, auth=(USERNAME, PASSWORD)).content
    return json.loads(resp)


@pytest.fixture(scope="module")
def image(data) -> str:
    return 'docker.software-univention.de/ucs-appbox-amd64:' + max(data['tags'])


@pytest.mark.skip()
@pytest.mark.exposure('dangerous')
def test_app_umc_install_setup(appcenter: Appcenter, data, image: str) -> None:  # get latest app box image
    # installation should fail if setup fails
    app_name = get_app_name()
    app = App(name=app_name, version='1.9', container_version=max(data['tags'])[:3], build_package=False)
    app.set_ini_parameter(DockerImage=image, DockerScriptSetup='/usr/sbin/setup')
    app.add_script(setup='''#!/bin/bash
echo "This message goes to stdout"
echo "This message goes to stderr" >&2
. /usr/share/univention-docker-container-mode/lib.sh
error_msg "This message goes to ERROR_FILE"
exit 1
''')
    app.add_to_local_appcenter()
    appcenter.update()
    try:
        try:
            app.install_via_umc()
        except UMCFailure as exc:
            _progress, errors = exc.args
            print(errors)
            assert {'message': 'This message goes to ERROR_FILE\n', 'level': 'CRITICAL'} in errors
        else:
            raise AssertionError('Should not have been installed successfully!')
    finally:
        app.uninstall()
        app.remove()


@pytest.mark.skip()
@pytest.mark.exposure('dangerous')
def test_app_umc_install(appcenter: Appcenter, data, image: str) -> None:
    # installation should succeed if setup is fine
    app_name = get_app_name()
    app = App(name=app_name, version='1.9', container_version=max(data['tags'])[:3], build_package=False)
    app.set_ini_parameter(DockerImage=image, DockerScriptSetup='/usr/sbin/setup')
    app.add_script(setup='''#!/bin/bash
echo "This message goes to stdout"
echo "This message goes to stderr but script returns 0" >&2
exit 0
''')
    app.add_to_local_appcenter()
    try:
        appcenter.update()
        app.install_via_umc()
    finally:
        app.uninstall()
        app.remove()


@pytest.mark.skip()
@pytest.mark.exposure('dangerous')
def test_app_umc_install_latest_appbox(appcenter: Appcenter, data, image: str) -> None:
    # test appbox app installation
    app_name = get_app_name()
    app_name = 'testapp'
    app = App(name=app_name, version='1.9', container_version=max(data['tags'])[:3], build_package=False)
    app.set_ini_parameter(
        DockerImage=image,
        DefaultPackages='mc',
    )
    app.add_to_local_appcenter()
    try:
        appcenter.update()
        app.install_via_umc()
        app.verify()
    finally:
        app.uninstall()
        app.remove()
