# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import re
import subprocess
import tempfile
import time
from collections.abc import Callable, Iterator

import pytest

import univention.lib.umc
from univention.appcenter.actions import get_action
from univention.appcenter.app_cache import Apps
from univention.testing import selenium as _sel, strings, ucr as _ucr, udm as _udm, umc, utils


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
    return utils.get_ldap_connection(admin_uldap=True)


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


@pytest.fixture(scope='session')
def test_diagnostic_module() -> Callable[[str, bool], []]:
    """
    Runs the given diagnostic module and fails via assert if an unexpected exitcode is returned.
    It also kills all running diagnostic modules in advance.
    No matter if this was expected, it also fails if the term "Traceback" is found in the output
    of the diagnostic module.
    """
    DIAGNOSTIC_RE = re.compile(
        r'(?:^ran ([\d\w]*) successfully.$)|(?:#+ Start ([\d\w]*) #+)\n(.*)\n(?:#+ End (?:\2) #+)',
        flags=re.M | re.S,
    )

    def _test_diagnostic_module(module: str, success_expected: bool = False):
        account = utils.UCSTestDomainAdminCredentials()
        with tempfile.NamedTemporaryFile() as fd:
            fd.write(account.bindpw.encode('UTF-8'))
            fd.flush()
            # kill existing diagnostic modules to not clog up memory
            subprocess.call(["pkill", "-f", "/usr/sbin/univention-management-console-module -m diagnostic"])
            args = ['/usr/bin/univention-run-diagnostic-checks', '--username', account.username, '--bindpwdfile', fd.name, "--test", module]
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = proc.communicate()
        if stdout:
            print("--- stdout of diagnostic module ---")
            print(stdout.decode('UTF-8', 'replace'))
            print("---")
        if stderr:
            print("--- stderr of diagnostic module ---")
            print(stderr.decode('UTF-8', 'replace'))
            print("---")
        params = {
            success or failed: {
                'success': bool(success and not failed),
                'error_message': error_message,
            } for success, failed, error_message in DIAGNOSTIC_RE.findall(stdout.decode('UTF-8', 'replace'))
        }
        for item in params.values():
            # print(f'\n-----------------\n{item["error_message"]}\n------------------')
            assert "Traceback" not in item["error_message"], "Unexpectedly a traceback happened in diagnostic module"
            assert item["success"] == success_expected, f'Diagnostic module unexpectedly {"failed" if success_expected else "passed"}'

    return _test_diagnostic_module
