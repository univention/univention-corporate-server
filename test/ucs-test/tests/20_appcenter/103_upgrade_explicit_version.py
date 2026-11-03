#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: univention-app upgrade respects an explicitly specified app version
## tags: [basic, coverage, skip_admember]
## bugs: [58543]
## timeout: 900
## packages:
##   - univention-appcenter-dev
## exposure: dangerous

import re
import subprocess

import pytest

from univention.appcenter.actions import get_action
from univention.appcenter.app_cache import Apps
from univention.appcenter.ucr import ucr_get

import appcentertest as app_test


DOCKER_INI = '''DockerImage = docker-test.software-univention.de/httpd:2.4.23-alpine
DockerScriptInit = httpd-foreground
DockerScriptStoreData =
DockerScriptRestoreDataBeforeSetup =
DockerScriptRestoreDataAfterSetup =
DockerScriptSetup =
DockerScriptUpdateAvailable =
DockerScriptUpdateAppVersion = /bin/true
PortsRedirection = 8080:80
WebInterface = /
WebInterfacePortHTTP = 8080
WebInterfacePortHTTPS = 0
AutoModProxy = False
UCSOverviewCategory = False
'''


def build_package(tmp_path, name, version):
    """
    Every version needs its own repository component: WithoutRepository apps
    are seen as installed in all their versions as soon as their packages are.
    """
    root = tmp_path / f'{name}_{version}'
    (root / 'DEBIAN').mkdir(parents=True)
    (root / 'DEBIAN' / 'control').write_text(f'Package: {name}\nVersion: {version}\nArchitecture: all\nMaintainer: ucs-test <ucs-test@example.com>\nDescription: ucs-test package\n')
    deb = tmp_path / f'{name}_{version}_all.deb'
    subprocess.run(['dpkg-deb', '-b', str(root), str(deb)], check=True)
    return str(deb)


def publish(tmp_path, app_id, version, docker):
    ini = f'''[Application]
ID = {app_id}
Code = TV
Name = Upgrade Version Test
Version = {version}
'''
    kwargs = {}
    if docker:
        ini += DOCKER_INI
    else:
        ini += f'License = free\nDefaultPackages = {app_id}-pkg\n'
        kwargs['packages'] = [build_package(tmp_path, f'{app_id}-pkg', version)]
    ini_file = tmp_path / 'app.ini'
    ini_file.write_text(ini)
    component_id = '%s_%s' % (app_id.replace('-', '_'), version.replace('.', '_'))
    get_action('dev-populate-appcenter').call(new=True, ini=str(ini_file), component_id=component_id, **kwargs)


@pytest.fixture(scope='module')
def local_appcenter():
    with app_test.local_appcenter():
        yield


@pytest.fixture
def credentials(tmp_path):
    username = re.match('uid=([^,]*),.*', ucr_get('tests/domainadmin/account')).groups()[0]
    pwdfile = tmp_path / 'password'
    pwdfile.write_text(ucr_get('tests/domainadmin/pwd'))
    return ['--noninteractive', '--username', username, '--pwdfile', str(pwdfile)]


@pytest.fixture(params=[False, True], ids=['package', 'docker'])
def app_with_newer_versions(request, local_appcenter, credentials, tmp_path):
    """Version 1.0 installed, with an older version and the newer versions 2.0 and 3.0 available."""
    docker = request.param
    app_id = 'test-version-docker' if docker else 'test-version-package'
    publish(tmp_path, app_id, '1.0', docker)
    subprocess.run(['apt-get', 'update'], check=True)
    subprocess.run(['univention-app', 'update'], check=True)
    subprocess.run(['univention-app', 'install', *credentials, app_id], check=True)
    try:
        for version in ('0.9', '2.0', '3.0'):
            publish(tmp_path, app_id, version, docker)
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run(['univention-app', 'update'], check=True)
        yield app_id
    finally:
        Apps().clear_cache()
        subprocess.run(['univention-app', 'remove', *credentials, app_id], check=True)


def upgrade(app_string, *options):
    # stdin is closed so that a question for credentials fails instead of blocking
    return subprocess.run(['univention-app', 'upgrade', *options, app_string], check=False, capture_output=True, text=True, stdin=subprocess.DEVNULL)


def installed_version(app_id):
    # not ucr_get: it caches and does not see what the univention-app subprocesses write
    return subprocess.run(['ucr', 'get', f'appcenter/apps/{app_id}/version'], check=True, capture_output=True, text=True).stdout.strip()


def test_explicit_versions(app_with_newer_versions, credentials):
    # A single test, as every upgrade changes the state the next step starts from
    app_id = app_with_newer_versions

    # no credentials: an explicit no-op must not ask for anything
    result = upgrade(f'{app_id}=1.0')
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'already installed' in result.stdout
    assert 'Going to upgrade' not in result.stdout
    assert installed_version(app_id) == '1.0'

    result = upgrade(f'{app_id}=0.9', *credentials)
    assert result.returncode == 1, result.stdout + result.stderr
    assert installed_version(app_id) == '1.0'

    result = upgrade(f'{app_id}=2.0', *credentials)
    assert result.returncode == 0, result.stdout + result.stderr
    assert installed_version(app_id) == '2.0'

    result = upgrade(app_id, *credentials)
    assert result.returncode == 0, result.stdout + result.stderr
    assert installed_version(app_id) == '3.0'
