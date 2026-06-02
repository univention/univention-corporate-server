#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Write docker logs into logfiles"
## exposure: safe
## tags: [apptest, keycloak]

import os
import subprocess

import docker
import pytest
from docker.errors import DockerException


def run(cmd):
    return subprocess.run(cmd, text=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.strip()


@pytest.mark.exposure('safe')
def test_write_docker_logfiles(ucr):
    try:
        cli = docker.DockerClient.from_env()
        cli.ping()
    except DockerException as exc:
        socket = os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock')
        pytest.fail(
            'Cannot connect to Docker daemon.\n'
            f'DOCKER_HOST: {socket}\n'
            f'Error: {exc!r}\n\n'
            'Diagnostics:\n'
            f'$ systemctl is-active docker\n{run(["systemctl", "is-active", "docker"])}\n\n'
            f'$ systemctl status docker --no-pager\n{run(["systemctl", "status", "docker", "--no-pager"])}\n\n'
            f'$ ls -l /var/run/docker.sock\n{run(["ls", "-l", "/var/run/docker.sock"])}\n',
            pytrace=False,
        )

    hostname = ucr.get('hostname')
    for container in cli.containers.list():
        logname = f'docker_logs_{hostname}_{container.name}_{container.short_id}.log'
        print(f'Writing logfile {logname} for container image {container.image}')
        with open(f'/root/{logname}', 'wb+') as logfile:
            logfile.write(container.logs())
