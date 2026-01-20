#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test the root_path configuration for UDM REST API
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-rest

import contextlib
import os
import subprocess
import time

import pytest
import requests

from univention.admin.rest.module import Application
from univention.config_registry import ucr


SYSTEMD_SERVICE = 'univention-directory-manager-rest'
SYSTEMD_OVERRIDE_DIR = f'/etc/systemd/system/{SYSTEMD_SERVICE}.service.d'
SYSTEMD_OVERRIDE_FILE = f'{SYSTEMD_OVERRIDE_DIR}/test-root-path.conf'


@contextlib.contextmanager
def service_with_root_path(root_path: str):
    """
    Context manager that temporarily configures the UDM REST service
    with a specific root_path environment variable.

    Restores the original configuration on exit.
    """
    os.makedirs(SYSTEMD_OVERRIDE_DIR, exist_ok=True)

    had_override = os.path.exists(SYSTEMD_OVERRIDE_FILE)
    original_content = None
    if had_override:
        with open(SYSTEMD_OVERRIDE_FILE) as f:
            original_content = f.read()

    check_path = f'{root_path}/udm/' if root_path else '/udm/'

    try:
        with open(SYSTEMD_OVERRIDE_FILE, 'w') as f:
            f.write(f'[Service]\nEnvironment="UDM_REST_API_ROOT_PATH={root_path}"\n')

        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'restart', SYSTEMD_SERVICE], check=True)

        _wait_for_service_ready(path=check_path)

        yield

    finally:
        if had_override and original_content is not None:
            with open(SYSTEMD_OVERRIDE_FILE, 'w') as f:
                f.write(original_content)
        elif os.path.exists(SYSTEMD_OVERRIDE_FILE):
            os.remove(SYSTEMD_OVERRIDE_FILE)

        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'restart', SYSTEMD_SERVICE], check=True)
        _wait_for_service_ready(path='/udm/')


def _wait_for_service_ready(path: str = '/udm/', timeout: int = 30):
    """Wait for the UDM REST service to be ready to accept requests."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(f'http://localhost:9979{path}', timeout=2)
            if response.status_code in (200, 401, 406):
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"Service not ready after {timeout} seconds")


def test_root_path_normalization():
    """Test that root_path is normalized correctly for various inputs."""
    test_cases = [
        ('', ''),
        ('  ', ''),
        ('api', '/api'),
        ('/api', '/api'),
        ('//api', '/api'),
        ('api/', '/api'),
        ('/api/', '/api'),
        ('  /api/  ', '/api'),
        ('univention', '/univention'),
        ('/univention', '/univention'),
    ]
    for input_value, expected in test_cases:
        root_path = input_value.strip().strip('/')
        result = f'/{root_path}' if root_path else ''
        assert result == expected, f"Input {input_value!r}: expected {expected!r}, got {result!r}"


def test_root_path_default_direct_access(account):
    """Test that direct access without X-Forwarded-Host uses /udm/ prefix."""
    auth = (account.username, account.bindpw)
    headers = {'Accept': 'application/json'}

    response = requests.get('http://localhost:9979/udm/', headers=headers, auth=auth)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()

    assert '_links' in data
    assert 'udm:ldap-base' in data['_links']
    ldap_base_href = data['_links']['udm:ldap-base'][0]['href']
    assert '/udm/ldap/base/' in ldap_base_href, f"Expected '/udm/ldap/base/' in {ldap_base_href}"
    assert '/univention/' not in ldap_base_href, f"Should not contain '/univention/' in {ldap_base_href}"

    assert 'curies' in data['_links']
    curies_href = data['_links']['curies'][0]['href']
    assert '/udm/relation/' in curies_href, f"Expected '/udm/relation/' in {curies_href}"
    assert '/univention/' not in curies_href, f"Should not contain '/univention/' in {curies_href}"


def test_root_path_default_via_apache_proxy(account):
    """Test that access via Apache proxy adds /univention prefix."""
    auth = (account.username, account.bindpw)
    headers = {'Accept': 'application/json'}

    response = requests.get(f'https://{ucr["ldap/master"]}/univention/udm/', headers=headers, auth=auth, verify=False)  # noqa: S501
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()

    assert '_links' in data
    assert 'udm:ldap-base' in data['_links']
    ldap_base_href = data['_links']['udm:ldap-base'][0]['href']
    assert '/univention/udm/ldap/base/' in ldap_base_href, f"Expected '/univention/udm/ldap/base/' in {ldap_base_href}"

    assert 'curies' in data['_links']
    curies_href = data['_links']['curies'][0]['href']
    assert '/univention/udm/relation/' in curies_href, f"Expected '/univention/udm/relation/' in {curies_href}"


def test_root_path_object_links_via_apache_proxy(account):
    """Test that object links via Apache proxy use the correct /univention prefix."""
    auth = (account.username, account.bindpw)
    headers = {'Accept': 'application/json'}

    response = requests.get(
        f'https://{ucr["ldap/master"]}/univention/udm/users/user/uid=Administrator,cn=users,{ucr["ldap/base"]}',
        headers=headers,
        auth=auth,
        verify=False,  # noqa: S501
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()

    assert '_links' in data
    assert 'self' in data['_links']
    self_href = data['_links']['self'][0]['href']
    assert '/univention/udm/users/user/' in self_href, f"Expected '/univention/udm/users/user/' in {self_href}"

    assert 'type' in data['_links']
    type_href = data['_links']['type'][0]['href']
    assert '/univention/udm/users/user/' in type_href, f"Expected '/univention/udm/users/user/' in {type_href}"

    assert 'curies' in data['_links']
    curies_href = data['_links']['curies'][0]['href']
    assert '/univention/udm/relation/' in curies_href, f"Expected '/univention/udm/relation/' in {curies_href}"


def test_application_root_path_attribute():
    """Test that Application class correctly sets root_path from environment."""
    import os

    original = os.environ.pop('UDM_REST_API_ROOT_PATH', None)
    try:
        app = Application()
        assert app.root_path == '', f"Expected empty root_path, got {app.root_path!r}"
    finally:
        if original is not None:
            os.environ['UDM_REST_API_ROOT_PATH'] = original

    os.environ['UDM_REST_API_ROOT_PATH'] = '/testapi'
    try:
        app = Application()
        assert app.root_path == '/testapi', f"Expected '/testapi', got {app.root_path!r}"
    finally:
        del os.environ['UDM_REST_API_ROOT_PATH']

    os.environ['UDM_REST_API_ROOT_PATH'] = 'testapi'
    try:
        app = Application()
        assert app.root_path == '/testapi', f"Expected '/testapi', got {app.root_path!r}"
    finally:
        del os.environ['UDM_REST_API_ROOT_PATH']

    os.environ['UDM_REST_API_ROOT_PATH'] = '/testapi/'
    try:
        app = Application()
        assert app.root_path == '/testapi', f"Expected '/testapi', got {app.root_path!r}"
    finally:
        del os.environ['UDM_REST_API_ROOT_PATH']


@pytest.mark.slow
def test_root_path_env_var_integration(account):
    """
    Integration test: Restart the service with UDM_REST_API_ROOT_PATH=/univention
    and verify that requests to /univention/udm/ work correctly.

    This simulates the Kubernetes/ingress-nginx scenario where the ingress
    does NOT strip the /univention prefix from the request path.
    """
    auth = (account.username, account.bindpw)
    headers = {'Accept': 'application/json'}

    with service_with_root_path('/univention'):
        response = requests.get('http://localhost:9979/univention/udm/', headers=headers, auth=auth)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()

        assert '_links' in data
        assert 'udm:ldap-base' in data['_links']
        ldap_base_href = data['_links']['udm:ldap-base'][0]['href']
        assert '/univention/udm/ldap/base/' in ldap_base_href, f"Expected '/univention/udm/ldap/base/' in {ldap_base_href}"

        assert 'curies' in data['_links']
        curies_href = data['_links']['curies'][0]['href']
        assert '/univention/udm/relation/' in curies_href, f"Expected '/univention/udm/relation/' in {curies_href}"

        response = requests.get(
            f'http://localhost:9979/univention/udm/users/user/uid=Administrator,cn=users,{ucr["ldap/base"]}',
            headers=headers,
            auth=auth,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()

        assert '_links' in data
        assert 'self' in data['_links']
        self_href = data['_links']['self'][0]['href']
        assert '/univention/udm/users/user/' in self_href, f"Expected '/univention/udm/users/user/' in {self_href}"

        response = requests.get('http://localhost:9979/udm/', headers=headers, auth=auth)
        assert response.status_code == 404, f"Expected 404 for /udm/ when root_path is set, got {response.status_code}"
