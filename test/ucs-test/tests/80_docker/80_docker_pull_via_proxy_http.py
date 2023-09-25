#!/usr/share/ucs-test/runner python3
## desc: Check App installation through proxy
## tags: [docker]
## exposure: dangerous
## packages:
##   - univention-docker
##   - univention-squid

from univention.config_registry import handler_set
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.utils import fail

from dockertest import (
    docker_image_is_present, docker_login, pull_docker_image, remove_docker_image, restart_docker, tiny_app,
)


class TestCase:

    def __init__(self):
        self.ucr = UCSTestConfigRegistry()
        self.ucr.load()

        self.imgname = tiny_app().ini['DockerImage']

        if not self.ucr.get('proxy/http'):
            handler_set(['proxy/http=http://127.0.0.1:3128'])
            restart_docker()
            self.ucr_changed = True
        else:
            self.ucr_changed = False

    def run(self):
        if docker_image_is_present(self.imgname):
            remove_docker_image(self.imgname)

        docker_login()
        pull_docker_image(self.imgname)
        if not docker_image_is_present(self.imgname):
            fail('The container could not be downloaded.')

    def cleanup(self):
        remove_docker_image(self.imgname)
        if self.ucr_changed:
            self.ucr.revert_to_original_registry()
            restart_docker()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            print(f'Cleanup after exception: {exc_type} {exc_value}')
        self.cleanup()


if __name__ == '__main__':
    with TestCase() as tc:
        tc.run()
