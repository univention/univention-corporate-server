import pytest

from dockertest import Appcenter


@pytest.fixture()
def appcenter():
    with Appcenter() as appcenter:
        yield appcenter
