import subprocess

import pytest

from univention.testing.umc import Client


@pytest.fixture(scope='session')
def umc_client():
    return Client.get_test_connection(language='en-US')


@pytest.fixture(scope='session')
def umc_allow_ucstest():
    from univention.management.console.modules.ucstest import joinscript, unjoinscript
    joinscript()
    subprocess.check_call(["systemctl", "restart", "univention-management-console-server"])
    try:
        yield
    finally:
        subprocess.call(['systemctl', 'restart', 'univention-management-console-server', 'apache2'])
        unjoinscript()
