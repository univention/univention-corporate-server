#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv --tb=native
## desc: Test security related HTTP headers are set
## exposure: dangerous
## packages: [univention-management-console-server]

import copy
import subprocess
import time
from collections import defaultdict
from http.client import HTTPConnection

import pytest

from univention.lib.umc import ServiceUnavailable, Unauthorized
from univention.testing import network, utils
from univention.testing.ucr import UCSTestConfigRegistry


class TestSecurityHeaders:

    @pytest.mark.parametrize('path', [
        'login/',
        'login/index.html',
        'login/blank.html',
        'login/login.html',
    ])
    def test_login_site(self, path, Client, ucr):
        client = Client()
        response = client.request('GET', path)
        assert response.get_header("X-Frame-Options") is None  # changed from: == "SAMEORIGIN"
        sso = '%(ucs/server/sso/uri)s/' % defaultdict(lambda: '', ucr)
        assert response.get_header("Content-Security-Policy") == "default-src 'self' 'unsafe-inline' 'unsafe-eval' %s  https://www.piwik.univention.de/ ; frame-ancestors 'self';" % sso

        assert response.get_header("X-Permitted-Cross-Domain-Policies") == "master-only"
        assert response.get_header("X-XSS-Protection") == "1; mode=block"
        assert response.get_header("X-Content-Type-Options") == "nosniff"

    @pytest.mark.parametrize('path', [
        '/languages.json',
        '/portal/',
        '/management/',
    ])
    def test_univention(self, path, ucr, Client):
        client = Client()
        response = client.request('GET', path)
        assert response.get_header("X-Permitted-Cross-Domain-Policies") == "master-only"
        assert response.get_header("X-XSS-Protection") == "1; mode=block"
        assert response.get_header("X-Content-Type-Options") == "nosniff"
        assert response.get_header("X-Frame-Options") is None  # changed from: == "DENY"
        if path == '/languages.json':
            assert response.get_header("Content-Security-Policy") == "frame-ancestors 'none';"
        else:
            sso = '%(ucs/server/sso/uri)s/' % defaultdict(lambda: '', ucr)
            if 'portal' in path:
                sso = '%(ucs/server/sso/uri)s/' % defaultdict(lambda: '', ucr)
            sso = sso.replace('http:///', '').replace('https:///', '').strip()
            expected = "frame-ancestors 'self' %s;" % sso
            assert expected in response.get_header("Content-Security-Policy")

    @pytest.mark.xfail(reason='Bug #52940')
    def test_ip_bound_to_session(self, Client, ucr, restart_umc_server):
        client = Client('%(hostname)s.%(domainname)s' % ucr)
        client.ConnectionType = HTTPConnection  # workaround TLS hostname mismatch

        account = utils.UCSTestDomainAdminCredentials()
        client.authenticate(account.username, account.bindpw)
        # make sure any UMC module is present (the session is not dropped to anonymous)
        assert any(x['id'] == 'top' for x in client.umc_get('modules').data['modules'])

        # change the external IP address
        with network.NetworkRedirector() as nethelper:
            nethelper.add_loop('1.2.3.4', '4.3.2.1')
            c = Client('1.2.3.4')
            c.ConnectionType = HTTPConnection  # workaround TLS hostname mismatch
            c.cookies = copy.deepcopy(client.cookies)
            with pytest.raises(Unauthorized) as exc:
                c.umc_get('modules')
            assert 'The current session is not valid with your IP address for security reasons.' in str(exc.value)

            # check if the session is still bound after the internal connection to the UMC-Server was lost
            restart_umc_server()
            c.cookies = copy.deepcopy(client.cookies)
            with pytest.raises(Unauthorized) as exc:
                c.umc_get('modules')
            assert 'The current session is not valid with your IP address for security reasons.' in str(exc.value)

        # make sure any UMC module is present (the session is not dropped to anonymous)
        assert any(x['id'] == 'top' for x in client.umc_get('modules').data['modules'])

        # make sure the same rules apply for localhost
        c2 = Client('localhost')
        c2.ConnectionType = HTTPConnection  # workaround TLS hostname mismatch
        c2.cookies = copy.deepcopy(client.cookies)
        assert any(x['id'] == 'top' for x in c2.umc_get('modules').data['modules'])

        # check if the session is still bound after the internal connection to the UMC-Server was lost
        restart_umc_server()
        c2.cookies = copy.deepcopy(client.cookies)
        assert any(x['id'] == 'top' for x in c2.umc_get('modules').data['modules'])

        # make sure any UMC module is present (the session is not dropped to anonymous)
        assert any(x['id'] == 'top' for x in client.umc_get('modules').data['modules'])

    @pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup')
    def test_header_smuggling(self, umc_allow_ucstest, umc_client):
        headers = {
            'x-user-dn': '"cn=admin"',
            'x-umc-authtype': 'AUTH',
            'x-umc-roles': '["guardian::super-admin"]',
            'x-umc-federated-account': 'true',
            'x-umc-method': 'METHOD',
            'x-umc-command': 'MYCMD',
            'x-umc-request-id': 'ID',
        }
        result = umc_client.umc_command('ucstest/all_headers', headers=dict(FOo='Bar', **headers)).result
        assert result['Foo'] == 'Bar'
        result_ci = {k.lower(): v for k, v in result.items()}
        for key, value in headers.items():
            assert result_ci.get(key.lower()) != value


REFERER_PATH_ERROR = 'The "Referer" HTTP header must start with "/univention/".'
REFERER_HOST_ERROR = 'The host of the "Referer" HTTP header does not match the requested host.'
REFERER_HOST_WARNING = 'HTTP Referer host does not match'
UMC_UCR_MODULE_LOG = '/var/log/univention/management-console-module-ucr.log'


def _restart_umc_server():
    subprocess.call(['deb-systemd-invoke', 'restart', 'univention-management-console-server.service'])
    time.sleep(2)


@pytest.fixture(scope='class')
def referer_check_host(request):
    """Set `umc/http/referer/check-host` to the `CHECK_HOST` attribute of the test class"""
    with UCSTestConfigRegistry() as ucr:
        ucr.handler_set([f'umc/http/referer/check-host={request.cls.CHECK_HOST}'])
        _restart_umc_server()
        try:
            yield
        finally:
            ucr.revert_to_original_registry()
            _restart_umc_server()


@pytest.mark.usefixtures('referer_check_host')
class TestRefererProtection:
    """Test Referer protection of UMC modules"""

    CHECK_HOST = 'true'

    @pytest.fixture
    def client(self, Client):
        return Client.get_test_connection(language='en-US')

    @pytest.fixture
    def allowed_hosts(self, ucr, restart_umc_server):
        ucr.handler_set(['umc/http/referer/allowed-hosts=my-proxy.example.com, other-proxy.example.com:8443'])
        restart_umc_server()
        try:
            yield
        finally:
            ucr.revert_to_original_registry()
            restart_umc_server()

    def ucr_get(self, client, referer):
        return client.umc_command('ucr/get', ['hostname'], headers={'Referer': referer})

    @pytest.mark.parametrize('referer', [
        'https://{fqdn}/univention/management/',
        'https://{FQDN}/univention/management/',
    ])
    def test_same_host(self, client, referer):
        referer = referer.format(fqdn=client.hostname, FQDN=client.hostname.upper())
        assert self.ucr_get(client, referer).status == 200

    @pytest.mark.parametrize('referer', [
        'https://evil.example/univention/anything',
        'https://{fqdn}.evil.example/univention/management/',
        'https://{fqdn}@evil.example/univention/management/',
        'https://my-proxy.example.com/univention/management/',
    ])
    def test_foreign_host(self, client, referer):
        referer = referer.format(fqdn=client.hostname)
        with pytest.raises(ServiceUnavailable) as exc:
            self.ucr_get(client, referer)
        assert REFERER_HOST_ERROR in exc.value.message

    @pytest.mark.parametrize('referer', [
        'https://{fqdn}/other/',
        'https://evil.example/other/',
    ])
    def test_foreign_path(self, client, referer):
        referer = referer.format(fqdn=client.hostname)
        with pytest.raises(ServiceUnavailable) as exc:
            self.ucr_get(client, referer)
        assert exc.value.message == REFERER_PATH_ERROR

    @pytest.mark.parametrize('referer,allowed', [
        ('https://{fqdn}/univention/management/', True),
        ('https://my-proxy.example.com/univention/management/', True),
        ('https://MY-PROXY.example.com:8443/univention/management/', True),
        ('https://other-proxy.example.com:8443/univention/management/', True),
        ('https://other-proxy.example.com/univention/management/', False),
        ('https://my-proxy.example.com.evil.example/univention/management/', False),
        ('https://evil.example/univention/anything', False),
    ])
    def test_allowed_hosts(self, allowed_hosts, client, referer, allowed):
        """Reverse proxies which rewrite the Host header can be allowed via UCR"""
        referer = referer.format(fqdn=client.hostname)
        if allowed:
            assert self.ucr_get(client, referer).status == 200
            return
        with pytest.raises(ServiceUnavailable) as exc:
            self.ucr_get(client, referer)
        assert REFERER_HOST_ERROR in exc.value.message


@pytest.mark.usefixtures('referer_check_host')
class TestRefererProtectionNotEnforced(TestRefererProtection):
    """Without `umc/http/referer/check-host` a non-matching Referer host is only logged (default on updated systems)"""

    CHECK_HOST = 'false'

    @pytest.mark.parametrize('referer', [
        'https://evil.example/univention/anything',
        'https://my-proxy.example.com/univention/management/',
    ])
    def test_foreign_host(self, client, referer):
        with open(UMC_UCR_MODULE_LOG) as fd:
            fd.seek(0, 2)
            assert self.ucr_get(client, referer).status == 200
            log = fd.read()
        assert REFERER_HOST_WARNING in log

    test_allowed_hosts = None
