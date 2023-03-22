#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Write docker logs into logfiles"
## exposure: safe
## tags: [apptest, keycloak]

import docker
import pytest


@pytest.mark.exposure('safe')
def test_write_docker_logfiles(ucr):
    cli = docker.DockerClient()
    hostname = ucr.get("hostname")
    for container in cli.containers.list():
        logname = f"docker_logs_{hostname}_{container.name}_{container.short_id}.log"
        with open(f"/root/{logname}", "wb+") as logfile:
            print(f"Writing logfile {logname} for container image {container.image}")
            logfile.write(container.logs())
