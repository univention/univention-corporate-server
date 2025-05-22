# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import subprocess
import time
from typing import TYPE_CHECKING

import pytest

from univention.appcenter.actions import get_action
from univention.appcenter.app_cache import Apps
from univention.testing import selenium as _sel, strings, ucr as _ucr, udm as _udm, umc, utils


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    import univention.lib.umc


pytest_plugins = ["univention.testing.conftest"]


@pytest.fixture
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


@pytest.fixture(scope="session")
def udm_rest_base_url(ucr_session):
    return 'https://%(hostname)s.%(domainname)s/univention/udm/' % ucr_session


@pytest.fixture(scope="session")
def udm_rest_client(ucr_session, account, udm_rest_base_url):
    from univention.admin.rest.client import UDM as UDM_REST

    udm_rest = UDM_REST(
        uri=udm_rest_base_url,
        username=account.username,
        password=account.bindpw,
    )
    assert udm_rest.get_ldap_base()
    return udm_rest


@pytest.fixture
def udm() -> Iterator[_udm.UCSTestUDM]:
    """Auto-reverting UDM wrapper."""
    with _udm.UCSTestUDM() as udm:
        yield udm


@pytest.fixture(scope='session')
def udm_session() -> Iterator[_udm.UCSTestUDM]:
    """Auto-reverting UDM wrapper."""
    with _udm.UCSTestUDM() as udm:
        yield udm


@pytest.fixture
def selenium() -> Iterator[_sel.UMCSeleniumTest]:
    """Browser based testing for UMC using Selenium."""
    with _sel.UMCSeleniumTest() as s:
        yield s


@pytest.fixture(scope='session')
def Client() -> type[umc.Client]:
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


@pytest.fixture
def change_app_setting():
    """Change settings of an app and revert"""
    data = {'app': None, 'configure': None, 'changes': {}}

    def _func(app_id: str, changes: dict, revert: bool = True) -> None:
        apps_cache = Apps()
        app = apps_cache.find(app_id, latest=True)
        data['app'] = app
        configure = get_action('configure')
        data['configure'] = configure
        settings = configure.list_config(app)
        known_settings = {x.get('name'): x.get('value') for x in settings}
        for change in changes:
            if change in known_settings:
                if revert:
                    data['changes'][change] = known_settings[change]
            else:
                raise Exception(f'Unknown setting: {change}')
        configure.call(app=app, set_vars=changes)

    yield _func

    if data['changes']:
        data['configure'].call(app=data['app'], set_vars=data['changes'])
