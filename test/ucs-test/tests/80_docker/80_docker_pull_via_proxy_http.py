#!/usr/share/ucs-test/runner pytest-3 -s -vv --tb=native
## desc: Check App installation through proxy
## tags: [docker]
## exposure: dangerous
## packages:
##   - univention-docker
##   - univention-squid

import pytest

from univention.config_registry import handler_set
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.utils import fail

from dockertest import (
    docker_image_is_present, docker_login, pull_docker_image, remove_docker_image, restart_docker, tiny_app,
)


@pytest.mark.exposure('dangerous')
def test_docker_pull_via_proxy_http():
    ucr = UCSTestConfigRegistry()
    ucr.load()

    imgname = tiny_app().ini['DockerImage']

    if not ucr.get('proxy/http'):
        handler_set(['proxy/http=http://127.0.0.1:3128'])
        restart_docker()
        ucr_changed = True
    else:
        ucr_changed = False

    try:
        if docker_image_is_present(imgname):
            remove_docker_image(imgname)

        docker_login()
        pull_docker_image(imgname)

        if not docker_image_is_present(imgname):
            fail('The container could not be downloaded.')
    finally:
        remove_docker_image(imgname)
        if ucr_changed:
            ucr.revert_to_original_registry()
            restart_docker()
