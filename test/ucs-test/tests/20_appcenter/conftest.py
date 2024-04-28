import logging
from typing import Iterator

import pytest

import appcentertest as app_test


@pytest.fixture(scope="module", autouse=True)
def appc_setup() -> Iterator[None]:
    """Local test AppCenter."""
    app_test.app_logger.log_to_stream()
    app_test.app_logger.get_base_logger().setLevel(logging.WARNING)
    with app_test.local_appcenter():
        yield


@pytest.fixture()
def app_center(appc_setup) -> app_test.AppCenterOperations:
    """Local test AppCenter operaions."""
    return app_test.AppCenterOperations()


@pytest.fixture()
def application(request) -> str:
    """Retrun a per-test application name."""
    return request.node.name.replace("_", "-")


@pytest.fixture()
def package(app_center, application) -> app_test.AppPackage:
    """Per test local test AppCenter package."""
    package = app_test.AppPackage.with_package(name=application)
    package.build_and_publish()
    package.remove_tempdir()
    return package
