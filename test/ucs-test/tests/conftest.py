# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import subprocess
import time
from typing import Callable, Iterator, Type

import pytest

import univention.lib.umc
from univention.testing import selenium as _sel, strings, ucr as _ucr, udm as _udm, umc, utils


pytest_plugins = ["univention.testing.conftest"]


@pytest.fixture()
def ucr() -> Iterator[_ucr.UCSTestConfigRegistry]:
    """Per `function` auto-reverting UCR instance."""
    with _ucr.UCSTestConfigRegistry() as ucr:
        yield ucr


@pytest.fixture(scope='session')
def ucr_session() -> Iterator[_ucr.UCSTestConfigRegistry]:
    """Per `session` auto-reverting UCR instance."""
    with _ucr.UCSTestConfigRegistry() as ucr:
        yield ucr


@pytest.fixture(scope='session')
def restart_s4connector_if_present() -> Callable[[], None]:
    """Function to restart S4 connector if present."""
    def restart():
        if utils.s4connector_present():
            print('restarting s4 connector')
            utils.restart_s4connector()
    return restart


@pytest.fixture(scope='session')
def restart_umc_server() -> Callable[[], None]:
    """Function to restart UMC server."""
    def _restart_umc_server():
        subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service'])
        time.sleep(2)
    return _restart_umc_server


@pytest.fixture(scope='session')
def server_role(ucr_session) -> str:
    """UCS server role string from UCR."""
    return ucr_session.get('server/role')


@pytest.fixture(scope='session')
def ldap_base(ucr_session) -> str:
    """LDAP base DN string from UCR."""
    return ucr_session.get('ldap/base')


@pytest.fixture(scope='session')
def ldap_master(ucr_session) -> str:
    """LDAP primary name from UCR."""
    return ucr_session.get('ldap/master')


@pytest.fixture()
def udm() -> Iterator[_udm.UCSTestUDM]:
    """Auto-reverting UDM wrapper."""
    with _udm.UCSTestUDM() as udm:
        yield udm


@pytest.fixture(scope='session')
def udm_session() -> Iterator[_udm.UCSTestUDM]:
    """Auto-reverting UDM wrapper."""
    with _udm.UCSTestUDM() as udm:
        yield udm


@pytest.fixture()
def selenium() -> Iterator[_sel.UMCSeleniumTest]:
    """Browser based testing for UMC using Selenium."""
    with _sel.UMCSeleniumTest() as s:
        yield s


@pytest.fixture(scope='session')
def Client() -> Type[umc.Client]:
    """Session scoped client factory to access UMC."""
    return umc.Client


@pytest.fixture(scope="module")
def lo() -> univention.admin.uldap.access:
    """Module scoped LDAP connection."""
    return utils.get_ldap_connection()


@pytest.fixture(scope='session')
def verify_ldap_object() -> Callable[..., None]:
    """Function to verify LDAP entries."""
    return utils.verify_ldap_object


@pytest.fixture(scope='session')
def verify_udm_object() -> Callable[..., None]:
    """Function to verify UDM objects."""
    return _udm.verify_udm_object


@pytest.fixture(scope='session')
def random_string() -> Callable[..., str]:
    """Function to generate random string."""
    return strings.random_string


@pytest.fixture(scope='session')
def random_name() -> Callable[..., str]:
    """Function to generate random name."""
    return strings.random_name


@pytest.fixture(scope='session')
def random_username() -> Callable[..., str]:
    """Function to generate random user name."""
    return strings.random_username


@pytest.fixture(scope='session')
def wait_for_replication() -> Callable[..., None]:
    """Function to wait for replication to finish."""
    return utils.wait_for_replication


@pytest.fixture(scope='session')
def account() -> utils.UCSTestDomainAdminCredentials:
    return utils.UCSTestDomainAdminCredentials()
