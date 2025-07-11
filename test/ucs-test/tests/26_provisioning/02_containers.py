#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Check the deployed containers of the Provisioning Stack
## tags: [provisioning]
## exposure: safe
## packages:
##   - python3-univention-provisioning-stack-listener

import docker
import pytest
from univention.testing import utils

STATUS_OK = "healthy"

@pytest.fixture
def check_container_health(container_names):

    client = docker.from_env()
    results = {}

    for name in container_names:

        try:

            container = client.containers.get(name)
            status = container.status
            health = container.attrs.get("State", {}).get("Health", {}).get("Status", "")

            if status == "running" and health in ("healthy", ""):
                results[name] = STATUS_OK
            else:
                results[name] = f"unhealthy ({status}, {health})"

        except docker.errors.NotFound:
            results[name] = "is missing"
        except Exception as e:
            results[name] = f"unable to communicate with docker: {e}"

    return results


def check_provisioning_container():

    containers = [
        "nubus-provisioning-udm-transformer",
        "nubus-provisioning-prefill",
        "nubus-provisioning-dispatcher",
        "nubus-provisioning-api",
        "udm-proxy",
        "compose_nats_1"
    ]

    health_status = check_container_health(containers)
    for name, status in health_status.items():
        if status != STATUS_OK:
            utils.fail(f"Provisioning container {name} {status}")